import json
from typing import Any, Dict, List

def extract_json(text: str) -> str:
    """Extract JSON from text that might contain markdown code blocks"""
    text = text.strip()
    if text.startswith("```"):
        # Remove fenced code block markers
        lines = [ln.rstrip() for ln in text.splitlines()]
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return text

def normalize_difficulty(value: str) -> str:
    """Normalize difficulty string"""
    v = (value or "").strip().lower()
    if v in ("med", "mid"):
        return "medium"
    return v

def difficulty_count(questions: List[Dict[str, Any]], difficulty: str) -> int:
    """Count questions of a specific difficulty"""
    d = normalize_difficulty(difficulty)
    return sum(1 for q in questions if normalize_difficulty(q.get("difficulty", "")) == d)

def existing_texts(questions: List[Dict[str, Any]], difficulty: str) -> set:
    """Get set of question texts for a specific difficulty"""
    d = normalize_difficulty(difficulty)
    return {
        (q.get("question") or "").strip().lower()
        for q in questions
        if normalize_difficulty(q.get("difficulty", "")) == d
    }