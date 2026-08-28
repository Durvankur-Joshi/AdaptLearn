# backend/learning_engine/question_generator.py
"""
Centralized Question Generation Service for AdaptiveLearning.

Architecture:
1. Provider: OpenRouter (OpenAI-compatible API at https://openrouter.ai/api/v1).
2. Configuration: Strictly reads API_KEY and MODEL from environment variables / Django settings.
3. Candidate Batching: Generates N + 1 candidates in 1 request for N needed questions.
4. Bounded Retries: At most 2 generation attempts with strict fail-fast error handling.
5. Novelty Gate: Pure-Python Jaccard and SequenceMatcher similarity detection against
   session history and intra-batch candidates. No local transformer models loaded.
6. Option Shuffling & Balancing: Programmatically randomizes option positions across
   A, B, C, D to permanently eliminate Option A bias while strictly preserving correct answer mapping.
7. Strict Candidate Validation: Missing or invalid correct answers are rejected (never defaulted to 0).
8. Zero Static Question Fallback: Deterministic static question templates are completely eliminated.
"""

import difflib
import json
import logging
import os
import random
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import requests
from django.conf import settings
from .openrouter_client import call_openrouter, parse_json_from_text

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

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Threshold above which two questions are considered duplicates (0.0 to 1.0)
QUESTION_SIMILARITY_THRESHOLD = 0.72

# Maximum bounded generation attempts
MAX_GENERATION_ATTEMPTS = 2

# Generation temperature for controlled creativity and diversity
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


# =====================================================================
# Strict Validation and Sanitization
# =====================================================================

def _validate_single_question(q: Any) -> Optional[Dict]:
    """
    Strict validation and sanitization for a single candidate question.
    Returns the sanitized dict if valid, or None if invalid.
    Rejects candidate if correct answer or options are invalid (NEVER defaults to 0).
    """
    if not isinstance(q, dict):
        return None

    question_text = str(q.get('question', '')).strip()
    word_count = len(question_text.split())
    if not question_text or word_count < 3 or word_count > 70:
        return None

    opts = q.get('options')
    if not isinstance(opts, list) or len(opts) != 4:
        return None

    cleaned_opts = [str(o).strip() for o in opts]
    if any(len(o) == 0 for o in cleaned_opts):
        return None
    if len(set(cleaned_opts)) != 4:
        return None  # Rejects duplicate options within the same question

    # Determine correct option index
    ci_int = None
    if 'correct_index' in q and q['correct_index'] is not None:
        try:
            val = int(q['correct_index'])
            if val in (0, 1, 2, 3):
                ci_int = val
        except (TypeError, ValueError):
            pass

    # If correct_index not given or invalid, attempt resolution via correct_answer text or letter
    if ci_int is None and 'correct_answer' in q and q['correct_answer']:
        ca_raw = str(q['correct_answer']).strip()
        # Direct string match with an option
        if ca_raw in cleaned_opts:
            ci_int = cleaned_opts.index(ca_raw)
        elif ca_raw.upper() in ('A', 'B', 'C', 'D'):
            ci_int = {'A': 0, 'B': 1, 'C': 2, 'D': 3}[ca_raw.upper()]
        elif ca_raw.isdigit() and int(ca_raw) in (0, 1, 2, 3):
            ci_int = int(ca_raw)

    if ci_int is None or ci_int not in (0, 1, 2, 3):
        return None  # Strictly rejected!

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
        'correct_index': ci_int,
        'explanation': str(q.get('explanation', '')).strip()
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

        # Place correct_text at target_ci, and incorrect_options in remaining 3 slots
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
        q_copy['correct_answer'] = correct_text

        # Verification assertion to guarantee integrity
        assert q_copy['options'][q_copy['correct_index']] == correct_text, "Option shuffle corrupted correct_index mapping!"
        processed_questions.append(q_copy)

    return processed_questions


# =====================================================================
# Robust JSON Parsing
# =====================================================================

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

    return []


# =====================================================================
# OpenRouter Question Provider
# =====================================================================

class BaseQuestionProvider:
    """Base interface for question generation AI providers."""
    provider_name: str = "Base"
    model_name: str = ""

    def is_permanent_error(self, err: Exception) -> bool:
        return False

    def generate_candidate_questions(
        self,
        prompt: str,
        needed_count: int,
        temperature: float = DEFAULT_GENERATION_TEMPERATURE,
        attempt: int = 1
    ) -> List[Dict]:
        raise NotImplementedError


class OpenRouterQuestionProvider(BaseQuestionProvider):
    """Primary question provider using OpenRouter (OpenAI-compatible REST API)."""
    provider_name: str = "OpenRouter"

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = getattr(settings, 'API_KEY', '') or os.getenv('API_KEY', '')

        if model_name is not None:
            self.model_name = model_name
        else:
            self.model_name = getattr(settings, 'MODEL', '') or os.getenv('MODEL', '')

    def is_permanent_error(self, err: Exception) -> bool:
        err_str = str(err).lower()
        if "400" in err_str or "bad request" in err_str:
            return True
        if "401" in err_str or "403" in err_str or "unauthorized" in err_str or "forbidden" in err_str or "invalid api key" in err_str:
            return True
        if "404" in err_str or "model_not_found" in err_str or "does not exist" in err_str or "not found" in err_str:
            return True
        return False

    def generate_candidate_questions(
        self,
        prompt: str,
        needed_count: int,
        temperature: float = DEFAULT_GENERATION_TEMPERATURE,
        attempt: int = 1
    ) -> List[Dict]:
        if not self.api_key:
            raise QuestionGenerationError("OpenRouter API_KEY is not configured in environment variables.")
        if not self.model_name:
            raise QuestionGenerationError("OpenRouter MODEL is not configured in environment variables.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://adaptlearn.local",
            "X-Title": "AdaptiveLearning"
        }

        # Request N + 1 candidates for N needed questions to minimize roundtrips
        candidate_count = needed_count + 1
        max_tokens = min(2048, max(500, 300 * candidate_count))

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional educational assessment engine. Generate multiple-choice questions in strict JSON format only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        logger.info(f"[OpenRouter] Attempt {attempt}")
        logger.info("[OpenRouter] Request started")
        start_time = time.time()

        try:
            response = requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            latency_ms = int((time.time() - start_time) * 1000)
            logger.info("[OpenRouter] Request completed")
            logger.info(f"[OpenRouter] Latency={latency_ms} ms")
        except requests.exceptions.Timeout as te:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.warning(f"[OpenRouter] Request timed out after {latency_ms} ms: {te}")
            raise Exception(f"OpenRouter connection timed out: {te}")
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.warning(f"[OpenRouter] Connection failed after {latency_ms} ms: {e}")
            raise Exception(f"OpenRouter connection error: {e}")

        if response.status_code != 200:
            err_msg = f"OpenRouter API returned HTTP {response.status_code}: {response.text[:300]}"
            logger.warning(f"[OpenRouter] API error: {err_msg}")
            raise Exception(err_msg)

        try:
            res_json = response.json()
            raw_text = res_json['choices'][0]['message']['content'] or ""
        except Exception as e:
            logger.warning(f"[OpenRouter] Failed to extract message content from response: {e}")
            raw_text = response.text or ""

        return safe_parse_json_questions(raw_text)


# =====================================================================
# Main QuestionGenerator Class (Centralized Orchestrator)
# =====================================================================

class QuestionGenerator:
    """Centralized orchestrator for question generation using OpenRouter."""

    def __init__(self, provider: Optional[OpenRouterQuestionProvider] = None):
        self.provider = provider or OpenRouterQuestionProvider()

    @staticmethod
    def _validate_questions(questions: list) -> list:
        """Validate and sanitize candidate questions list."""
        validated = []
        for q in questions:
            sanitized = _validate_single_question(q)
            if sanitized:
                validated.append(sanitized)
        return validated

    def _execute_generation_pipeline(
        self,
        build_prompt_fn,
        total_needed: int,
        need_easy: int,
        need_medium: int,
        need_hard: int,
        history_pool: List[Union[Dict, str]],
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Generic OpenRouter generation engine:
        1. Attempt 1: Request N + 1 candidate batch from OpenRouter.
        2. Validate candidate structures strictly (reject invalid correct_index/answer).
        3. Filter duplicate candidates via NOVELTY_GATE against session history & batch.
        4. If fewer than total_needed, execute Attempt 2 for remaining count + 1.
        5. If still fewer than total_needed, raise QuestionGenerationError (NO static fallback).
        6. Apply backend option shuffling & balancing across A/B/C/D.
        """
        accepted_questions: List[Dict] = []
        remaining_easy = need_easy
        remaining_medium = need_medium
        remaining_hard = need_hard

        logger.info(f"[QuestionGeneration] Session={session_id or 'N/A'} Provider=OpenRouter Model={self.provider.model_name} Requested questions={total_needed}")

        for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
            needed_now = total_needed - len(accepted_questions)
            if needed_now <= 0:
                break

            prompt = build_prompt_fn(needed_now, remaining_easy, remaining_medium, remaining_hard, history_pool)

            try:
                candidates = self.provider.generate_candidate_questions(
                    prompt=prompt,
                    needed_count=needed_now,
                    temperature=DEFAULT_GENERATION_TEMPERATURE,
                    attempt=attempt
                )
            except Exception as e:
                is_perm = self.provider.is_permanent_error(e)
                logger.warning(f"[OpenRouter] Generation attempt {attempt} failed: {e} (permanent={is_perm})")
                if is_perm:
                    logger.error("[OpenRouter] Encountered permanent error; terminating generation pipeline.")
                    break
                if attempt == MAX_GENERATION_ATTEMPTS:
                    logger.error("[OpenRouter] Exhausted retries.")
                continue

            novelty_accepted = 0
            novelty_rejected = 0

            for candidate in candidates:
                sanitized = _validate_single_question(candidate)
                if not sanitized:
                    logger.warning("[QUALITY_GATE] Candidate rejected due to schema/validation failure.")
                    continue

                is_novel, sim_score, matched_q = is_novel_question(sanitized, history_pool)
                if not is_novel:
                    novelty_rejected += 1
                    logger.info(
                        f"[NoveltyGate] Duplicate rejected (sim={sim_score:.3f} >= {QUESTION_SIMILARITY_THRESHOLD}) "
                        f"matched: '{matched_q}' | candidate: '{sanitized['question']}'"
                    )
                    continue

                novelty_accepted += 1
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

            logger.info(f"[NoveltyGate] Accepted={novelty_accepted} Rejected={novelty_rejected}")

            if len(accepted_questions) >= total_needed:
                break

        if len(accepted_questions) < total_needed:
            logger.error(
                f"[QuestionGeneration] OpenRouter failed to produce {total_needed} questions. "
                f"Generated only {len(accepted_questions)}/{total_needed}. Raising QuestionGenerationError."
            )
            raise QuestionGenerationError(
                f"Question generation failed. Produced {len(accepted_questions)}/{total_needed}."
            )

        final_batch = accepted_questions[:total_needed]
        balanced_batch = shuffle_and_balance_options(final_batch)
        logger.info(f"[QuestionGeneration] Completed Returned={len(balanced_batch)}")
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
        previous_questions: Optional[List[Union[Dict, str]]] = None,
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Generate novel assessment questions based on teaching content using OpenRouter.
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
            # Request N + 1 candidates to ensure quota efficiency
            candidate_target = needed_count + 1
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
You are an experienced educator creating conceptual assessment questions to evaluate deep student understanding.

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
Generate EXACTLY {candidate_target} distinct multiple-choice question candidates testing conceptual understanding of "{atom}".

DIFFICULTY GUIDELINES:
- Aim for {rem_easy} Easy, {rem_med} Medium, {rem_hard} Hard questions.

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
7. Exactly one correct option. "correct_answer" MUST match the exact text of the correct option.
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
                "Option 1",
                "Option 2",
                "Option 3",
                "Option 4"
            ],
            "correct_answer": "Option 2",
            "explanation": "Why this option is correct."
        }}
    ]
}}
"""

        return self._execute_generation_pipeline(
            build_prompt_fn=build_teaching_prompt,
            total_needed=total_needed,
            need_easy=need_easy,
            need_medium=need_medium,
            need_hard=need_hard,
            history_pool=history_pool,
            session_id=session_id
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
        previous_questions: Optional[List[Union[Dict, str]]] = None,
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Generate questions for an atom with dynamic difficulty using OpenRouter.
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
            candidate_target = needed_count + 1
            history_lines = [f"- {q.get('question', str(q))}" for q in pool[-10:] if str(q).strip()]
            history_sec = ""
            if history_lines:
                history_sec = f"PREVIOUS QUESTIONS (DO NOT DUPLICATE):\n" + "\n".join(history_lines) + "\n"

            return f"""
You are an experienced educator creating conceptual assessment questions to evaluate deep student understanding.

Subject: {subject}
Concept: {concept}
Atomic Concept: {atom}
Student Level: {knowledge_level.upper()}
Target Difficulty: {target_difficulty.upper()}

Generate EXACTLY {candidate_target} distinct {target_difficulty} question(s) with these characteristics:
- Complexity: {adj['complexity']}
- Cognitive levels: {', '.join(allowed_cognitive)}
- Hint level: {adj['hint_level']}

{error_context}
{history_sec}

CRITICAL QUALITY REQUIREMENTS:
- Test CONCEPTUAL UNDERSTANDING, application, or reasoning — NOT simple definition recall.
- Avoid obvious or trivial keyword matching.
- Each question must have exactly 4 plausible options in the same conceptual category.
- Exactly one correct option. "correct_answer" must match the exact string of the correct option.
- Output STRICT JSON ONLY.

OUTPUT FORMAT:
{{
    "questions": [
        {{
            "difficulty": "{target_difficulty}",
            "cognitive_operation": "{allowed_cognitive[0]}",
            "estimated_time": 45,
            "question": "Question text here?",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "correct_answer": "Option 1",
            "explanation": "Why this option is correct."
        }}
    ]
}}
"""

        return self._execute_generation_pipeline(
            build_prompt_fn=build_dynamic_prompt,
            total_needed=count,
            need_easy=easy_c,
            need_medium=med_c,
            need_hard=hard_c,
            history_pool=history_pool,
            session_id=session_id
        )

    def generate_initial_quiz(
        self,
        subject: str,
        concept: str,
        knowledge_level: str = 'intermediate',
        count: int = 5,
        previous_questions: Optional[List[Union[Dict, str]]] = None,
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """Diagnostic quiz based on subject/concept/knowledge level using a single OpenRouter request."""
        if count <= 0:
            return []

        easy_count = max(1, count // 2)
        medium_count = count - easy_count
        history_pool: List[Union[Dict, str]] = list(previous_questions or [])

        def build_quiz_prompt(needed_count: int, rem_easy: int, rem_med: int, rem_hard: int, pool: List[Union[Dict, str]]) -> str:
            candidate_target = needed_count + 1
            recent_history = pool[-10:]
            history_lines = []
            for idx, q in enumerate(recent_history, start=1):
                q_text = q.get('question', '') if isinstance(q, dict) else str(q)
                if q_text.strip():
                    history_lines.append(f"{idx}. {q_text.strip()}")

            history_section = ""
            if history_lines:
                history_section = f"""
PREVIOUSLY ASKED QUESTIONS (DO NOT REPEAT OR REWORD THESE):
{chr(10).join(history_lines)}
"""

            return f"""
You are an expert diagnostic assessment designer creating an initial evaluation quiz.

Subject: {subject}
Concept: {concept}
Student Knowledge Level: {knowledge_level.upper()}

{history_section}

TASK:
Generate EXACTLY {candidate_target} distinct multiple-choice questions to evaluate the student's baseline understanding of "{concept}".

DIFFICULTY DISTRIBUTION:
- {rem_easy} Easy question(s) testing fundamental terminology, core identification, or basic facts.
- {rem_med} Medium question(s) testing concept relationships, cause-and-effect, or simple application.

CRITICAL RULES:
1. Each question must have exactly 4 plausible options.
2. Exactly one correct option. "correct_answer" must match the exact string of the correct option.
3. Questions must test conceptual understanding rather than trivial trick questions.
4. Output STRICT JSON ONLY.

OUTPUT FORMAT:
{{
    "questions": [
        {{
            "difficulty": "easy",
            "cognitive_operation": "recall",
            "estimated_time": 30,
            "question": "Question text here?",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "correct_answer": "Option 1",
            "explanation": "Why this option is correct."
        }}
    ]
}}
"""

        return self._execute_generation_pipeline(
            build_prompt_fn=build_quiz_prompt,
            total_needed=count,
            need_easy=easy_count,
            need_medium=medium_count,
            need_hard=0,
            history_pool=history_pool,
            session_id=session_id
        )

    def generate_atoms(self, subject: str, concept: str) -> List[str]:
        """Generate atomic concepts using OpenRouter. Returns empty list on failure so 503 is returned."""
        if not self.provider.api_key or not self.provider.model_name:
            raise QuestionGenerationError("OpenRouter API_KEY or MODEL is not configured.")

        prompt = f"""
You are an expert curriculum designer breaking down concepts into atomic learning units.
Subject: {subject}
Concept: {concept}

Generate EXACTLY 4 to 6 atomic sub-concepts ("atoms").
Each atom must be a noun or noun phrase (maximum 4 words).

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
            raw = call_openrouter(
                prompt=prompt,
                system_prompt="You are an expert curriculum designer. Output valid JSON only.",
                temperature=0.3,
                max_tokens=400,
                api_key=self.provider.api_key,
                model=self.provider.model_name
            )
            parsed = parse_json_from_text(raw)
            if isinstance(parsed, dict):
                atoms = parsed.get("atoms", [])
            elif isinstance(parsed, list):
                atoms = parsed
            else:
                atoms = []

            cleaned_atoms = [str(a).strip() for a in atoms if a and str(a).strip()]
            if len(cleaned_atoms) >= 3:
                return cleaned_atoms[:6]
            logger.error(f"OpenRouter returned invalid atoms payload: {raw[:200]}")
            return []
        except Exception as e:
            logger.error(f"OpenRouter atom generation failed for {concept} in {subject}: {e}")
            return []

    def generate_concept_overview(self, subject: str, concept: str, atoms: List[str]) -> Dict:
        """Generate overview for zero-knowledge students using OpenRouter."""
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
        if self.provider.api_key and self.provider.model_name:
            try:
                raw = call_openrouter(
                    prompt=prompt,
                    system_prompt="You are an expert tutor. Output valid JSON only.",
                    temperature=0.3,
                    max_tokens=600,
                    api_key=self.provider.api_key,
                    model=self.provider.model_name
                )
                parsed = parse_json_from_text(raw)
                if isinstance(parsed, dict) and "overview" in parsed:
                    return parsed
            except Exception as e:
                logger.error(f"Error in generate_concept_overview with OpenRouter: {e}")

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
        """Generate concise summary after atom completion using OpenRouter."""
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
        if self.provider.api_key and self.provider.model_name:
            try:
                raw = call_openrouter(
                    prompt=prompt,
                    system_prompt="You are an expert tutor. Output valid JSON only.",
                    temperature=0.3,
                    max_tokens=600,
                    api_key=self.provider.api_key,
                    model=self.provider.model_name
                )
                parsed = parse_json_from_text(raw)
                if isinstance(parsed, dict) and "summary" in parsed:
                    return parsed
            except Exception as e:
                logger.error(f"Error in generate_atom_summary with OpenRouter: {e}")

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