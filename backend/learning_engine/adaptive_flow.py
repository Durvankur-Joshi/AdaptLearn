# backend/learning_engine/adaptive_flow.py - TRUE Adaptive Learning Engine
# ─────────────────────────────────────────────────────────────
# Core function: get_next_learning_step(user, concept, session)
#
# ENGINE STATES MODEL:
#   NOT_STARTED → LEARNING → PRACTICING → MASTERED → FRAGILE
#
# ADAPTIVE LOOP:
#   Select weakest atom → Decide action (TEACH/PRACTICE/ADVANCE)
#   → Deliver content → Student answers → Update mastery
#   → Update velocity → Detect fragile → Select next atom
#
# STOP CONDITION: Subject complete when all atoms mastery >= 80%
# ─────────────────────────────────────────────────────────────

import json
import random
import re
from typing import Dict, List, Optional, Tuple, Any
from django.conf import settings
from groq import Groq
from .models import TeachingAtomState, LearningPhase
from .knowledge_tracing import calculate_updated_mastery, classify_error_type
from .pacing_engine import (
    PacingEngine, PacingContext, PacingDecision, NextAction,
    PacingResult, FatigueLevel,
)


# ════════════════════════════════════════════════════════════════
#  Constants for the adaptive engine
# ════════════════════════════════════════════════════════════════
MASTERY_THRESHOLD = 0.80       # Atom mastered when >= 80%
TEACH_THRESHOLD = 0.40         # Below 40% → TEACH
PRACTICE_THRESHOLD = 0.80      # 40-80% → PRACTICE, >=80 → ADVANCE
FRAGILE_DECAY = 0.15           # Mastery penalty when fragile detected
FRAGILE_TIME_RATIO = 2.0       # Correct but >2x expected time → fragile


class AdaptiveLearningEngine:
    """
    TRUE Adaptive Learning Engine — Decision-based learning system.
    
    Core function: get_next_learning_step(user, concept, session)
    
    Performs:
        1. Select atom (weakest eligible, priority-based)
        2. Decide action (TEACH / PRACTICE / ADVANCE)
        3. Fetch content
        4. Return response
    """
    
    def __init__(self):
        self.groq_client = None
        groq_key = getattr(settings, 'GROQ_API_KEY', '')
        if groq_key:
            self.groq_client = Groq(api_key=groq_key)
        
        self.pacing_engine = PacingEngine()

    # ════════════════════════════════════════════════════════════════
    #  CORE ENGINE FUNCTION (Main Brain)
    # ════════════════════════════════════════════════════════════════

    def get_next_learning_step(self, user, concept, session=None) -> Dict[str, Any]:
        """
        THE single most important function — the adaptive engine brain.
        
        Performs:
            1. Select atom (weakest eligible, priority-based)
            2. Decide action (TEACH / PRACTICE / ADVANCE)
            3. Return response with atom + action + metadata
        
        Atom States:
            NOT_STARTED → TEACHING (LEARNING) → PRACTICE (PRACTICING)
            → COMPLETE (MASTERED) → FRAGILE (if performance drops)
        
        Priority order for atom selection:
            1. Fragile atom (mastered but performance dropped)
            2. Weakest active atom (lowest mastery, currently learning)
            3. New atom (not started yet)
            4. Reinforcement atom
        
        Args:
            user: Django User object
            concept: Concept model instance
            session: Optional LearningSession for additional context
        
        Returns:
            Dict with action, atom info, mastery, phase, message
        """
        from accounts.models import StudentProgress, TeachingAtom

        atoms = TeachingAtom.objects.filter(concept=concept).order_by('order')
        if not atoms.exists():
            return {'action': 'NO_ATOMS', 'message': 'No atoms found for this concept.'}

        # ── Build progress map for all atoms ──
        atom_progress_list = []
        for atom in atoms:
            progress, created = StudentProgress.objects.get_or_create(
                user=user, atom=atom,
                defaults={'mastery_score': 0.0, 'phase': 'not_started'}
            )
            atom_progress_list.append({
                'atom': atom,
                'progress': progress,
                'mastery': float(progress.mastery_score),
                'phase': progress.phase,
                'streak': progress.streak,
                'error_history': progress.error_history or [],
                'times_practiced': progress.times_practiced or 0,
            })

        # ── Check STOP CONDITION: all atoms mastered ──
        all_mastered = all(
            p['mastery'] >= MASTERY_THRESHOLD for p in atom_progress_list
        )
        if all_mastered:
            return {
                'action': 'SUBJECT_COMPLETE',
                'message': 'Congratulations! All atoms mastered. Subject complete.',
                'all_mastered': True,
                'atoms': [
                    {'id': p['atom'].id, 'name': p['atom'].name,
                     'mastery': round(p['mastery'], 4), 'phase': p['phase']}
                    for p in atom_progress_list
                ],
            }

        # ── Find candidate atoms (not yet mastered) ──
        candidates = [
            p for p in atom_progress_list
            if p['mastery'] < MASTERY_THRESHOLD and p['phase'] != 'complete'
        ]

        # Also include fragile atoms (were mastered, but performance dropped)
        fragile = [
            p for p in atom_progress_list if p['phase'] == 'fragile'
        ]
        # Merge fragile into candidates if not already there
        fragile_ids = {p['atom'].id for p in fragile}
        candidate_ids = {p['atom'].id for p in candidates}
        for f in fragile:
            if f['atom'].id not in candidate_ids:
                candidates.append(f)

        if not candidates:
            # Edge case: all atoms either complete or no viable candidates
            # Re-check if truly all mastered
            return {
                'action': 'SUBJECT_COMPLETE',
                'message': 'All atoms mastered!',
                'all_mastered': True,
                'atoms': [
                    {'id': p['atom'].id, 'name': p['atom'].name,
                     'mastery': round(p['mastery'], 4), 'phase': p['phase']}
                    for p in atom_progress_list
                ],
            }

        # ── Priority sort (Step 1.2) ──
        # 1. Fragile atoms (highest priority — knowledge decaying)
        # 2. Weakest active atoms (lowest mastery, currently being learned)
        # 3. New atoms (not_started — follow curriculum order)
        def atom_priority(item):
            phase = item['phase']
            mastery = item['mastery']

            if phase == 'fragile':
                return (0, mastery)  # Highest priority, weakest first
            elif phase in ('teaching', 'practice', 'reinforcement',
                           'mastery_check', 'diagnostic'):
                return (1, mastery)  # Active atoms, weakest first
            elif phase == 'not_started':
                return (2, item['atom'].order)  # New atoms by order
            else:
                return (3, mastery)

        candidates.sort(key=atom_priority)

        target = candidates[0]
        target_atom = target['atom']
        target_progress = target['progress']
        target_mastery = target['mastery']
        target_phase = target['phase']

        # ── Decide LEARNING ACTION (Phase 2) ──
        if target_mastery < TEACH_THRESHOLD:
            action = 'TEACH'
            if target_phase in ('not_started', 'diagnostic', 'fragile'):
                target_progress.phase = 'teaching'
                target_progress.save()
            message = f"Let's learn about {target_atom.name}."

        elif target_mastery < PRACTICE_THRESHOLD:
            action = 'PRACTICE'
            if target_phase not in ('practice', 'mastery_check'):
                target_progress.phase = 'practice'
                target_progress.save()
            message = f"Let's practice {target_atom.name} to strengthen understanding."

        else:
            # Mastery >= 80% — mark complete
            action = 'ADVANCE'
            target_progress.phase = 'complete'
            target_progress.save()
            message = f"{target_atom.name} mastered! Moving to next concept."

        return {
            'action': action,
            'atom': target_atom,
            'mastery': round(target_mastery, 4),
            'phase': target_progress.phase,
            'message': message,
            'all_mastered': False,
            'progress_summary': [
                {
                    'id': p['atom'].id,
                    'name': p['atom'].name,
                    'mastery': round(p['mastery'], 4),
                    'phase': p['phase'],
                }
                for p in atom_progress_list
            ],
        }

    # ════════════════════════════════════════════════════════════════
    #  ATOM STATE TRANSITIONS
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def update_atom_state(progress, new_mastery: float, correct: bool) -> str:
        """
        Update atom state based on mastery score.
        
        State transitions:
            NOT_STARTED → TEACHING     (when learning begins)
            TEACHING    → PRACTICE     (mastery >= 40%)
            PRACTICE    → COMPLETE     (mastery >= 80% + streak >= 2)
            COMPLETE    → FRAGILE      (if performance drops)
            FRAGILE     → PRACTICE     (when re-practicing)
        
        Returns:
            New phase string
        """
        old_phase = progress.phase

        if new_mastery >= MASTERY_THRESHOLD and progress.streak >= 2:
            progress.phase = 'complete'
        elif new_mastery >= TEACH_THRESHOLD:
            if old_phase in ('not_started', 'teaching', 'diagnostic'):
                progress.phase = 'practice'
            elif old_phase == 'fragile':
                progress.phase = 'practice'
            # If already in practice/mastery_check, stay there
        elif old_phase in ('not_started', 'diagnostic'):
            progress.phase = 'teaching'

        progress.mastery_score = new_mastery
        progress.save()
        return progress.phase

    # ════════════════════════════════════════════════════════════════
    #  FRAGILE KNOWLEDGE DETECTION
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def detect_fragile_knowledge(progress, correct: bool,
                                  time_taken: float,
                                  estimated_time: float = 60.0) -> bool:
        """
        Detect if a mastered/completed atom has become fragile.
        
        Conditions:
            - Atom was mastered (phase='complete')
            - Wrong answer on mastered content → FRAGILE
            - Correct but very slow (>2x expected) → FRAGILE
        
        Returns:
            True if atom is now fragile
        """
        if progress.phase != 'complete':
            return False

        time_ratio = time_taken / estimated_time if estimated_time > 0 else 1.0

        # Wrong answer on mastered content
        if not correct:
            progress.phase = 'fragile'
            progress.mastery_score = max(0.0, float(progress.mastery_score) - FRAGILE_DECAY)
            progress.save()
            return True

        # Correct but very slow response
        if correct and time_ratio > FRAGILE_TIME_RATIO:
            progress.phase = 'fragile'
            progress.mastery_score = max(0.0, float(progress.mastery_score) - 0.05)
            progress.save()
            return True

        return False

    # ════════════════════════════════════════════════════════════════
    #  LEARNING VELOCITY
    # ════════════════════════════════════════════════════════════════

    @staticmethod
    def update_learning_velocity(user, concept, session=None) -> Dict[str, float]:
        """
        Calculate learning velocity.
        
        Formula: atoms_mastered / total_time_minutes
        """
        from accounts.models import StudentProgress, TeachingAtom
        from django.utils import timezone as tz

        atoms = TeachingAtom.objects.filter(concept=concept)
        progress_records = StudentProgress.objects.filter(
            user=user, atom__in=atoms
        )
        atoms_mastered = progress_records.filter(phase='complete').count()
        total_atoms = atoms.count()

        total_time = 0.0
        if session:
            elapsed = (tz.now() - session.start_time).total_seconds() / 60.0
            total_time = max(elapsed, 1.0)
        else:
            total_time = max(1.0, sum(
                float(p.times_practiced or 1) * 5.0
                for p in progress_records
            ))

        velocity = atoms_mastered / total_time if total_time > 0 else 0.0

        return {
            'atoms_mastered': atoms_mastered,
            'total_atoms': total_atoms,
            'total_time_minutes': round(total_time, 2),
            'velocity': round(velocity, 4),
            'completion_pct': round(atoms_mastered / max(total_atoms, 1) * 100, 1),
        }

    def determine_pacing(self, diagnostic_results: Dict, knowledge_level: str) -> str:
        """
        Compatibility helper for legacy callers.
        Translates aggregate diagnostics into a PacingContext and returns a pacing decision string.
        """
        accuracy = float(diagnostic_results.get('accuracy', 0))
        mastery = float(diagnostic_results.get('mastery', 0))
        streak = int(diagnostic_results.get('streak', 0))
        error_types = diagnostic_results.get('error_types', []) or []
        theta = float(diagnostic_results.get('theta', 0.0))
        questions_answered = int(diagnostic_results.get('questions_answered', 0))

        context = PacingContext(
            accuracy=accuracy,
            mastery_score=mastery,
            streak=streak,
            error_types=error_types,
            theta=theta,
            questions_answered=questions_answered,
            knowledge_level=knowledge_level,
            phase=diagnostic_results.get('phase', 'practice'),
            # Enriched signals from diagnostic_results
            avg_response_time=float(diagnostic_results.get('avg_response_time', 0)),
            expected_response_time=float(diagnostic_results.get('expected_response_time', 60)),
            time_per_question_history=diagnostic_results.get('time_per_question_history', []),
            hint_usage_count=int(diagnostic_results.get('hint_usage_count', 0)),
            session_duration_minutes=float(diagnostic_results.get('session_duration_minutes', 0)),
            total_questions_session=int(diagnostic_results.get('total_questions_session', 0)),
            recent_accuracy_trend=diagnostic_results.get('recent_accuracy_trend', []),
            recent_response_times=diagnostic_results.get('recent_response_times', []),
            last_practiced_minutes_ago=float(diagnostic_results.get('last_practiced_minutes_ago', 0)),
            retention_score=float(diagnostic_results.get('retention_score', 1.0)),
            retention_checks_passed=int(diagnostic_results.get('retention_checks_passed', 0)),
            engagement_score=float(diagnostic_results.get('engagement_score', 0.7)),
            diagnostic_accuracy=diagnostic_results.get('diagnostic_accuracy'),
        )

        result: PacingResult = self.pacing_engine.decide_pacing(context)
        return result.decision.value if hasattr(result.decision, 'value') else result.decision

    def determine_pacing_full(self, diagnostic_results: Dict, knowledge_level: str, session=None) -> Dict[str, Any]:
        """
        Full pacing decision with all 10-feature signals.
        Returns a rich dict with decision, fatigue, retention, hints, velocity, etc.
        Optionally accepts a session object to enrich context with session-level data.
        """
        accuracy = float(diagnostic_results.get('accuracy', 0))
        mastery = float(diagnostic_results.get('mastery', 0))
        streak = int(diagnostic_results.get('streak', 0))
        error_types = diagnostic_results.get('error_types', []) or []
        theta = float(diagnostic_results.get('theta', 0.0))
        questions_answered = int(diagnostic_results.get('questions_answered', 0))

        context = PacingContext(
            accuracy=accuracy,
            mastery_score=mastery,
            streak=streak,
            error_types=error_types,
            theta=theta,
            questions_answered=questions_answered,
            knowledge_level=knowledge_level,
            phase=diagnostic_results.get('phase', 'practice'),
            avg_response_time=float(diagnostic_results.get('avg_response_time', 0)),
            expected_response_time=float(diagnostic_results.get('expected_response_time', 60)),
            time_per_question_history=diagnostic_results.get('time_per_question_history', []),
            hint_usage_count=int(diagnostic_results.get('hint_usage_count', 0)),
            session_duration_minutes=float(diagnostic_results.get('session_duration_minutes', 0)),
            total_questions_session=int(diagnostic_results.get('total_questions_session', 0)),
            recent_accuracy_trend=diagnostic_results.get('recent_accuracy_trend', []),
            recent_response_times=diagnostic_results.get('recent_response_times', []),
            last_practiced_minutes_ago=float(diagnostic_results.get('last_practiced_minutes_ago', 0)),
            retention_score=float(diagnostic_results.get('retention_score', 1.0)),
            retention_checks_passed=int(diagnostic_results.get('retention_checks_passed', 0)),
            retention_checks_failed=int(diagnostic_results.get('retention_checks_failed', 0)),
            engagement_score=float(diagnostic_results.get('engagement_score', 0.7)),
            consecutive_skips=int(diagnostic_results.get('consecutive_skips', 0)),
            drop_off_risk=float(diagnostic_results.get('drop_off_risk', 0)),
            diagnostic_accuracy=diagnostic_results.get('diagnostic_accuracy'),
        )

        # Enrich context from session object if available
        if session is not None:
            from django.utils import timezone as tz
            elapsed = (tz.now() - session.start_time).total_seconds() / 60.0
            context.session_duration_minutes = max(context.session_duration_minutes, elapsed)
            context.consecutive_skips = getattr(session, 'consecutive_skips', 0)
            perf = (session.session_data or {}).get('performance_history', [])
            if perf and not context.time_per_question_history:
                context.time_per_question_history = [p.get('time_taken', 30) for p in perf]

        result: PacingResult = self.pacing_engine.decide_pacing(context)

        return {
            'pacing': result.decision.value,
            'decision': result.decision.value,
            'next_action': result.next_action.value,
            'fatigue': result.fatigue.value,
            'recommended_difficulty': result.recommended_difficulty,
            'mastery_verdict': result.mastery_verdict,
            'retention_action': result.retention_action,
            'hint_warning': result.hint_warning,
            'velocity_snapshot': result.velocity_snapshot,
            'engagement_adjustment': result.engagement_adjustment,
            'reasoning': result.reasoning,
        }
    
    def evaluate_initial_quiz(
        self,
        quiz_questions: List[Dict],
        quiz_answers: List[Dict],
        knowledge_level: str,
        current_theta: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Evaluate the initial diagnostic quiz using full adaptive flow.

        Processes every answer through IRT theta updates, BKT mastery updates,
        and error classification to produce a seeded mastery score, updated
        theta, error analysis, and an adaptive next-action recommendation.

        Returns a rich dict consumed by CompleteInitialQuizView.
        """
        from .knowledge_tracing import (
            calculate_updated_mastery, classify_error_type, update_theta,
            bkt_update, classify_behavior,
        )

        theta = current_theta
        mastery = 0.3  # Starting prior
        streak = 0
        error_types: List[str] = []
        correct_count = 0
        total_time = 0.0
        per_question_metrics: List[Dict] = []

        for ans in quiz_answers:
            idx = ans.get('question_index', 0)
            if idx < 0 or idx >= len(quiz_questions):
                continue
            question = quiz_questions[idx]
            selected = ans.get('selected')
            time_taken = float(ans.get('time_taken', 30))
            total_time += time_taken

            correct = ans.get('correct', False)

            # Classify error if wrong
            error_type = None
            if not correct and selected is not None:
                error_type = classify_error_type(
                    question, selected, time_taken,
                    atom_name='initial_quiz'
                )
                if error_type:
                    error_types.append(error_type)

            # Real-time mastery + theta update through the full pipeline
            new_mastery, new_theta, metrics = calculate_updated_mastery(
                current_mastery=mastery,
                current_theta=theta,
                question=question,
                correct=correct,
                time_taken=time_taken,
                error_type=error_type,
            )

            mastery = new_mastery
            theta = new_theta

            if correct:
                correct_count += 1
                streak = max(streak + 1, 1)
            else:
                streak = min(streak - 1, -1)

            per_question_metrics.append({
                'question_index': idx,
                'correct': correct,
                'error_type': error_type,
                'mastery_after': round(mastery, 4),
                'theta_after': round(theta, 4),
                'time_taken': time_taken,
                'confidence': metrics.get('confidence', 0),
            })

        total = len(quiz_answers) or 1
        accuracy = correct_count / total
        avg_time = total_time / total if total else 30

        # ── Error analysis ──
        from collections import Counter
        error_counter = Counter(error_types)
        dominant_error = error_counter.most_common(1)[0][0] if error_counter else None

        # ── Full pacing decision (10-feature) ──
        pacing_context = PacingContext(
            accuracy=accuracy,
            mastery_score=mastery,
            streak=streak,
            error_types=error_types[-5:],
            theta=theta,
            questions_answered=total,
            knowledge_level=knowledge_level,
            phase='initial_quiz',
            avg_response_time=avg_time,
            expected_response_time=60.0,
            time_per_question_history=[m['time_taken'] for m in per_question_metrics],
            diagnostic_accuracy=accuracy,
        )

        pacing_result: PacingResult = self.pacing_engine.decide_pacing(pacing_context)

        # ── Determine adaptive next-step ──
        if mastery >= 0.65 and accuracy >= 0.8:
            next_step = 'skip_to_practice'
            next_step_message = "Great diagnostic! You already know the basics — let's jump to practice questions."
        elif mastery >= 0.45 and accuracy >= 0.6:
            next_step = 'normal_teaching'
            next_step_message = "Good foundation. Let's reinforce with focused teaching."
        elif mastery >= 0.3 and accuracy >= 0.4:
            next_step = 'detailed_teaching'
            next_step_message = "Some gaps found. We'll go through the material step by step."
        else:
            next_step = 'foundational_teaching'
            next_step_message = "Let's build from the ground up with detailed explanations."

        # ── Knowledge-level adjustment ──
        if accuracy >= 0.8 and knowledge_level in ('beginner', 'zero'):
            adjusted_level = 'intermediate'
        elif accuracy < 0.3 and knowledge_level in ('advanced', 'intermediate'):
            adjusted_level = 'beginner'
        elif accuracy < 0.5 and knowledge_level == 'advanced':
            adjusted_level = 'intermediate'
        else:
            adjusted_level = knowledge_level

        return {
            'accuracy': round(accuracy, 4),
            'mastery': round(mastery, 4),
            'theta': round(theta, 4),
            'streak': streak,
            'error_types': error_types,
            'error_analysis': {
                'dominant_error': dominant_error,
                'error_counts': dict(error_counter),
                'total_errors': len(error_types),
            },
            'per_question_metrics': per_question_metrics,
            'pacing': pacing_result.decision.value if hasattr(pacing_result.decision, 'value') else pacing_result.decision,
            'next_action': pacing_result.next_action.value if hasattr(pacing_result.next_action, 'value') else pacing_result.next_action,
            'fatigue': pacing_result.fatigue.value if hasattr(pacing_result.fatigue, 'value') else str(pacing_result.fatigue),
            'recommended_difficulty': pacing_result.recommended_difficulty,
            'mastery_verdict': pacing_result.mastery_verdict,
            'reasoning': pacing_result.reasoning,
            'next_step': next_step,
            'next_step_message': next_step_message,
            'adjusted_knowledge_level': adjusted_level,
            'avg_response_time': round(avg_time, 2),
        }

    def process_answer(self, 
                      atom_state: TeachingAtomState,
                      theta: float,
                      question: Dict[str, Any],
                      selected_answer: int,
                      time_taken: float,
                      knowledge_level: str,
                      questions_history: List[Dict]) -> Dict[str, Any]:
        """
        Process a single answer with real-time mastery update and pacing decision
        
        Args:
            atom_state: Current atom state
            theta: Current ability estimate
            question: Question that was answered
            selected_answer: User's answer index
            time_taken: Time taken in seconds
            knowledge_level: Self-reported knowledge level
            questions_history: List of previous questions/answers
        
        Returns:
            Dict with updated state and next actions
        """
        # Determine correctness
        correct = (selected_answer == question.get('correct_index', -1))
        
        # Classify error type if wrong
        error_type = None
        if not correct:
            error_type = classify_error_type(
                question, selected_answer, time_taken, atom_state.name
            )
        
        # REAL-TIME MASTERY UPDATE (after EVERY answer)
        new_mastery, new_theta, metrics = calculate_updated_mastery(
            current_mastery=atom_state.mastery_score,
            current_theta=theta,
            question=question,
            correct=correct,
            time_taken=time_taken,
            error_type=error_type
        )
        
        # Update atom state
        atom_state.mastery_score = new_mastery
        
        if correct:
            atom_state.streak = atom_state.streak + 1 if atom_state.streak > 0 else 1
        else:
            atom_state.streak = atom_state.streak - 1 if atom_state.streak < 0 else -1
        
        if error_type:
            atom_state.error_history.append(error_type)
        
        # Calculate recent metrics for pacing
        recent_questions = questions_history[-5:] if questions_history else []
        recent_correct = sum(1 for q in recent_questions if q.get('correct', False))
        recent_accuracy = recent_correct / len(recent_questions) if recent_questions else (1.0 if correct else 0.0)
        
        # Get recent error types
        recent_errors = [e for e in atom_state.error_history[-5:] if e]
        
        # Collect time-per-question history from questions_history
        time_history = [q.get('time_taken', 30) for q in questions_history if 'time_taken' in q]
        time_history.append(time_taken)

        # Compute accuracy trend (rolling window of recent correctness)
        accuracy_trend = []
        for q in questions_history[-10:]:
            accuracy_trend.append(1.0 if q.get('correct', False) else 0.0)
        accuracy_trend.append(1.0 if correct else 0.0)

        # Hint usage count from atom state
        hint_count = atom_state.hint_usage

        # Expected response time from question
        expected_time = question.get('estimated_time', 60)

        # Create enriched pacing context with all 10 features
        pacing_context = PacingContext(
            accuracy=recent_accuracy,
            mastery_score=new_mastery,
            streak=atom_state.streak,
            error_types=recent_errors,
            theta=new_theta,
            questions_answered=len(questions_history) + 1,
            knowledge_level=knowledge_level,
            phase=atom_state.phase.value if hasattr(atom_state.phase, 'value') else atom_state.phase,
            # Feature 2: learning speed
            avg_response_time=time_taken,
            expected_response_time=float(expected_time),
            time_per_question_history=time_history,
            # Feature 7: hint depth
            hint_usage_count=hint_count,
            # Feature 8: fatigue (session-level, passed from caller if available)
            recent_accuracy_trend=accuracy_trend,
            recent_response_times=time_history[-10:],
            # Feature 6: retention
            retention_score=getattr(atom_state, 'retention_score', 1.0),
            retention_checks_passed=getattr(atom_state, 'retention_checks_passed', 0),
            last_practiced_minutes_ago=getattr(atom_state, 'last_practiced_minutes_ago', 0),
        )

        # Get full pacing result (10-feature)
        pacing_result: PacingResult = self.pacing_engine.decide_pacing(pacing_context)
        pacing_decision = pacing_result.decision
        next_action = pacing_result.next_action
        reasoning = pacing_result.reasoning
        
        # Determine next difficulty based on ability and pacing
        next_difficulty = self.pacing_engine.get_next_difficulty(
            new_theta, pacing_decision, knowledge_level
        )
        
        # Check if atom is complete
        atom_complete = self._check_atom_complete(atom_state, pacing_context)
        
        # Store velocity snapshot on atom state
        if hasattr(atom_state, 'velocity_snapshots'):
            atom_state.velocity_snapshots.append(pacing_result.velocity_snapshot)

        # Store time_taken on atom state for per-atom speed tracking
        if hasattr(atom_state, 'time_per_question'):
            atom_state.time_per_question.append(time_taken)

        # Fatigue recommendation
        fatigue_rec = self.pacing_engine.get_fatigue_recommendation(pacing_result.fatigue)

        # Prepare result with all 10 feature outputs
        result = {
            'correct': correct,
            'error_type': error_type,
            'updated_mastery': new_mastery,
            'updated_theta': new_theta,
            'metrics': metrics,
            'pacing_decision': pacing_decision.value if hasattr(pacing_decision, 'value') else pacing_decision,
            'next_action': next_action.value if hasattr(next_action, 'value') else next_action,
            'next_difficulty': next_difficulty,
            'reasoning': reasoning,
            'atom_complete': atom_complete,
            'streak': atom_state.streak,
            # ── Feature 5: mastery verdict ──
            'mastery_verdict': pacing_result.mastery_verdict,
            # ── Feature 6: retention ──
            'retention_action': pacing_result.retention_action,
            # ── Feature 7: hint warning ──
            'hint_warning': pacing_result.hint_warning,
            # ── Feature 8: fatigue ──
            'fatigue': {
                'level': pacing_result.fatigue.value,
                'message': fatigue_rec.get('message', ''),
                'break_suggested': fatigue_rec.get('break_suggested', False),
                'lighter_mode': fatigue_rec.get('lighter_mode', False),
            },
            # ── Feature 9: engagement ──
            'engagement_adjustment': pacing_result.engagement_adjustment,
            # ── Feature 10: velocity snapshot ──
            'velocity_snapshot': pacing_result.velocity_snapshot,
        }

        # Add specific recommendations
        if next_action == NextAction.RETEACH:
            result['recommendation'] = 'review_teaching'
            result['message'] = "Let's review the teaching material again."
        elif next_action == NextAction.ADVANCE_NEXT_ATOM:
            result['recommendation'] = 'advance'
            result['message'] = "Great job! Ready for the next concept."
        elif next_action == NextAction.TAKE_BREAK:
            result['recommendation'] = 'take_break'
            result['message'] = fatigue_rec.get('message', "Time for a short break!")
        elif next_action == NextAction.LIGHTER_TASK:
            result['recommendation'] = 'lighter_task'
            result['message'] = "Switching to lighter tasks to keep you going."
        elif next_action == NextAction.INSERT_REVIEW:
            result['recommendation'] = 'review_old_content'
            result['message'] = "Let's quickly review some earlier content to keep it fresh."
        elif pacing_decision == PacingDecision.SHARP_SLOWDOWN:
            result['recommendation'] = 'easier_questions'
            result['message'] = "Let's try some easier questions to build confidence."
        elif pacing_decision == PacingDecision.SPEED_UP:
            result['recommendation'] = 'challenge'
            result['message'] = "You're doing great! Ready for a challenge?"

        return result
    
    def _check_atom_complete(self, atom_state: TeachingAtomState, 
                            context: PacingContext) -> bool:
        """
        Check if atom should be marked complete using the engine's should_exit_atom.
        """
        should_exit, reason = self.pacing_engine.should_exit_atom(context)
        return should_exit
    
    def select_next_questions(self, 
                             atom_state: TeachingAtomState,
                             theta: float,
                             pacing_decision: PacingDecision,
                             knowledge_level: str,
                             available_questions: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Select next questions based on ability, not fixed counts
        """
        selected = []
        
        # Determine target difficulty based on theta
        if theta < -0.3:
            target_difficulty = 'easy'
        elif theta < 0.6:
            target_difficulty = 'medium'
        else:
            target_difficulty = 'hard'
        
        # Adjust based on pacing
        if pacing_decision == PacingDecision.SHARP_SLOWDOWN:
            # Focus on easy questions
            target_difficulty = 'easy'
            count = 3
        elif pacing_decision == PacingDecision.SLOW_DOWN:
            # Mix of easy and medium
            easy_count = 2
            medium_count = 1
        elif pacing_decision == PacingDecision.STAY:
            # Mix based on ability
            if target_difficulty == 'easy':
                easy_count, medium_count, hard_count = 2, 1, 0
            elif target_difficulty == 'medium':
                easy_count, medium_count, hard_count = 1, 2, 0
            else:  # hard
                easy_count, medium_count, hard_count = 0, 2, 1
        else:  # SPEED_UP
            # Challenge with harder questions
            if target_difficulty == 'easy':
                easy_count, medium_count, hard_count = 1, 2, 0
            elif target_difficulty == 'medium':
                easy_count, medium_count, hard_count = 0, 2, 1
            else:  # hard
                easy_count, medium_count, hard_count = 0, 1, 2
        
        # Select questions (up to available)
        for difficulty, count in [('easy', easy_count), ('medium', medium_count), ('hard', hard_count)]:
            if count > 0 and difficulty in available_questions:
                pool = available_questions[difficulty]
                # Select without replacement
                to_select = min(count, len(pool))
                if to_select > 0:
                    selected.extend(random.sample(pool, to_select))
        
        return selected
    
    def generate_teaching_content(self, atom_name: str, subject: str, 
                                  concept: str, knowledge_level: str,
                                  error_history: List[str] = None,
                                  mastery_score: float = None) -> Dict[str, str]:
        """
        Generate personalized teaching content based on knowledge level,
        error history, AND quiz mastery score.

        mastery_score drives the depth of teaching:
          - low  (<0.35): teach from absolute basics, ground-up
          - moderate (0.35-0.65): normal, balanced teaching
          - high (>0.65): go deep — advanced insights, edge cases
        """
        # If reteaching due to errors, focus on problem areas
        if error_history and len(error_history) > 0:
            recent_errors = error_history[-3:]
            error_focus = self._get_error_focus(recent_errors)
        else:
            error_focus = None
        
        if not self.groq_client:
            return self._get_fallback_content(atom_name, concept, knowledge_level, error_focus)
        
        level_descriptions = {
            'zero': "Complete beginner - needs fundamental concepts explained from scratch",
            'beginner': "Has basic understanding but needs clear explanations and examples",
            'intermediate': "Knows the basics - needs deeper insights and applications",
            'advanced': "Strong understanding - needs advanced concepts and edge cases"
        }

        # ── Mastery-driven depth instruction ──
        mastery_depth_instruction = ""
        if mastery_score is not None:
            if mastery_score < 0.35:
                mastery_depth_instruction = f"""
**IMPORTANT — MASTERY-BASED DEPTH (mastery = {mastery_score:.0%}):**
The student scored VERY LOW on the diagnostic quiz. They have little to no prior understanding.
- Teach from ABSOLUTE BASICS. Assume zero prior knowledge of this specific topic.
- Use the simplest language possible. Define every term.
- Give extremely concrete, step-by-step explanations.
- Use very relatable, everyday analogies — nothing abstract.
- Reinforce the core idea multiple times in different ways.
- Do NOT skip foundational steps or assume any background.
"""
            elif mastery_score < 0.65:
                mastery_depth_instruction = f"""
**MASTERY-BASED DEPTH (mastery = {mastery_score:.0%}):**
The student has a MODERATE understanding from the diagnostic quiz.
- Teach at a standard level — cover the core idea clearly.
- Include practical examples and applications.
- Don't over-simplify, but don't assume deep expertise either.
- Balance foundational clarity with useful insights.
"""
            else:
                mastery_depth_instruction = f"""
**MASTERY-BASED DEPTH (mastery = {mastery_score:.0%}):**
The student scored HIGH on the diagnostic quiz — they already know the basics well.
- Go DEEP into the concept. Skip trivial basics.
- Focus on edge cases, subtle nuances, and common pitfalls at an advanced level.
- Include implementation details, performance considerations, or real-world gotchas.
- Challenge their understanding with non-obvious insights.
- Connect the concept to related advanced ideas.
"""
        
        error_context = ""
        if error_focus:
            error_context = f"""
            The student has struggled with these types of errors recently:
            {', '.join(error_focus)}
            
            Please address these specific difficulties in your explanation.
            """
        
        prompt = f"""
You are creating a personalized teaching module for a single atomic concept.  
Your goal is to ensure the user fully understands this concept.

Subject: {subject}  
Concept: {concept}  
Atomic Concept: {atom_name}  
Student Knowledge Level: {level_descriptions.get(knowledge_level, 'intermediate')}  

{mastery_depth_instruction}

{error_context}

Generate a teaching module with the following components, adhering strictly to these guidelines:

1. **Explanation** (2‑4 sentences, but formatted pointwise – use bullet points or numbered steps for clarity):  
   - Break down the idea into simple, logical parts.  
   - If the concept involves programming, include a short, illustrative code snippet or pseudo‑code directly within the explanation.  
   - Avoid jargon; define any necessary terms briefly.  

2. **Example** (concrete and level‑appropriate):  
   - Provide a real‑world, tangible scenario that the student can easily visualize.  
   - Steer clear of abstract or overly theoretical illustrations – make it relatable to everyday life or the student’s likely experience.  

3. **Analogy** (from everyday life):  
   - Choose an analogy that matches the student’s understanding and makes the abstract idea intuitive.  

4. **Common Misconception**:  
   - Identify a typical mistake or misunderstanding about this concept, and briefly explain why it’s wrong.  

5. **Practical Application** (“why this matters”):  
   - Show a concrete, real‑life situation where this concept is useful or necessary.  

Rules to follow:  
- Focus on ONE atomic idea only.  
- No unexplained jargon.  
- Make the content memorable and directly relevant to the student’s level.  
- If the student is advanced or has high mastery, include edge cases, limitations, or deeper insights.  
- If the student is a beginner or has low mastery, focus on fundamentals and simple explanations.  
- If this is a reteach (due to a previous error), explain the concept in a completely different way from before.  

Return the result as a strict JSON object with exactly these keys:  
{{
    "explanation": "Clear, pointwise explanation here (use bullet points or numbers). Include a code snippet if appropriate.",
    "example": "Concrete, real‑world example here.",
    "analogy": "Everyday analogy here.",
    "misconception": "Common mistake students make about this concept.",
    "practical_application": "Why this matters in real life."
}}
"""
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800,
            )
            
            raw_text = response.choices[0].message.content
            if "```" in raw_text:
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            
            # Sanitize control characters inside JSON string values
            raw_text = re.sub(r'[\x00-\x1f\x7f]', lambda m: ' ' if m.group() in ('\n', '\r', '\t') else '', raw_text)
            
            return json.loads(raw_text.strip())
        except Exception as e:
            print(f"Warning: Could not generate teaching content: {e}")
            return self._get_fallback_content(atom_name, concept, knowledge_level, error_focus)
    
    def _get_error_focus(self, error_types: List[str]) -> List[str]:
        """Convert error types to focus areas for teaching"""
        focus_map = {
            'conceptual': 'fundamental concepts',
            'structural': 'relationships between ideas',
            'procedural': 'step-by-step processes',
            'factual': 'key facts and definitions',
            'guessing': 'building confidence with basics'
        }
        return [focus_map.get(e, e) for e in error_types if e in focus_map]
    
    def _get_fallback_content(self, atom_name: str, concept: str, level: str, 
                             error_focus: List[str] = None) -> Dict:
        """Enhanced fallback content"""
        focus_text = ""
        if error_focus:
            focus_text = f" focusing on {', '.join(error_focus)}"
        
        if level == 'advanced':
            return {
                "explanation": f"{atom_name} represents an advanced aspect of {concept} with complex interactions and edge cases{focus_text}.",
                "example": f"Advanced example: In production systems, {atom_name} manifests through...",
                "analogy": f"Think of {atom_name} like a sophisticated system where multiple components interact.",
                "misconception": f"Even experts sometimes confuse {atom_name} with similar advanced concepts.",
                "practical_application": f"Understanding {atom_name} helps in optimizing system performance."
            }
        elif level == 'intermediate':
            return {
                "explanation": f"{atom_name} is a key component of {concept} that builds on foundational knowledge{focus_text}.",
                "example": f"Example: When working with {concept}, {atom_name} helps you...",
                "analogy": f"Think of {atom_name} like a well-organized tool in your toolkit.",
                "misconception": f"Don't confuse {atom_name} with its related concepts.",
                "practical_application": f"Mastering {atom_name} improves your problem-solving efficiency."
            }
        else:  # zero or beginner
            return {
                "explanation": f"{atom_name} is a fundamental building block of {concept}. It's like learning a basic rule{focus_text}.",
                "example": f"Simple example: Just like learning the alphabet before writing words, {atom_name} comes first.",
                "analogy": f"Think of {atom_name} like learning to crawl before you walk.",
                "misconception": f"Beginners often think {atom_name} is harder than it really is.",
                "practical_application": f"Understanding {atom_name} opens the door to mastering {concept}."
            }