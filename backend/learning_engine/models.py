from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class LearningPhase(str, Enum):
    NOT_STARTED = "not_started"
    DIAGNOSTIC = "diagnostic"
    TEACHING = "teaching"
    PRACTICE = "practice"
    REINFORCEMENT = "reinforcement"
    MASTERY_CHECK = "mastery_check"
    COMPLETE = "complete"
    FRAGILE = "fragile"


class ErrorType(str, Enum):
    CONCEPTUAL = "conceptual"
    PROCEDURAL = "procedural"
    FACTUAL = "factual"
    GUESSING = "guessing"
    STRUCTURAL = "structural"
    ATTENTIONAL = "attentional"


class PacingDecision(str, Enum):
    SPEED_UP = "speed_up"
    SLOW_DOWN = "slow_down"
    SHARP_SLOWDOWN = "sharp_slowdown"
    STAY = "stay"
    REINFORCE = "reinforce"
    ADVANCE = "advance"
    RETREAT = "retreat"


@dataclass
class TeachingAtomState:
    """Represents a teaching atom's state in memory — enriched for the 10-feature pacing engine."""
    id: int
    name: str
    mastery_score: float = 0.0
    phase: LearningPhase = LearningPhase.NOT_STARTED
    streak: int = 0
    hint_usage: int = 0
    error_history: List[str] = None
    retention_verified: bool = False

    # ── Per-atom learning speed (feature 2) ──
    time_per_question: List[float] = None

    # ── Retention tracking (feature 6) ──
    retention_score: float = 1.0
    retention_checks_passed: int = 0
    retention_checks_failed: int = 0
    last_practiced_minutes_ago: float = 0.0

    # ── Velocity snapshots (feature 10) ──
    velocity_snapshots: List[Dict] = None

    def __post_init__(self):
        if self.error_history is None:
            self.error_history = []
        if self.time_per_question is None:
            self.time_per_question = []
        if self.velocity_snapshots is None:
            self.velocity_snapshots = []

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'mastery_score': self.mastery_score,
            'phase': self.phase.value if hasattr(self.phase, 'value') else self.phase,
            'streak': self.streak,
            'hint_usage': self.hint_usage,
            'retention_verified': self.retention_verified,
            'error_history': self.error_history[-5:],
            'retention_score': self.retention_score,
            'retention_checks_passed': self.retention_checks_passed,
            'time_per_question': self.time_per_question[-10:],
            'velocity_snapshots': self.velocity_snapshots[-20:],
        }
