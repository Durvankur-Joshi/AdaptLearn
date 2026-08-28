# learning_engine/ai_assistant.py
"""
Adaptive AI Tutor / Assistant powered by centralized OpenRouter integration.
"""

import logging
from .openrouter_client import call_openrouter

logger = logging.getLogger('learning_engine.ai_assistant')


def generate_ai_response(question, topic, level, accuracy=None):
    """
    Core Learning Engine Logic - AI Doubt Solver
    """
    # Adaptive Level Based on Accuracy (Optional)
    if accuracy is not None:
        try:
            acc_val = float(accuracy)
            if acc_val < 50:
                level = "Beginner"
            elif acc_val < 80:
                level = "Intermediate"
            else:
                level = "Advanced"
        except (ValueError, TypeError):
            pass

    difficulty_instruction = {
        "Beginner": "Explain in very simple language using a real-life analogy.",
        "Intermediate": "Explain clearly with one technical example.",
        "Advanced": "Explain deeply with edge cases and complexity."
    }

    prompt = f"""
You are an adaptive AI tutor.

Student Level: {level}
Topic: {topic}

{difficulty_instruction.get(level, 'Explain clearly and step-by-step.')}

Question: {question}

Only answer if the question is related to academic syllabus.
Keep answer under 200 words.
"""

    try:
        return call_openrouter(
            prompt=prompt,
            system_prompt="You are an adaptive AI tutor. Provide concise, high-quality explanations.",
            temperature=0.4,
            max_tokens=400
        )
    except Exception as e:
        logger.error(f"AI Assistant OpenRouter call failed: {e}")
        return f"I'm sorry, I could not process your question about {topic} right now. Please try again in a moment."