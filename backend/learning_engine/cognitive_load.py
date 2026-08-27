# backend/learning_engine/cognitive_load.py
# Live cognitive load signal and session-shape actions.
# Combines session duration, question count, response time ratio, accuracy, hints, fatigue
# to produce a load score 0-1 and a recommended session-shape action.

from typing import Tuple


def compute_cognitive_load(
    session_duration_minutes: float,
    total_questions_session: int,
    time_taken: float,
    expected_time: float,
    recent_accuracy: float,
    hint_usage_ratio: float,
    fatigue_level: str,
) -> Tuple[float, str]:
    """
    Compute cognitive load score (0 = low, 1 = high) and session-shape action.

    Args:
        session_duration_minutes: Minutes since session start.
        total_questions_session: Total questions answered in this session.
        time_taken: Seconds taken for the last question.
        expected_time: Expected seconds for the question (e.g. estimated_time).
        recent_accuracy: Accuracy over last N answers (0-1).
        hint_usage_ratio: Hints used / questions in session (0-1).
        fatigue_level: 'fresh' | 'mild' | 'moderate' | 'high' | 'critical'.

    Returns:
        (load_score, session_shape_action)
    """
    raw = 0.0

    # Time ratio: slow response suggests higher load
    if expected_time and expected_time > 0:
        time_ratio = time_taken / expected_time
        if time_ratio > 2.0:
            raw += 0.25
        elif time_ratio > 1.5:
            raw += 0.15
        elif time_ratio > 1.2:
            raw += 0.08

    # Session duration: longer session → more load
    if session_duration_minutes > 35:
        raw += 0.25
    elif session_duration_minutes > 25:
        raw += 0.15
    elif session_duration_minutes > 18:
        raw += 0.08

    # Question count: many questions → more load
    if total_questions_session > 35:
        raw += 0.2
    elif total_questions_session > 25:
        raw += 0.12
    elif total_questions_session > 18:
        raw += 0.06

    # Recent accuracy: drop suggests load or struggle
    if recent_accuracy < 0.4:
        raw += 0.2
    elif recent_accuracy < 0.6:
        raw += 0.1

    # Hint usage: high dependency suggests load
    if hint_usage_ratio > 0.5:
        raw += 0.15
    elif hint_usage_ratio > 0.3:
        raw += 0.08

    # Fatigue: map to load
    fatigue_map = {
        'critical': 0.35,
        'high': 0.22,
        'moderate': 0.12,
        'mild': 0.05,
        'fresh': 0.0,
    }
    raw += fatigue_map.get(
        (fatigue_level or 'fresh').lower().strip(),
        fatigue_map['fresh'],
    )

    # Normalize to 0-1 (cap at 1)
    load_score = min(1.0, raw / 0.85)

    # Session-shape action
    if load_score >= 0.75:
        session_shape_action = 'suggest_end'
    elif load_score >= 0.6:
        session_shape_action = 'switch_easy'
    elif load_score >= 0.5:
        session_shape_action = 'suggest_break'
    elif load_score < 0.35 and total_questions_session >= 3:
        session_shape_action = 'offer_one_more'
    else:
        session_shape_action = 'continue'

    return (round(load_score, 3), session_shape_action)


def get_session_shape_message(action: str) -> str:
    """Return user-facing message for the session-shape action."""
    messages = {
        'continue': '',
        'offer_one_more': "You're in the zone – want one more?",
        'suggest_break': "Time for a short break?",
        'switch_easy': "Let's switch to something lighter next.",
        'suggest_end': "Session ending soon – you've done a lot.",
    }
    return messages.get(action, '')
