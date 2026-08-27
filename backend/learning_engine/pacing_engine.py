# backend/learning_engine/pacing_engine.py
# Robust Adaptive Pacing Engine — 10-feature design
# ─────────────────────────────────────────────────────────────
# 1. Diagnostic micro-quiz → initial baseline
# 2. Learning speed per concept atom
# 3. Error-type tracking (weighted)
# 4. Adaptive pacing rules (core engine)
# 5. Mastery thresholds (dynamic exit)
# 6. Retention checks (spaced review)
# 7. Adaptive hint depth
# 8. Fatigue detection
# 9. Interest-based example adjustment
# 10. Learning velocity graph data
# ─────────────────────────────────────────────────────────────

from __future__ import annotations

import math
import time as _time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ════════════════════════════════════════════════════════════════
#  Enums
# ════════════════════════════════════════════════════════════════

class PacingDecision(str, Enum):
    SPEED_UP = "speed_up"
    STAY = "stay"
    SLOW_DOWN = "slow_down"
    SHARP_SLOWDOWN = "sharp_slowdown"


class NextAction(str, Enum):
    CONTINUE_PRACTICE = "continue_practice"
    RETEACH = "reteach"
    ADVANCE_NEXT_ATOM = "advance_next_atom"
    MASTERY_CHECK = "mastery_check"
    COMPLETE_ATOM = "complete_atom"
    RETENTION_CHECK = "retention_check"
    TAKE_BREAK = "take_break"
    LIGHTER_TASK = "lighter_task"
    INSERT_REVIEW = "insert_review"


class FatigueLevel(str, Enum):
    FRESH = "fresh"
    MILD = "mild"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


# ════════════════════════════════════════════════════════════════
#  Data classes
# ════════════════════════════════════════════════════════════════

@dataclass
class PacingContext:
    """All signals the pacing engine consumes for one decision."""
    # Core performance
    accuracy: float                         # Recent window accuracy 0-1
    mastery_score: float                    # BKT / IRT mastery 0-1
    streak: int                             # +N correct / -N wrong
    error_types: List[str]                  # Recent classified errors
    theta: float                            # IRT ability
    questions_answered: int                 # In current atom
    knowledge_level: str                    # zero|beginner|intermediate|advanced
    phase: str                              # Current learning phase

    # ── Feature 2: learning speed ──
    avg_response_time: float = 0.0          # seconds
    expected_response_time: float = 60.0    # seconds
    time_per_question_history: List[float] = field(default_factory=list)

    # ── Feature 7: hint depth ──
    hint_usage_count: int = 0
    hints_available: int = 3
    hint_dependency_ratio: float = 0.0      # questions needing hints / total

    # ── Feature 8: fatigue ──
    session_duration_minutes: float = 0.0
    total_questions_session: int = 0
    recent_accuracy_trend: List[float] = field(default_factory=list)  # last N accuracies
    recent_response_times: List[float] = field(default_factory=list)  # last N times

    # ── Feature 6: retention ──
    last_practiced_minutes_ago: float = 0.0
    retention_score: float = 1.0            # 0-1, decays over time
    retention_checks_passed: int = 0
    retention_checks_failed: int = 0

    # ── Feature 9: interest / engagement ──
    engagement_score: float = 0.7           # 0-1 derived from behaviour
    consecutive_skips: int = 0
    drop_off_risk: float = 0.0              # 0-1

    # ── Feature 1: diagnostic baseline ──
    diagnostic_accuracy: Optional[float] = None
    diagnostic_pacing: Optional[str] = None


@dataclass
class PacingResult:
    """Rich result returned by the engine."""
    decision: PacingDecision
    next_action: NextAction
    reasoning: Dict[str, Any]
    fatigue: FatigueLevel
    recommended_difficulty: str
    mastery_verdict: str                    # "not_reached" | "approaching" | "reached" | "exceeded"
    retention_action: Optional[str]         # None | "schedule_review" | "insert_review_now"
    hint_warning: Optional[str]             # None | "hint_dependent" | "healthy"
    velocity_snapshot: Dict[str, float]     # point-in-time velocity data
    engagement_adjustment: Optional[str]    # None | "use_interest_examples" | "switch_mode"


# ════════════════════════════════════════════════════════════════
#  Main Engine
# ════════════════════════════════════════════════════════════════

class PacingEngine:
    """
    Robust adaptive pacing engine.

    Call  ``decide_pacing(ctx)``  to get a full ``PacingResult``.
    Legacy callers can still use  ``decide_pacing_legacy(ctx)``  which
    returns the old  ``(PacingDecision, NextAction, dict)``  tuple.
    """

    # ── Accuracy thresholds by knowledge level ──────────────────
    ACCURACY_THRESHOLDS = {
        "zero":         {"speed_up": 0.80, "stay": 0.60, "slow_down": 0.40, "sharp_slowdown": 0.25},
        "beginner":     {"speed_up": 0.80, "stay": 0.60, "slow_down": 0.45, "sharp_slowdown": 0.30},
        "intermediate": {"speed_up": 0.85, "stay": 0.70, "slow_down": 0.55, "sharp_slowdown": 0.40},
        "advanced":     {"speed_up": 0.90, "stay": 0.80, "slow_down": 0.65, "sharp_slowdown": 0.50},
    }

    MASTERY_THRESHOLDS = {
        "zero":         {"speed_up": 0.70, "stay": 0.50, "slow_down": 0.35, "sharp_slowdown": 0.20},
        "beginner":     {"speed_up": 0.75, "stay": 0.55, "slow_down": 0.40, "sharp_slowdown": 0.25},
        "intermediate": {"speed_up": 0.80, "stay": 0.60, "slow_down": 0.45, "sharp_slowdown": 0.30},
        "advanced":     {"speed_up": 0.85, "stay": 0.70, "slow_down": 0.55, "sharp_slowdown": 0.40},
    }

    # ── Feature 5: dynamic mastery exit thresholds ──────────────
    MASTERY_EXIT = {
        "zero":         {"min_mastery": 0.65, "min_accuracy": 0.70, "min_streak": 2, "min_questions": 5, "max_questions": 20},
        "beginner":     {"min_mastery": 0.70, "min_accuracy": 0.75, "min_streak": 2, "min_questions": 4, "max_questions": 16},
        "intermediate": {"min_mastery": 0.75, "min_accuracy": 0.80, "min_streak": 2, "min_questions": 3, "max_questions": 12},
        "advanced":     {"min_mastery": 0.80, "min_accuracy": 0.85, "min_streak": 3, "min_questions": 3, "max_questions": 10},
    }

    # ── Feature 3: error-type weights ───────────────────────────
    ERROR_WEIGHTS: Dict[str, float] = {
        "guessing":     1.2,
        "attentional":  0.5,
        "factual":      1.0,
        "procedural":   1.3,
        "conceptual":   1.8,
        "structural":   1.5,
    }

    # ── Feature 8: fatigue thresholds ───────────────────────────
    FATIGUE_TIME_THRESHOLDS = [15, 30, 45, 60]        # minutes
    FATIGUE_QUESTION_THRESHOLDS = [15, 30, 50, 70]    # count

    # ── Feature 6: retention decay constant ─────────────────────
    RETENTION_HALF_LIFE_HOURS = 24.0
    RETENTION_REVIEW_THRESHOLD = 0.6

    # ── Feature 7: hint dependency threshold ────────────────────
    HINT_DEPENDENCY_THRESHOLD = 0.5   # >50 % questions with hints → warning

    # ────────────────────────────────────────────────────────────
    #  PUBLIC API
    # ────────────────────────────────────────────────────────────

    def decide_pacing(self, ctx: PacingContext) -> PacingResult:
        """Full-featured pacing decision."""

        reasoning: Dict[str, Any] = {
            "accuracy": ctx.accuracy,
            "mastery": ctx.mastery_score,
            "streak": ctx.streak,
            "primary_factors": [],
            "error_analysis": {},
            "fatigue_factors": [],
            "retention_factors": [],
            "hint_factors": [],
            "velocity_factors": [],
        }

        # ── 1  Diagnostic baseline (feature 1) ─────────────────
        initial_band, initial_pace = self._diagnostic_baseline(ctx)
        reasoning["diagnostic_baseline"] = {
            "initial_difficulty_band": initial_band,
            "initial_pace": initial_pace,
        }

        # ── 2  Learning speed analysis (feature 2) ─────────────
        speed_signal = self._learning_speed_signal(ctx)
        reasoning["learning_speed"] = speed_signal

        # ── 3  Error-type analysis (feature 3) ─────────────────
        error_signal = self._error_type_signal(ctx)
        reasoning["error_analysis"] = error_signal

        # ── 7  Hint depth analysis (feature 7) ─────────────────
        hint_signal = self._hint_depth_signal(ctx)
        reasoning["hint_factors"] = hint_signal

        # ── 8  Fatigue detection (feature 8) ───────────────────
        fatigue_level = self._detect_fatigue(ctx)
        reasoning["fatigue_level"] = fatigue_level.value

        # ── 6  Retention check (feature 6) ─────────────────────
        retention_action = self._retention_signal(ctx)
        reasoning["retention_action"] = retention_action

        # ── 9  Engagement / interest signal (feature 9) ────────
        engagement_adj = self._engagement_signal(ctx)
        reasoning["engagement_adjustment"] = engagement_adj

        # ── 10  Velocity snapshot (feature 10) ─────────────────
        velocity = self._velocity_snapshot(ctx, speed_signal)
        reasoning["velocity_snapshot"] = velocity

        # ── 4  Core adaptive pacing rules (feature 4) ──────────
        decision, next_action = self._core_pacing_rules(
            ctx, error_signal, speed_signal, hint_signal,
            fatigue_level, retention_action, reasoning,
        )

        # Override next_action for fatigue if critical
        if fatigue_level in (FatigueLevel.HIGH, FatigueLevel.CRITICAL):
            if next_action not in (NextAction.RETEACH, NextAction.TAKE_BREAK):
                next_action = NextAction.LIGHTER_TASK if fatigue_level == FatigueLevel.HIGH else NextAction.TAKE_BREAK
                reasoning["primary_factors"].append("fatigue_override")

        # Override for retention if poor
        if retention_action == "insert_review_now" and next_action == NextAction.ADVANCE_NEXT_ATOM:
            next_action = NextAction.INSERT_REVIEW
            reasoning["primary_factors"].append("retention_override")

        # ── 5  Mastery verdict (feature 5) ─────────────────────
        mastery_verdict = self._mastery_verdict(ctx)

        # Recommended difficulty
        recommended_diff = self._recommend_difficulty(ctx.theta, decision, ctx.knowledge_level)

        # Hint warning
        hint_warning = "hint_dependent" if hint_signal.get("dependency_ratio", 0) > self.HINT_DEPENDENCY_THRESHOLD else "healthy"

        return PacingResult(
            decision=decision,
            next_action=next_action,
            reasoning=reasoning,
            fatigue=fatigue_level,
            recommended_difficulty=recommended_diff,
            mastery_verdict=mastery_verdict,
            retention_action=retention_action,
            hint_warning=hint_warning,
            velocity_snapshot=velocity,
            engagement_adjustment=engagement_adj,
        )

    # Legacy compat — returns the old 3-tuple
    def decide_pacing_legacy(self, ctx: PacingContext) -> Tuple[PacingDecision, NextAction, Dict]:
        r = self.decide_pacing(ctx)
        return r.decision, r.next_action, r.reasoning

    # ────────────────────────────────────────────────────────────
    #  FEATURE 1 — Diagnostic micro-quiz baseline
    # ────────────────────────────────────────────────────────────

    def _diagnostic_baseline(self, ctx: PacingContext) -> Tuple[str, str]:
        """
        From diagnostic accuracy → initial difficulty band & pace.
        Strong student → jump ahead.  Weak student → slower intro.
        """
        acc = ctx.diagnostic_accuracy if ctx.diagnostic_accuracy is not None else ctx.accuracy

        if acc >= 0.85:
            return "hard", "fast"
        elif acc >= 0.65:
            return "medium", "normal"
        elif acc >= 0.45:
            return "easy", "slow"
        else:
            return "easy", "very_slow"

    def compute_diagnostic_result(self, answers: List[Dict]) -> Dict[str, Any]:
        """
        Process raw micro-quiz answers to produce a diagnostic summary.

        Each answer dict: {correct: bool, time_taken: float, difficulty: str, error_type: str|None}

        Returns dict with accuracy, avg_time, error_breakdown,
        recommended_difficulty_band, recommended_pace.
        """
        if not answers:
            return {
                "accuracy": 0.0,
                "avg_time": 0.0,
                "error_breakdown": {},
                "recommended_band": "easy",
                "recommended_pace": "very_slow",
                "theta_estimate": -1.0,
            }

        total = len(answers)
        correct = sum(1 for a in answers if a.get("correct"))
        accuracy = correct / total

        times = [a.get("time_taken", 30) for a in answers]
        avg_time = sum(times) / len(times)

        errors: Dict[str, int] = {}
        for a in answers:
            et = a.get("error_type")
            if et:
                errors[et] = errors.get(et, 0) + 1

        # Simple theta estimation from diagnostic
        if accuracy >= 0.9:
            theta_est = 1.5
        elif accuracy >= 0.7:
            theta_est = 0.5
        elif accuracy >= 0.5:
            theta_est = 0.0
        elif accuracy >= 0.3:
            theta_est = -0.5
        else:
            theta_est = -1.0

        # Speed bonus / penalty
        avg_expected = 45
        speed_ratio = avg_time / avg_expected if avg_expected > 0 else 1.0
        if speed_ratio < 0.7 and accuracy >= 0.7:
            theta_est += 0.3
        elif speed_ratio > 1.5 and accuracy < 0.5:
            theta_est -= 0.3

        band, pace = self._diagnostic_baseline(
            PacingContext(
                accuracy=accuracy, mastery_score=0.3, streak=0,
                error_types=list(errors.keys()), theta=theta_est,
                questions_answered=total, knowledge_level="intermediate",
                phase="diagnostic", diagnostic_accuracy=accuracy,
            )
        )

        return {
            "accuracy": round(accuracy, 3),
            "avg_time": round(avg_time, 1),
            "error_breakdown": errors,
            "recommended_band": band,
            "recommended_pace": pace,
            "theta_estimate": round(theta_est, 2),
        }

    # ────────────────────────────────────────────────────────────
    #  FEATURE 2 — Learning speed per concept atom
    # ────────────────────────────────────────────────────────────

    def _learning_speed_signal(self, ctx: PacingContext) -> Dict[str, Any]:
        """
        Analyse per-atom response times to decide per-skill pacing.
        Fast atom → skip repetitive practice.
        Slow atom → insert more reps or hints.
        """
        if not ctx.time_per_question_history:
            ratio = ctx.avg_response_time / ctx.expected_response_time if ctx.expected_response_time > 0 else 1.0
        else:
            recent = ctx.time_per_question_history[-5:]
            avg_recent = sum(recent) / len(recent)
            ratio = avg_recent / ctx.expected_response_time if ctx.expected_response_time > 0 else 1.0

        if ratio <= 0.0:
            ratio = 1.0

        if ratio < 0.6:
            classification = "very_fast"
            recommendation = "skip_repetitive"
        elif ratio < 0.85:
            classification = "fast"
            recommendation = "reduce_reps"
        elif ratio <= 1.15:
            classification = "normal"
            recommendation = "maintain"
        elif ratio <= 1.5:
            classification = "slow"
            recommendation = "add_reps"
        else:
            classification = "very_slow"
            recommendation = "add_hints_and_reps"

        trend = "stable"
        if len(ctx.time_per_question_history) >= 4:
            first_half = ctx.time_per_question_history[: len(ctx.time_per_question_history) // 2]
            second_half = ctx.time_per_question_history[len(ctx.time_per_question_history) // 2 :]
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            if avg_second < avg_first * 0.8:
                trend = "improving"
            elif avg_second > avg_first * 1.2:
                trend = "deteriorating"

        return {
            "speed_ratio": round(ratio, 3),
            "classification": classification,
            "recommendation": recommendation,
            "trend": trend,
        }

    # ────────────────────────────────────────────────────────────
    #  FEATURE 3 — Error-type tracking
    # ────────────────────────────────────────────────────────────

    def _error_type_signal(self, ctx: PacingContext) -> Dict[str, Any]:
        """
        Weighted error analysis.
        Careless mistake → keep pace.
        Conceptual error → slow down / break into sub-atoms.
        """
        recent = ctx.error_types[-5:] if ctx.error_types else []
        if not recent:
            return {
                "error_count": 0,
                "weighted_severity": 0.0,
                "dominant_type": None,
                "action": "continue",
            }

        counts: Dict[str, int] = {}
        for e in recent:
            counts[e] = counts.get(e, 0) + 1

        total_weight = sum(
            counts.get(etype, 0) * self.ERROR_WEIGHTS.get(etype, 1.0)
            for etype in counts
        )
        weighted_severity = total_weight / max(len(recent), 1)

        dominant = max(counts, key=counts.get) if counts else None

        repeated_same = len(recent) >= 3 and len(set(recent[-3:])) == 1

        if weighted_severity >= 1.5 or (dominant == "conceptual" and counts.get("conceptual", 0) >= 2):
            action = "break_into_sub_atoms"
        elif weighted_severity >= 1.0 or repeated_same:
            action = "slow_and_reinforce"
        elif dominant == "attentional":
            action = "continue"
        elif weighted_severity >= 0.6:
            action = "add_practice"
        else:
            action = "continue"

        return {
            "error_count": len(recent),
            "error_counts": counts,
            "weighted_severity": round(weighted_severity, 3),
            "dominant_type": dominant,
            "repeated_same_error": repeated_same,
            "action": action,
        }

    # ────────────────────────────────────────────────────────────
    #  FEATURE 4 — Core adaptive pacing rules
    # ────────────────────────────────────────────────────────────

    def _core_pacing_rules(
        self,
        ctx: PacingContext,
        error_signal: Dict,
        speed_signal: Dict,
        hint_signal: Dict,
        fatigue: FatigueLevel,
        retention_action: Optional[str],
        reasoning: Dict,
    ) -> Tuple[PacingDecision, NextAction]:
        """
        Converts all signals into a single pacing decision + next action.
        """
        level = ctx.knowledge_level
        acc_t = self.ACCURACY_THRESHOLDS.get(level, self.ACCURACY_THRESHOLDS["intermediate"])
        mas_t = self.MASTERY_THRESHOLDS.get(level, self.MASTERY_THRESHOLDS["intermediate"])

        accuracy = ctx.accuracy
        mastery = ctx.mastery_score
        streak = ctx.streak

        # ── LAYER 1: Critical conditions → SHARP_SLOWDOWN ──
        critical: List[str] = []

        if error_signal.get("action") == "break_into_sub_atoms":
            critical.append("severe_errors")
        if accuracy < acc_t["sharp_slowdown"]:
            critical.append("very_low_accuracy")
        if mastery < mas_t["sharp_slowdown"]:
            critical.append("very_low_mastery")
        if streak <= -3:
            critical.append("deep_negative_streak")
        if hint_signal.get("dependency_ratio", 0) > 0.7:
            critical.append("heavy_hint_dependency")

        if critical:
            reasoning["primary_factors"] = critical
            reasoning["severity"] = "critical"

            if mastery < 0.3 or error_signal.get("dominant_type") == "conceptual":
                return PacingDecision.SHARP_SLOWDOWN, NextAction.RETEACH
            return PacingDecision.SHARP_SLOWDOWN, NextAction.CONTINUE_PRACTICE

        # ── LAYER 2: Moderate conditions → SLOW_DOWN ────────
        moderate: List[str] = []

        if accuracy < acc_t["slow_down"]:
            moderate.append("low_accuracy")
        if mastery < mas_t["slow_down"]:
            moderate.append("low_mastery")
        if streak < 0:
            moderate.append("negative_streak")
        if error_signal.get("action") in ("slow_and_reinforce", "add_practice"):
            moderate.append("error_pattern")
        if speed_signal.get("classification") in ("slow", "very_slow"):
            moderate.append("slow_learner_on_atom")
        if hint_signal.get("dependency_ratio", 0) > self.HINT_DEPENDENCY_THRESHOLD:
            moderate.append("hint_dependent")
        if fatigue in (FatigueLevel.MODERATE,):
            moderate.append("moderate_fatigue")

        if moderate:
            reasoning["primary_factors"] = moderate
            reasoning["severity"] = "moderate"
            return PacingDecision.SLOW_DOWN, NextAction.CONTINUE_PRACTICE

        # ── LAYER 3: Speed-up conditions ────────────────────
        speedup: List[str] = []

        if accuracy >= acc_t["speed_up"]:
            speedup.append("high_accuracy")
        if mastery >= mas_t["speed_up"]:
            speedup.append("high_mastery")
        if streak >= 3:
            speedup.append("strong_streak")
        if speed_signal.get("classification") in ("fast", "very_fast"):
            speedup.append("fast_on_atom")
        if hint_signal.get("dependency_ratio", 0) < 0.15:
            speedup.append("no_hint_dependency")

        if len(speedup) >= 2:
            reasoning["primary_factors"] = speedup
            reasoning["severity"] = "positive"

            exit_cfg = self.MASTERY_EXIT.get(level, self.MASTERY_EXIT["intermediate"])
            if (
                mastery >= exit_cfg["min_mastery"]
                and accuracy >= exit_cfg["min_accuracy"]
                and streak >= exit_cfg["min_streak"]
                and ctx.questions_answered >= exit_cfg["min_questions"]
            ):
                if ctx.phase in ("diagnostic", "teaching"):
                    return PacingDecision.SPEED_UP, NextAction.ADVANCE_NEXT_ATOM
                elif ctx.phase == "practice" and mastery >= exit_cfg["min_mastery"] + 0.05:
                    return PacingDecision.SPEED_UP, NextAction.MASTERY_CHECK
                else:
                    return PacingDecision.SPEED_UP, NextAction.CONTINUE_PRACTICE

            return PacingDecision.SPEED_UP, NextAction.CONTINUE_PRACTICE

        # ── LAYER 4: Default → STAY ────────────────────────
        reasoning["primary_factors"] = ["normal_performance"]
        reasoning["severity"] = "normal"
        return PacingDecision.STAY, NextAction.CONTINUE_PRACTICE

    # ────────────────────────────────────────────────────────────
    #  FEATURE 5 — Mastery thresholds
    # ────────────────────────────────────────────────────────────

    def _mastery_verdict(self, ctx: PacingContext) -> str:
        exit_cfg = self.MASTERY_EXIT.get(ctx.knowledge_level, self.MASTERY_EXIT["intermediate"])

        if ctx.mastery_score >= exit_cfg["min_mastery"] + 0.1 and ctx.accuracy >= exit_cfg["min_accuracy"]:
            return "exceeded"
        elif (
            ctx.mastery_score >= exit_cfg["min_mastery"]
            and ctx.accuracy >= exit_cfg["min_accuracy"]
            and ctx.streak >= exit_cfg["min_streak"]
        ):
            return "reached"
        elif ctx.mastery_score >= exit_cfg["min_mastery"] - 0.1:
            return "approaching"
        else:
            return "not_reached"

    def should_exit_atom(self, ctx: PacingContext) -> Tuple[bool, str]:
        """Should the student move on from this atom?"""
        exit_cfg = self.MASTERY_EXIT.get(ctx.knowledge_level, self.MASTERY_EXIT["intermediate"])
        verdict = self._mastery_verdict(ctx)

        if verdict in ("reached", "exceeded"):
            if ctx.questions_answered >= exit_cfg["min_questions"]:
                recent = ctx.error_types[-3:] if ctx.error_types else []
                if "conceptual" not in recent and "structural" not in recent:
                    return True, "mastery_reached"
            return True, "mastery_reached_early" if ctx.questions_answered >= exit_cfg["min_questions"] - 1 else "wait_min_questions"

        if ctx.questions_answered >= exit_cfg["max_questions"]:
            return True, "max_questions_reached"

        return False, "not_ready"

    # ────────────────────────────────────────────────────────────
    #  FEATURE 6 — Retention checks
    # ────────────────────────────────────────────────────────────

    def _retention_signal(self, ctx: PacingContext) -> Optional[str]:
        hours_since = ctx.last_practiced_minutes_ago / 60.0
        if hours_since <= 0:
            return None

        decay = math.exp(-0.693 * hours_since / self.RETENTION_HALF_LIFE_HOURS)
        effective_retention = ctx.retention_score * decay

        if effective_retention < 0.4:
            return "insert_review_now"
        elif effective_retention < self.RETENTION_REVIEW_THRESHOLD:
            return "schedule_review"
        return None

    def compute_retention_score(self, mastery: float, last_accuracy: float,
                                 hours_since_practice: float,
                                 checks_passed: int = 0) -> float:
        base = (mastery + last_accuracy) / 2.0
        effective_half = self.RETENTION_HALF_LIFE_HOURS * (1 + 0.5 * checks_passed)
        decay = math.exp(-0.693 * hours_since_practice / effective_half)
        return round(min(1.0, max(0.0, base * decay)), 3)

    def schedule_next_review(self, mastery: float, checks_passed: int) -> float:
        """Returns recommended minutes until next review (expanding intervals)."""
        base_hours = self.RETENTION_HALF_LIFE_HOURS * (1 + 0.5 * checks_passed)
        target_decay = 0.6
        t_hours = -base_hours * math.log(target_decay) / 0.693
        t_hours *= (0.5 + mastery)
        return round(t_hours * 60, 1)

    # ────────────────────────────────────────────────────────────
    #  FEATURE 7 — Adaptive hint depth
    # ────────────────────────────────────────────────────────────

    def _hint_depth_signal(self, ctx: PacingContext) -> Dict[str, Any]:
        total_q = max(ctx.questions_answered, 1)
        dep_ratio = ctx.hint_usage_count / total_q

        if dep_ratio > 0.7:
            progress_quality = "illusory"
            recommendation = "slow_down_reinforce"
        elif dep_ratio > self.HINT_DEPENDENCY_THRESHOLD:
            progress_quality = "fragile"
            recommendation = "add_scaffolding"
        elif dep_ratio > 0.2:
            progress_quality = "developing"
            recommendation = "maintain"
        else:
            progress_quality = "solid"
            recommendation = "safe_to_accelerate"

        return {
            "hint_count": ctx.hint_usage_count,
            "total_questions": total_q,
            "dependency_ratio": round(dep_ratio, 3),
            "progress_quality": progress_quality,
            "recommendation": recommendation,
        }

    # ────────────────────────────────────────────────────────────
    #  FEATURE 8 — Fatigue detection
    # ────────────────────────────────────────────────────────────

    def _detect_fatigue(self, ctx: PacingContext) -> FatigueLevel:
        signals = 0

        # Signal 1: Session duration
        dur = ctx.session_duration_minutes
        if dur > self.FATIGUE_TIME_THRESHOLDS[3]:
            signals += 2
        elif dur > self.FATIGUE_TIME_THRESHOLDS[2]:
            signals += 1.5
        elif dur > self.FATIGUE_TIME_THRESHOLDS[1]:
            signals += 1
        elif dur > self.FATIGUE_TIME_THRESHOLDS[0]:
            signals += 0.5

        # Signal 2: Question volume
        qcount = ctx.total_questions_session
        if qcount > self.FATIGUE_QUESTION_THRESHOLDS[3]:
            signals += 2
        elif qcount > self.FATIGUE_QUESTION_THRESHOLDS[2]:
            signals += 1.5
        elif qcount > self.FATIGUE_QUESTION_THRESHOLDS[1]:
            signals += 1
        elif qcount > self.FATIGUE_QUESTION_THRESHOLDS[0]:
            signals += 0.5

        # Signal 3: Declining accuracy trend
        trend = ctx.recent_accuracy_trend
        if len(trend) >= 4:
            first_half = trend[: len(trend) // 2]
            second_half = trend[len(trend) // 2 :]
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            if avg_second < avg_first - 0.15:
                signals += 1.5
            elif avg_second < avg_first - 0.05:
                signals += 0.5

        # Signal 4: Increasing response times
        times = ctx.recent_response_times
        if len(times) >= 4:
            first_half = times[: len(times) // 2]
            second_half = times[len(times) // 2 :]
            avg_first_t = sum(first_half) / len(first_half) if first_half else 1
            avg_second_t = sum(second_half) / len(second_half) if second_half else 1
            if avg_first_t > 0 and avg_second_t / avg_first_t > 1.4:
                signals += 1.5
            elif avg_first_t > 0 and avg_second_t / avg_first_t > 1.15:
                signals += 0.5

        if signals >= 5:
            return FatigueLevel.CRITICAL
        elif signals >= 3.5:
            return FatigueLevel.HIGH
        elif signals >= 2:
            return FatigueLevel.MODERATE
        elif signals >= 1:
            return FatigueLevel.MILD
        else:
            return FatigueLevel.FRESH

    def get_fatigue_recommendation(self, fatigue: FatigueLevel) -> Dict[str, Any]:
        recommendations = {
            FatigueLevel.FRESH: {
                "message": "You're doing great! Full steam ahead.",
                "action": "continue",
                "break_suggested": False,
                "lighter_mode": False,
            },
            FatigueLevel.MILD: {
                "message": "Slight fatigue detected. Consider a short break soon.",
                "action": "continue_with_awareness",
                "break_suggested": False,
                "lighter_mode": False,
            },
            FatigueLevel.MODERATE: {
                "message": "Fatigue building up. Easier questions incoming to maintain flow.",
                "action": "reduce_difficulty",
                "break_suggested": True,
                "lighter_mode": True,
            },
            FatigueLevel.HIGH: {
                "message": "High cognitive load detected. Take a 5-minute break.",
                "action": "suggest_break",
                "break_suggested": True,
                "lighter_mode": True,
            },
            FatigueLevel.CRITICAL: {
                "message": "You've been working hard! Please take a break to consolidate learning.",
                "action": "force_break",
                "break_suggested": True,
                "lighter_mode": True,
            },
        }
        return recommendations.get(fatigue, recommendations[FatigueLevel.FRESH])

    # ────────────────────────────────────────────────────────────
    #  FEATURE 9 — Interest-based examples (engagement)
    # ────────────────────────────────────────────────────────────

    def _engagement_signal(self, ctx: PacingContext) -> Optional[str]:
        if ctx.consecutive_skips >= 3:
            return "switch_mode"
        if ctx.engagement_score < 0.3:
            return "switch_mode"
        if ctx.engagement_score < 0.5 or ctx.drop_off_risk > 0.6:
            return "use_interest_examples"
        return None

    def compute_engagement_score(
        self,
        accuracy: float,
        avg_response_time: float,
        expected_time: float,
        streak: int,
        consecutive_skips: int = 0,
    ) -> float:
        score = 0.5
        score += min(0.25, accuracy * 0.25)

        ratio = avg_response_time / expected_time if expected_time > 0 else 1.0
        if 0.5 <= ratio <= 1.2:
            score += 0.15
        elif ratio > 2.0:
            score -= 0.1

        if streak >= 3:
            score += 0.1
        elif streak <= -3:
            score -= 0.15

        score -= consecutive_skips * 0.1

        return round(max(0.0, min(1.0, score)), 3)

    # ────────────────────────────────────────────────────────────
    #  FEATURE 10 — Learning velocity graph data
    # ────────────────────────────────────────────────────────────

    def _velocity_snapshot(self, ctx: PacingContext, speed_signal: Dict) -> Dict[str, float]:
        return {
            "mastery": round(ctx.mastery_score, 3),
            "theta": round(ctx.theta, 3),
            "accuracy": round(ctx.accuracy, 3),
            "speed_ratio": speed_signal.get("speed_ratio", 1.0),
            "questions_answered": ctx.questions_answered,
            "fatigue_score": self._fatigue_numeric(ctx),
            "engagement": round(ctx.engagement_score, 3),
            "hint_dependency": round(ctx.hint_usage_count / max(ctx.questions_answered, 1), 3),
        }

    def _fatigue_numeric(self, ctx: PacingContext) -> float:
        f = self._detect_fatigue(ctx)
        mapping = {
            FatigueLevel.FRESH: 0.0,
            FatigueLevel.MILD: 0.25,
            FatigueLevel.MODERATE: 0.5,
            FatigueLevel.HIGH: 0.75,
            FatigueLevel.CRITICAL: 1.0,
        }
        return mapping.get(f, 0.0)

    def compute_velocity_graph(self, snapshots: List[Dict[str, float]]) -> Dict[str, Any]:
        if not snapshots:
            return {"points": [], "trend": "none", "avg_velocity": 0.0}

        points = []
        for i, s in enumerate(snapshots):
            points.append({
                "index": i,
                "mastery": s.get("mastery", 0),
                "theta": s.get("theta", 0),
                "accuracy": s.get("accuracy", 0),
                "speed_ratio": s.get("speed_ratio", 1.0),
                "fatigue": s.get("fatigue_score", 0),
                "engagement": s.get("engagement", 0.5),
            })

        if len(points) >= 3:
            deltas = [points[i + 1]["mastery"] - points[i]["mastery"] for i in range(len(points) - 1)]
            avg_delta = sum(deltas) / len(deltas)
            if avg_delta > 0.02:
                trend = "accelerating"
            elif avg_delta < -0.02:
                trend = "decelerating"
            else:
                trend = "steady"
        else:
            trend = "insufficient_data"

        avg_velocity = sum(p["mastery"] for p in points) / len(points) if points else 0.0

        return {
            "points": points,
            "trend": trend,
            "avg_velocity": round(avg_velocity, 3),
            "total_points": len(points),
        }

    # ────────────────────────────────────────────────────────────
    #  Difficulty selector
    # ────────────────────────────────────────────────────────────

    def _recommend_difficulty(self, theta: float, decision: PacingDecision, level: str) -> str:
        if theta < -0.5:
            base = "easy"
        elif theta < 0.5:
            base = "medium"
        else:
            base = "hard"

        adjustments = {
            PacingDecision.SPEED_UP:        {"easy": "medium", "medium": "hard",   "hard": "hard"},
            PacingDecision.STAY:            {"easy": "easy",   "medium": "medium", "hard": "medium"},
            PacingDecision.SLOW_DOWN:       {"easy": "easy",   "medium": "easy",   "hard": "medium"},
            PacingDecision.SHARP_SLOWDOWN:  {"easy": "easy",   "medium": "easy",   "hard": "easy"},
        }

        result = adjustments.get(decision, {}).get(base, base)

        if level == "zero" and result == "hard":
            result = "medium"
        elif level == "advanced" and result == "easy" and decision != PacingDecision.SHARP_SLOWDOWN:
            result = "medium"

        return result

    # ────────────────────────────────────────────────────────────
    #  Legacy helpers
    # ────────────────────────────────────────────────────────────

    def get_next_difficulty(self, theta: float, current_pacing: PacingDecision, knowledge_level: str) -> str:
        return self._recommend_difficulty(theta, current_pacing, knowledge_level)

    def should_reteach(self, ctx: PacingContext) -> bool:
        error_types = ctx.error_types[-3:] if ctx.error_types else []
        return any([
            any(e in ("conceptual", "structural") for e in error_types),
            ctx.mastery_score < 0.3,
            ctx.streak <= -2 and ctx.mastery_score < 0.5,
            ctx.accuracy < 0.4 and "conceptual" in error_types,
        ])

    def should_advance(self, ctx: PacingContext) -> bool:
        ok, _ = self.should_exit_atom(ctx)
        return ok
