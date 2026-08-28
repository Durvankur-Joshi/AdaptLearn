# backend/learning_engine/question_generator.py
"""
Question Generator for AdaptiveLearning.

Multi-Provider Architecture:
1. Primary Provider: Groq (default model: llama-3.1-8b-instant, configurable via GROQ_MODEL).
2. Fallback Provider: Google Gemini (default model: gemini-2.5-flash, configurable via GEMINI_MODEL).
3. Provider Sequence: Groq (max 2 attempts) -> Gemini (max 2 attempts) -> controlled HTTP 503.
4. Smart Error Classification: Permanent errors (404 model_not_found, 401/403 auth) immediately
   switch to Gemini without wasted retries. Transient errors receive 1 retry before fallback.
5. Missing Question Handoff: If Groq produces a partial set of valid novel questions, Gemini
   is prompted only for the remaining missing questions.
6. Zero Static Fallback: Deterministic static question generation is completely eliminated.
7. Backend Option Shuffling & Balancing: Programmatically randomizes option positions across
   A, B, C, D to permanently eliminate Option A bias while strictly preserving correct_index mapping.
8. Shared Strict Validation & Lightweight Deduplication: Both providers pass through the exact
   same candidate validation and Jaccard/SequenceMatcher novelty gating.
"""

import difflib
import json
import logging
import os
import random
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from django.conf import settings
from google import genai
from google.genai import types as genai_types
from groq import Groq

# Structured logger for question generation pipeline
logger = logging.getLogger('learning_engine.question_generator')

# =====================================================================
# Custom Exceptions
# =====================================================================

class QuestionGenerationError(Exception):
    """Raised when question generation fails after all provider attempts."""
    pass


# =====================================================================
# Configuration Constants
# =====================================================================
# Threshold above which two questions are considered duplicates (0.0 to 1.0)
QUESTION_SIMILARITY_THRESHOLD = 0.72

# Bounded provider attempts
GROQ_MAX_ATTEMPTS = 2
GEMINI_MAX_ATTEMPTS = 2

# Moderate generation temperature for controlled creativity and diversity
DEFAULT_GENERATION_TEMPERATURE = 0.7

# Common stopwords to ignore when comparing semantic content
STOPWORDS: Set[str] = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'about', 'against',
    'between', 'into', 'through', 'during', 'before', 'after', 'above',
    'below', 'from', 'up', 'down', 'out', 'off', 'over', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
    'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
    'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now',
    'which', 'what', 'who', 'whom', 'this', 'that', 'these', 'those',
    'following', 'statement', 'best', 'describes', 'defined', 'correct',
    'true', 'false', 'primary', 'main', 'purpose'
}


# =====================================================================
# Lightweight Novelty & Similarity Detection Engine (Pure Python)
# =====================================================================

def normalize_question_text(text: str) -> str:
    """
    Normalize question text for comparison:
    - Lowercase
    - Strip punctuation
    - Collapse extra whitespace
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', ' ', text)
    words = text.split()
    return ' '.join(words)


def get_significant_tokens(text: str) -> Set[str]:
    """Extract significant content words excluding stopwords and single letters."""
    norm = normalize_question_text(text)
    return {w for w in norm.split() if w not in STOPWORDS and len(w) > 2}


def get_ngrams(words: List[str], n: int = 2) -> Set[Tuple[str, ...]]:
    """Extract word n-grams from a word list."""
    if len(words) < n:
        return set()
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def calculate_question_similarity(q1_text: str, q2_text: str) -> float:
    """
    Calculate lightweight hybrid similarity between two question texts.
    Combines:
    1. SequenceMatcher ratio (structural sequence match)
    2. Significant token Jaccard similarity (overlap of key concept terms)
    3. Word bigram Jaccard similarity (local phrase structure overlap)
    """
    n1 = normalize_question_text(q1_text)
    n2 = normalize_question_text(q2_text)

    if not n1 or not n2:
        return 0.0

    if n1 == n2:
        return 1.0

    # 1. Structural sequence ratio
    seq_ratio = difflib.SequenceMatcher(None, n1, n2).ratio()

    # 2. Significant token Jaccard
    tokens1 = get_significant_tokens(q1_text)
    tokens2 = get_significant_tokens(q2_text)
    if tokens1 and tokens2:
        token_jaccard = len(tokens1 & tokens2) / len(tokens1 | tokens2)
    else:
        words1 = set(n1.split())
        words2 = set(n2.split())
        token_jaccard = len(words1 & words2) / max(1, len(words1 | words2))

    # 3. Bigram Jaccard
    w1 = n1.split()
    w2 = n2.split()
    bg1 = get_ngrams(w1, 2)
    bg2 = get_ngrams(w2, 2)
    if bg1 and bg2:
        bg_jaccard = len(bg1 & bg2) / len(bg1 | bg2)
    else:
        bg_jaccard = 0.0

    # Composite similarity favoring sequence structure and core concept tokens
    composite = 0.45 * seq_ratio + 0.40 * token_jaccard + 0.15 * bg_jaccard
    combined_score = max(seq_ratio, composite)
    return round(float(combined_score), 4)


def is_novel_question(
    candidate_q: Union[Dict, str],
    history: List[Union[Dict, str]],
    threshold: float = QUESTION_SIMILARITY_THRESHOLD
) -> Tuple[bool, float, Optional[str]]:
    """
    Check if a candidate question is sufficiently novel compared to previously asked questions.
    Returns: (is_novel: bool, max_similarity: float, most_similar_question: Optional[str])
    """
    cand_text = candidate_q.get('question', '') if isinstance(candidate_q, dict) else str(candidate_q)
    cand_text = cand_text.strip()
    if not cand_text:
        return False, 1.0, "Empty question text"

    max_sim = 0.0
    most_similar = None

    for prev in history:
        prev_text = prev.get('question', '') if isinstance(prev, dict) else str(prev)
        prev_text = prev_text.strip()
        if not prev_text:
            continue
        sim = calculate_question_similarity(cand_text, prev_text)
        if sim > max_sim:
            max_sim = sim
            most_similar = prev_text
        if sim >= threshold:
            return False, sim, prev_text

    return True, max_sim, most_similar


def _validate_single_question(q: Any) -> Optional[Dict]:
    """
    Strict validation and sanitization for a single candidate question.
    Returns the sanitized dict if valid, or None if invalid.
    Rejects candidate if correct_index is invalid or missing (NEVER defaults to 0).
    """
    if not isinstance(q, dict):
        return None

    question_text = str(q.get('question', '')).strip()
    word_count = len(question_text.split())
    if not question_text or word_count < 4 or word_count > 60:
        return None

    opts = q.get('options')
    if not isinstance(opts, list) or len(opts) != 4:
        return None

    cleaned_opts = [str(o).strip() for o in opts]
    if any(len(o) == 0 for o in cleaned_opts):
        return None
    if len(set(cleaned_opts)) != 4:
        return None  # Rejects duplicate options within the same question

    ci = q.get('correct_index')
    if ci is None:
        return None

    try:
        ci_int = int(ci)
    except (TypeError, ValueError):
        return None

    if ci_int not in (0, 1, 2, 3):
        return None

    diff = str(q.get('difficulty', 'medium')).lower()
    if diff not in ('easy', 'medium', 'hard'):
        diff = 'medium'

    cog = str(q.get('cognitive_operation', 'apply')).lower()
    if cog not in ('recall', 'apply', 'analyze'):
        cog = 'apply'

    est_time = q.get('estimated_time', 60)
    try:
        est_time = int(est_time)
        if est_time <= 0:
            est_time = 60
    except (TypeError, ValueError):
        est_time = 60

    return {
        'difficulty': diff,
        'cognitive_operation': cog,
        'estimated_time': est_time,
        'question': question_text,
        'options': cleaned_opts,
        'correct_index': ci_int
    }


def shuffle_and_balance_options(questions: List[Dict]) -> List[Dict]:
    """
    Shuffles question options and balances the correct answer position across A, B, C, D.
    Ensures:
    1. Correct answer does NOT cluster on Option A (0).
    2. Correct answer positions are evenly distributed across the batch.
    3. Position sequence remains non-predictable (randomized permutations).
    4. Mapping between correct answer string and correct_index is strictly preserved.
    """
    if not questions:
        return []

    n = len(questions)
    base_pool = [0, 1, 2, 3]
    target_positions = []
    while len(target_positions) < n:
        perm = base_pool.copy()
        random.shuffle(perm)
        target_positions.extend(perm)
    target_positions = target_positions[:n]

    processed_questions = []
    for i, q in enumerate(questions):
        orig_options = q.get('options', [])
        orig_ci = q.get('correct_index')

        if not isinstance(orig_options, list) or len(orig_options) != 4 or orig_ci not in (0, 1, 2, 3):
            processed_questions.append(q)
            continue

        target_ci = target_positions[i]
        correct_text = orig_options[orig_ci]
        incorrect_options = [opt for idx, opt in enumerate(orig_options) if idx != orig_ci]
        random.shuffle(incorrect_options)

        # Place correct_text at target_ci, and incorrect_options in the remaining 3 slots
        new_options = [None] * 4
        new_options[target_ci] = correct_text

        inc_idx = 0
        for slot in range(4):
            if slot != target_ci:
                new_options[slot] = incorrect_options[inc_idx]
                inc_idx += 1

        # Create updated copy of question dict
        q_copy = dict(q)
        q_copy['options'] = new_options
        q_copy['correct_index'] = target_ci

        # Verification assertion to guarantee integrity
        assert q_copy['options'][q_copy['correct_index']] == correct_text, "Option shuffle corrupted correct_index mapping!"
        processed_questions.append(q_copy)

    return processed_questions


# =====================================================================
# AI Provider Abstraction
# =====================================================================

class BaseQuestionProvider:
    """Base interface for question generation AI providers."""
    provider_name: str = "Base"
    model_name: str = ""

    def is_permanent_error(self, err: Exception) -> bool:
        """Return True if error should not be retried on this provider."""
        return False

    def generate_candidate_questions(
        self,
        prompt: str,
        needed_count: int,
        temperature: float = DEFAULT_GENERATION_TEMPERATURE
    ) -> List[Dict]:
        """Generate raw candidate question dicts from AI."""
        raise NotImplementedError


def safe_parse_json_questions(raw_text: str) -> List[Dict]:
    """Robust parser for LLM JSON outputs handling markdown fences, trailing commas, truncation, and formatting variations."""
    if not raw_text or not raw_text.strip():
        return []

    text = raw_text.strip()
    if text.startswith("```"):
        lines = [ln.rstrip() for ln in text.splitlines()]
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()

    # Attempt 1: Direct parse
    try:
        cleaned_text = re.sub(r'[\x00-\x1f\x7f]', lambda m: ' ' if m.group() in ('\n', '\r', '\t') else '', text)
        parsed = json.loads(cleaned_text.strip())
        if isinstance(parsed, dict):
            return parsed.get("questions", [])
        elif isinstance(parsed, list):
            return parsed
    except Exception:
        pass

    # Attempt 2: Extract JSON substring via regex
    match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
    if match:
        extracted = match.group(1).strip()
        cleaned_extracted = re.sub(r'[\x00-\x1f\x7f]', lambda m: ' ' if m.group() in ('\n', '\r', '\t') else '', extracted)
        try:
            parsed = json.loads(cleaned_extracted)
            if isinstance(parsed, dict):
                return parsed.get("questions", [])
            elif isinstance(parsed, list):
                return parsed
        except Exception:
            # Clean trailing commas
            cleaned_commas = re.sub(r',\s*([\]\}])', r'\1', cleaned_extracted)
            try:
                parsed = json.loads(cleaned_commas)
                if isinstance(parsed, dict):
                    return parsed.get("questions", [])
                elif isinstance(parsed, list):
                    return parsed
            except Exception:
                pass

    # Attempt 3: If JSON was slightly truncated at the end, attempt auto-closing
    if '"questions"' in text:
        last_obj_idx = text.rfind('}')
        if last_obj_idx != -1:
            truncated_valid = text[:last_obj_idx + 1] + '\n]}'
            try:
                q_start = truncated_valid.find('{')
                if q_start != -1:
                    clean_trunc = re.sub(r'[\x00-\x1f\x7f]', lambda m: ' ' if m.group() in ('\n', '\r', '\t') else '', truncated_valid[q_start:])
                    clean_trunc = re.sub(r',\s*([\]\}])', r'\1', clean_trunc)
                    parsed = json.loads(clean_trunc)
                    if isinstance(parsed, dict):
                        return parsed.get("questions", [])
            except Exception:
                pass

    logger.warning(f"safe_parse_json_questions failed to parse raw text ({len(raw_text)} chars): {repr(raw_text)}")
    return []


class GroqQuestionProvider(BaseQuestionProvider):
    """Primary question provider using Groq API."""
    provider_name: str = "Groq"

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'GROQ_API_KEY', '') or os.getenv('GROQ_API_KEY', '')
        self.model_name = model_name or getattr(settings, 'GROQ_MODEL', '') or os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def is_permanent_error(self, err: Exception) -> bool:
        err_str = str(err).lower()
        if "model_not_found" in err_str or "does not exist" in err_str or "404" in err_str:
            return True
        if "invalid_api_key" in err_str or "authentication" in err_str or "401" in err_str or "403" in err_str:
            return True
        return False

    def generate_candidate_questions(
        self,
        prompt: str,
        needed_count: int,
        temperature: float = DEFAULT_GENERATION_TEMPERATURE
    ) -> List[Dict]:
        if not self.client:
            raise QuestionGenerationError("Groq client is not configured (missing GROQ_API_KEY).")

        max_tokens = min(4096, max(2048, 1024 * needed_count))
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )

        raw_text = response.choices[0].message.content or ""
        return safe_parse_json_questions(raw_text)


class GeminiQuestionProvider(BaseQuestionProvider):
    """Fallback question provider using Google Gemini API."""
    provider_name: str = "Gemini"

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = (
            api_key or
            getattr(settings, 'GEMINI_API_KEY', '') or
            getattr(settings, 'GOOGLE_API_KEY', '') or
            os.getenv('GEMINI_API_KEY', '') or
            os.getenv('GOOGLE_API_KEY', '')
        )
        self.model_name = model_name or getattr(settings, 'GEMINI_MODEL', '') or os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def is_permanent_error(self, err: Exception) -> bool:
        err_str = str(err).lower()
        if "not_found" in err_str or "404" in err_str or "no longer available" in err_str:
            return True
        if "api_key_invalid" in err_str or "permission_denied" in err_str or "401" in err_str or "403" in err_str:
            return True
        return False

    def generate_candidate_questions(
        self,
        prompt: str,
        needed_count: int,
        temperature: float = DEFAULT_GENERATION_TEMPERATURE
    ) -> List[Dict]:
        if not self.client:
            raise QuestionGenerationError("Gemini client is not configured (missing GEMINI_API_KEY / GOOGLE_API_KEY).")

        max_tokens = min(4096, max(2048, 1024 * needed_count))
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )

        raw_text = response.text or ""
        return safe_parse_json_questions(raw_text)


# =====================================================================
# Main QuestionGenerator Class (Multi-Provider Orchestration)
# =====================================================================

class QuestionGenerator:
    """Orchestrates multi-provider question generation (Groq Primary -> Gemini Fallback)."""

    def __init__(
        self,
        groq_provider: Optional[GroqQuestionProvider] = None,
        gemini_provider: Optional[GeminiQuestionProvider] = None
    ):
        self.groq_provider = groq_provider or GroqQuestionProvider()
        self.gemini_provider = gemini_provider or GeminiQuestionProvider()

    @staticmethod
    def _validate_questions(questions: list) -> list:
        """Validate and sanitize AI-generated questions list."""
        validated = []
        for q in questions:
            sanitized = _validate_single_question(q)
            if sanitized:
                validated.append(sanitized)
        return validated

    def _execute_multi_provider_pipeline(
        self,
        build_prompt_fn,
        total_needed: int,
        need_easy: int,
        need_medium: int,
        need_hard: int,
        history_pool: List[Union[Dict, str]]
    ) -> List[Dict]:
        """
        Generic multi-provider execution engine:
        1. Try Groq provider (up to GROQ_MAX_ATTEMPTS).
        2. If Groq encounters permanent error, immediately switch to Gemini.
        3. If Groq produces fewer than total_needed, call Gemini for remaining count.
        4. Try Gemini provider (up to GEMINI_MAX_ATTEMPTS).
        5. If still fewer than total_needed, raise QuestionGenerationError (NO static fallback).
        6. Apply backend option shuffling & balancing across A/B/C/D.
        """
        accepted_questions: List[Dict] = []
        remaining_easy = need_easy
        remaining_medium = need_medium
        remaining_hard = need_hard

        def _process_candidates(candidates: List[Dict], provider_name: str):
            nonlocal remaining_easy, remaining_medium, remaining_hard
            for candidate in candidates:
                sanitized = _validate_single_question(candidate)
                if not sanitized:
                    logger.warning(f"QUALITY_GATE [{provider_name}]: Candidate rejected due to schema/validation failure: {candidate}")
                    continue

                is_novel, sim_score, matched_q = is_novel_question(sanitized, history_pool)
                if not is_novel:
                    logger.info(
                        f"NOVELTY_GATE [{provider_name}]: Duplicate rejected (sim={sim_score:.3f} >= {QUESTION_SIMILARITY_THRESHOLD}) "
                        f"matched: '{matched_q}' | candidate: '{sanitized['question']}'"
                    )
                    continue

                logger.info(f"NOVELTY_GATE [{provider_name}]: Accepted novel candidate (max_sim={sim_score:.3f}): '{sanitized['question']}'")
                accepted_questions.append(sanitized)
                history_pool.append(sanitized)

                cand_diff = sanitized.get('difficulty', 'medium')
                if cand_diff == 'easy' and remaining_easy > 0:
                    remaining_easy -= 1
                elif cand_diff == 'hard' and remaining_hard > 0:
                    remaining_hard -= 1
                elif remaining_medium > 0:
                    remaining_medium -= 1
                elif remaining_easy > 0:
                    remaining_easy -= 1
                elif remaining_hard > 0:
                    remaining_hard -= 1

                if len(accepted_questions) >= total_needed:
                    break

        # ==========================================
        # Phase 1: Primary Provider (Groq)
        # ==========================================
        logger.info(f"Question generation started. Provider=Groq, Model={self.groq_provider.model_name}")
        for attempt in range(1, GROQ_MAX_ATTEMPTS + 1):
            needed_now = total_needed - len(accepted_questions)
            if needed_now <= 0:
                break

            logger.info(f"Groq Attempt {attempt}/{GROQ_MAX_ATTEMPTS} requesting {needed_now} question(s)")
            prompt = build_prompt_fn(needed_now, remaining_easy, remaining_medium, remaining_hard, history_pool)

            try:
                candidates = self.groq_provider.generate_candidate_questions(
                    prompt=prompt,
                    needed_count=needed_now,
                    temperature=DEFAULT_GENERATION_TEMPERATURE
                )
                _process_candidates(candidates, "Groq")
                if len(accepted_questions) >= total_needed:
                    logger.info(f"Groq generation succeeded. Accepted: {len(accepted_questions)}/{total_needed}")
                    break
            except Exception as e:
                is_perm = self.groq_provider.is_permanent_error(e)
                logger.warning(f"Groq generation attempt {attempt} failed: {e} (permanent={is_perm})")
                if is_perm:
                    logger.info("Groq encountered permanent error; immediately switching to Gemini fallback.")
                    break
                if attempt == GROQ_MAX_ATTEMPTS:
                    logger.info("Groq exhausted retries; switching to Gemini fallback.")

        # ==========================================
        # Phase 2: Fallback Provider (Gemini)
        # ==========================================
        if len(accepted_questions) < total_needed:
            missing_count = total_needed - len(accepted_questions)
            logger.info(f"Switching provider: Gemini (Model={self.gemini_provider.model_name}) for {missing_count} missing question(s)")

            for attempt in range(1, GEMINI_MAX_ATTEMPTS + 1):
                needed_now = total_needed - len(accepted_questions)
                if needed_now <= 0:
                    break

                logger.info(f"Gemini Attempt {attempt}/{GEMINI_MAX_ATTEMPTS} requesting {needed_now} question(s)")
                prompt = build_prompt_fn(needed_now, remaining_easy, remaining_medium, remaining_hard, history_pool)

                try:
                    candidates = self.gemini_provider.generate_candidate_questions(
                        prompt=prompt,
                        needed_count=needed_now,
                        temperature=DEFAULT_GENERATION_TEMPERATURE
                    )
                    _process_candidates(candidates, "Gemini")
                    if len(accepted_questions) >= total_needed:
                        logger.info(f"Gemini generation succeeded. Accepted: {len(accepted_questions)}/{total_needed}")
                        break
                except Exception as e:
                    is_perm = self.gemini_provider.is_permanent_error(e)
                    logger.warning(f"Gemini generation attempt {attempt} failed: {e} (permanent={is_perm})")
                    if is_perm:
                        logger.error("Gemini encountered permanent error; terminating generation pipeline.")
                        break

        # ==========================================
        # Phase 3: Evaluation & Shuffling (No Static Fallback)
        # ==========================================
        if len(accepted_questions) < total_needed:
            logger.error(
                f"Both Groq and Gemini failed to produce {total_needed} questions. "
                f"Generated only {len(accepted_questions)}/{total_needed}. Raising QuestionGenerationError."
            )
            raise QuestionGenerationError(
                f"Question generation failed after trying Groq and Gemini. Produced {len(accepted_questions)}/{total_needed}."
            )

        final_batch = accepted_questions[:total_needed]
        balanced_batch = shuffle_and_balance_options(final_batch)
        logger.info(f"Question generation completed successfully. Returning {len(balanced_batch)} novel, position-balanced questions.")
        return balanced_batch

    def generate_questions_from_teaching(
        self,
        subject: str,
        concept: str,
        atom: str,
        teaching_content: Dict,
        need_easy: int = 1,
        need_medium: int = 2,
        need_hard: int = 0,
        knowledge_level: str = 'intermediate',
        previous_questions: Optional[List[Union[Dict, str]]] = None
    ) -> List[Dict]:
        """
        Generate novel assessment questions based on teaching content using Groq -> Gemini fallback.
        """
        total_needed = need_easy + need_medium + need_hard
        if total_needed <= 0:
            return []

        history_pool: List[Union[Dict, str]] = list(previous_questions or [])
        explanation = teaching_content.get('explanation', '') if teaching_content else ''
        analogy = teaching_content.get('analogy', '') if teaching_content else ''
        examples = teaching_content.get('examples', []) if teaching_content else []
        examples_text = "\n".join([f"- {ex}" for ex in examples if ex])

        def build_teaching_prompt(needed_count: int, rem_easy: int, rem_med: int, rem_hard: int, pool: List[Union[Dict, str]]) -> str:
            recent_history = pool[-10:]
            history_lines = []
            for idx, q in enumerate(recent_history, start=1):
                q_text = q.get('question', '') if isinstance(q, dict) else str(q)
                if q_text.strip():
                    history_lines.append(f"{idx}. {q_text.strip()}")

            history_section = ""
            if history_lines:
                history_section = f"""
PREVIOUSLY ASKED QUESTIONS (CRITICAL: DO NOT REPEAT OR REWORD THESE):
{chr(10).join(history_lines)}

QUESTION NOVELTY REQUIREMENT:
The new question must differ conceptually from all previous questions supplied above.
- Do NOT repeat any previous question.
- Do NOT produce a lightly reworded or synonym-swapped version of a previous question.
- Avoid repeating the same scenario, numerical values, option structure, or reasoning path.
- Test the atomic concept "{atom}" from a DIFFERENT pedagogical angle (e.g. application scenario, prediction, comparison, cause & effect, troubleshooting, misconception).
"""

            return f"""
You are an experienced teacher creating conceptual assessment questions to evaluate deep student understanding.

Subject: {subject}
Concept: {concept}
Atomic Concept: {atom}
Student Level: {knowledge_level.upper()}

TEACHING CONTENT SHOWN TO STUDENT:
Explanation:
{explanation}

Analogy:
{analogy}

Examples/Applications:
{examples_text}

{history_section}

TASK:
Generate EXACTLY {needed_count} multiple-choice question(s) testing conceptual understanding of "{atom}".

DIFFICULTY REQUIREMENTS:
- Easy count: {rem_easy}
- Medium count: {rem_med}
- Hard count: {rem_hard}

CRITICAL RULES:
1. Ground every question strictly in the provided teaching content.
2. DO NOT ask questions about the analogy itself or trivia from the examples.
3. Instead, create NEW conceptual situations where the student must APPLY the concept.
4. Intentionally vary question angles across:
   - Application & real-world scenario
   - Prediction / outcome analysis
   - Cause and effect
   - Comparison / distinction
   - Misconception detection
   - Troubleshooting / system behavior
5. Question length: 14 to 40 words.
6. Exactly 4 plausible, believable options.
7. Exactly one correct option. "correct_index" MUST be an integer (0, 1, 2, or 3) indicating which option is correct.
8. Output STRICT JSON ONLY matching the schema.

OUTPUT FORMAT:
{{
    "questions": [
        {{
            "difficulty": "easy|medium|hard",
            "cognitive_operation": "recall|apply|analyze",
            "estimated_time": 45,
            "question": "Question text here?",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "correct_index": 0
        }}
    ]
}}
"""

        return self._execute_multi_provider_pipeline(
            build_prompt_fn=build_teaching_prompt,
            total_needed=total_needed,
            need_easy=need_easy,
            need_medium=need_medium,
            need_hard=need_hard,
            history_pool=history_pool
        )

    def generate_questions(
        self,
        subject: str,
        concept: str,
        atom: str,
        target_difficulty: str,
        count: int,
        knowledge_level: str = 'intermediate',
        error_focus: List[str] = None,
        previous_questions: Optional[List[Union[Dict, str]]] = None
    ) -> List[Dict]:
        """
        Generate questions for an atom with dynamic difficulty using Groq -> Gemini fallback.
        """
        if count <= 0:
            return []

        history_pool: List[Union[Dict, str]] = list(previous_questions or [])

        level_adjustments = {
            'zero': {'cognitive': ['recall'], 'time_factor': 1.5, 'complexity': 'very simple, foundational', 'hint_level': 'detailed'},
            'beginner': {'cognitive': ['recall', 'apply'], 'time_factor': 1.2, 'complexity': 'straightforward', 'hint_level': 'clear'},
            'intermediate': {'cognitive': ['recall', 'apply', 'analyze'], 'time_factor': 1.0, 'complexity': 'moderate', 'hint_level': 'moderate'},
            'advanced': {'cognitive': ['apply', 'analyze'], 'time_factor': 0.8, 'complexity': 'challenging', 'hint_level': 'subtle'}
        }
        adj = level_adjustments.get(knowledge_level, level_adjustments['intermediate'])

        if target_difficulty == 'easy':
            allowed_cognitive = ['recall']
            easy_c, med_c, hard_c = count, 0, 0
        elif target_difficulty == 'medium':
            allowed_cognitive = ['recall', 'apply']
            easy_c, med_c, hard_c = 0, count, 0
        else:
            allowed_cognitive = ['apply', 'analyze']
            easy_c, med_c, hard_c = 0, 0, count

        error_context = ""
        if error_focus:
            error_context = f"\nFocus on addressing these common errors: {', '.join(error_focus)}\n"

        def build_dynamic_prompt(needed_count: int, rem_easy: int, rem_med: int, rem_hard: int, pool: List[Union[Dict, str]]) -> str:
            history_lines = [f"- {q.get('question', str(q))}" for q in pool[-10:] if str(q).strip()]
            history_sec = ""
            if history_lines:
                history_sec = f"PREVIOUS QUESTIONS (DO NOT DUPLICATE):\n" + "\n".join(history_lines) + "\n"

            return f"""
You are an experienced teacher creating conceptual assessment questions to evaluate deep student understanding.

Subject: {subject}
Concept: {concept}
Atomic Concept: {atom}
Student Level: {knowledge_level.upper()}
Target Difficulty: {target_difficulty.upper()}

Generate EXACTLY {needed_count} {target_difficulty} question(s) with these characteristics:
- Complexity: {adj['complexity']}
- Cognitive levels: {', '.join(allowed_cognitive)}
- Hint level: {adj['hint_level']}

{error_context}
{history_sec}

CRITICAL QUALITY REQUIREMENTS:
- Test CONCEPTUAL UNDERSTANDING, application, or reasoning — NOT simple definition recall.
- Avoid obvious or trivial keyword matching.
- Each question must have exactly 4 plausible options in the same conceptual category.
- Exactly one correct option. "correct_index" must be an integer (0, 1, 2, or 3).
- Output STRICT JSON ONLY.

OUTPUT FORMAT:
{{
    "questions": [
        {{
            "difficulty": "{target_difficulty}",
            "cognitive_operation": "{allowed_cognitive[0]}",
            "estimated_time": 45,
            "question": "Question text here?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_index": 0
        }}
    ]
}}
"""

        return self._execute_multi_provider_pipeline(
            build_prompt_fn=build_dynamic_prompt,
            total_needed=count,
            need_easy=easy_c,
            need_medium=med_c,
            need_hard=hard_c,
            history_pool=history_pool
        )

    def generate_initial_quiz(
        self,
        subject: str,
        concept: str,
        knowledge_level: str = 'intermediate',
        count: int = 5,
        previous_questions: Optional[List[Union[Dict, str]]] = None
    ) -> List[Dict]:
        """Diagnostic quiz based on subject/concept/knowledge level with Groq -> Gemini fallback."""
        easy_count = max(1, count // 2)
        medium_count = max(0, count - easy_count)

        questions = []
        questions.extend(self.generate_questions(
            subject=subject,
            concept=concept,
            atom=concept,
            target_difficulty='easy',
            count=easy_count,
            knowledge_level=knowledge_level,
            previous_questions=previous_questions
        ))
        if medium_count > 0:
            medium_prev = list(previous_questions or []) + questions
            questions.extend(self.generate_questions(
                subject=subject,
                concept=concept,
                atom=concept,
                target_difficulty='medium',
                count=medium_count,
                knowledge_level=knowledge_level,
                previous_questions=medium_prev
            ))

        return questions

    def generate_atoms(self, subject: str, concept: str) -> List[str]:
        """Generate atomic concepts using Gemini."""
        client = getattr(self.gemini_provider, 'client', None)
        if not client:
            logger.info("Gemini client not available, using fallback atoms")
            return self._get_fallback_atoms(subject, concept)

        prompt = f"""
        You are a master curriculum designer and senior educator with over 30 years of classroom teaching experience, specializing in breaking down subjects into precise, teachable, and assessable atomic learning units.

        Your task is to generate atomic sub-concepts ("atoms") for curriculum design.

        Subject: {subject}
        Concept: {concept}

        Your atoms must reflect how an expert teacher would naturally divide this concept for step-by-step teaching, assessment, and mastery tracking in a real classroom.

        PEDAGOGICAL REQUIREMENTS:
        1. Each atom must represent ONE distinct, teachable knowledge unit that can be:
        * Explained independently
        * Taught in a short lesson (5–15 minutes)
        * Assessed with 1–3 focused questions

        2. All atoms must be at the SAME pedagogical level:
        * Do NOT mix beginner and advanced units
        * Do NOT mix theory and applications

        3. Atoms must be mutually exclusive (no overlap).
        4. Generate EXACTLY 4 to 6 atoms.
        5. Each atom must be a noun or noun phrase (maximum 4 words).

        Output STRICT JSON only:
        {{
        "atoms": [
        "Atom 1",
        "Atom 2",
        "Atom 3",
        "Atom 4"
        ]
        }}
        """

        try:
            response = client.models.generate_content(
                model=self.gemini_provider.model_name,
                contents=prompt,
                config=genai_types.GenerateContentConfig(response_mime_type="application/json")
            )
            raw = response.text or ""
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            parsed = json.loads(raw.strip())
            atoms = parsed.get("atoms", [])
            if len(atoms) < 4 or len(atoms) > 6:
                return self._get_fallback_atoms(subject, concept)
            return atoms
        except Exception as e:
            logger.error(f"Error generating atoms via Gemini: {e}")
            return self._get_fallback_atoms(subject, concept)

    def _get_fallback_atoms(self, subject: str, concept: str) -> List[str]:
        """Provide fallback curriculum atoms when AI atom generation fails."""
        fallbacks = {
            "Memory Organization": ["Address Space", "Memory Hierarchy", "Cache Memory", "RAM vs ROM", "Memory Mapping"],
            "Address Space": ["Address Lines", "Memory Locations", "Address Decoding", "Word Size", "Byte Addressing"],
            "Cache Memory": ["Cache Levels", "Cache Hit/Miss", "Cache Mapping", "Replacement Policy", "Write Policy"],
            "Arrays": ["Array Declaration", "Index Access", "Contiguous Memory", "Insertion and Deletion", "Traversal"]
        }
        for key, atoms in fallbacks.items():
            if key.lower() in concept.lower():
                return atoms

        return [
            f"{concept} Basics",
            f"{concept} Structure",
            f"{concept} Operations",
            f"{concept} Applications",
            f"{concept} Limitations"
        ]

    def generate_concept_overview(self, subject: str, concept: str, atoms: List[str]) -> Dict:
        """Generate overview for zero-knowledge students."""
        atoms_text = "\n".join([f"  {i+1}. {a}" for i, a in enumerate(atoms)])

        prompt = f"""
You are creating a SHORT, beginner-friendly overview for a student who has ZERO prior knowledge.

Subject: {subject}
Concept: {concept}
Atomic sub-topics:
{atoms_text}

Generate a JSON overview with these keys:
1. "overview" — 3-5 sentences explaining what this concept is about in the simplest possible language.
2. "why_it_matters" — 2-3 sentences on why this concept matters in real life.
3. "what_you_will_learn" — Array of short strings (one per atom).
4. "key_terms" — Array of objects with "term" and "simple_definition".
5. "encouragement" — One motivational sentence for a beginner.

Return STRICT JSON only.
{{
  "overview": "...",
  "why_it_matters": "...",
  "what_you_will_learn": ["...", "..."],
  "key_terms": [{{"term": "...", "simple_definition": "..."}}],
  "encouragement": "..."
}}
"""
        # Try Groq first, then Gemini
        for provider in [self.groq_provider, self.gemini_provider]:
            if not getattr(provider, 'client', None):
                continue
            try:
                if isinstance(provider, GroqQuestionProvider):
                    resp = provider.client.chat.completions.create(
                        model=provider.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.4,
                        max_tokens=1024,
                        response_format={"type": "json_object"}
                    )
                    raw = resp.choices[0].message.content or ""
                else:
                    resp = provider.client.models.generate_content(
                        model=provider.model_name,
                        contents=prompt,
                        config=genai_types.GenerateContentConfig(response_mime_type="application/json")
                    )
                    raw = resp.text or ""

                if "```" in raw:
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                raw = re.sub(r'[\x00-\x1f\x7f]', lambda m: ' ' if m.group() in ('\n', '\r', '\t') else '', raw)
                return json.loads(raw.strip())
            except Exception as e:
                logger.warning(f"Error in generate_concept_overview with {provider.provider_name}: {e}")

        return {
            "overview": f"{concept} is a fundamental topic in {subject}. It covers several important ideas that build on each other.",
            "why_it_matters": f"Understanding {concept} will help you grasp core principles of {subject} and apply them in practice.",
            "what_you_will_learn": [f"You will learn about {a}" for a in atoms],
            "key_terms": [{"term": a, "simple_definition": f"A key part of {concept}"} for a in atoms[:4]],
            "encouragement": "Every expert was once a beginner. Let's start this journey together!"
        }

    def generate_atom_summary(
        self,
        subject: str,
        concept: str,
        atom_name: str,
        teaching_content: Dict,
        mastery_score: float,
        error_types: List[str] = None
    ) -> Dict:
        """Generate concise summary after atom completion."""
        explanation = teaching_content.get('explanation', '') if teaching_content else ''
        analogy = teaching_content.get('analogy', '') if teaching_content else ''

        error_context = ""
        if error_types:
            from collections import Counter
            err_counts = Counter(error_types)
            error_context = f"\nThe student made these types of errors: {dict(err_counts)}. Address the most common ones in your tips."

        mastery_label = "low" if mastery_score < 0.5 else "moderate" if mastery_score < 0.75 else "high"

        prompt = f"""
You are summarizing an atomic concept that a student just finished learning.

Subject: {subject}
Concept: {concept}
Atom: {atom_name}
Mastery: {mastery_score:.0%} ({mastery_label})

Teaching content shown:
Explanation: {explanation[:500]}
Analogy: {analogy[:200]}
{error_context}

Generate a concise review summary as JSON:
1. "summary" — 2-3 sentence recap of the core idea.
2. "quick_notes" — Array of 3-5 bullet-point strings.
3. "must_remember" — Array of 2-3 strings: the absolute essentials.
4. "common_pitfalls" — Array of 1-3 strings.
5. "suggestions" — Array of 1-3 strings.
6. "confidence_boost" — One short motivational line.

Return STRICT JSON only.
"""
        for provider in [self.groq_provider, self.gemini_provider]:
            if not getattr(provider, 'client', None):
                continue
            try:
                if isinstance(provider, GroqQuestionProvider):
                    resp = provider.client.chat.completions.create(
                        model=provider.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=800,
                        response_format={"type": "json_object"}
                    )
                    raw = resp.choices[0].message.content or ""
                else:
                    resp = provider.client.models.generate_content(
                        model=provider.model_name,
                        contents=prompt,
                        config=genai_types.GenerateContentConfig(response_mime_type="application/json")
                    )
                    raw = resp.text or ""

                if "```" in raw:
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                raw = re.sub(r'[\x00-\x1f\x7f]', lambda m: ' ' if m.group() in ('\n', '\r', '\t') else '', raw)
                return json.loads(raw.strip())
            except Exception as e:
                logger.warning(f"Error in generate_atom_summary with {provider.provider_name}: {e}")

        if mastery_score >= 0.75:
            boost = f"Excellent work on {atom_name}! You've built a strong foundation."
            suggestions = ["Try connecting this concept to the next atom.", "You're ready to tackle harder problems."]
        elif mastery_score >= 0.5:
            boost = f"Good progress on {atom_name}. A quick review will make it stick."
            suggestions = ["Revisit the explanation once more.", "Practice one more round for confidence."]
        else:
            boost = f"Don't worry — {atom_name} takes time. Every attempt makes you stronger."
            suggestions = ["Re-read the teaching material carefully.", "Focus on the basics before moving on."]
        return {
            "summary": f"{atom_name} is a key building block of {concept}.",
            "quick_notes": [f"Core idea: {atom_name} is fundamental to {concept}", "Review the analogy to reinforce understanding"],
            "must_remember": [f"The definition and role of {atom_name}", "How it relates to the broader concept"],
            "common_pitfalls": [f"Confusing {atom_name} with related but different ideas"],
            "suggestions": suggestions,
            "confidence_boost": boost
        }