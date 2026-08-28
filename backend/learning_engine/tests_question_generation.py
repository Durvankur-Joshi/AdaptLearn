# backend/learning_engine/tests_question_generation.py
"""
Comprehensive test suite for the Multi-Provider Question Generation Pipeline.
Tests Groq (Primary) + Google Gemini (Fallback) orchestration, error classification,
smart immediate fallback on permanent errors, bounded retries on transient errors,
intra-batch/history novelty gating, option shuffling and position balancing,
strict correct_index validation, HTTP 503 error handling, and adaptive learning preservation.
"""

from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import Concept, TeachingAtom, LearningSession, StudentProgress, LearningProfile
from learning_engine.question_generator import (
    QuestionGenerator,
    GroqQuestionProvider,
    GeminiQuestionProvider,
    QuestionGenerationError,
    normalize_question_text,
    calculate_question_similarity,
    is_novel_question,
    shuffle_and_balance_options,
    _validate_single_question,
    QUESTION_SIMILARITY_THRESHOLD
)
from learning_engine.knowledge_tracing import calculate_updated_mastery


class LightweightSimilarityAndSchemaTests(TestCase):
    """Unit tests for novelty detection, schema validation, and option shuffling."""

    def test_no_sentence_transformers_or_local_embeddings(self):
        """TEST 14: Ensure no sentence-transformers or local embedding models are imported."""
        import sys
        self.assertNotIn('sentence_transformers', sys.modules)

    def test_normalize_question_text(self):
        """Test normalization: casing, punctuation, whitespace."""
        raw = "  What IS Cache   Mapping, and how does it work?!  "
        normalized = normalize_question_text(raw)
        self.assertEqual(normalized, "what is cache mapping and how does it work")

    def test_exact_and_near_duplicate_similarity(self):
        """Test exact and semantically similar questions are flagged with high similarity."""
        q1 = "What is the primary purpose of cache mapping?"
        q2 = "What does cache mapping mean?"
        q3 = "Which statement best describes the primary purpose of cache mapping?"
        q4 = "Two memory blocks repeatedly map to the same cache slot. What problem occurs?"

        sim_exact = calculate_question_similarity(q1, q1)
        self.assertEqual(sim_exact, 1.0)

        sim_reword = calculate_question_similarity(q1, q3)
        self.assertGreaterEqual(sim_reword, QUESTION_SIMILARITY_THRESHOLD)

        sim_diff = calculate_question_similarity(q1, q4)
        self.assertLess(sim_diff, QUESTION_SIMILARITY_THRESHOLD)

    def test_validate_single_question_strict_correct_index(self):
        """TEST 8: Missing or invalid correct_index is rejected and NEVER defaulted to 0."""
        # Valid question
        valid_q = {
            "difficulty": "easy",
            "cognitive_operation": "apply",
            "estimated_time": 40,
            "question": "Where does block 0x10 map in a direct-mapped cache?",
            "options": ["Slot 0", "Slot 1", "Slot 2", "Slot 3"],
            "correct_index": 2
        }
        res = _validate_single_question(valid_q)
        self.assertIsNotNone(res)
        self.assertEqual(res["correct_index"], 2)

        # Missing correct_index -> MUST BE REJECTED (None)
        missing_ci = {
            "difficulty": "easy",
            "cognitive_operation": "apply",
            "estimated_time": 40,
            "question": "Where does block 0x10 map in a direct-mapped cache?",
            "options": ["Slot 0", "Slot 1", "Slot 2", "Slot 3"]
        }
        self.assertIsNone(_validate_single_question(missing_ci))

        # Invalid out-of-range correct_index -> MUST BE REJECTED (None)
        out_of_range_ci = {
            "difficulty": "easy",
            "cognitive_operation": "apply",
            "estimated_time": 40,
            "question": "Where does block 0x10 map in a direct-mapped cache?",
            "options": ["Slot 0", "Slot 1", "Slot 2", "Slot 3"],
            "correct_index": 4
        }
        self.assertIsNone(_validate_single_question(out_of_range_ci))

        # Non-numeric correct_index -> MUST BE REJECTED (None)
        non_numeric_ci = {
            "difficulty": "easy",
            "cognitive_operation": "apply",
            "estimated_time": 40,
            "question": "Where does block 0x10 map in a direct-mapped cache?",
            "options": ["Slot 0", "Slot 1", "Slot 2", "Slot 3"],
            "correct_index": "invalid"
        }
        self.assertIsNone(_validate_single_question(non_numeric_ci))

    def test_shuffle_and_balance_options(self):
        """TEST 9 & 10: Options are shuffled, correct_index accurately maps, positions vary across A/B/C/D."""
        batch = [
            {"question": "Q1", "options": ["Correct_A", "W1", "W2", "W3"], "correct_index": 0},
            {"question": "Q2", "options": ["Correct_B", "W1", "W2", "W3"], "correct_index": 0},
            {"question": "Q3", "options": ["Correct_C", "W1", "W2", "W3"], "correct_index": 0},
            {"question": "Q4", "options": ["Correct_D", "W1", "W2", "W3"], "correct_index": 0},
        ]

        shuffled_batch = shuffle_and_balance_options(batch)
        self.assertEqual(len(shuffled_batch), 4)

        for idx, q in enumerate(shuffled_batch):
            expected_correct_text = f"Correct_{['A', 'B', 'C', 'D'][idx]}"
            actual_correct_index = q['correct_index']
            self.assertEqual(q['options'][actual_correct_index], expected_correct_text)
            self.assertEqual(len(q['options']), 4)
            self.assertEqual(len(set(q['options'])), 4)

        assigned_indices = {q['correct_index'] for q in shuffled_batch}
        self.assertEqual(assigned_indices, {0, 1, 2, 3})


class MultiProviderOrchestrationTests(TestCase):
    """Unit tests for Groq (Primary) + Gemini (Fallback) orchestration logic."""

    def setUp(self):
        self.mock_groq_prov = MagicMock(spec=GroqQuestionProvider)
        self.mock_groq_prov.provider_name = "Groq"
        self.mock_groq_prov.model_name = "llama-3.1-8b-instant"
        self.mock_groq_prov.is_permanent_error = GroqQuestionProvider.is_permanent_error.__get__(self.mock_groq_prov)

        self.mock_gemini_prov = MagicMock(spec=GeminiQuestionProvider)
        self.mock_gemini_prov.provider_name = "Gemini"
        self.mock_gemini_prov.model_name = "gemini-2.5-flash"
        self.mock_gemini_prov.is_permanent_error = GeminiQuestionProvider.is_permanent_error.__get__(self.mock_gemini_prov)

        self.generator = QuestionGenerator(
            groq_provider=self.mock_groq_prov,
            gemini_provider=self.mock_gemini_prov
        )

        self.teaching_content = {
            "explanation": "Cache mapping defines memory address to cache line correspondence.",
            "analogy": "Assigned lockers.",
            "examples": ["Direct", "Associative", "Set-associative"]
        }

    def test_groq_succeeds_gemini_not_called(self):
        """TEST 1: When Groq succeeds on attempt 1, Gemini is never called."""
        groq_candidates = [
            {
                "difficulty": "easy",
                "cognitive_operation": "apply",
                "estimated_time": 40,
                "question": "In direct mapping, how is the line index determined?",
                "options": ["Modulo calculation", "Random selection", "LRU hash", "Disk lookup"],
                "correct_index": 0
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 60,
                "question": "What happens when multiple memory blocks map to the exact same cache line?",
                "options": ["Conflict misses cause thrashing", "Capacity doubles", "CPU halts", "Addresses merge"],
                "correct_index": 0
            }
        ]
        self.mock_groq_prov.generate_candidate_questions.return_value = groq_candidates

        questions = self.generator.generate_questions_from_teaching(
            subject="Computer Architecture",
            concept="Memory Organization",
            atom="Cache Mapping",
            teaching_content=self.teaching_content,
            need_easy=1,
            need_medium=1,
            need_hard=0,
            previous_questions=[]
        )

        self.assertEqual(len(questions), 2)
        self.assertEqual(self.mock_groq_prov.generate_candidate_questions.call_count, 1)
        self.mock_gemini_prov.generate_candidate_questions.assert_not_called()

    def test_groq_404_model_not_found_immediately_calls_gemini(self):
        """TEST 2: When Groq returns 404 model_not_found, it switches to Gemini immediately without retrying Groq."""
        self.mock_groq_prov.generate_candidate_questions.side_effect = Exception("404 - model_not_found: llama-3.3-70b-versatile does not exist")

        gemini_candidates = [
            {
                "difficulty": "easy",
                "cognitive_operation": "apply",
                "estimated_time": 40,
                "question": "How does fully associative cache placement differ from direct mapping?",
                "options": ["Block can occupy any line", "No tag bits required", "Only one line available", "DRAM is bypassed"],
                "correct_index": 0
            }
        ]
        self.mock_gemini_prov.generate_candidate_questions.return_value = gemini_candidates

        questions = self.generator.generate_questions_from_teaching(
            subject="Computer Architecture",
            concept="Memory Organization",
            atom="Cache Mapping",
            teaching_content=self.teaching_content,
            need_easy=1,
            need_medium=0,
            need_hard=0,
            previous_questions=[]
        )

        self.assertEqual(len(questions), 1)
        # Groq called exactly once (because 404 is a permanent error and immediately switches to Gemini)
        self.assertEqual(self.mock_groq_prov.generate_candidate_questions.call_count, 1)
        # Gemini was called to generate the question
        self.assertEqual(self.mock_gemini_prov.generate_candidate_questions.call_count, 1)

    def test_groq_timeout_retries_then_gemini_fallback(self):
        """TEST 3: When Groq encounters a transient timeout, it retries once, then falls back to Gemini."""
        self.mock_groq_prov.generate_candidate_questions.side_effect = Exception("ReadTimeout connection timed out")

        gemini_candidates = [
            {
                "difficulty": "easy",
                "cognitive_operation": "apply",
                "estimated_time": 40,
                "question": "Why does a 2-way set-associative cache reduce conflict misses?",
                "options": ["Provides two placement options per set", "Doubles clock frequency", "Eliminates cache tags", "Replaces RAM"],
                "correct_index": 0
            }
        ]
        self.mock_gemini_prov.generate_candidate_questions.return_value = gemini_candidates

        questions = self.generator.generate_questions_from_teaching(
            subject="Computer Architecture",
            concept="Memory Organization",
            atom="Cache Mapping",
            teaching_content=self.teaching_content,
            need_easy=1,
            need_medium=0,
            need_hard=0,
            previous_questions=[]
        )

        self.assertEqual(len(questions), 1)
        # Groq retried up to GROQ_MAX_ATTEMPTS (2)
        self.assertEqual(self.mock_groq_prov.generate_candidate_questions.call_count, 2)
        # Gemini was invoked and succeeded
        self.assertEqual(self.mock_gemini_prov.generate_candidate_questions.call_count, 1)

    def test_groq_invalid_json_retries_then_gemini_fallback(self):
        """TEST 4: When Groq returns invalid JSON, it retries and falls back to Gemini if unrecovered."""
        self.mock_groq_prov.generate_candidate_questions.side_effect = Exception("JSONDecodeError: Expecting value: line 1 column 1")

        gemini_candidates = [
            {
                "difficulty": "easy",
                "cognitive_operation": "apply",
                "estimated_time": 40,
                "question": "What is the function of the cache line offset field?",
                "options": ["Selects specific byte or word within line", "Identifies cache set", "Compares tag directory", "Controls write buffer"],
                "correct_index": 0
            }
        ]
        self.mock_gemini_prov.generate_candidate_questions.return_value = gemini_candidates

        questions = self.generator.generate_questions_from_teaching(
            subject="Computer Architecture",
            concept="Memory Organization",
            atom="Cache Mapping",
            teaching_content=self.teaching_content,
            need_easy=1,
            need_medium=0,
            need_hard=0,
            previous_questions=[]
        )

        self.assertEqual(len(questions), 1)
        self.assertEqual(self.mock_groq_prov.generate_candidate_questions.call_count, 2)
        self.assertEqual(self.mock_gemini_prov.generate_candidate_questions.call_count, 1)

    def test_groq_partial_duplicate_gemini_fills_missing(self):
        """TEST 5 & 6: Groq produces 1 valid + 1 duplicate question; Gemini generates the missing 1 question."""
        # Groq returns 1 novel question and 1 duplicate
        groq_resp = [
            {
                "difficulty": "easy",
                "cognitive_operation": "apply",
                "estimated_time": 40,
                "question": "How does direct mapping determine line index?",
                "options": ["Modulo address", "Random", "LRU", "Disk"],
                "correct_index": 0
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 60,
                "question": "What is cache mapping in computer systems?",  # Duplicate of history
                "options": ["A mechanism for placing memory blocks in cache", "A disk format", "A CPU routine", "A protocol"],
                "correct_index": 0
            }
        ]
        # On attempt 2, Groq fails
        self.mock_groq_prov.generate_candidate_questions.side_effect = [
            groq_resp,
            Exception("Groq rate limit 429")
        ]

        # Gemini produces the missing 1 medium question
        gemini_resp = [
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 60,
                "question": "Under what access pattern will direct-mapped cache suffer severe thrashing?",
                "options": ["Alternating access to blocks mapping to same slot", "Purely sequential access", "Single block loops", "Zero-stride array access"],
                "correct_index": 0
            }
        ]
        self.mock_gemini_prov.generate_candidate_questions.return_value = gemini_resp

        history = [{"question": "What is cache mapping in computer systems?"}]
        questions = self.generator.generate_questions_from_teaching(
            subject="Computer Architecture",
            concept="Memory Organization",
            atom="Cache Mapping",
            teaching_content=self.teaching_content,
            need_easy=1,
            need_medium=1,
            need_hard=0,
            previous_questions=history
        )

        self.assertEqual(len(questions), 2)
        # Verify 1 came from Groq and 1 from Gemini
        q_texts = [q['question'] for q in questions]
        self.assertIn("How does direct mapping determine line index?", q_texts)
        self.assertIn("Under what access pattern will direct-mapped cache suffer severe thrashing?", q_texts)

    def test_both_providers_fail_raises_question_generation_error(self):
        """TEST 7: When both Groq and Gemini fail, raise QuestionGenerationError without static fallback."""
        self.mock_groq_prov.generate_candidate_questions.side_effect = Exception("Groq down")
        self.mock_gemini_prov.generate_candidate_questions.side_effect = Exception("Gemini down")

        with self.assertRaises(QuestionGenerationError):
            self.generator.generate_questions_from_teaching(
                subject="Computer Architecture",
                concept="Memory Organization",
                atom="Cache Mapping",
                teaching_content=self.teaching_content,
                need_easy=1,
                need_medium=1,
                need_hard=0,
                previous_questions=[]
            )


class APIViewAndAdaptiveEngineIntegrationTests(TestCase):
    """Integration tests for views, force_new, HTTP 503 errors, and adaptive engine."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="teststudent", password="password123")
        self.client.force_authenticate(user=self.user)

        self.profile = LearningProfile.objects.create(user=self.user, overall_theta=0.1)

        self.concept = Concept.objects.create(
            name="Arrays",
            subject="Data Structures",
            difficulty="easy"
        )
        self.atom = TeachingAtom.objects.create(
            name="Contiguous Memory",
            concept=self.concept,
            explanation="Arrays store elements in consecutive memory locations.",
            analogy="Houses lined up on a single street.",
            examples=["Index indexing", "Base pointer offset calculation"]
        )
        self.progress = StudentProgress.objects.create(
            user=self.user,
            atom=self.atom,
            mastery_score=0.2,
            phase="teaching"
        )
        self.session = LearningSession.objects.create(
            user=self.user,
            concept=self.concept,
            knowledge_level="intermediate",
            session_data={}
        )

    @patch.object(GroqQuestionProvider, 'generate_candidate_questions')
    def test_force_new_behavior_and_novelty(self, mock_groq_gen):
        """TEST 11: force_new=False reuses uncompleted batch; force_new=True generates fresh novel questions."""
        batch1 = [
            {
                "difficulty": "easy",
                "cognitive_operation": "apply",
                "estimated_time": 40,
                "question": "How is the physical memory address of array element arr[i] computed?",
                "options": ["base_address + i * element_size", "base_address * i", "base_address + i", "pointer_hash(i)"],
                "correct_index": 0
            },
            {
                "difficulty": "easy",
                "cognitive_operation": "apply",
                "estimated_time": 40,
                "question": "What primary hardware advantage results from storing elements in contiguous memory?",
                "options": ["Spatial locality and cache line prefetching", "Automatic dynamic resizing", "Garbage collection exemption", "Zero memory overhead"],
                "correct_index": 0
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 60,
                "question": "Why does inserting an element at index 0 of an array take O(n) time?",
                "options": ["All subsequent elements must be shifted right", "Memory must be re-initialized to zeros", "CPU cache is invalidated", "Operating system context switch occurs"],
                "correct_index": 0
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 60,
                "question": "What occurs if an application writes past the allocated contiguous bounds of an array?",
                "options": ["Buffer overflow corrupting adjacent memory", "Array automatically doubles capacity", "Compilation warning halts execution", "Index resets to zero"],
                "correct_index": 0
            }
        ]

        batch2 = [
            {
                "difficulty": "easy",
                "cognitive_operation": "apply",
                "estimated_time": 40,
                "question": "In a 64-bit architecture, how many bytes separate adjacent integer elements in a contiguous array?",
                "options": ["4 or 8 bytes depending on integer type size", "Always 1 byte", "16 bytes", "64 bytes"],
                "correct_index": 0
            },
            {
                "difficulty": "easy",
                "cognitive_operation": "apply",
                "estimated_time": 40,
                "question": "Which constant-time operation is directly enabled by contiguous memory allocation?",
                "options": ["Random index access in O(1)", "Arbitrary element deletion in O(1)", "Dynamic resizing in O(1)", "Sorted search in O(1)"],
                "correct_index": 0
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 60,
                "question": "How does memory fragmentation prevent allocation of a large contiguous array even when total free RAM is sufficient?",
                "options": ["No single uninterrupted memory block is large enough", "Virtual memory is disabled", "CPU registers are full", "RAM bandwidth is exceeded"],
                "correct_index": 0
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 60,
                "question": "Why do 2D matrices stored in row-major order exhibit better cache performance when traversed row by row?",
                "options": ["Consecutive memory addresses align with cache lines", "Columns have smaller data types", "Row headers are cached in CPU", "Pointers are not dereferenced"],
                "correct_index": 0
            }
        ]

        mock_groq_gen.side_effect = [batch1, batch2]

        # 1. First call with force_new=False
        resp1 = self.client.post('/auth/api/generate-questions-from-teaching/', {
            'session_id': self.session.id,
            'atom_id': self.atom.id,
            'force_new': False
        }, format='json')
        self.assertEqual(resp1.status_code, 200)
        q_set_1 = resp1.data['questions']
        self.assertEqual(len(q_set_1), 4)

        # 2. Second call with force_new=False -> should reuse existing questions
        resp2 = self.client.post('/auth/api/generate-questions-from-teaching/', {
            'session_id': self.session.id,
            'atom_id': self.atom.id,
            'force_new': False
        }, format='json')
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(resp2.data.get('reused', False))
        self.assertEqual(resp1.data['questions'][0]['question'], resp2.data['questions'][0]['question'])

        # 3. Third call with force_new=True -> should generate a fresh novel set
        resp3 = self.client.post('/auth/api/generate-questions-from-teaching/', {
            'session_id': self.session.id,
            'atom_id': self.atom.id,
            'force_new': True
        }, format='json')
        self.assertEqual(resp3.status_code, 200)
        self.assertFalse(resp3.data.get('reused', False))
        q_set_3 = resp3.data['questions']
        self.assertEqual(len(q_set_3), 4)

        # Verify questions in set 3 are novel compared to set 1
        for q3 in q_set_3:
            is_novel, sim, _ = is_novel_question(q3, q_set_1)
            self.assertTrue(is_novel, f"force_new=True returned duplicate: {q3['question']}")

    @patch.object(GroqQuestionProvider, 'generate_candidate_questions')
    @patch.object(GeminiQuestionProvider, 'generate_candidate_questions')
    def test_both_providers_failing_returns_http_503(self, mock_gemini_gen, mock_groq_gen):
        """TEST 7: When both providers fail, API returns HTTP 503 Service Unavailable."""
        mock_groq_gen.side_effect = Exception("Groq 500 error")
        mock_gemini_gen.side_effect = Exception("Gemini 500 error")

        resp = self.client.post('/auth/api/generate-questions-from-teaching/', {
            'session_id': self.session.id,
            'atom_id': self.atom.id,
            'force_new': True
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("error", resp.data)
        self.assertIn("temporarily unavailable", resp.data["error"])

    def test_existing_mastery_and_accuracy_pipeline_remains_functional(self):
        """TEST 12 & 13: Ensure calculate_updated_mastery and adaptive engine updates work with shuffled questions."""
        question = {
            "difficulty": "medium",
            "cognitive_operation": "apply",
            "estimated_time": 60,
            "question": "How is an element offset computed in a contiguous array?",
            "options": ["Random memory address", "Linked node lookup", "base_address + index * size", "Virtual page table"],
            "correct_index": 2  # Shuffled to Option C
        }

        # Calculate mastery update on correct answer
        initial_mastery = 0.3
        initial_theta = 0.0
        new_mastery, new_theta, metrics = calculate_updated_mastery(
            current_mastery=initial_mastery,
            current_theta=initial_theta,
            question=question,
            correct=True,
            time_taken=30.0,
            error_type=None
        )

        # Verify mastery and theta increase on correct answer
        self.assertGreater(new_mastery, initial_mastery)
        self.assertGreater(new_theta, initial_theta)
        self.assertIn('mastery_change', metrics)
        self.assertIn('theta_change', metrics)
        self.assertIn('confidence', metrics)
