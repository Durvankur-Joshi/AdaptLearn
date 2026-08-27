# learning_engine/ai_assistant.py

import google.generativeai as genai
from django.conf import settings


# Configure Gemini
genai.configure(api_key=settings.GOOGLE_API_KEY)

model = genai.GenerativeModel("gemini-3-flash-preview")


def generate_ai_response(question, topic, level, accuracy=None):
    """
    Core Learning Engine Logic
    """

    # Adaptive Level Based on Accuracy (Optional)
    if accuracy is not None:
        if accuracy < 50:
            level = "Beginner"
        elif accuracy < 80:
            level = "Intermediate"
        else:
            level = "Advanced"

    difficulty_instruction = {
        "Beginner": "Explain in very simple language using real-life analogy.",
        "Intermediate": "Explain clearly with one technical example.",
        "Advanced": "Explain deeply with edge cases and complexity."
    }

    prompt = f"""
    You are an adaptive AI tutor.

    Student Level: {level}
    Topic: {topic}

    {difficulty_instruction.get(level)}

    Question: {question}

    Only answer if the question is related to academic syllabus.
    Keep answer under 200 words.
    """

    response = model.generate_content(prompt)

    return response.text