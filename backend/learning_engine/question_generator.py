# backend/learning_engine/question_generator.py - Complete fixed version

import json
import os
from typing import Dict, List, Optional
from groq import Groq
from google import genai
from django.conf import settings
import re   

class QuestionGenerator:
    """Generate questions and atoms for learning using AI"""
    
    def __init__(self):
        # Initialize Groq client
        groq_key = getattr(settings, 'GROQ_API_KEY', '')
        self.groq_client = Groq(api_key=groq_key) if groq_key else None
        
        # Initialize Gemini client
        gemini_key = getattr(settings, 'GOOGLE_API_KEY', '')
        if gemini_key:
            self.gemini_client = genai.Client(api_key=gemini_key)
        else:
            self.gemini_client = None

    @staticmethod
    def _validate_questions(questions: list) -> list:
        """
        Validate and sanitise AI-generated questions.
        - Ensures correct_index is an int within [0, len(options)-1]
        - Ensures options is a list of exactly 4 strings
        - Drops any malformed question instead of passing it through
        """
        validated = []
        for q in questions:
            opts = q.get('options')
            if not isinstance(opts, list) or len(opts) != 4:
                continue  # Skip malformed question

            ci = q.get('correct_index')
            try:
                ci = int(ci)
            except (TypeError, ValueError):
                ci = 0  # Fallback to first option

            if ci < 0 or ci >= len(opts):
                ci = 0  # Clamp to safe default

            q['correct_index'] = ci
            validated.append(q)
        return validated
    
    def generate_atoms(self, subject: str, concept: str) -> List[str]:
        """
        Generate atomic concepts using Gemini
        
        Args:
            subject: Subject name (e.g., 'Microprocessor')
            concept: Concept name (e.g., 'Memory Organization')
        
        Returns:
            List of atomic concept names
        """
        if not self.gemini_client:
            print("Gemini client not available, using fallback atoms")
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
        * Do NOT mix definition-level and mastery-level units

        3. Atoms must be mutually exclusive:

        * No overlap
        * No redundancy
        * No containment relationships
        * No parent–child relationships

        4. Together, atoms should cover the core structural understanding of the concept,
        as expected in a standard academic curriculum.

        STRUCTURAL RULES:

        5. Generate EXACTLY 4 to 6 atoms.

        6. Each atom must be:

        * A noun or noun phrase
        * Maximum 4 words
        * No verbs
        * No full sentences

        7. Do NOT include:

        * The concept name itself
        * Examples
        * Applications
        * Real-world use cases
        * Problem-solving techniques
        * Compound multi-idea phrases

        8. Prefer academically standard terminology used in textbooks.

        9. Avoid artificial fragmentation. Each atom must feel natural to a teacher.

        OUTPUT RULES:

        10. Output STRICT JSON only.

        11. Do NOT include explanations.

        Output format:

        {{
        "atoms": [
        "Atom 1",
        "Atom 2",
        "Atom 3",
        "Atom 4"
        ]
        }}

        If proper pedagogically valid atoms cannot be generated, return:

        {{"atoms": []}}

        """
        
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            
            # Extract JSON from response
            text = response.text
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            
            result = json.loads(text.strip())
            atoms = result.get("atoms", [])
            
            # Validate atom count
            if len(atoms) < 4 or len(atoms) > 6:
                print(f"Invalid atom count: {len(atoms)}, using fallback")
                return self._get_fallback_atoms(subject, concept)
            
            return atoms
            
        except Exception as e:
            print(f"Error generating atoms: {e}")
            return self._get_fallback_atoms(subject, concept)
    
    # backend/learning_engine/question_generator.py - Updated method

    def generate_questions(self, subject: str, concept: str, atom: str,
                        target_difficulty: str, count: int, 
                        knowledge_level: str = 'intermediate',
                        error_focus: List[str] = None) -> List[Dict]:
        """
        Generate questions for an atom with dynamic difficulty
        
        Args:
            subject: Subject name
            concept: Concept name
            atom: Atomic concept name
            target_difficulty: Specific difficulty to generate ('easy', 'medium', 'hard')
            count: Number of questions needed
            knowledge_level: Student's knowledge level
            error_focus: Optional list of error types to address
        
        Returns:
            List of question dictionaries
        """
        print(f"Generating {count} {target_difficulty} questions for atom: {atom}")
        
        if not self.groq_client or count == 0:
            return self._get_fallback_questions(atom, target_difficulty, count, knowledge_level)
        
        # Adjust based on knowledge level
        level_adjustments = {
            'zero': {
                'cognitive': ['recall'],
                'time_factor': 1.5,
                'complexity': 'very simple, foundational',
                'hint_level': 'detailed'
            },
            'beginner': {
                'cognitive': ['recall', 'apply'],
                'time_factor': 1.2,
                'complexity': 'straightforward',
                'hint_level': 'clear'
            },
            'intermediate': {
                'cognitive': ['recall', 'apply', 'analyze'],
                'time_factor': 1.0,
                'complexity': 'moderate',
                'hint_level': 'moderate'
            },
            'advanced': {
                'cognitive': ['apply', 'analyze'],
                'time_factor': 0.8,
                'complexity': 'challenging',
                'hint_level': 'subtle'
            }
        }
        
        adj = level_adjustments.get(knowledge_level, level_adjustments['intermediate'])
        
        # Determine cognitive operations for this difficulty
        if target_difficulty == 'easy':
            allowed_cognitive = ['recall']
        elif target_difficulty == 'medium':
            allowed_cognitive = ['recall', 'apply']
        else:  # hard
            allowed_cognitive = ['apply', 'analyze']
        
        # Add error focus if provided
        error_context = ""
        if error_focus:
            error_context = f"""
            Focus on addressing these common errors:
            {', '.join(error_focus)}
            
            Create questions that help the student overcome these specific difficulties.
            """
        
        prompt = f"""
            You are an experienced teacher creating high-quality conceptual assessment questions to evaluate deep student understanding.

            Subject: {subject}
            Concept: {concept}
            Atomic Concept: {atom}
            Student Level: {knowledge_level.upper()}
            Target Difficulty: {target_difficulty.upper()}

            Generate EXACTLY {count} {target_difficulty} question(s) with these characteristics:

            - Complexity: {adj['complexity']}
            - Cognitive levels: {', '.join(allowed_cognitive)}
            - Hint level: {adj['hint_level']}

            {error_context}

            CRITICAL QUALITY REQUIREMENTS:

            The goal is to test CONCEPTUAL UNDERSTANDING, not memorization.

            Each question MUST:

            - Be written like an experienced teacher checking real understanding
            - Require thinking, reasoning, or application — NOT simple definition recall
            - Be scenario-based, example-based, comparison-based, or reasoning-based whenever possible
            - Explicitly involve the atomic concept in a meaningful way
            - Avoid trivial, obvious, or keyword-matching questions
            - Avoid fill-in-the-blank style

            OPTIONS REQUIREMENTS (VERY IMPORTANT):

            Each question must have exactly 4 options where:

            - All options are plausible and believable
            - All options belong to the SAME conceptual category
            - Incorrect options must reflect common student misconceptions or mistakes
            - Avoid joke options, extreme options, or obviously wrong answers
            - Avoid options that differ only in grammar or wording tricks

            QUESTION LENGTH:

            - 10 to 35 words REQUIRED
            - Must be self-contained and clear

            DIFFICULTY REQUIREMENTS:

            For {target_difficulty} questions:

            Easy:
            - Simple scenario or example
            - Direct conceptual application

            Medium:
            - Requires reasoning, interpretation, or comparison

            Hard:
            - Multi-step reasoning, prediction, or analysis


            Each question MUST include:

            - "difficulty": "{target_difficulty}"
            - "cognitive_operation": one of {allowed_cognitive}
            - "estimated_time": integer (seconds)
                recall: 20-40
                apply: 40-90
                analyze: 90-150
            - "question": string
            - "options": array of exactly 4 strings
            - "correct_index": integer (0-3)

            OUTPUT STRICT JSON ONLY:

            {{
                "questions": [
                    {{
                        "difficulty": "{target_difficulty}",
                        "cognitive_operation": "recall",
                        "estimated_time": 30,
                        "question": "Question text here?",
                        "options": [
                            "Option A",
                            "Option B",
                            "Option C",
                            "Option D"
                        ],
                        "correct_index": 1
                    }}
                ]
            }}

            If constraints cannot be satisfied, return:

            {{"questions": []}}
            """

        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2048,
            )
            
            raw_text = response.choices[0].message.content
            if "```" in raw_text:
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            
            raw_text = re.sub(r'[\x00-\x1f\x7f]', lambda m: ' ' if m.group() in ('\n', '\r', '\t') else '', raw_text)
            result = json.loads(raw_text.strip())
            questions = result.get("questions", [])

            # Validate correct_index and options for every question
            questions = self._validate_questions(questions)
            
            # Adjust estimated time based on knowledge level
            for q in questions:
                q['estimated_time'] = int(q.get('estimated_time', 60) * adj['time_factor'])
            
            print(f"Generated {len(questions)} {target_difficulty} questions")
            return questions
            
        except Exception as e:
            print(f"Error generating questions: {e}")
            return self._get_fallback_questions(atom, target_difficulty, count, knowledge_level)
    
    def _get_fallback_atoms(self, subject: str, concept: str) -> List[str]:
        """Provide fallback atoms when AI generation fails"""
        # Common fallback atoms based on concept
        fallbacks = {
            "Memory Organization": [
                "Address Space",
                "Memory Hierarchy",
                "Cache Memory",
                "RAM vs ROM",
                "Memory Mapping"
            ],
            "Address Space": [
                "Address Lines",
                "Memory Locations",
                "Address Decoding",
                "Word Size",
                "Byte Addressing"
            ],
            "Cache Memory": [
                "Cache Levels",
                "Cache Hit/Miss",
                "Cache Mapping",
                "Replacement Policy",
                "Write Policy"
            ]
        }
        
        # Try to find matching fallback
        for key, atoms in fallbacks.items():
            if key.lower() in concept.lower():
                return atoms
        
        # Generic fallback
        return [
            f"{concept} Basics",
            f"{concept} Structure",
            f"{concept} Operations",
            f"{concept} Applications",
            f"{concept} Limitations"
        ]
    
    def _get_fallback_questions(self, atom: str, target_difficulty: str, count: int,
                                level: str = 'intermediate') -> List[Dict]:
        """Provide fallback questions when AI generation fails"""
        questions = []

        for _ in range(count):
            if target_difficulty == 'easy':
                questions.append({
                    "difficulty": "easy",
                    "cognitive_operation": "recall",
                    "estimated_time": 30,
                    "question": f"What is the primary purpose of {atom}?",
                    "options": [
                        f"To manage {atom} operations",
                        "To store data permanently",
                        "To execute instructions",
                        "To control peripherals"
                    ],
                    "correct_index": 0
                })
            elif target_difficulty == 'medium':
                questions.append({
                    "difficulty": "medium",
                    "cognitive_operation": "apply",
                    "estimated_time": 60,
                    "question": f"Which scenario best demonstrates the application of {atom}?",
                    "options": [
                        f"When implementing {atom} in a real system",
                        "During basic operations",
                        "In simple calculations",
                        "At the start of processing"
                    ],
                    "correct_index": 0
                })
            else:
                questions.append({
                    "difficulty": "hard",
                    "cognitive_operation": "analyze",
                    "estimated_time": 90,
                    "question": f"What would happen if {atom} was implemented incorrectly?",
                    "options": [
                        "System performance would degrade",
                        "Nothing would change",
                        "The system would run faster",
                        "Data would be more secure"
                    ],
                    "correct_index": 0
                })

        return questions
    
    def generate_complete_concept(self, subject: str, concept: str) -> Dict:
        """
        Generate complete concept with atoms and questions
        
        Args:
            subject: Subject name
            concept: Concept name
        
        Returns:
            Dictionary with atoms and questions
        """
        print(f"Generating complete concept for {subject} - {concept}")
        
        # Generate atoms
        atoms = self.generate_atoms(subject, concept)
        print(f"Generated {len(atoms)} atoms: {atoms}")
        
        result = {
            "concept": concept,
            "subject": subject,
            "atoms": {}
        }
        
        # Generate questions for each atom
        for atom in atoms:
            print(f"Generating questions for atom: {atom}")
            # Generate 2 easy and 2 medium questions per atom
            questions = []
            questions.extend(self.generate_questions(
                subject=subject,
                concept=concept,
                atom=atom,
                target_difficulty='easy',
                count=2,
                knowledge_level='intermediate'
            ))
            questions.extend(self.generate_questions(
                subject=subject,
                concept=concept,
                atom=atom,
                target_difficulty='medium',
                count=2,
                knowledge_level='intermediate'
            ))
            
            result["atoms"][atom] = {
                "name": atom,
                "questions": questions
            }
            
            print(f"Generated {len(questions)} questions for {atom}")
        
        return result
    
    
    
    def generate_initial_quiz(self, subject: str, concept: str,
                              knowledge_level: str = 'intermediate',
                              count: int = 5) -> List[Dict]:
        """
        Simple diagnostic quiz based only on subject/concept/knowledge level.
        Uses the same question generator with atom=concept for simplicity.
        """
        easy_count = max(1, count // 2)
        medium_count = max(0, count - easy_count)

        questions = []
        questions.extend(self.generate_questions(
            subject=subject,
            concept=concept,
            atom=concept,
            target_difficulty='easy',
            count=easy_count,
            knowledge_level=knowledge_level
        ))
        if medium_count > 0:
            questions.extend(self.generate_questions(
                subject=subject,
                concept=concept,
                atom=concept,
                target_difficulty='medium',
                count=medium_count,
                knowledge_level=knowledge_level
            ))

        return questions

    # ── NEW: Concept overview for zero-knowledge students ──
    def generate_concept_overview(self, subject: str, concept: str, atoms: List[str]) -> Dict:
        """
        Generate a quick, beginner-friendly overview of the concept and its atoms.
        Used when knowledge_level == 'zero' BEFORE the diagnostic quiz.
        """
        atoms_text = "\n".join([f"  {i+1}. {a}" for i, a in enumerate(atoms)])

        prompt = f"""
You are creating a SHORT, beginner-friendly overview for a student who has ZERO prior knowledge.

Subject: {subject}
Concept: {concept}
Atomic sub-topics:
{atoms_text}

Generate a JSON overview with these keys:

1. "overview" — 3-5 sentences explaining what this concept is about in the simplest possible language.
   Use analogies, everyday language, no jargon so the student can develop a mental model.

2. "why_it_matters" — 2-3 sentences on why this concept matters in real life.

3. "what_you_will_learn" — A JSON array of short strings (one per atom), each describing
   what the student will learn in 8-12 words. Written in second person ("You will learn...").

4. "key_terms" — A JSON array of objects, each with "term" and "simple_definition" (1 sentence, plain English).
   List 3-5 key terms the student will encounter.

5. "encouragement" — One motivational sentence for a beginner.

Return STRICT JSON only. No markdown, no explanation outside the JSON.

{{
  "overview": "...",
  "why_it_matters": "...",
  "what_you_will_learn": ["...", "..."],
  "key_terms": [{{"term": "...", "simple_definition": "..."}}],
  "encouragement": "..."
}}
"""
        if not self.groq_client:
            return self._fallback_concept_overview(subject, concept, atoms)

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=1024,
            )
            raw = response.choices[0].message.content
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = re.sub(r'[\x00-\x1f\x7f]', lambda m: ' ' if m.group() in ('\n', '\r', '\t') else '', raw)
            return json.loads(raw.strip())
        except Exception as e:
            print(f"Error generating concept overview: {e}")
            return self._fallback_concept_overview(subject, concept, atoms)

    def _fallback_concept_overview(self, subject, concept, atoms):
        return {
            "overview": f"{concept} is a fundamental topic in {subject}. It covers several important ideas that build on each other. Don't worry if it sounds complex — we'll break it into small, easy pieces.",
            "why_it_matters": f"Understanding {concept} will help you grasp core principles of {subject} and apply them in practice.",
            "what_you_will_learn": [f"You will learn about {a}" for a in atoms],
            "key_terms": [{"term": a, "simple_definition": f"A key part of {concept}"} for a in atoms[:4]],
            "encouragement": "Every expert was once a beginner. Let's start this journey together!"
        }

    # ── NEW: Atom summary after completion ──
    def generate_atom_summary(self, subject: str, concept: str, atom_name: str,
                              teaching_content: Dict, mastery_score: float,
                              error_types: List[str] = None) -> Dict:
        """
        Generate a concise summary after atom completion: quick notes, must-remember items,
        common pitfalls, and suggestions.
        """
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

1. "summary" — 2-3 sentence recap of the core idea (simple, memorable).
2. "quick_notes" — Array of 3-5 bullet-point strings, each a key fact or insight.
3. "must_remember" — Array of 2-3 strings: the absolute essentials that MUST stick.
4. "common_pitfalls" — Array of 1-3 strings: typical mistakes to watch out for.
5. "suggestions" — Array of 1-3 strings: what to do next based on mastery level.
   If mastery is low, suggest review. If high, suggest connecting to next atoms.
6. "confidence_boost" — One short motivational line based on their mastery.

Return STRICT JSON only:
{{
  "summary": "...",
  "quick_notes": ["...", "..."],
  "must_remember": ["...", "..."],
  "common_pitfalls": ["..."],
  "suggestions": ["..."],
  "confidence_boost": "..."
}}
"""
        if not self.groq_client:
            return self._fallback_atom_summary(atom_name, concept, mastery_score)

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800,
            )
            raw = response.choices[0].message.content
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = re.sub(r'[\x00-\x1f\x7f]', lambda m: ' ' if m.group() in ('\n', '\r', '\t') else '', raw)
            return json.loads(raw.strip())
        except Exception as e:
            print(f"Error generating atom summary: {e}")
            return self._fallback_atom_summary(atom_name, concept, mastery_score)

    def _fallback_atom_summary(self, atom_name, concept, mastery_score):
        if mastery_score >= 0.75:
            boost = f"Excellent work on {atom_name}! You've built a strong foundation."
            suggestions = ["Try connecting this concept to the next atom.", "You're ready to tackle harder problems."]
        elif mastery_score >= 0.5:
            boost = f"Good progress on {atom_name}. A quick review will make it stick."
            suggestions = ["Revisit the explanation once more.", "Practice one more round for confidence."]
        else:
            boost = f"Don't worry — {atom_name} takes time. Every attempt makes you stronger."
            suggestions = ["Re-read the teaching material carefully.", "Focus on the basics before moving on.", "Try explaining it to yourself in your own words."]
        return {
            "summary": f"{atom_name} is a key building block of {concept}. Understanding it well will help you with the remaining atoms.",
            "quick_notes": [f"Core idea: {atom_name} is fundamental to {concept}", "Review the analogy to reinforce your understanding", "Connect it to real-world examples"],
            "must_remember": [f"The definition and role of {atom_name}", "How it relates to the broader concept"],
            "common_pitfalls": [f"Confusing {atom_name} with related but different ideas"],
            "suggestions": suggestions,
            "confidence_boost": boost
        }

    def generate_questions_from_teaching(self, subject, concept, atom, teaching_content, 
                                        need_easy=1, need_medium=2, need_hard=0, 
                                        knowledge_level='intermediate'):
        """
        Generate questions based on the teaching content that was shown
        
        Args:
            subject: Subject name
            concept: Concept name
            atom: Atomic concept name
            teaching_content: Dict with explanation, analogy, examples
            need_easy: Number of easy questions
            need_medium: Number of medium questions
            need_hard: Number of hard questions
            knowledge_level: Student's knowledge level
        
        Returns:
            List of question dictionaries
        """
        print(f"Generating questions from teaching for atom: {atom}")
        
        if not self.groq_client:
            print("Groq client not available, using fallback")
            return self._get_fallback_questions_from_teaching(atom, need_easy, need_medium, need_hard)
        
        total_needed = need_easy + need_medium + need_hard
        
        # Extract teaching content
        explanation = teaching_content.get('explanation', '')
        analogy = teaching_content.get('analogy', '')
        examples = teaching_content.get('examples', [])
        
        examples_text = "\n".join([f"- {ex}" for ex in examples if ex])
        
        prompt = f"""
            You are an experienced teacher generating conceptual assessment questions to verify whether a student truly understood the concept that was just taught.

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


            TASK:

            Generate EXACTLY {total_needed} multiple-choice questions that test CONCEPTUAL UNDERSTANDING of "{atom}" based on the teaching content.

            IMPORTANT:

            The goal is NOT to test memory of the explanation, analogy, or examples.

            The goal is to test whether the student understood the underlying CONCEPT.


            CRITICAL RULES:

            1. DO NOT ask questions about the analogy itself
            2. DO NOT ask questions about the specific examples themselves
            3. DO NOT ask questions that require recalling sentences from the explanation

            4. Instead, create NEW conceptual situations where the student must APPLY the concept

            5. Questions must test:

            - understanding of how the concept works
            - when the concept applies
            - when the concept does NOT apply
            - consequences of using or misusing the concept

            6. Each question must be meaningful, realistic, and require thinking

            7. Avoid definition questions starting with:

            - What is
            - Define
            - Identify

            8. Each question must be 18–35 words

            9. Each question must have exactly 4 options

            10. All options must be:

            - plausible
            - same conceptual category
            - based on realistic student mistakes or misconceptions

            11. Avoid obvious wrong answers


            DIFFICULTY DISTRIBUTION:

            Easy ({need_easy}):

            - Simple conceptual application

            Medium ({need_medium}):

            - Requires reasoning or interpretation

            Hard ({need_hard}):

            - Requires deeper reasoning, prediction, or identifying incorrect application



            OUTPUT STRICT JSON ONLY:

            {{
                "questions": [
                    {{
                        "difficulty": "easy",
                        "cognitive_operation": "apply",
                        "estimated_time": 40,
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

        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2048,
            )
            
            raw_text = response.choices[0].message.content
            if "```" in raw_text:
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            
            raw_text = re.sub(r'[\x00-\x1f\x7f]', lambda m: ' ' if m.group() in ('\n', '\r', '\t') else '', raw_text)
            result = json.loads(raw_text.strip())
            questions = result.get("questions", [])

            # Validate correct_index and options for every question
            questions = self._validate_questions(questions)
            
            print(f"Generated {len(questions)} questions from teaching")
            return questions
            
        except Exception as e:
            print(f"Error generating questions from teaching: {e}")
            return self._get_fallback_questions_from_teaching(atom, need_easy, need_medium, need_hard)

    def _get_fallback_questions_from_teaching(self, atom, need_easy, need_medium, need_hard):
        """Fallback questions based on teaching content"""
        questions = []
        
        # Easy questions
        for i in range(need_easy):
            questions.append({
                "difficulty": "easy",
                "cognitive_operation": "recall",
                "estimated_time": 30,
                "question": f"What is the main purpose of {atom}?",
                "options": [
                    f"To {atom.lower()} efficiently",
                    "To store data permanently",
                    "To execute instructions",
                    "To control peripherals"
                ],
                "correct_index": 0
            })
        
        # Medium questions
        for i in range(need_medium):
            questions.append({
                "difficulty": "medium",
                "cognitive_operation": "apply",
                "estimated_time": 60,
                "question": f"Which scenario best demonstrates the application of {atom}?",
                "options": [
                    f"When implementing {atom} in a real system",
                    "During basic operations",
                    "In simple calculations",
                    "At the start of processing"
                ],
                "correct_index": 0
            })
        
        # Hard questions
        for i in range(need_hard):
            questions.append({
                "difficulty": "hard",
                "cognitive_operation": "analyze",
                "estimated_time": 90,
                "question": f"What would happen if {atom} was implemented incorrectly?",
                "options": [
                    "System performance would degrade",
                    "Nothing would change",
                    "The system would run faster",
                    "Data would be more secure"
                ],
                "correct_index": 0
            })
        
        return questions