# backend/test_question_generator.py

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from learning_engine.question_generator import QuestionGenerator
from django.conf import settings

def test_generator():
    print("=" * 50)
    print("Testing QuestionGenerator")
    print("=" * 50)
    
    print(f"GROQ_API_KEY present: {'Yes' if settings.GROQ_API_KEY else 'No'}")
    print(f"GOOGLE_API_KEY present: {'Yes' if settings.GOOGLE_API_KEY else 'No'}")
    
    generator = QuestionGenerator()
    print(f"Groq client initialized: {'Yes' if generator.groq_client else 'No'}")
    print(f"Gemini model initialized: {'Yes' if generator.gemini_model else 'No'}")
    
    if not generator.groq_client and not generator.gemini_model:
        print("\n❌ ERROR: No AI clients available! Check your API keys.")
        return
    
    print("\n" + "=" * 50)
    print("Test 1: Generate atoms")
    print("=" * 50)
    atoms = generator.generate_atoms("Microprocessor", "Memory Organization")
    print(f"Generated atoms: {atoms}")
    
    if atoms:
        print("\n" + "=" * 50)
        print("Test 2: Generate questions for first atom")
        print("=" * 50)
        questions = []
        questions.extend(generator.generate_questions(
            subject="Microprocessor",
            concept="Memory Organization",
            atom=atoms[0],
            target_difficulty="easy",
            count=2,
            knowledge_level='intermediate'
        ))
        questions.extend(generator.generate_questions(
            subject="Microprocessor",
            concept="Memory Organization",
            atom=atoms[0],
            target_difficulty="medium",
            count=2,
            knowledge_level='intermediate'
        ))
        print(f"Generated {len(questions)} questions")
        for i, q in enumerate(questions):
            print(f"\nQ{i+1}: {q.get('question', 'No question')}")
            print(f"   Difficulty: {q.get('difficulty')}")
            print(f"   Cognitive: {q.get('cognitive_operation')}")
            print(f"   Time: {q.get('estimated_time')}s")
    
    print("\n" + "=" * 50)
    print("Test 3: Generate complete concept")
    print("=" * 50)
    result = generator.generate_complete_concept("Microprocessor", "Memory Organization")
    print(f"Generated concept with {len(result.get('atoms', {}))} atoms")
    for atom_name, atom_data in result['atoms'].items():
        print(f"  - {atom_name}: {len(atom_data['questions'])} questions")

if __name__ == "__main__":
    test_generator()