# backend/accounts/ai_planner.py
import google.generativeai as genai
import os
import json
import re
from datetime import date, timedelta

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# List available models (for debugging)
try:
    for m in genai.list_models():
        print(f"Available model: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")

# Use a valid model - gemini-1.5-flash or gemini-1.5-pro
model = genai.GenerativeModel("gemini-2.0-flash")  # Changed from gemini-2.5-flash

def generate_subtopics(subject, goal, num_topics=8):
    """
    Generate subtopics for a given subject using Gemini AI
    
    Args:
        subject: The subject name (e.g., "Mathematics", "Physics")
        goal: The learning goal (e.g., "Exam Preparation", "Regular Study")
        num_topics: Number of topics to generate (default 8)
    
    Returns:
        List of subtopics
    """
    prompt = f"""
    You are an expert curriculum designer. Break down the subject "{subject}" into {num_topics} structured subtopics.
    
    Goal: {goal}
    
    Requirements:
    - Each topic should be a clear, specific learning unit
    - Topics should progress from fundamentals to advanced concepts
    - Each topic should be 2-5 words long
    - Topics should be mutually exclusive
    
    Return ONLY a valid JSON array of strings. No explanations, no markdown, no additional text.
    
    Example format:
    ["Introduction to Algebra", "Linear Equations", "Quadratic Functions", "Polynomials", "Factoring", "Rational Expressions", "Exponents", "Logarithms"]
    
    Generate exactly {num_topics} topics for {subject}:
    """

    try:
        print(f"Generating topics for {subject}...")
        response = model.generate_content(prompt)
        
        # Get the response text
        response_text = response.text
        print(f"Raw response: {response_text[:200]}...")  # Debug print
        
        # Clean the response - remove markdown code blocks if present
        cleaned_text = clean_json_response(response_text)
        
        # Parse JSON
        try:
            topics = json.loads(cleaned_text)
            if isinstance(topics, list) and len(topics) > 0:
                print(f"Successfully generated {len(topics)} topics")
                return topics[:num_topics]  # Ensure we don't exceed requested number
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            # Try to extract array using regex as fallback
            topics = extract_topics_from_text(response_text)
            if topics:
                return topics[:num_topics]
        
        # If all else fails, return default topics
        return get_default_topics(subject)
        
    except Exception as e:
        print(f"Error generating topics: {e}")
        return get_default_topics(subject)

def clean_json_response(text):
    """Remove markdown code blocks and clean up JSON response"""
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    # Remove any leading/trailing whitespace
    text = text.strip()
    
    # If the text doesn't start with [, wrap it in array brackets
    if not text.startswith('['):
        # Try to find array pattern
        match = re.search(r'\[(.*?)\]', text, re.DOTALL)
        if match:
            text = match.group(0)
    
    return text

def extract_topics_from_text(text):
    """Extract topics from text when JSON parsing fails"""
    # Look for bullet points or numbered lists
    lines = text.split('\n')
    topics = []
    
    for line in lines:
        line = line.strip()
        # Remove bullet points, numbers, and dashes
        cleaned = re.sub(r'^[•\-*\d+\.\s]+', '', line)
        if cleaned and len(cleaned) > 3 and len(cleaned) < 50:
            # Avoid adding lines that look like instructions
            if not any(word in cleaned.lower() for word in ['json', 'array', 'format', 'example']):
                topics.append(cleaned)
    
    return topics

def get_default_topics(subject):
    """Return default topics for common subjects"""
    default_topics = {
        'mathematics': [
            "Number Systems", "Algebra Basics", "Linear Equations", 
            "Quadratic Equations", "Geometry", "Trigonometry", 
            "Calculus", "Statistics"
        ],
        'physics': [
            "Mechanics", "Kinematics", "Dynamics", "Thermodynamics",
            "Waves and Optics", "Electricity", "Magnetism", "Modern Physics"
        ],
        'chemistry': [
            "Atomic Structure", "Chemical Bonding", "Periodic Table",
            "Stoichiometry", "Thermochemistry", "Organic Chemistry",
            "Inorganic Chemistry", "Chemical Kinetics"
        ],
        'computer science': [
            "Programming Basics", "Data Structures", "Algorithms",
            "Database Systems", "Operating Systems", "Networks",
            "Web Development", "Software Engineering"
        ],
        'biology': [
            "Cell Biology", "Genetics", "Evolution", "Ecology",
            "Human Anatomy", "Physiology", "Biochemistry", "Molecular Biology"
        ]
    }
    
    # Find matching subject (case insensitive)
    subject_lower = subject.lower()
    for key, topics in default_topics.items():
        if key in subject_lower or subject_lower in key:
            return topics
    
    # Generic topics for unknown subjects
    return [
        f"Introduction to {subject}",
        f"Fundamental Concepts of {subject}",
        f"Core Principles",
        f"Advanced Topics in {subject}",
        f"Applications of {subject}",
        f"Problem Solving Techniques",
        f"Case Studies",
        f"Review and Assessment"
    ]

def distribute_topics(planner, subjects_with_topics):
    """
    Distribute topics across days based on planner settings
    
    Args:
        planner: StudyPlanner instance
        subjects_with_topics: List of dicts with subject_name and topics
    
    Returns:
        List of schedule items
    """
    from datetime import date, timedelta
    
    today = date.today()
    
    # Determine number of days based on planner option
    if planner.day_option == "mon_fri":
        # Skip weekends - find next Monday if today is weekend
        current_date = today
        while current_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            current_date += timedelta(days=1)
        days_to_schedule = 5
    else:
        current_date = today
        days_to_schedule = 7
    
    schedule = []
    
    # Create a round-robin distribution of topics
    subject_queues = {}
    for subject_data in subjects_with_topics:
        subject_queues[subject_data["subject_name"]] = {
            'topics': subject_data["topics"].copy(),
            'index': 0
        }
    
    # Calculate hours per subject per day
    hours_per_subject = planner.free_hours_per_day / len(subjects_with_topics)
    
    # Generate schedule for each day
    for day_num in range(days_to_schedule):
        # Skip weekends if mon_fri option
        if planner.day_option == "mon_fri" and current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue
            
        day_schedule = []
        
        for subject_data in subjects_with_topics:
            subject_name = subject_data["subject_name"]
            queue = subject_queues[subject_name]
            
            # Get next topic (cycle through topics)
            if queue['topics']:
                topic = queue['topics'][queue['index'] % len(queue['topics'])]
                queue['index'] += 1
            else:
                topic = f"Review {subject_name}"
            
            day_schedule.append({
                "subject": subject_name,
                "topic": topic,
                "hours": round(hours_per_subject, 1)
            })
        
        schedule.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "day": current_date.strftime("%A"),
            "sessions": day_schedule,
            "total_hours": planner.free_hours_per_day
        })
        
        current_date += timedelta(days=1)
    
    return schedule

# Test function
if __name__ == "__main__":
    # Test the generator
    topics = generate_subtopics("Mathematics", "Exam Preparation", 8)
    print(f"Generated topics: {topics}")
    
    # Test with a mock planner
    class MockPlanner:
        def __init__(self):
            self.day_option = "mon_sun"
            self.free_hours_per_day = 3
    
    mock_planner = MockPlanner()
    subjects = [
        {"subject_name": "Mathematics", "topics": generate_subtopics("Mathematics", "Study", 5)},
        {"subject_name": "Physics", "topics": generate_subtopics("Physics", "Study", 5)}
    ]
    
    schedule = distribute_topics(mock_planner, subjects)
    print("\nSchedule:")
    for day in schedule[:3]:  # Show first 3 days
        print(f"\n{day['date']} ({day['day']}):")
        for session in day['sessions']:
            print(f"  - {session['subject']}: {session['topic']} ({session['hours']} hrs)")