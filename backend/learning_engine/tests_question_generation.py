# backend/learning_engine/tests_question_generation.py
"""
Comprehensive test suite for OpenRouter Question Generation Architecture.
Covers:
- TEST 1: Question generation via OpenRouter returns structured questions.
- TEST 2 & 3: Novelty filtering against past session history rejects duplicates and paraphrases.
- TEST 4 & 5: Backend option shuffling distributes correct answers across A/B/C/D and eliminates Option A bias.
- TEST 6: Robust JSON parsing of LLM responses.
- TEST 7: Malformed JSON handling does not crash.
- TEST 8: Simulated duplicate candidate is rejected by NOVELTY_GATE.
- TEST 9: Invalid/missing correct answer is rejected and never converted to 0.
- TEST 10: Centralized question generation service is used.
- TEST 11: Groq is no longer used in question generation.
- TEST 12: Gemini is no longer used in question generation.
- TEST 13: Missing API_KEY raises clear configuration error.
- TEST 14: Missing MODEL raises clear configuration error.
- TEST 15: Model name is read dynamically from environment variable MODEL.
- TEST 16: No sentence-transformers or local embedding models loaded.
- Adaptive learning engine mastery/accuracy calculation remains functional.
"""

import json
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import Concept, TeachingAtom, LearningSession, StudentProgress, LearningProfile
from learning_engine.question_generator import (
    QuestionGenerator,
    OpenRouterQuestionProvider,
    QuestionGenerationError,
    normalize_question_text,
    calculate_question_similarity,
    is_novel_question,
    shuffle_and_balance_options,
    _validate_single_question,
    safe_parse_json_questions,
    QUESTION_SIMILARITY_THRESHOLD
)
from learning_engine.knowledge_tracing import calculate_updated_mastery


class ArchitectureAndConfigurationTests(TestCase):
    """Tests for environment configuration, model dynamics, and provider retirement."""

    def test_no_sentence_transformers_or_local_embeddings(self):
        """TEST 16: Ensure no sentence-transformers or local embedding models are imported."""
        import sys
        self.assertNotIn('sentence_transformers', sys.modules)

    def test_missing_api_key_raises_configuration_error(self):
        """TEST 13: Temporarily missing API_KEY raises clear configuration error."""
        provider = OpenRouterQuestionProvider(api_key="", model_name="test-model")
        with self.assertRaises(QuestionGenerationError) as ctx:
            provider.generate_candidate_questions("Generate 1 question", 1)
        self.assertIn("API_KEY", str(ctx.exception))

    def test_missing_model_raises_configuration_error(self):
        """TEST 14: Temporarily missing MODEL raises clear configuration error."""
        provider = OpenRouterQuestionProvider(api_key="valid-key", model_name="")
        with self.assertRaises(QuestionGenerationError) as ctx:
            provider.generate_candidate_questions("Generate 1 question", 1)
        self.assertIn("MODEL", str(ctx.exception))

    def test_model_name_is_dynamic_and_not_hardcoded(self):
        """TEST 15: Verify model name is read dynamically from MODEL environment variable."""
        custom_model = "test-custom-provider/model-v1:free"
        provider = OpenRouterQuestionProvider(api_key="test-key", model_name=custom_model)
        self.assertEqual(provider.model_name, custom_model)

    def test_groq_and_gemini_removed_from_question_generator(self):
        """TEST 11 & 12: Verify Groq and Gemini are no longer used in question_generator.py."""
        import inspect
        import learning_engine.question_generator as qg_mod
        src = inspect.getsource(qg_mod)
        self.assertNotIn("GroqQuestionProvider", src)
        self.assertNotIn("GeminiQuestionProvider", src)
        self.assertNotIn("llama-3.1-8b-instant", src)
        self.assertNotIn("gemini-2.5-flash", src)


class LightweightSimilarityAndSchemaTests(TestCase):
    """Unit tests for novelty detection, schema validation, and option shuffling."""

    def test_normalize_question_text(self):
        """Test normalization: casing, punctuation, whitespace."""
        raw = "  What IS Cache   Mapping, and how does it work?!  "
        normalized = normalize_question_text(raw)
        self.assertEqual(normalized, "what is cache mapping and how does it work")

    def test_exact_and_near_duplicate_similarity(self):
        """TEST 8: Test exact and semantically similar questions are flagged by NOVELTY_GATE."""
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

        # Novelty gate rejection check
        is_novel, sim, matched = is_novel_question(q3, [q1])
        self.assertFalse(is_novel)
        self.assertEqual(matched, q1)

    def test_validate_single_question_strict_correct_index_and_answer(self):
        """TEST 9: Missing or invalid correct answer is rejected and NEVER defaulted to 0."""
        # Valid with correct_index
        valid_q1 = {
            "difficulty": "easy",
            "cognitive_operation": "apply",
            "estimated_time": 40,
            "question": "Where does block 0x10 map in a direct-mapped cache?",
            "options": ["Slot 0", "Slot 1", "Slot 2", "Slot 3"],
            "correct_index": 2
        }
        res1 = _validate_single_question(valid_q1)
        self.assertIsNotNone(res1)
        self.assertEqual(res1["correct_index"], 2)

        # Valid with correct_answer string
        valid_q2 = {
            "difficulty": "easy",
            "cognitive_operation": "apply",
            "estimated_time": 40,
            "question": "Where does block 0x10 map in a direct-mapped cache?",
            "options": ["Slot 0", "Slot 1", "Slot 2", "Slot 3"],
            "correct_answer": "Slot 2"
        }
        res2 = _validate_single_question(valid_q2)
        self.assertIsNotNone(res2)
        self.assertEqual(res2["correct_index"], 2)

        # Missing correct_answer / correct_index -> MUST BE REJECTED (None)
        missing_ca = {
            "difficulty": "easy",
            "cognitive_operation": "apply",
            "estimated_time": 40,
            "question": "Where does block 0x10 map in a direct-mapped cache?",
            "options": ["Slot 0", "Slot 1", "Slot 2", "Slot 3"]
        }
        self.assertIsNone(_validate_single_question(missing_ca))

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

        # Non-matching correct_answer string -> MUST BE REJECTED (None)
        non_matching_ca = {
            "difficulty": "easy",
            "cognitive_operation": "apply",
            "estimated_time": 40,
            "question": "Where does block 0x10 map in a direct-mapped cache?",
            "options": ["Slot 0", "Slot 1", "Slot 2", "Slot 3"],
            "correct_answer": "Non-existent option"
        }
        self.assertIsNone(_validate_single_question(non_matching_ca))

    def test_shuffle_and_balance_options(self):
        """TEST 4 & 5: Options are shuffled, correct_index accurately maps, positions vary across A/B/C/D."""
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

    def test_json_parsing_valid_and_malformed(self):
        """TEST 6 & 7: Test safe_parse_json_questions on valid, markdown-fenced, and malformed JSON."""
        # Valid JSON with questions list
        raw_valid = '{"questions": [{"question": "Q1 text?", "options": ["A", "B", "C", "D"], "correct_index": 0}]}'
        parsed1 = safe_parse_json_questions(raw_valid)
        self.assertEqual(len(parsed1), 1)
        self.assertEqual(parsed1[0]['question'], "Q1 text?")

        # Markdown-wrapped JSON
        raw_md = '```json\n{"questions": [{"question": "Q2 text?", "options": ["A", "B", "C", "D"], "correct_index": 1}]}\n```'
        parsed2 = safe_parse_json_questions(raw_md)
        self.assertEqual(len(parsed2), 1)
        self.assertEqual(parsed2[0]['question'], "Q2 text?")

        # Malformed / broken JSON does not crash and returns empty list
        raw_malformed = 'This is random text without JSON.'
        parsed3 = safe_parse_json_questions(raw_malformed)
        self.assertEqual(parsed3, [])


class OpenRouterQuestionGeneratorTests(TestCase):
    """Unit and integration tests for OpenRouter question generation orchestrator."""

    def setUp(self):
        self.mock_provider = MagicMock(spec=OpenRouterQuestionProvider)
        self.mock_provider.api_key = "test-openrouter-key"
        self.mock_provider.model_name = "test-model:free"
        self.mock_provider.is_permanent_error.return_value = False

        self.generator = QuestionGenerator(provider=self.mock_provider)

        self.teaching_content = {
            "explanation": "Arrays store elements in contiguous memory locations.",
            "analogy": "Consecutive mailboxes.",
            "examples": ["Direct indexing arr[i]"]
        }

    def test_openrouter_candidate_generation_success(self):
        """TEST 1: Verify successful OpenRouter candidate batch generation and return."""
        candidates = [
            {
                "difficulty": "easy",
                "cognitive_operation": "apply",
                "estimated_time": 40,
                "question": "What is the primary memory property of arrays?",
                "options": ["Contiguous memory allocation", "Linked pointers", "Dynamic hashing", "Tree hierarchy"],
                "correct_answer": "Contiguous memory allocation"
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 60,
                "question": "Why does array index lookup operate in O(1) time?",
                "options": ["Offset formula base + i * size", "Binary search", "Hash table lookup", "Pointer traversal"],
                "correct_answer": "Offset formula base + i * size"
            }
        ]
        self.mock_provider.generate_candidate_questions.return_value = candidates

        questions = self.generator.generate_questions_from_teaching(
            subject="Data Structures",
            concept="Arrays",
            atom="Contiguous Memory",
            teaching_content=self.teaching_content,
            need_easy=1,
            need_medium=1,
            need_hard=0,
            previous_questions=[]
        )

        self.assertEqual(len(questions), 2)
        self.assertEqual(self.mock_provider.generate_candidate_questions.call_count, 1)

    def test_repeated_generation_applies_novelty_gate(self):
        """TEST 2 & 3: Novelty gate rejects duplicates against history across generation attempts."""
        prev_q = {"question": "What is the primary memory property of arrays?"}

        # Attempt 1 returns 1 duplicate and 1 novel candidate
        attempt1_candidates = [
            {
                "difficulty": "easy",
                "cognitive_operation": "apply",
                "estimated_time": 40,
                "question": "What is the primary memory property of arrays?",  # Duplicate!
                "options": ["Contiguous memory", "Linked nodes", "Hash table", "Trees"],
                "correct_answer": "Contiguous memory"
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 60,
                "question": "Why does array index lookup operate in O(1) time?",  # Novel
                "options": ["Base plus offset computation", "Binary search", "Hashing", "Linear scan"],
                "correct_answer": "Base plus offset computation"
            }
        ]

        # Attempt 2 produces the missing 1 easy question
        attempt2_candidates = [
            {
                "difficulty": "easy",
                "cognitive_operation": "apply",
                "estimated_time": 40,
                "question": "How are elements arranged physically in array storage?",  # Novel replacement
                "options": ["In consecutive memory addresses", "Scattered randomly", "In linked blocks", "On secondary disk only"],
                "correct_answer": "In consecutive memory addresses"
            }
        ]

        self.mock_provider.generate_candidate_questions.side_effect = [
            attempt1_candidates,
            attempt2_candidates
        ]

        questions = self.generator.generate_questions_from_teaching(
            subject="Data Structures",
            concept="Arrays",
            atom="Contiguous Memory",
            teaching_content=self.teaching_content,
            need_easy=1,
            need_medium=1,
            need_hard=0,
            previous_questions=[prev_q]
        )

        self.assertEqual(len(questions), 2)
        self.assertEqual(self.mock_provider.generate_candidate_questions.call_count, 2)
        q_texts = [q['question'] for q in questions]
        self.assertNotIn("What is the primary memory property of arrays?", q_texts)
        self.assertIn("Why does array index lookup operate in O(1) time?", q_texts)
        self.assertIn("How are elements arranged physically in array storage?", q_texts)

    def test_provider_exhaustion_raises_question_generation_error(self):
        """Verify that provider failure across all attempts raises QuestionGenerationError without static fallback."""
        self.mock_provider.generate_candidate_questions.side_effect = Exception("OpenRouter 500 error")

        with self.assertRaises(QuestionGenerationError):
            self.generator.generate_questions_from_teaching(
                subject="Data Structures",
                concept="Arrays",
                atom="Contiguous Memory",
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
            difficulty="easy",
            created_by=self.user
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

    @patch.object(OpenRouterQuestionProvider, 'generate_candidate_questions')
    def test_initial_quiz_endpoint_generates_questions(self, mock_gen):
        """TEST 10: Verify /auth/api/initial-quiz/ uses centralized QuestionGenerator."""
        candidates = [
            {
                "difficulty": "easy",
                "cognitive_operation": "recall",
                "estimated_time": 30,
                "question": "What is the primary memory property of arrays?",
                "options": ["Contiguous memory", "Linked nodes", "Dynamic hashing", "Tree hierarchy"],
                "correct_answer": "Contiguous memory"
            },
            {
                "difficulty": "easy",
                "cognitive_operation": "apply",
                "estimated_time": 30,
                "question": "How is the physical memory address of element arr[i] calculated?",
                "options": ["base + i * size", "base * i", "base + i", "pointer_hash(i)"],
                "correct_answer": "base + i * size"
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 45,
                "question": "Why does inserting an item at the beginning of an array take O(n) time?",
                "options": ["All elements must be shifted", "Memory is reallocated", "CPU cache is cleared", "Page fault occurs"],
                "correct_answer": "All elements must be shifted"
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 45,
                "question": "What hardware performance benefit arises from spatial locality in arrays?",
                "options": ["CPU cache line prefetching", "Automatic garbage collection", "Zero fragmentation", "Thread safety"],
                "correct_answer": "CPU cache line prefetching"
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "apply",
                "estimated_time": 45,
                "question": "Which constant-time operation is directly enabled by contiguous allocation?",
                "options": ["Random index access in O(1)", "Arbitrary deletion in O(1)", "Dynamic resizing", "Sorted binary search"],
                "correct_answer": "Random index access in O(1)"
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 45,
                "question": "What occurs when an application writes past allocated array bounds?",
                "options": ["Buffer overflow", "Automatic expansion", "Zeroing memory", "Compiler warning only"],
                "correct_answer": "Buffer overflow"
            }
        ]
        mock_gen.return_value = candidates

        resp = self.client.post('/auth/api/initial-quiz/', {
            'session_id': self.session.id
        }, format='json')

        self.assertEqual(resp.status_code, 200)
        self.assertIn('questions', resp.data)
        self.assertEqual(len(resp.data['questions']), 5)

    @patch.object(OpenRouterQuestionProvider, 'generate_candidate_questions')
    def test_provider_failure_returns_http_503(self, mock_gen):
        """Verify API returns HTTP 503 when OpenRouter fails."""
        mock_gen.side_effect = Exception("OpenRouter down")

        resp = self.client.post('/auth/api/generate-questions-from-teaching/', {
            'session_id': self.session.id,
            'atom_id': self.atom.id,
            'force_new': True
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("error", resp.data)

    @patch('learning_engine.question_generator.call_openrouter')
    def test_generate_concept_view_creates_atoms_via_openrouter(self, mock_call):
        """Verify GenerateConceptView generates atoms for new concepts using OpenRouter."""
        mock_call.return_value = '{"atoms": ["Declaration", "Index Access", "Memory Layout", "Bounds Checking"]}'

        resp = self.client.post('/auth/api/generate-concept/', {
            'subject': 'Computer Science',
            'concept': 'Dynamic Arrays',
            'knowledge_level': 'intermediate'
        }, format='json')

        self.assertEqual(resp.status_code, 200)
        self.assertIn('atoms', resp.data)
        self.assertEqual(len(resp.data['atoms']), 4)
        self.assertIn('Generated 4 atoms for Dynamic Arrays', resp.data['message'])

    def test_generate_concept_view_returns_existing_atoms_without_unbound_error(self):
        """Verify GenerateConceptView does not raise UnboundLocalError when concept already has atoms."""
        resp = self.client.post('/auth/api/generate-concept/', {
            'subject': 'Data Structures',
            'concept': 'Arrays',
            'knowledge_level': 'intermediate'
        }, format='json')

        self.assertEqual(resp.status_code, 200)
        self.assertIn('atoms', resp.data)
        self.assertEqual(len(resp.data['atoms']), 1)
        self.assertIn('Generated 1 atoms for Arrays', resp.data['message'])

    @patch('learning_engine.question_generator.call_openrouter')
    def test_generate_concept_view_returns_503_on_atom_generation_failure(self, mock_call):
        """Verify GenerateConceptView returns controlled HTTP 503 when OpenRouter fails."""
        mock_call.side_effect = Exception("OpenRouter 503 error")

        resp = self.client.post('/auth/api/generate-concept/', {
            'subject': 'Computer Science',
            'concept': 'Failing Concept',
            'knowledge_level': 'intermediate'
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('error', resp.data)

    @patch('learning_engine.adaptive_flow.call_openrouter')
    def test_adaptive_flow_generate_teaching_content_uses_openrouter(self, mock_call):
        """Verify AdaptiveLearningEngine.generate_teaching_content uses OpenRouter."""
        mock_call.return_value = json.dumps({
            "explanation": "Arrays store items in contiguous memory.",
            "example": "Shopping list in numbered rows.",
            "analogy": "Consecutive lockers in a gym.",
            "misconception": "Arrays resize dynamically in all languages.",
            "practical_application": "Fast cache-friendly data processing."
        })

        from learning_engine.adaptive_flow import AdaptiveLearningEngine
        engine = AdaptiveLearningEngine()
        content = engine.generate_teaching_content(
            atom_name="Contiguous Storage",
            subject="Data Structures",
            concept="Arrays",
            knowledge_level="intermediate"
        )

        self.assertEqual(content["analogy"], "Consecutive lockers in a gym.")
        self.assertTrue(mock_call.called)

    def test_existing_mastery_and_accuracy_pipeline_remains_functional(self):
        """Ensure calculate_updated_mastery and adaptive engine updates work with shuffled questions."""
        question = {
            "difficulty": "medium",
            "cognitive_operation": "apply",
            "estimated_time": 60,
            "question": "How is an element offset computed in a contiguous array?",
            "options": ["Random memory address", "Linked node lookup", "base_address + index * size", "Virtual page table"],
            "correct_index": 2  # Shuffled to Option C
        }

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

        self.assertGreater(new_mastery, initial_mastery)
        self.assertGreater(new_theta, initial_theta)
        self.assertIn('mastery_change', metrics)
        self.assertIn('theta_change', metrics)
        self.assertIn('confidence', metrics)

    @patch.object(OpenRouterQuestionProvider, 'generate_candidate_questions')
    def test_duplicate_initial_quiz_request_returns_cached_questions(self, mock_gen):
        """Verify that concurrent or duplicate calls to /auth/api/initial-quiz/ return cached questions without extra LLM requests."""
        candidates = [
            {
                "difficulty": "easy",
                "cognitive_operation": "recall",
                "estimated_time": 30,
                "question": "What is an array?",
                "options": ["Contiguous memory block", "Linked list", "Tree", "Graph"],
                "correct_answer": "Contiguous memory block"
            },
            {
                "difficulty": "easy",
                "cognitive_operation": "apply",
                "estimated_time": 30,
                "question": "How to access index 0?",
                "options": ["arr[0]", "arr.get(0)", "arr->0", "arr.first()"],
                "correct_answer": "arr[0]"
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 45,
                "question": "What is the time complexity of random access?",
                "options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"],
                "correct_answer": "O(1)"
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 45,
                "question": "What happens on insertion at start?",
                "options": ["Elements shift right", "Elements shift left", "No change", "Error thrown"],
                "correct_answer": "Elements shift right"
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "apply",
                "estimated_time": 45,
                "question": "Which memory layout is used?",
                "options": ["Linear contiguous addresses", "Non-linear addresses", "Disk blocks", "Registers"],
                "correct_answer": "Linear contiguous addresses"
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 45,
                "question": "What is the space overhead?",
                "options": ["Minimal / None for pointers", "High overhead", "Variable per element", "Double size"],
                "correct_answer": "Minimal / None for pointers"
            }
        ]
        mock_gen.return_value = candidates

        # First request
        resp1 = self.client.post('/auth/api/initial-quiz/', {'session_id': self.session.id}, format='json')
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(len(resp1.data['questions']), 5)
        self.assertEqual(mock_gen.call_count, 1)

        # Duplicate second request
        resp2 = self.client.post('/auth/api/initial-quiz/', {'session_id': self.session.id}, format='json')
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(resp2.data.get('reused'))
        self.assertEqual(len(resp2.data['questions']), 5)
        # LLM must NOT be called again
        self.assertEqual(mock_gen.call_count, 1)

    @patch.object(OpenRouterQuestionProvider, 'generate_candidate_questions')
    def test_duplicate_teaching_questions_request_returns_cached_questions(self, mock_gen):
        """Verify that duplicate calls to generate-questions-from-teaching without force_new return cached questions."""
        candidates = [
            {
                "difficulty": "easy",
                "cognitive_operation": "recall",
                "estimated_time": 30,
                "question": "What is contiguous memory?",
                "options": ["Adjacent memory cells", "Scattered memory cells", "Virtual cache", "Secondary storage"],
                "correct_answer": "Adjacent memory cells"
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "apply",
                "estimated_time": 45,
                "question": "How does cache prefetching benefit arrays?",
                "options": ["Loads consecutive memory words", "Clears cache", "Sorts items", "Free memory"],
                "correct_answer": "Loads consecutive memory words"
            },
            {
                "difficulty": "medium",
                "cognitive_operation": "analyze",
                "estimated_time": 45,
                "question": "What causes spatial locality?",
                "options": ["Consecutive memory accesses", "Random memory accesses", "Branch misprediction", "Page faults"],
                "correct_answer": "Consecutive memory accesses"
            },
            {
                "difficulty": "hard",
                "cognitive_operation": "analyze",
                "estimated_time": 60,
                "question": "How does hardware translation handle row-major multi-dimensional indexing?",
                "options": ["Row stride offset multiplication", "Pointer indirection array", "Hash bucket lookup", "Dynamic relocation table"],
                "correct_answer": "Row stride offset multiplication"
            },
            {
                "difficulty": "hard",
                "cognitive_operation": "apply",
                "estimated_time": 60,
                "question": "Under what memory access pattern does an array suffer high cache miss penalty?",
                "options": ["Non-unit large column stride access", "Sequential traversal", "Reverse traversal", "Contiguous iteration"],
                "correct_answer": "Non-unit large column stride access"
            }
        ]
        mock_gen.return_value = candidates

        # First request
        resp1 = self.client.post('/auth/api/generate-questions-from-teaching/', {
            'session_id': self.session.id,
            'atom_id': self.atom.id
        }, format='json')
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(mock_gen.call_count, 1)

        # Duplicate request (e.g. fast double-click or concurrent render)
        resp2 = self.client.post('/auth/api/generate-questions-from-teaching/', {
            'session_id': self.session.id,
            'atom_id': self.atom.id
        }, format='json')
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(resp2.data.get('reused'))
        # LLM must NOT be called again
        self.assertEqual(mock_gen.call_count, 1)

    def test_permanent_error_fails_fast_without_retrying(self):
        """Verify that permanent errors (e.g. 401 Unauthorized, 404 Model Not Found) terminate immediately on Attempt 1."""
        mock_provider = MagicMock(spec=OpenRouterQuestionProvider)
        mock_provider.api_key = "bad-key"
        mock_provider.model_name = "test-model"
        mock_provider.is_permanent_error.return_value = True
        mock_provider.generate_candidate_questions.side_effect = Exception("OpenRouter API returned HTTP 401: Unauthorized")

        gen = QuestionGenerator(provider=mock_provider)
        with self.assertRaises(QuestionGenerationError):
            gen.generate_questions_from_teaching(
                subject="Computer Science",
                concept="Arrays",
                atom="Contiguous Memory",
                teaching_content={"explanation": "test"},
                need_easy=1,
                need_medium=1,
                need_hard=0
            )

        # Permanent error must fail fast after exactly 1 attempt
        self.assertEqual(mock_provider.generate_candidate_questions.call_count, 1)

    def test_transient_error_allows_one_retry(self):
        """Verify that transient errors (e.g. 429 Rate Limit, timeout) are retried at most once (2 total attempts)."""
        mock_provider = MagicMock(spec=OpenRouterQuestionProvider)
        mock_provider.api_key = "valid-key"
        mock_provider.model_name = "test-model"
        mock_provider.is_permanent_error.return_value = False
        mock_provider.generate_candidate_questions.side_effect = Exception("OpenRouter connection timed out")

        gen = QuestionGenerator(provider=mock_provider)
        with self.assertRaises(QuestionGenerationError):
            gen.generate_questions_from_teaching(
                subject="Computer Science",
                concept="Arrays",
                atom="Contiguous Memory",
                teaching_content={"explanation": "test"},
                need_easy=1,
                need_medium=1,
                need_hard=0
            )

        # Transient error allows at most 2 attempts
        self.assertEqual(mock_provider.generate_candidate_questions.call_count, 2)


