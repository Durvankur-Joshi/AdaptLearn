import calendar as cal_module
import json
import secrets
from datetime import date, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from learning_engine.ai_assistant import generate_ai_response
import logging
from django.db import models
from django.db.models import Max
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.views import APIView, csrf_exempt
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import StudyPlanner, PlannerSubject
from .planner_engine import generate_timetable
from learning_engine.ai_study_planner import generate_subtopics, distribute_topics
from .models import StudyPlanItem
from datetime import datetime



from .models import (
    Concept, TeachingAtom, Question, StudentProgress,
    LearningSession, LearningProfile, KnowledgeLevel, UserXP,
    TeacherProfile, TeacherContent, QuestionApproval,
    TeacherOverride, TeacherGoal,
    ParentProfile, ParentChild,
)
from .serializers import (
    RegisterSerializer, UserSerializer, ConceptSerializer,
    TeachingAtomSerializer, QuestionSerializer,
    TeacherProfileSerializer, TeacherRegisterSerializer,
    TeacherContentSerializer, QuestionApprovalSerializer,
    TeacherOverrideSerializer, TeacherGoalSerializer,
    StudentDetailSerializer, StudentProgressSerializer,
    ParentProfileSerializer, ParentRegisterSerializer, ParentChildSerializer,
)
from learning_engine.question_generator import QuestionGenerator
from learning_engine.adaptive_flow import AdaptiveLearningEngine, MASTERY_THRESHOLD
from django.conf import settings
from learning_engine.knowledge_tracing import (
    bkt_update, update_theta, classify_behavior, 
    update_mastery_from_behavior, classify_error_type
)


from learning_engine.pacing_engine import PacingEngine, PacingContext
from learning_engine.models import TeachingAtomState

logger = logging.getLogger(__name__)


def _normalize_pacing_value(pacing_entry, default='stay'):
    if isinstance(pacing_entry, dict):
        return pacing_entry.get('pacing', default)
    if isinstance(pacing_entry, str):
        return pacing_entry
    return default


def _friendly_wrong_explanation(question, teaching_content=None, error_type=None):
    options = question.get('options', []) or []
    correct_index = question.get('correct_index')
    correct_option = None

    if isinstance(correct_index, int) and 0 <= correct_index < len(options):
        correct_option = options[correct_index]

    if teaching_content and isinstance(teaching_content, dict):
        misconception = teaching_content.get('misconception')
        if misconception:
            if correct_option:
                return f"Correct answer: {correct_option}. Tip: {misconception}"
            return f"Tip: {misconception}"

        explanation = teaching_content.get('explanation')
        if explanation:
            short_expl = explanation if len(explanation) <= 220 else explanation[:220].rstrip() + "..."
            if correct_option:
                return f"Correct answer: {correct_option}. Why: {short_expl}"
            return f"Why: {short_expl}"

    if error_type == 'conceptual':
        base = "You may be mixing the core idea with a related concept."
    elif error_type == 'procedural':
        base = "The sequence/steps seem to be the issue."
    elif error_type == 'factual':
        base = "This needs a quick fact/definition recall."
    elif error_type == 'guessing':
        base = "Try eliminating options and map each one to the taught content."
    else:
        base = "Review the taught explanation and try again."

    if correct_option:
        return f"Correct answer: {correct_option}. {base}"
    return base

# ==================== AUTH VIEWS ====================

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'user': UserSerializer(user).data,
                'message': 'User created successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.learning_profile
        except:
            profile = LearningProfile.objects.create(user=request.user)
        
        return Response({
            'user': UserSerializer(request.user).data,
            'dashboard_data': {
                'learning_streak': profile.learning_streak,
                'total_time_spent': profile.total_time_spent,
                'overall_theta': profile.overall_theta
            },
            'message': f'Welcome back, {request.user.first_name}!'
        })


# ==================== SUGGESTION / AUTOCOMPLETE ====================

import time as _time
from google import genai as _genai

# --- Caches ---
# subject_key → { "concepts": [...], "ts": timestamp }
_concept_cache = {}
# (subject_key, query) → { "concepts": [...], "ts": timestamp }
_query_cache = {}

_CACHE_TTL = 600          # 10 minutes
_CONCEPT_CACHE_TTL = 900  # 15 minutes for full subject concepts


def _get_gemini_client():
    """Lazy singleton for Gemini client. Uses GEMINI_API_KEY only to avoid conflict warnings."""
    gemini_key = getattr(settings, 'GEMINI_API_KEY', '') or getattr(settings, 'GOOGLE_API_KEY', '')
    if not gemini_key:
        return None
    # Temporarily unset GOOGLE_API_KEY env var to avoid the SDK warning
    # "Both GOOGLE_API_KEY and GEMINI_API_KEY are set. Using GOOGLE_API_KEY."
    import os as _os
    saved = _os.environ.pop('GOOGLE_API_KEY', None)
    try:
        return _genai.Client(api_key=gemini_key)
    finally:
        if saved is not None:
            _os.environ['GOOGLE_API_KEY'] = saved


def _gemini_generate(prompt, max_tokens=400, temperature=0.4):
    """Call Gemini and return raw text, or '' on failure."""
    client = _get_gemini_client()
    if not client:
        return ''
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=_genai.types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )
        return (response.text or '').strip()
    except Exception as e:
        logger.warning(f"Gemini suggestion call failed: {e}")
        return ''


def _parse_json_array(raw):
    """Extract a JSON array of strings from raw LLM output."""
    if not raw:
        return []
    try:
        if '```' in raw:
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        import re as _re
        raw = _re.sub(r'[\x00-\x1f\x7f]', '', raw)
        data = json.loads(raw.strip())
        if isinstance(data, list):
            return [str(c).strip() for c in data if c]
    except Exception:
        pass
    return []


def _is_stale(entry, ttl):
    return entry is None or (_time.time() - entry.get('ts', 0)) > ttl


POPULAR_SUBJECTS = [
    # ── Computer Science & IT ──
    "Computer Science", "Data Structures", "Algorithms", "Operating Systems",
    "Database Management", "DBMS", "Computer Networks", "Compiler Design",
    "Theory of Computation", "Computer Architecture", "Computer Organization",
    "Software Engineering", "Object Oriented Programming", "OOP",
    "Computer Graphics", "Distributed Systems", "Parallel Computing",
    "Information Theory", "Formal Languages", "Automata Theory",
    "System Design", "Design Patterns", "API Design",

    # ── Programming Languages ──
    "Python Programming", "Java Programming", "C Programming",
    "C++ Programming", "JavaScript", "TypeScript", "Rust Programming",
    "Go Programming", "Kotlin Programming", "Swift Programming",
    "Ruby Programming", "PHP Programming", "R Programming",
    "Scala Programming", "Perl Programming", "Haskell",
    "Assembly Language", "SQL", "Shell Scripting", "MATLAB",

    # ── Web & Mobile Development ──
    "Web Development", "Frontend Development", "Backend Development",
    "Full Stack Development", "React", "Angular", "Vue.js", "Next.js",
    "Node.js", "Django", "Flask", "Spring Boot", "Express.js",
    "HTML and CSS", "REST API", "GraphQL", "WebSockets",
    "Mobile App Development", "Android Development", "iOS Development",
    "React Native", "Flutter", "Progressive Web Apps",

    # ── AI / ML / Data ──
    "Machine Learning", "Artificial Intelligence", "Deep Learning",
    "Natural Language Processing", "Computer Vision", "Reinforcement Learning",
    "Neural Networks", "Data Science", "Data Analytics", "Big Data",
    "Data Mining", "Data Engineering", "MLOps",
    "Generative AI", "Large Language Models", "Prompt Engineering",
    "TensorFlow", "PyTorch", "Scikit-learn",
    "Feature Engineering", "Model Deployment",

    # ── Cloud & DevOps ──
    "Cloud Computing", "AWS", "Microsoft Azure", "Google Cloud Platform",
    "Docker", "Kubernetes", "DevOps", "CI/CD",
    "Terraform", "Ansible", "Jenkins", "Linux Administration",
    "Microservices Architecture", "Serverless Computing",
    "Site Reliability Engineering", "Infrastructure as Code",

    # ── Cyber Security ──
    "Cyber Security", "Ethical Hacking", "Penetration Testing",
    "Cryptography", "Network Security", "Information Security",
    "Web Security", "Malware Analysis", "Digital Forensics",
    "Security Operations", "OWASP", "Blockchain Security",

    # ── Networking & Systems ──
    "Networking", "TCP/IP", "Wireless Networks",
    "Network Administration", "Firewalls and VPN",
    "Embedded Systems", "Internet of Things", "IoT",
    "Real Time Operating Systems", "Edge Computing",

    # ── Hardware & Electronics ──
    "Microprocessor", "Microcontroller", "Digital Electronics",
    "Analog Electronics", "Signal Processing", "VLSI Design",
    "Embedded C", "Arduino", "Raspberry Pi", "PCB Design",
    "Communication Systems", "Antenna Design",
    "Control Systems", "Instrumentation", "Sensors and Actuators",
    "Power Electronics", "Electrical Machines",

    # ── Mathematics ──
    "Mathematics", "Calculus", "Linear Algebra", "Discrete Mathematics",
    "Probability", "Statistics", "Number Theory", "Real Analysis",
    "Complex Analysis", "Abstract Algebra", "Topology",
    "Differential Equations", "Numerical Methods", "Mathematical Logic",
    "Graph Theory", "Combinatorics", "Optimization",
    "Operations Research", "Game Theory", "Stochastic Processes",

    # ── Physics ──
    "Physics", "Classical Mechanics", "Quantum Mechanics",
    "Thermodynamics", "Electromagnetism", "Optics",
    "Nuclear Physics", "Particle Physics", "Astrophysics",
    "Relativity", "Solid State Physics", "Fluid Mechanics",
    "Acoustics", "Plasma Physics", "Biophysics",
    "Semiconductor Physics", "Nanotechnology",

    # ── Chemistry ──
    "Chemistry", "Organic Chemistry", "Inorganic Chemistry",
    "Physical Chemistry", "Analytical Chemistry", "Biochemistry",
    "Polymer Chemistry", "Medicinal Chemistry", "Environmental Chemistry",
    "Electrochemistry", "Spectroscopy", "Chemical Engineering",

    # ── Biology & Life Sciences ──
    "Biology", "Cell Biology", "Molecular Biology", "Genetics",
    "Microbiology", "Biotechnology", "Bioinformatics",
    "Ecology", "Zoology", "Botany", "Human Anatomy",
    "Physiology", "Immunology", "Neuroscience",
    "Evolutionary Biology", "Marine Biology",

    # ── Engineering Core ──
    "Electrical Engineering", "Mechanical Engineering",
    "Civil Engineering", "Electronics Engineering",
    "Chemical Engineering", "Aerospace Engineering",
    "Biomedical Engineering", "Industrial Engineering",
    "Environmental Engineering", "Materials Science",
    "Manufacturing Engineering", "Mechatronics",
    "Structural Analysis", "Engineering Drawing",
    "Strength of Materials", "Engineering Mechanics",

    # ── Blockchain & Emerging Tech ──
    "Blockchain", "Cryptocurrency", "Smart Contracts",
    "Solidity Programming", "DeFi", "NFTs", "Web3",
    "Quantum Computing", "Augmented Reality", "Virtual Reality",
    "Metaverse", "3D Printing", "Autonomous Vehicles",
    "Drone Technology", "Brain Computer Interface",

    # ── Business & Management ──
    "Economics", "Microeconomics", "Macroeconomics",
    "Business Analytics", "Financial Accounting",
    "Marketing", "Digital Marketing", "Entrepreneurship",
    "Project Management", "Supply Chain Management",
    "Human Resource Management", "Organizational Behavior",
    "Business Communication", "Corporate Finance",
    "Stock Market", "Investment Banking",

    # ── Social Sciences & Humanities ──
    "Psychology", "Sociology", "Philosophy",
    "Political Science", "History", "Geography",
    "Anthropology", "Linguistics", "Cultural Studies",
    "International Relations", "Public Administration",
    "English Literature", "Creative Writing",
    "Journalism", "Mass Communication",

    # ── Data & Analytics Tools ──
    "Power BI", "Tableau", "Excel Advanced", "Google Analytics",
    "Apache Spark", "Hadoop", "Kafka", "Airflow",
    "Snowflake", "MongoDB", "PostgreSQL", "Redis",
    "Elasticsearch", "Neo4j", "Cassandra",

    # ── Testing & Quality ──
    "Software Testing", "Automation Testing", "Selenium",
    "Unit Testing", "Performance Testing", "Test Driven Development",
    "Quality Assurance", "Agile Methodology", "Scrum",

    # ── Robotics & Automation ──
    "Robotics", "Robot Operating System", "Industrial Automation",
    "PLC Programming", "SCADA", "Computer Aided Design",
    "Computer Aided Manufacturing", "Finite Element Analysis",

    # ── Competitive & Interview Prep ──
    "Competitive Programming", "System Design Interview",
    "Data Structures and Algorithms", "Aptitude and Reasoning",
    "Verbal Ability", "Logical Reasoning", "Quantitative Aptitude",
]

# ─── Concept maps for every subject (offline, zero API calls for subjects) ───
FALLBACK_CONCEPTS = {
    # ── CS & IT ──
    "computer science": ["Data Structures", "Algorithms", "Operating Systems", "Computer Networks", "Database Systems", "Compiler Design", "Theory of Computation", "Computer Architecture", "Software Engineering", "Artificial Intelligence", "Machine Learning", "OOP", "Discrete Mathematics", "Computer Graphics", "Distributed Systems"],
    "data structures": ["Arrays", "Linked Lists", "Stacks", "Queues", "Trees", "Binary Search Trees", "Heaps", "Hash Tables", "Graphs", "Tries", "AVL Trees", "Red-Black Trees", "B-Trees", "Priority Queues", "Disjoint Sets"],
    "algorithms": ["Sorting Algorithms", "Searching Algorithms", "Dynamic Programming", "Greedy Algorithms", "Divide and Conquer", "Graph Algorithms", "Backtracking", "Recursion", "Time Complexity", "Space Complexity", "BFS and DFS", "Shortest Path", "Minimum Spanning Tree", "String Matching", "NP-Completeness"],
    "operating systems": ["Process Management", "Thread Management", "CPU Scheduling", "Memory Management", "Virtual Memory", "File Systems", "I/O Management", "Deadlocks", "Synchronization", "Paging", "Segmentation", "Disk Scheduling", "System Calls", "Interrupts", "Booting Process"],
    "database management": ["SQL", "Normalization", "ER Diagrams", "Relational Model", "Indexing", "Transactions", "ACID Properties", "Joins", "Views", "Stored Procedures", "NoSQL", "Query Optimization", "Concurrency Control", "Data Warehousing", "Database Security"],
    "dbms": ["SQL", "Normalization", "ER Diagrams", "Relational Model", "Indexing", "Transactions", "ACID Properties", "Joins", "Views", "Stored Procedures", "NoSQL", "Query Optimization", "Concurrency Control", "Data Warehousing", "Database Security"],
    "computer networks": ["OSI Model", "TCP/IP", "HTTP", "DNS", "Routing", "Switching", "IP Addressing", "Subnetting", "Firewalls", "VPN", "Wi-Fi", "Ethernet", "Network Security", "Socket Programming", "Load Balancing"],
    "compiler design": ["Lexical Analysis", "Syntax Analysis", "Semantic Analysis", "Intermediate Code", "Code Optimization", "Code Generation", "Symbol Table", "Parsing Techniques", "LL Parsing", "LR Parsing", "Syntax Trees", "Regular Expressions", "Context Free Grammar", "Type Checking", "Error Handling"],
    "theory of computation": ["Finite Automata", "Regular Languages", "Context Free Grammar", "Pushdown Automata", "Turing Machines", "Decidability", "Complexity Classes", "P vs NP", "Regular Expressions", "Chomsky Hierarchy", "Pumping Lemma", "Church Turing Thesis", "Halting Problem", "Reduction", "Rice Theorem"],
    "computer architecture": ["CPU Design", "Instruction Set Architecture", "Pipelining", "Cache Memory", "Memory Hierarchy", "Bus Architecture", "I/O Systems", "RISC vs CISC", "Parallel Processing", "Superscalar", "Branch Prediction", "Virtual Memory Hardware", "Multicore Processors", "ALU Design", "Microprogramming"],
    "computer organization": ["CPU Design", "Instruction Set Architecture", "Pipelining", "Cache Memory", "Memory Hierarchy", "Bus Architecture", "I/O Systems", "RISC vs CISC", "Parallel Processing", "ALU Design", "Register Transfer", "Control Unit", "Microprogramming", "Addressing Modes", "Interrupt Handling"],
    "software engineering": ["SDLC", "Agile", "Scrum", "UML Diagrams", "Design Patterns", "Testing", "Version Control", "Requirements Engineering", "Code Review", "CI/CD", "Microservices", "API Design", "Documentation", "Debugging", "Project Management"],
    "object oriented programming": ["Classes and Objects", "Inheritance", "Polymorphism", "Encapsulation", "Abstraction", "Constructors", "Destructors", "Method Overloading", "Method Overriding", "Interfaces", "Abstract Classes", "Design Patterns", "SOLID Principles", "Composition", "Association"],
    "oop": ["Classes and Objects", "Inheritance", "Polymorphism", "Encapsulation", "Abstraction", "Constructors", "Destructors", "Method Overloading", "Method Overriding", "Interfaces", "Abstract Classes", "Design Patterns", "SOLID Principles", "Composition", "Association"],
    "computer graphics": ["Rasterization", "Ray Tracing", "Transformations", "Clipping", "Shading", "Texture Mapping", "3D Rendering", "Bezier Curves", "OpenGL", "WebGL", "Color Models", "Anti-Aliasing", "Hidden Surface Removal", "Projection", "Animation"],
    "distributed systems": ["CAP Theorem", "Consensus Algorithms", "Replication", "Partitioning", "MapReduce", "RPC", "Distributed Databases", "Leader Election", "Eventual Consistency", "Clock Synchronization", "Fault Tolerance", "Load Balancing", "Microservices", "Message Queues", "Gossip Protocol"],
    "system design": ["Scalability", "Load Balancing", "Caching", "Database Sharding", "CAP Theorem", "Microservices", "Message Queues", "API Gateway", "Rate Limiting", "Consistent Hashing", "CDN", "Replication", "Monitoring", "Logging", "Design Patterns"],
    "design patterns": ["Singleton", "Factory", "Observer", "Strategy", "Decorator", "Adapter", "Proxy", "Command", "Iterator", "State", "Template Method", "Builder", "Prototype", "Facade", "MVC"],

    # ── Programming Languages ──
    "python programming": ["Variables and Data Types", "Control Flow", "Functions", "OOP in Python", "List Comprehensions", "File Handling", "Exception Handling", "Modules and Packages", "Decorators", "Generators", "Regular Expressions", "Lambda Functions", "Data Structures in Python", "NumPy and Pandas", "Django and Flask"],
    "java programming": ["OOP Concepts", "Classes and Objects", "Inheritance", "Polymorphism", "Exception Handling", "Collections Framework", "Multithreading", "File I/O", "JDBC", "Generics", "Lambda Expressions", "Streams API", "Design Patterns", "Spring Framework", "JVM Architecture"],
    "c programming": ["Variables and Data Types", "Operators", "Control Structures", "Functions", "Pointers", "Arrays", "Strings", "Structures", "Unions", "File Handling", "Memory Management", "Preprocessor Directives", "Dynamic Memory", "Linked Lists in C", "Bitwise Operations"],
    "c++ programming": ["OOP in C++", "Classes and Objects", "Inheritance", "Polymorphism", "Templates", "STL", "Smart Pointers", "Exception Handling", "Operator Overloading", "Virtual Functions", "RAII", "Move Semantics", "Lambda Expressions", "Multithreading", "Memory Management"],
    "javascript": ["Variables and Scope", "Functions and Closures", "Promises and Async/Await", "DOM Manipulation", "Event Handling", "Prototypes", "ES6+ Features", "Modules", "Error Handling", "JSON", "Fetch API", "Class Syntax", "Destructuring", "Spread Operator", "Web APIs"],
    "typescript": ["Type System", "Interfaces", "Generics", "Enums", "Type Guards", "Utility Types", "Decorators", "Modules", "Namespaces", "Declaration Files", "Strict Mode", "Mapped Types", "Conditional Types", "Intersection Types", "Union Types"],
    "rust programming": ["Ownership", "Borrowing", "Lifetimes", "Pattern Matching", "Enums", "Traits", "Generics", "Error Handling", "Concurrency", "Smart Pointers", "Closures", "Iterators", "Modules", "Cargo", "Unsafe Rust"],
    "go programming": ["Goroutines", "Channels", "Interfaces", "Structs", "Error Handling", "Packages", "Concurrency", "Pointers", "Slices", "Maps", "Defer", "Testing", "HTTP Server", "Context", "Modules"],
    "sql": ["SELECT Queries", "Joins", "Subqueries", "Aggregation", "Group By", "Indexing", "Normalization", "Views", "Stored Procedures", "Triggers", "Transactions", "Window Functions", "CTEs", "Constraints", "Performance Tuning"],
    "r programming": ["Data Types", "Vectors", "Data Frames", "Functions", "Control Structures", "ggplot2", "dplyr", "tidyr", "Statistical Tests", "Regression", "Data Import/Export", "Visualization", "R Markdown", "Shiny", "Packages"],

    # ── Web Development ──
    "web development": ["HTML", "CSS", "JavaScript", "React", "Node.js", "REST API", "Responsive Design", "HTTP Protocol", "Authentication", "Databases", "Git", "TypeScript", "CSS Frameworks", "State Management", "Deployment"],
    "frontend development": ["HTML Semantics", "CSS Flexbox and Grid", "JavaScript ES6+", "React or Vue", "State Management", "Responsive Design", "Accessibility", "Performance Optimization", "Build Tools", "Testing", "CSS Preprocessors", "Web APIs", "PWA", "TypeScript", "Browser DevTools"],
    "backend development": ["Server Architecture", "REST API Design", "Authentication", "Database Design", "ORM", "Caching", "Message Queues", "Middleware", "Error Handling", "Logging", "Rate Limiting", "File Upload", "WebSockets", "Security", "Deployment"],
    "react": ["JSX", "Components", "Props", "State", "Hooks", "useEffect", "Context API", "React Router", "Redux", "Forms", "Lifecycle Methods", "Memoization", "Refs", "Portals", "Error Boundaries"],
    "angular": ["Components", "Modules", "Services", "Dependency Injection", "Routing", "Forms", "Pipes", "Directives", "Observables", "RxJS", "HTTP Client", "Guards", "Interceptors", "NgRx", "Testing"],
    "vue.js": ["Vue Instance", "Components", "Directives", "Computed Properties", "Watchers", "Vue Router", "Vuex/Pinia", "Lifecycle Hooks", "Slots", "Transitions", "Composition API", "Provide/Inject", "Teleport", "Suspense", "Testing"],
    "node.js": ["Event Loop", "Modules", "Express.js", "Middleware", "File System", "Streams", "Buffers", "Async Patterns", "Error Handling", "REST API", "Authentication", "Database Integration", "WebSockets", "Testing", "Deployment"],
    "django": ["Models", "Views", "Templates", "URL Routing", "ORM", "Forms", "Authentication", "Admin Panel", "Middleware", "REST Framework", "Signals", "Migrations", "Static Files", "Caching", "Testing"],
    "flask": ["Routes", "Templates", "Request/Response", "Blueprints", "Database with SQLAlchemy", "Forms with WTForms", "Authentication", "RESTful API", "Error Handling", "Middleware", "Sessions", "File Upload", "Deployment", "Extensions", "Testing"],
    "next.js": ["Pages Router", "App Router", "Server Components", "API Routes", "SSR", "SSG", "ISR", "Middleware", "Data Fetching", "Image Optimization", "Routing", "Authentication", "Deployment", "SEO", "Performance"],
    "html and css": ["HTML Semantics", "Forms", "Tables", "CSS Selectors", "Box Model", "Flexbox", "CSS Grid", "Positioning", "Responsive Design", "Media Queries", "Animations", "Transitions", "Variables", "Pseudo-elements", "Accessibility"],
    "rest api": ["HTTP Methods", "Status Codes", "Endpoints Design", "Authentication", "Rate Limiting", "Pagination", "Versioning", "Error Handling", "CORS", "JSON", "HATEOAS", "OpenAPI", "Caching", "Security", "Testing"],
    "graphql": ["Queries", "Mutations", "Subscriptions", "Schema", "Resolvers", "Types", "Fragments", "Directives", "Apollo Client", "Apollo Server", "Caching", "Error Handling", "Authentication", "Pagination", "N+1 Problem"],

    # ── AI / ML / Data ──
    "machine learning": ["Supervised Learning", "Unsupervised Learning", "Regression", "Classification", "Neural Networks", "Decision Trees", "Random Forests", "SVM", "K-Means Clustering", "Gradient Descent", "Overfitting", "Cross Validation", "Feature Engineering", "Ensemble Methods", "Dimensionality Reduction"],
    "artificial intelligence": ["Search Algorithms", "Knowledge Representation", "Expert Systems", "NLP", "Computer Vision", "Machine Learning", "Deep Learning", "Reinforcement Learning", "Genetic Algorithms", "Fuzzy Logic", "Neural Networks", "Robotics", "Planning", "Probabilistic Reasoning", "Ethics in AI"],
    "deep learning": ["Neural Networks", "Backpropagation", "CNN", "RNN", "LSTM", "Transformers", "GANs", "Autoencoders", "Transfer Learning", "Attention Mechanism", "Batch Normalization", "Dropout", "Activation Functions", "Loss Functions", "Optimizers"],
    "natural language processing": ["Tokenization", "Word Embeddings", "TF-IDF", "Sentiment Analysis", "Named Entity Recognition", "POS Tagging", "Language Models", "Transformers", "BERT", "GPT", "Seq2Seq", "Attention", "Text Classification", "Machine Translation", "Question Answering"],
    "computer vision": ["Image Classification", "Object Detection", "Image Segmentation", "CNNs", "Feature Extraction", "Edge Detection", "Image Filtering", "YOLO", "ResNet", "Transfer Learning", "Data Augmentation", "GANs for Images", "Optical Flow", "Face Recognition", "Pose Estimation"],
    "reinforcement learning": ["Markov Decision Process", "Q-Learning", "Policy Gradient", "Actor-Critic", "Deep Q-Network", "SARSA", "Monte Carlo Methods", "Temporal Difference", "Reward Shaping", "Multi-Armed Bandit", "Environment Design", "OpenAI Gym", "PPO", "A3C", "Exploration vs Exploitation"],
    "data science": ["Data Cleaning", "EDA", "Feature Engineering", "Regression", "Classification", "Clustering", "Visualization", "Pandas", "NumPy", "Scikit-learn", "Statistical Analysis", "A/B Testing", "Time Series", "Big Data", "ETL Pipeline"],
    "data analytics": ["Data Collection", "Data Cleaning", "Descriptive Statistics", "Visualization", "Dashboards", "SQL for Analytics", "Excel Analytics", "Hypothesis Testing", "Regression", "Segmentation", "KPI Metrics", "Reporting", "Predictive Analytics", "Business Intelligence", "Storytelling with Data"],
    "big data": ["Hadoop", "MapReduce", "HDFS", "Spark", "Hive", "Pig", "Kafka", "Flink", "Data Lakes", "Data Warehousing", "NoSQL", "Distributed Computing", "ETL", "Stream Processing", "Data Governance"],
    "data mining": ["Association Rules", "Clustering", "Classification", "Regression", "Anomaly Detection", "Decision Trees", "KNN", "Naive Bayes", "Apriori Algorithm", "Feature Selection", "Data Preprocessing", "Dimensionality Reduction", "Text Mining", "Web Mining", "Pattern Recognition"],
    "data engineering": ["ETL Pipelines", "Data Warehousing", "Data Lakes", "Apache Spark", "Airflow", "Kafka", "SQL and NoSQL", "Data Modeling", "Schema Design", "Data Quality", "Batch Processing", "Stream Processing", "Cloud Data Services", "dbt", "Orchestration"],
    "generative ai": ["Large Language Models", "Transformers", "GPT Architecture", "Prompt Engineering", "Fine-Tuning", "RAG", "Diffusion Models", "VAE", "GANs", "Text Generation", "Image Generation", "Embeddings", "Tokenization", "RLHF", "AI Safety"],
    "large language models": ["Transformer Architecture", "Attention Mechanism", "Tokenization", "Pre-training", "Fine-tuning", "Prompt Engineering", "RAG", "InContext Learning", "Chain of Thought", "RLHF", "Hallucination", "Embeddings", "Context Window", "Model Evaluation", "Deployment"],
    "prompt engineering": ["Zero-Shot Prompting", "Few-Shot Prompting", "Chain of Thought", "Prompt Templates", "System Prompts", "Instruction Tuning", "Context Management", "Output Formatting", "Temperature and Top-P", "Prompt Chaining", "RAG", "Evaluation", "Guardrails", "Adversarial Prompts", "Best Practices"],
    "tensorflow": ["Tensors", "Keras API", "Sequential Model", "Functional API", "Layers", "Loss Functions", "Optimizers", "Training Loop", "Callbacks", "Data Pipeline", "CNN with TF", "RNN with TF", "Transfer Learning", "TensorBoard", "Model Deployment"],
    "pytorch": ["Tensors", "Autograd", "nn.Module", "DataLoader", "Loss Functions", "Optimizers", "Training Loop", "CNN", "RNN", "Transfer Learning", "GPU Training", "Custom Datasets", "Torchvision", "Model Saving", "Deployment"],

    # ── Cloud & DevOps ──
    "cloud computing": ["Virtualization", "IaaS", "PaaS", "SaaS", "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Serverless", "Load Balancing", "Auto Scaling", "Cloud Security", "Microservices", "CI/CD"],
    "aws": ["EC2", "S3", "Lambda", "RDS", "DynamoDB", "VPC", "IAM", "CloudFront", "SQS", "SNS", "ECS", "EKS", "Route 53", "CloudWatch", "API Gateway"],
    "microsoft azure": ["Virtual Machines", "App Service", "Azure Functions", "Blob Storage", "Cosmos DB", "Azure SQL", "AKS", "Azure DevOps", "Active Directory", "Logic Apps", "Service Bus", "Key Vault", "Azure Monitor", "CDN", "Networking"],
    "google cloud platform": ["Compute Engine", "Cloud Functions", "Cloud Storage", "BigQuery", "Cloud SQL", "GKE", "Pub/Sub", "Cloud Run", "IAM", "Firestore", "Dataflow", "Cloud CDN", "Monitoring", "Networking", "AI Platform"],
    "docker": ["Containers", "Images", "Dockerfile", "Docker Compose", "Volumes", "Networks", "Registry", "Multi-stage Builds", "Environment Variables", "Port Mapping", "Layers", "Best Practices", "Security", "Orchestration", "Debugging"],
    "kubernetes": ["Pods", "Deployments", "Services", "Namespaces", "ConfigMaps", "Secrets", "Ingress", "Volumes", "StatefulSets", "DaemonSets", "Helm", "RBAC", "Networking", "Monitoring", "Auto Scaling"],
    "devops": ["CI/CD", "Version Control", "Containerization", "Infrastructure as Code", "Monitoring", "Logging", "Configuration Management", "Automated Testing", "Deployment Strategies", "Cloud Services", "Scripting", "Security", "Collaboration", "Incident Management", "SRE"],
    "ci/cd": ["Continuous Integration", "Continuous Deployment", "Jenkins", "GitHub Actions", "GitLab CI", "Pipeline Design", "Automated Testing", "Build Automation", "Deployment Strategies", "Blue-Green Deployment", "Canary Release", "Rollback", "Artifacts", "Infrastructure as Code", "Monitoring"],
    "linux administration": ["File System", "User Management", "Permissions", "Shell Scripting", "Process Management", "Networking", "Package Management", "Systemd", "Cron Jobs", "Log Management", "Firewall", "SSH", "Disk Management", "Performance Tuning", "Security"],
    "microservices architecture": ["Service Decomposition", "API Gateway", "Service Discovery", "Load Balancing", "Circuit Breaker", "Event-Driven", "Message Queues", "Database per Service", "Saga Pattern", "CQRS", "Monitoring", "Logging", "Containerization", "Security", "Testing"],

    # ── Cyber Security ──
    "cyber security": ["Encryption", "Firewalls", "Penetration Testing", "Malware Analysis", "Network Security", "Cryptography", "Authentication", "Access Control", "Vulnerability Assessment", "Ethical Hacking", "SQL Injection", "XSS", "HTTPS/TLS", "Incident Response", "Security Policies"],
    "ethical hacking": ["Reconnaissance", "Scanning", "Enumeration", "Exploitation", "Post-Exploitation", "Social Engineering", "Web App Hacking", "Network Hacking", "Wireless Hacking", "Password Cracking", "Privilege Escalation", "Metasploit", "Burp Suite", "Nmap", "Report Writing"],
    "cryptography": ["Symmetric Encryption", "Asymmetric Encryption", "Hashing", "Digital Signatures", "Public Key Infrastructure", "AES", "RSA", "Diffie-Hellman", "Elliptic Curve", "Block Ciphers", "Stream Ciphers", "Key Management", "SSL/TLS", "Zero Knowledge Proofs", "Quantum Cryptography"],
    "network security": ["Firewalls", "IDS/IPS", "VPN", "SSL/TLS", "Access Control", "Network Monitoring", "Packet Analysis", "Port Security", "DMZ", "Network Segmentation", "DDoS Protection", "Wireless Security", "Proxy Servers", "Security Protocols", "Incident Response"],

    # ── Electronics & Hardware ──
    "microprocessor": ["8085 Architecture", "8086 Architecture", "Instruction Set", "Addressing Modes", "Interrupts", "Memory Interfacing", "I/O Interfacing", "Assembly Language", "Bus Structure", "Timing Diagrams", "DMA", "Programmable Peripheral Interface", "Serial Communication", "Instruction Pipelining", "RISC vs CISC"],
    "microcontroller": ["Architecture", "GPIO", "Timers", "Interrupts", "ADC/DAC", "Serial Communication", "I2C", "SPI", "PWM", "Memory Organization", "Embedded C", "ARM Cortex", "AVR", "PIC", "Programming"],
    "digital electronics": ["Logic Gates", "Boolean Algebra", "Combinational Circuits", "Sequential Circuits", "Flip-Flops", "Counters", "Registers", "Multiplexers", "Decoders", "Encoders", "ADC and DAC", "Memory Devices", "Karnaugh Maps", "Number Systems", "PLDs and FPGAs"],
    "analog electronics": ["Diodes", "BJT", "MOSFET", "Amplifiers", "Oscillators", "Op-Amp", "Filters", "Power Supplies", "Voltage Regulators", "Signal Conditioning", "Feedback", "Frequency Response", "Noise", "ADC/DAC", "Modulation"],
    "signal processing": ["Fourier Transform", "Laplace Transform", "Z-Transform", "Sampling Theorem", "Convolution", "Filtering", "DFT", "FFT", "FIR Filters", "IIR Filters", "Windowing", "Spectral Analysis", "Modulation", "Noise Reduction", "DSP Applications"],
    "vlsi design": ["CMOS Technology", "Logic Design", "Circuit Simulation", "Layout Design", "Verilog", "VHDL", "FPGA", "ASIC", "Timing Analysis", "Power Analysis", "Design Verification", "Synthesis", "Place and Route", "DFT", "SoC Design"],
    "embedded systems": ["Microcontrollers", "RTOS", "Memory Management", "Interrupts", "GPIO", "Communication Protocols", "Firmware Development", "Embedded C", "Device Drivers", "Power Management", "Debugging", "Boot Loaders", "Sensors", "Actuators", "IoT Integration"],
    "internet of things": ["IoT Architecture", "Sensors", "Actuators", "Communication Protocols", "MQTT", "CoAP", "Edge Computing", "Cloud Integration", "IoT Security", "Raspberry Pi", "Arduino", "Data Analytics", "Smart Home", "Wearables", "Industrial IoT"],
    "iot": ["IoT Architecture", "Sensors", "Actuators", "Communication Protocols", "MQTT", "CoAP", "Edge Computing", "Cloud Integration", "IoT Security", "Raspberry Pi", "Arduino", "Data Analytics", "Smart Home", "Wearables", "Industrial IoT"],
    "control systems": ["Transfer Functions", "Block Diagrams", "Signal Flow Graphs", "Stability", "Root Locus", "Bode Plot", "Nyquist Plot", "PID Controller", "State Space", "Controllability", "Observability", "Feedback Systems", "Frequency Response", "Digital Control", "System Modeling"],
    "communication systems": ["Analog Modulation", "Digital Modulation", "AM", "FM", "PSK", "QAM", "OFDM", "Multiplexing", "Channel Coding", "Error Correction", "Antenna Theory", "Satellite Communication", "Fiber Optics", "Wireless Communication", "5G"],

    # ── Mathematics ──
    "mathematics": ["Algebra", "Calculus", "Trigonometry", "Geometry", "Number Theory", "Set Theory", "Probability", "Statistics", "Linear Algebra", "Differential Equations", "Real Analysis", "Complex Numbers", "Vectors", "Matrices", "Integration"],
    "calculus": ["Limits", "Derivatives", "Integration", "Chain Rule", "Product Rule", "Partial Derivatives", "Multiple Integrals", "Differential Equations", "Taylors Series", "Maxima and Minima", "Area Under Curve", "Volume of Revolution", "Gradient", "Divergence", "Curl"],
    "linear algebra": ["Vectors", "Matrices", "Determinants", "Eigenvalues", "Eigenvectors", "Linear Transformations", "Vector Spaces", "Inner Product", "Orthogonality", "Matrix Decomposition", "Rank", "Null Space", "Systems of Equations", "Diagonalization", "Singular Value Decomposition"],
    "discrete mathematics": ["Set Theory", "Logic", "Relations", "Functions", "Graph Theory", "Combinatorics", "Probability", "Number Theory", "Boolean Algebra", "Recurrence Relations", "Proof Techniques", "Trees", "Lattices", "Groups", "Permutations"],
    "probability": ["Sample Space", "Events", "Conditional Probability", "Bayes Theorem", "Random Variables", "PDFs and CDFs", "Expected Value", "Variance", "Normal Distribution", "Binomial Distribution", "Poisson Distribution", "Joint Probability", "Independence", "Law of Large Numbers", "Central Limit Theorem"],
    "statistics": ["Mean Median Mode", "Standard Deviation", "Probability Distributions", "Hypothesis Testing", "Confidence Intervals", "Regression Analysis", "Correlation", "ANOVA", "Chi-Square Test", "Bayesian Statistics", "Sampling Methods", "Central Limit Theorem", "T-Test", "Z-Test", "Statistical Inference"],
    "differential equations": ["First Order ODE", "Second Order ODE", "Homogeneous Equations", "Non-Homogeneous Equations", "Laplace Transform", "Power Series", "Fourier Series", "Partial Differential Equations", "Boundary Value Problems", "Exact Equations", "Integrating Factors", "Variation of Parameters", "Existence and Uniqueness", "Systems of ODEs", "Numerical Methods"],
    "number theory": ["Divisibility", "Prime Numbers", "GCD and LCM", "Modular Arithmetic", "Eulers Theorem", "Fermats Little Theorem", "Chinese Remainder Theorem", "Quadratic Residues", "Diophantine Equations", "Continued Fractions", "Prime Factorization", "Congruences", "Cryptographic Applications", "Perfect Numbers", "Fibonacci Numbers"],
    "graph theory": ["Graphs and Digraphs", "Paths and Cycles", "Trees", "Spanning Trees", "Graph Coloring", "Planarity", "Eulerian Paths", "Hamiltonian Paths", "Network Flow", "Matching", "Connectivity", "Bipartite Graphs", "Graph Algorithms", "Adjacency Matrix", "Shortest Path"],
    "numerical methods": ["Root Finding", "Interpolation", "Numerical Integration", "Numerical Differentiation", "Linear Systems", "Curve Fitting", "ODE Solvers", "Eigenvalue Methods", "Error Analysis", "Gauss Elimination", "Newton-Raphson", "Simpson Rule", "Runge-Kutta", "Finite Differences", "Optimization"],
    "optimization": ["Linear Programming", "Convex Optimization", "Gradient Descent", "Simplex Method", "Lagrange Multipliers", "Duality", "Integer Programming", "Dynamic Programming", "Genetic Algorithms", "Simulated Annealing", "Constrained Optimization", "Multi-Objective", "Stochastic Optimization", "Network Optimization", "Global vs Local"],
    "operations research": ["Linear Programming", "Transportation Problem", "Assignment Problem", "Game Theory", "Queuing Theory", "Inventory Models", "Network Models", "Decision Analysis", "Simulation", "Integer Programming", "Goal Programming", "Sensitivity Analysis", "Dynamic Programming", "CPM/PERT", "Markov Chains"],
    "game theory": ["Nash Equilibrium", "Dominant Strategies", "Mixed Strategies", "Cooperative Games", "Non-Cooperative Games", "Prisoners Dilemma", "Shapley Value", "Zero-Sum Games", "Extensive Form Games", "Mechanism Design", "Auctions", "Bargaining", "Evolutionary Game Theory", "Repeated Games", "Bayesian Games"],

    # ── Physics ──
    "physics": ["Mechanics", "Thermodynamics", "Electromagnetism", "Optics", "Quantum Physics", "Wave Motion", "Gravitation", "Fluid Mechanics", "Nuclear Physics", "Relativity", "Kinematics", "Dynamics", "Rotational Motion", "Oscillations", "Electric Circuits"],
    "classical mechanics": ["Newtons Laws", "Kinematics", "Dynamics", "Work and Energy", "Momentum", "Rotational Motion", "Gravitation", "Oscillations", "Lagrangian Mechanics", "Hamiltonian Mechanics", "Central Forces", "Rigid Body Dynamics", "Elastic Collisions", "Projectile Motion", "Simple Harmonic Motion"],
    "quantum mechanics": ["Wave-Particle Duality", "Schrodinger Equation", "Quantum States", "Operators", "Heisenberg Uncertainty", "Hydrogen Atom", "Angular Momentum", "Spin", "Perturbation Theory", "Quantum Tunneling", "Entanglement", "Quantum Numbers", "Harmonic Oscillator", "Measurement", "Quantum Computing Basics"],
    "thermodynamics": ["Laws of Thermodynamics", "Heat Transfer", "Entropy", "Enthalpy", "Carnot Cycle", "Ideal Gas Laws", "Work and Heat", "Phase Transitions", "Thermal Equilibrium", "Internal Energy", "Free Energy", "Specific Heat", "Conduction", "Convection", "Radiation"],
    "electromagnetism": ["Electric Fields", "Magnetic Fields", "Maxwells Equations", "Coulombs Law", "Gauss Law", "Faradays Law", "Amperes Law", "Electromagnetic Waves", "Capacitance", "Inductance", "AC Circuits", "Electromagnetic Induction", "Lorentz Force", "Dielectrics", "Poynting Vector"],
    "optics": ["Reflection", "Refraction", "Interference", "Diffraction", "Polarization", "Lenses", "Mirrors", "Fiber Optics", "Optical Instruments", "Laser", "Wave Optics", "Geometric Optics", "Dispersion", "Huygens Principle", "Photonics"],
    "fluid mechanics": ["Fluid Statics", "Fluid Dynamics", "Bernoullis Equation", "Viscosity", "Laminar Flow", "Turbulent Flow", "Navier-Stokes Equations", "Continuity Equation", "Reynolds Number", "Pipe Flow", "Boundary Layer", "Drag and Lift", "Compressible Flow", "Open Channel Flow", "Dimensional Analysis"],

    # ── Chemistry ──
    "chemistry": ["Atomic Structure", "Chemical Bonding", "Periodic Table", "Organic Chemistry", "Inorganic Chemistry", "Physical Chemistry", "Thermochemistry", "Electrochemistry", "Chemical Kinetics", "Equilibrium", "Acids and Bases", "Redox Reactions", "Polymers", "Solutions", "Catalysis"],
    "organic chemistry": ["Hydrocarbons", "Functional Groups", "Nomenclature", "Isomerism", "Reaction Mechanisms", "Alkanes", "Alkenes", "Alkynes", "Alcohols", "Aldehydes and Ketones", "Carboxylic Acids", "Amines", "Aromatic Compounds", "Polymers", "Stereochemistry"],
    "inorganic chemistry": ["Periodic Properties", "Chemical Bonding", "Coordination Compounds", "s-Block Elements", "p-Block Elements", "d-Block Elements", "f-Block Elements", "Crystal Field Theory", "Metallurgy", "Acids Bases Salts", "Qualitative Analysis", "Bioinorganic Chemistry", "Organometallics", "Nuclear Chemistry", "Solid State"],
    "physical chemistry": ["Thermodynamics", "Chemical Kinetics", "Equilibrium", "Electrochemistry", "Quantum Chemistry", "Spectroscopy", "Surface Chemistry", "Solutions", "Phase Diagrams", "Colligative Properties", "Chemical Thermodynamics", "Photochemistry", "Nuclear Chemistry", "Molecular Structure", "Statistical Mechanics"],
    "biochemistry": ["Amino Acids", "Proteins", "Enzymes", "Carbohydrates", "Lipids", "Nucleic Acids", "Metabolism", "Glycolysis", "Krebs Cycle", "Electron Transport Chain", "DNA Replication", "Transcription", "Translation", "Vitamins", "Hormones"],

    # ── Biology ──
    "biology": ["Cell Biology", "Genetics", "Evolution", "Ecology", "Human Anatomy", "Plant Biology", "Microbiology", "Biochemistry", "Molecular Biology", "Immunology", "Zoology", "Botany", "Physiology", "Taxonomy", "Biotechnology"],
    "cell biology": ["Cell Structure", "Cell Membrane", "Organelles", "Cell Division", "Mitosis", "Meiosis", "Cell Signaling", "Cytoskeleton", "Endoplasmic Reticulum", "Golgi Apparatus", "Lysosomes", "Nucleus", "Cell Cycle", "Apoptosis", "Transport Mechanisms"],
    "genetics": ["DNA Structure", "RNA", "Genes", "Chromosomes", "Mendelian Genetics", "Gene Expression", "Mutations", "Genetic Disorders", "PCR", "Gel Electrophoresis", "Gene Therapy", "Epigenetics", "Population Genetics", "Genomics", "CRISPR"],
    "microbiology": ["Bacteria", "Viruses", "Fungi", "Protozoa", "Microbial Growth", "Sterilization", "Antibiotics", "Immune Response", "Fermentation", "Applied Microbiology", "Microbial Genetics", "Pathogenesis", "Epidemiology", "Lab Techniques", "Biofilms"],
    "biotechnology": ["Genetic Engineering", "Recombinant DNA", "PCR", "Cloning", "Gene Therapy", "Bioinformatics", "Genomics", "Proteomics", "Fermentation Technology", "Enzyme Technology", "Monoclonal Antibodies", "Biosensors", "Agricultural Biotech", "Industrial Biotech", "Bioethics"],

    # ── Engineering Core ──
    "electrical engineering": ["Circuit Analysis", "Electromagnetics", "Power Systems", "Electrical Machines", "Control Systems", "Signal Processing", "Power Electronics", "Transmission Lines", "Transformers", "Induction Motors", "Synchronous Machines", "Protection Systems", "Renewable Energy", "Instrumentation", "PLC"],
    "mechanical engineering": ["Thermodynamics", "Fluid Mechanics", "Strength of Materials", "Machine Design", "Manufacturing", "Heat Transfer", "Engineering Mechanics", "Dynamics of Machinery", "Vibrations", "CAD/CAM", "Refrigeration", "IC Engines", "Robotics", "Material Science", "Finite Element Analysis"],
    "civil engineering": ["Structural Analysis", "Concrete Technology", "Soil Mechanics", "Surveying", "Transportation Engineering", "Fluid Mechanics", "Environmental Engineering", "Steel Structures", "Foundation Engineering", "Construction Management", "Building Materials", "Earthquake Engineering", "Water Resources", "Highway Engineering", "Estimation and Costing"],
    "electronics engineering": ["Analog Electronics", "Digital Electronics", "Microprocessors", "Communication Systems", "Signal Processing", "VLSI", "Embedded Systems", "Control Systems", "Electromagnetics", "Power Electronics", "Antenna Design", "Optical Communication", "Radar Systems", "PCB Design", "Instrumentation"],
    "strength of materials": ["Stress and Strain", "Elastic Constants", "Shear Force Diagrams", "Bending Moment Diagrams", "Deflection of Beams", "Torsion", "Columns", "Thin Cylinders", "Mohr Circle", "Principal Stresses", "Strain Energy", "Springs", "Riveted Joints", "Welded Joints", "Combined Loading"],
    "engineering mechanics": ["Statics", "Dynamics", "Force Systems", "Equilibrium", "Friction", "Center of Gravity", "Moment of Inertia", "Kinematics", "Kinetics", "Work and Energy", "Impulse and Momentum", "Projectile Motion", "Circular Motion", "Virtual Work", "Trusses"],

    # ── Blockchain & Emerging Tech ──
    "blockchain": ["Distributed Ledger", "Consensus Mechanisms", "Smart Contracts", "Hashing", "Merkle Trees", "Mining", "Proof of Work", "Proof of Stake", "Ethereum", "Bitcoin", "DeFi", "NFTs", "Tokenomics", "Solidity", "dApps"],
    "quantum computing": ["Qubits", "Superposition", "Entanglement", "Quantum Gates", "Quantum Circuits", "Quantum Algorithms", "Grover's Algorithm", "Shor's Algorithm", "Decoherence", "Quantum Error Correction", "Quantum Supremacy", "Qiskit", "Quantum Teleportation", "Quantum Cryptography", "Applications"],

    # ── Business & Economics ──
    "economics": ["Supply and Demand", "Market Structures", "GDP", "Inflation", "Monetary Policy", "Fiscal Policy", "International Trade", "Microeconomics", "Macroeconomics", "Game Theory", "Elasticity", "Consumer Behavior", "Production Theory", "Cost Analysis", "Economic Growth"],
    "microeconomics": ["Supply and Demand", "Elasticity", "Consumer Theory", "Production Theory", "Cost Analysis", "Market Structures", "Perfect Competition", "Monopoly", "Oligopoly", "Game Theory", "Utility", "Indifference Curves", "Budget Constraints", "Externalities", "Public Goods"],
    "macroeconomics": ["GDP", "Inflation", "Unemployment", "Monetary Policy", "Fiscal Policy", "Aggregate Demand", "Aggregate Supply", "Business Cycles", "Economic Growth", "International Trade", "Exchange Rates", "Central Banking", "Government Debt", "Phillips Curve", "IS-LM Model"],
    "financial accounting": ["Journal Entries", "Ledger", "Trial Balance", "Balance Sheet", "Income Statement", "Cash Flow Statement", "Depreciation", "Inventory Valuation", "Bank Reconciliation", "Ratio Analysis", "Accounting Standards", "Tax Accounting", "Auditing", "Cost Accounting", "Financial Reporting"],
    "marketing": ["Marketing Mix (4Ps)", "STP", "Consumer Behavior", "Branding", "Digital Marketing", "Market Research", "Pricing Strategies", "Distribution Channels", "Advertising", "Content Marketing", "Social Media Marketing", "SEO", "Email Marketing", "CRM", "Marketing Analytics"],
    "project management": ["Project Planning", "Scope Management", "Time Management", "Cost Management", "Risk Management", "Quality Management", "Stakeholder Management", "Agile", "Scrum", "Kanban", "Gantt Charts", "WBS", "Critical Path", "Earned Value", "Project Closure"],

    # ── Social Sciences ──
    "psychology": ["Cognitive Psychology", "Behavioral Psychology", "Developmental Psychology", "Social Psychology", "Abnormal Psychology", "Neuropsychology", "Personality Theories", "Learning Theories", "Memory", "Perception", "Motivation", "Emotion", "Intelligence", "Psychotherapy", "Research Methods"],
    "sociology": ["Social Structure", "Culture", "Socialization", "Social Stratification", "Deviance", "Race and Ethnicity", "Gender", "Family", "Education", "Religion", "Social Movements", "Urbanization", "Globalization", "Research Methods", "Social Change"],
    "philosophy": ["Ethics", "Epistemology", "Metaphysics", "Logic", "Aesthetics", "Political Philosophy", "Philosophy of Mind", "Existentialism", "Utilitarianism", "Kant Ethics", "Ancient Philosophy", "Modern Philosophy", "Free Will", "Consciousness", "Philosophy of Science"],
    "history": ["Ancient Civilizations", "Medieval Period", "Renaissance", "Industrial Revolution", "World War I", "World War II", "Cold War", "Independence Movements", "Modern History", "Constitutional History", "Social History", "Economic History", "Cultural History", "Historiography", "Contemporary History"],
    "political science": ["Political Theory", "Comparative Politics", "International Relations", "Public Administration", "Indian Constitution", "Legislature", "Executive", "Judiciary", "Elections", "Political Parties", "Federalism", "Democracy", "Foreign Policy", "Political Economy", "Human Rights"],

    # ── Tools & Databases ──
    "mongodb": ["Documents", "Collections", "CRUD Operations", "Indexing", "Aggregation Pipeline", "Replication", "Sharding", "Schema Design", "Mongoose", "Transactions", "Performance Tuning", "Security", "Atlas", "Change Streams", "GridFS"],
    "postgresql": ["SQL Queries", "Joins", "Indexing", "Transactions", "Views", "Functions", "Triggers", "Partitioning", "JSON Support", "Full Text Search", "Performance Tuning", "Replication", "Backup and Recovery", "Extensions", "Security"],
    "redis": ["Data Structures", "Strings", "Hashes", "Lists", "Sets", "Sorted Sets", "Pub/Sub", "Caching Patterns", "Persistence", "Replication", "Clustering", "Transactions", "Lua Scripting", "Rate Limiting", "Session Management"],
    "power bi": ["Data Import", "Data Transformation", "DAX", "Measures", "Calculated Columns", "Visualizations", "Reports", "Dashboards", "Relationships", "Row-Level Security", "Power Query", "Filters", "Bookmarks", "Publishing", "Gateway"],
    "tableau": ["Data Connection", "Worksheets", "Dashboards", "Calculated Fields", "Filters", "Parameters", "LOD Expressions", "Maps", "Dual Axis", "Blending", "Joins", "Table Calculations", "Storytelling", "Server Publishing", "Performance"],
    "git": ["Repository", "Commits", "Branches", "Merging", "Rebasing", "Pull Requests", "Conflicts", "Stashing", "Cherry-Pick", "Tagging", "Remote Repositories", "Gitignore", "Git Flow", "Bisect", "Hooks"],

    # ── Testing & QA ──
    "software testing": ["Unit Testing", "Integration Testing", "System Testing", "Acceptance Testing", "Regression Testing", "Black Box Testing", "White Box Testing", "Test Planning", "Test Cases", "Bug Reporting", "Automation Testing", "Performance Testing", "Security Testing", "API Testing", "TDD"],
    "automation testing": ["Selenium", "Cypress", "Playwright", "TestNG", "JUnit", "Page Object Model", "Data Driven Testing", "Framework Design", "CI/CD Integration", "Cross Browser Testing", "API Automation", "Performance Testing", "Mobile Testing", "BDD", "Reporting"],

    # ── Robotics ──
    "robotics": ["Kinematics", "Dynamics", "Sensors", "Actuators", "Path Planning", "Control Systems", "Computer Vision", "SLAM", "ROS", "Manipulators", "Mobile Robots", "Inverse Kinematics", "PID Control", "Human-Robot Interaction", "Swarm Robotics"],

    # ── Competitive Programming ──
    "competitive programming": ["Arrays and Strings", "Sorting", "Searching", "Recursion", "Dynamic Programming", "Graphs", "Trees", "Greedy", "Bit Manipulation", "Number Theory", "Geometry", "Segment Trees", "Fenwick Trees", "String Algorithms", "Math Tricks"],
    "data structures and algorithms": ["Arrays", "Linked Lists", "Stacks", "Queues", "Trees", "Graphs", "Sorting", "Searching", "Dynamic Programming", "Greedy", "Hashing", "Heaps", "Tries", "Divide and Conquer", "Backtracking"],
}


class SuggestSubjectsView(APIView):
    """Subject suggestions — purely local from DB + curated list (no API calls)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = (request.query_params.get('q', '') or '').strip().lower()

        # 1. Subjects the user already studied (DB)
        db_subjects = list(
            Concept.objects.filter(created_by=request.user)
            .values_list('subject', flat=True).distinct()
        )
        all_subjects = list(
            Concept.objects.values_list('subject', flat=True).distinct()
        )

        # 2. Merge with curated list (deduplicated, case-insensitive)
        seen = set()
        combined = []
        for s in db_subjects + all_subjects + POPULAR_SUBJECTS:
            key = s.strip().lower()
            if key and key not in seen:
                seen.add(key)
                combined.append(s.strip())

        # 3. Filter by query
        if q:
            combined = [s for s in combined if q in s.lower()]

        # 4. Sort: user's own subjects first, then alphabetical
        db_lower = {s.lower() for s in db_subjects}
        combined.sort(key=lambda s: (0 if s.lower() in db_lower else 1, s.lower()))

        return Response({'suggestions': combined[:20]})


class SuggestConceptsView(APIView):
    """Dynamic concept suggestions — DB + Gemini AI, cached & query-aware."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        subject = (request.query_params.get('subject', '') or '').strip()
        q = (request.query_params.get('q', '') or '').strip().lower()

        if not subject:
            return Response({'suggestions': []})

        subject_key = subject.lower()

        # 1. DB concepts for this subject
        db_concepts = list(
            Concept.objects.filter(subject__iexact=subject)
            .values_list('name', flat=True).distinct()
        )

        # 2. Get or generate the base concept list for the subject (cached)
        base_entry = _concept_cache.get(subject_key)
        if _is_stale(base_entry, _CONCEPT_CACHE_TTL):
            base_concepts = self._generate_base_concepts(subject)
            _concept_cache[subject_key] = {'concepts': base_concepts, 'ts': _time.time()}
        else:
            base_concepts = base_entry['concepts']

        # 3. Merge DB + base AI concepts
        seen = set()
        combined = []
        for c in db_concepts + base_concepts:
            key = c.strip().lower()
            if key and key not in seen:
                seen.add(key)
                combined.append(c.strip())

        # 4. If user is typing (q ≥ 2 chars), do a targeted dynamic query
        if q and len(q) >= 2:
            # First filter locally
            local_matches = [c for c in combined if q in c.lower()]

            # If few local matches, ask Gemini for query-specific suggestions (cached)
            if len(local_matches) < 4:
                dynamic = self._query_specific_concepts(subject, q)
                for c in dynamic:
                    key = c.strip().lower()
                    if key not in seen:
                        seen.add(key)
                        local_matches.append(c.strip())

            combined = local_matches
        elif q:
            # Single char — just filter locally
            combined = [c for c in combined if q in c.lower()]

        return Response({'suggestions': combined[:15]})

    @staticmethod
    def _generate_base_concepts(subject):
        """Generate the core concept list for a subject via Gemini (one-time per subject, with fallback)."""
        prompt = (
            f'List 20 important concepts/topics a student should learn in "{subject}". '
            f'Cover fundamentals to advanced. '
            f'Return ONLY a JSON array of strings — no explanation.\n'
            f'Example: ["Concept A", "Concept B"]'
        )
        result = _parse_json_array(_gemini_generate(prompt, max_tokens=500, temperature=0.4))

        # Fallback: check FALLBACK_CONCEPTS if Gemini returned nothing
        if not result:
            key = subject.strip().lower()
            result = FALLBACK_CONCEPTS.get(key, [])
            # Also try partial matching
            if not result:
                for fb_key, fb_vals in FALLBACK_CONCEPTS.items():
                    if key in fb_key or fb_key in key:
                        result = fb_vals
                        break

        return result

    @staticmethod
    def _query_specific_concepts(subject, query):
        """Ask Gemini for concepts that match a partial query within a subject (cached, with fallback)."""
        cache_key = (subject.lower(), query.lower().strip())
        entry = _query_cache.get(cache_key)
        if not _is_stale(entry, _CACHE_TTL):
            return entry['concepts']

        prompt = (
            f'In the subject "{subject}", a student is searching for concepts matching "{query}". '
            f'Suggest 8 specific topics/concepts that match this partial input. '
            f'Return ONLY a JSON array of strings.\n'
            f'Example: ["Topic A", "Topic B"]'
        )
        concepts = _parse_json_array(_gemini_generate(prompt, max_tokens=250, temperature=0.3))

        # Fallback: filter from FALLBACK_CONCEPTS if Gemini returned nothing
        if not concepts:
            fb_key = subject.strip().lower()
            fallback_list = FALLBACK_CONCEPTS.get(fb_key, [])
            if not fallback_list:
                for fk, fv in FALLBACK_CONCEPTS.items():
                    if fb_key in fk or fk in fb_key:
                        fallback_list = fv
                        break
            q = query.lower()
            concepts = [c for c in fallback_list if q in c.lower()][:8]

        _query_cache[cache_key] = {'concepts': concepts, 'ts': _time.time()}
        return concepts


# ==================== CONCEPT MANAGEMENT ====================

class ConceptListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        concepts = Concept.objects.filter(created_by=request.user)
        serializer = ConceptSerializer(concepts, many=True)
        return Response(serializer.data)


class GenerateConceptView(APIView):
    """Step 1: Generate atoms for a concept (no questions yet)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        subject = request.data.get('subject')
        concept_name = request.data.get('concept')
        knowledge_level = request.data.get('knowledge_level', 'intermediate')
        
        if not subject or not concept_name:
            return Response({'error': 'Subject and concept are required'}, status=400)
        
        # Check if concept already exists for this user
        concept, created = Concept.objects.get_or_create(
            name=concept_name,
            subject=subject,
            created_by=request.user,
            defaults={'description': f'{concept_name} in {subject}'}
        )
        
        # If concept already has atoms, return them directly (skip AI call)
        existing_atoms = TeachingAtom.objects.filter(concept=concept).order_by('order')
        if existing_atoms.exists():
            atom_objects = [
                {'id': atom.id, 'name': atom.name, 'order': atom.order}
                for atom in existing_atoms
            ]
        else:
            # Generate atoms using AI only for new concepts
            generator = QuestionGenerator()
            atoms = generator.generate_atoms(subject, concept_name)
            
            if not atoms:
                return Response({'error': 'Failed to generate atoms'}, status=500)
            
            # Create atom records (without questions)
            atom_objects = []
            for i, atom_name in enumerate(atoms):
                atom, _ = TeachingAtom.objects.get_or_create(
                    name=atom_name,
                    concept=concept,
                    defaults={'order': i}
                )
                atom_objects.append({
                    'id': atom.id,
                    'name': atom.name,
                    'order': atom.order
                })
        
        return Response({
            'concept_id': concept.id,
            'concept_name': concept.name,
            'subject': concept.subject,
            'atoms': atom_objects,
            'knowledge_level': knowledge_level,
            'message': f'Generated {len(atoms)} atoms for {concept_name}'
        })


# ==================== TEACHING-FIRST FLOW WITH PACING ====================

class StartTeachingSessionView(APIView):
    """Step 2: Start a learning session for a concept"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        concept_id = request.data.get('concept_id')
        knowledge_level = request.data.get('knowledge_level', 'intermediate')

        if not concept_id:
            return Response({'error': 'concept_id is required'}, status=400)

        try:
            concept = Concept.objects.get(id=concept_id)
        except Concept.DoesNotExist:
            return Response({'error': 'Concept not found'}, status=404)

        # Check if there's an existing incomplete session
        existing_session = LearningSession.objects.filter(
            user=user, 
            concept=concept, 
            end_time__isnull=True
        ).first()

        if existing_session:
            # Resume existing session
            session = existing_session
        else:
            # Create new session
            session = LearningSession.objects.create(
                user=user,
                concept=concept,
                knowledge_level=knowledge_level,
                session_data={
                    'pacing_history': [],
                    'performance_history': [],
                    'answers': [],
                    'initial_quiz_questions': [],
                    'initial_quiz_answers': [],
                    'final_questions': [],
                    'final_answers': []
                }
            )

        # Get or create progress records for this concept's atoms
        # Each atom starts at 0.0 mastery and 'not_started' phase
        atoms = TeachingAtom.objects.filter(concept=concept).order_by('order')
        
        atom_states = []
        for atom in atoms:
            progress, created = StudentProgress.objects.get_or_create(
                user=user,
                atom=atom,
                defaults={
                    'mastery_score': 0.0,
                    'phase': 'not_started',
                    'error_history': []
                }
            )
            
            atom_states.append(TeachingAtomState(
                id=atom.id,
                name=atom.name,
                mastery_score=progress.mastery_score,
                phase=progress.phase,
                streak=progress.streak,
                hint_usage=progress.hint_usage,
                error_history=progress.error_history or [],
                retention_verified=progress.retention_verified
            ))

        # Use adaptive engine to find best next atom (weakest eligible)
        engine = AdaptiveLearningEngine()
        next_step = engine.get_next_learning_step(user, concept, session)
        
        current_atom = None
        if next_step.get('atom'):
            target_id = next_step['atom'].id
            for atom_state in atom_states:
                if atom_state.id == target_id:
                    current_atom = atom_state
                    break
        
        # Fallback: first incomplete atom
        if not current_atom:
            for atom_state in atom_states:
                if atom_state.phase not in ('complete',):
                    current_atom = atom_state
                    break

        if not current_atom and atom_states:
            # All atoms complete - concept is mastered
            current_atom = atom_states[-1]  # Return last atom

        # Determine initial pacing based on knowledge level
        pacing_engine = PacingEngine()
        pacing_context = PacingContext(
            accuracy=0.5,  # Default accuracy
            mastery_score=current_atom.mastery_score if current_atom else 0.0,
            streak=current_atom.streak if current_atom else 0,
            error_types=current_atom.error_history[-5:] if current_atom and current_atom.error_history else [],
            theta=0.0,  # Initial theta
            questions_answered=0,
            knowledge_level=knowledge_level,
            phase=current_atom.phase.value if current_atom and hasattr(current_atom.phase, 'value') else 'diagnostic'
        )

        pacing_result = pacing_engine.decide_pacing(pacing_context)
        initial_pacing = pacing_result.decision
        next_action = pacing_result.next_action
        reasoning = pacing_result.reasoning

        # Get user's learning profile
        try:
            profile = LearningProfile.objects.get(user=user)
        except LearningProfile.DoesNotExist:
            profile = LearningProfile.objects.create(user=user)

        return Response({
            'session_id': session.id,
            'concept_id': concept.id,
            'concept_name': concept.name,
            'subject': concept.subject,
            'atoms': [state.to_dict() for state in atom_states],
            'current_atom': current_atom.to_dict() if current_atom else None,
            'initial_pacing': initial_pacing.value if hasattr(initial_pacing, 'value') else initial_pacing,
            'next_action': next_action.value if hasattr(next_action, 'value') else next_action,
            'reasoning': reasoning,
            'fatigue': pacing_result.fatigue.value if hasattr(pacing_result.fatigue, 'value') else str(pacing_result.fatigue) if pacing_result.fatigue else 'fresh',
            'recommended_difficulty': pacing_result.recommended_difficulty,
            'overall_theta': profile.overall_theta,
            'knowledge_level': knowledge_level
        })


class GenerateInitialQuizView(APIView):
    """Step 1.5: Generate a simple diagnostic quiz (subject + concept + knowledge level)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')

        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
        except LearningSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)

        concept = session.concept
        generator = QuestionGenerator()
        questions = generator.generate_initial_quiz(
            subject=concept.subject,
            concept=concept.name,
            knowledge_level=session.knowledge_level,
            count=5
        )

        # Store full questions for grading
        session_data = session.session_data or {}
        session_data['initial_quiz_questions'] = questions
        session_data['initial_quiz_answers'] = []
        session_data['current_phase'] = 'initial_quiz'
        session.session_data = session_data
        session.save()

        # Return without correct_index
        questions_payload = []
        for q in questions:
            questions_payload.append({
                'difficulty': q['difficulty'],
                'cognitive_operation': q['cognitive_operation'],
                'estimated_time': q['estimated_time'],
                'question': q['question'],
                'options': q['options']
            })

        return Response({
            'questions': questions_payload,
            'total_questions': len(questions_payload)
        })


class SubmitInitialQuizAnswerView(APIView):
    """Submit answer for initial diagnostic quiz — with real-time mastery update per question."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from learning_engine.knowledge_tracing import calculate_updated_mastery, classify_error_type

        session_id = request.data.get('session_id')
        question_index = request.data.get('question_index')
        selected = request.data.get('selected')
        time_taken = request.data.get('time_taken', 30)

        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
        except LearningSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)

        try:
            question_index = int(question_index)
        except (TypeError, ValueError):
            return Response({'error': 'Invalid question index'}, status=400)

        questions = session.session_data.get('initial_quiz_questions', [])
        if question_index < 0 or question_index >= len(questions):
            return Response({'error': 'Invalid question index'}, status=400)

        question = questions[question_index]

        # Type-safe comparison: ensure both are ints
        try:
            selected_int = int(selected) if selected is not None else None
        except (TypeError, ValueError):
            selected_int = None
        stored_correct = question.get('correct_index')
        try:
            correct_index_int = int(stored_correct) if stored_correct is not None else None
        except (TypeError, ValueError):
            correct_index_int = None

        correct = (selected_int is not None and selected_int == correct_index_int)

        # ── Real-time mastery update per question ──
        # Retrieve running mastery & theta from session data (or defaults)
        running = session.session_data.get('quiz_running_state', {
            'mastery': 0.0,
            'theta': 0.0,
            'streak': 0,
            'error_types': []
        })
        current_mastery = float(running.get('mastery', 0.0))
        current_theta = float(running.get('theta', 0.0))

        # Get user profile theta if this is the first question
        if question_index == 0 and current_theta == 0.0:
            try:
                profile = request.user.learning_profile
                current_theta = float(profile.overall_theta)
            except LearningProfile.DoesNotExist:
                pass

        # Classify error if wrong
        error_type = None
        if not correct and selected_int is not None:
            error_type = classify_error_type(
                question, selected_int, float(time_taken),
                atom_name='initial_quiz'
            )

        # Calculate updated mastery & theta
        new_mastery, new_theta, mastery_metrics = calculate_updated_mastery(
            current_mastery=current_mastery,
            current_theta=current_theta,
            question=question,
            correct=correct,
            time_taken=float(time_taken),
            error_type=error_type,
        )

        # Update streak
        streak = int(running.get('streak', 0))
        if correct:
            streak = max(streak + 1, 1)
        else:
            streak = min(streak - 1, -1)

        # Accumulate error types
        error_types = running.get('error_types', [])
        if error_type:
            error_types.append(error_type)

        # Persist running state in session data
        session.session_data['quiz_running_state'] = {
            'mastery': round(new_mastery, 4),
            'theta': round(new_theta, 4),
            'streak': streak,
            'error_types': error_types
        }

        # Store answer
        answers = session.session_data.get('initial_quiz_answers', [])
        answers.append({
            'question_index': question_index,
            'correct': correct,
            'time_taken': time_taken,
            'selected': selected_int,
            'mastery_after': round(new_mastery, 4),
            'theta_after': round(new_theta, 4),
            'error_type': error_type
        })
        session.session_data['initial_quiz_answers'] = answers
        session.save()

        explanation = ''
        if not correct:
            correct_index = correct_index_int
            correct_option = question.get('options', [None])[correct_index] if correct_index is not None and 0 <= correct_index < len(question.get('options', [])) else None
            explanation = f"Correct answer: {correct_option}. It best matches the question focus." if correct_option else "Review the concept and try again."

        return Response({
            'correct': correct,
            'correct_index': question.get('correct_index') if not correct else None,
            'explanation': explanation,
            'updated_mastery': round(new_mastery, 4),
            'updated_theta': round(new_theta, 4),
            'error_type': error_type,
            'streak': streak,
            'mastery_change': round(mastery_metrics.get('mastery_change', 0), 4),
            'theta_change': round(mastery_metrics.get('theta_change', 0), 4),
        })


class CompleteInitialQuizView(APIView):
    """Finalize initial quiz with full adaptive flow — mastery seeding, theta update, error analysis."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')

        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
        except LearningSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)

        answers = session.session_data.get('initial_quiz_answers', [])
        questions = session.session_data.get('initial_quiz_questions', [])
        if not answers:
            return Response({'error': 'No initial quiz answers'}, status=400)

        # ── Get or create learning profile ──
        try:
            profile = request.user.learning_profile
        except LearningProfile.DoesNotExist:
            profile = LearningProfile.objects.create(user=request.user)

        # ── Run full adaptive evaluation ──
        engine = AdaptiveLearningEngine()
        evaluation = engine.evaluate_initial_quiz(
            quiz_questions=questions,
            quiz_answers=answers,
            knowledge_level=session.knowledge_level,
            current_theta=profile.overall_theta,
        )

        seeded_mastery = evaluation['mastery']
        updated_theta = evaluation['theta']
        pacing = evaluation['pacing']
        next_step = evaluation['next_step']
        adjusted_level = evaluation['adjusted_knowledge_level']

        # ── Update LearningProfile theta ──
        profile.overall_theta = updated_theta
        profile.save()

        # ────────────────────────────────────────────────────────
        # FIX: Do NOT seed diagnostic mastery to ALL atoms!
        # The diagnostic quiz assesses overall concept readiness,
        # NOT per-atom mastery. Each atom must EARN its mastery
        # through actual learning interaction.
        #
        # Instead: Only the FIRST atom gets a small head-start
        # (capped at 30%). All other atoms stay at 0.0.
        # ────────────────────────────────────────────────────────
        concept = session.concept
        atoms = TeachingAtom.objects.filter(concept=concept).order_by('order')
        for i, atom in enumerate(atoms):
            progress, _ = StudentProgress.objects.get_or_create(
                user=request.user,
                atom=atom,
                defaults={'phase': 'not_started', 'mastery_score': 0.0}
            )
            if i == 0:
                # First atom: cap initial mastery at 30% from diagnostic
                capped_mastery = min(float(seeded_mastery), 0.30)
                progress.mastery_score = capped_mastery
                progress.phase = 'teaching'
            else:
                # Other atoms: start fresh at 0.0
                if progress.phase in ('diagnostic', 'not_started'):
                    progress.mastery_score = 0.0
                    progress.phase = 'not_started'
            progress.error_history = evaluation.get('error_types', [])
            progress.save()

        # ── Update session knowledge level if adjusted ──
        if adjusted_level != session.knowledge_level:
            session.knowledge_level = adjusted_level

        # ── Store pacing + evaluation in session data ──
        session_data = session.session_data or {}
        session_data['pacing_history'] = session_data.get('pacing_history', []) + [{
            'phase': 'initial_quiz',
            'pacing': pacing,
            'accuracy': evaluation['accuracy'],
            'mastery': seeded_mastery,
            'theta': updated_theta,
            'next_step': next_step,
            'timestamp': str(timezone.now()),
        }]
        session_data['initial_quiz_evaluation'] = evaluation
        session_data['current_phase'] = 'teaching'
        session.session_data = session_data
        session.save()

        # ── Friendly recommendation ──
        friendly = {
            'speed_up': 'Great start! You can move faster.',
            'stay': 'Good start. Keep a steady pace.',
            'slow_down': 'Take it slowly and build confidence.',
            'sharp_slowdown': 'Focus on basics first; go step by step.',
        }

        return Response({
            'accuracy': evaluation['accuracy'],
            'mastery': seeded_mastery,
            'theta': updated_theta,
            'initial_pacing': pacing,
            'next_step': next_step,
            'next_step_message': evaluation['next_step_message'],
            'adjusted_knowledge_level': adjusted_level,
            'error_analysis': evaluation['error_analysis'],
            'mastery_verdict': evaluation.get('mastery_verdict', ''),
            'recommended_difficulty': evaluation.get('recommended_difficulty', 'medium'),
            'reasoning': evaluation.get('reasoning', ''),
            'recommendation': friendly.get(pacing, 'Learn at your own pace'),
        })
    
    def _get_pacing_message(self, pacing):
        messages = {
            'sharp_slowdown': 'Take it very slow - focus on fundamentals',
            'slow_down': 'Take your time with each concept',
            'stay': 'Maintain your current pace',
            'speed_up': "You're ready to move faster!"
        }
        return messages.get(pacing, 'Learn at your own pace')


class GetTeachingContentView(APIView):
    """Step 3: Get teaching content for an atom"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        session_id = request.data.get('session_id')
        atom_id = request.data.get('atom_id')
        force_new = bool(request.data.get('force_new', False))
        
        
        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
            atom = TeachingAtom.objects.get(id=atom_id)
        except (LearningSession.DoesNotExist, TeachingAtom.DoesNotExist):
            return Response({'error': 'Session or atom not found'}, status=404)
        
        # Get or create progress
        progress, _ = StudentProgress.objects.get_or_create(
            user=request.user,
            atom=atom,
            defaults={'mastery_score': 0.0, 'phase': 'not_started'}
        )
        
        # Get pacing from session data
        session_data = session.session_data
        pacing_history = session_data.get('pacing_history', [])
        current_pacing = _normalize_pacing_value(pacing_history[-1], 'stay') if pacing_history else 'stay'
        
        # ── Derive quiz mastery for teaching depth adaptation ──
        quiz_eval = session_data.get('initial_quiz_evaluation', {})
        quiz_running = session_data.get('quiz_running_state', {})
        quiz_mastery = float(
            quiz_eval.get('mastery', quiz_running.get('mastery', 0.0))
        )

        # Generate teaching content if not already cached (or force_new)
        if not atom.explanation or force_new:
            engine = AdaptiveLearningEngine()
            
            # Adjust teaching based on pacing
            level_adjustment = self._adjust_for_pacing(session.knowledge_level, current_pacing)
            
            teaching_content = engine.generate_teaching_content(
                atom_name=atom.name,
                subject=atom.concept.subject,
                concept=atom.concept.name,
                knowledge_level=level_adjustment,
                mastery_score=quiz_mastery
            )
            
            # Save to atom for future use
            atom.explanation = teaching_content.get('explanation', '')
            atom.analogy = teaching_content.get('analogy', '')
            atom.examples = [teaching_content.get('example', '')]
            atom.save()
        else:
            teaching_content = {
                'explanation': atom.explanation,
                'analogy': atom.analogy,
                'examples': atom.examples
            }
        
        # Fetch external resources (videos + images) for the atom
        from learning_engine.external_resources import ExternalResourceFetcher
        try:
            fetcher = ExternalResourceFetcher()
            resources = fetcher.get_resources_for_concept(
                subject=atom.concept.subject,
                concept=atom.concept.name,
                atom_name=atom.name
            )
        except Exception as e:
            logger.warning(f"External resource fetch failed: {e}")
            resources = {'videos': [], 'images': []}

        # Update session data
        session_data['current_atom_index'] = atom.order
        session_data['current_phase'] = 'teaching'
        session.session_data = session_data
        session.save()

        # Update atom phase to 'teaching' if not_started
        if progress.phase in ('not_started', 'diagnostic'):
            progress.phase = 'teaching'
            progress.save()
        
        return Response({
            'atom_id': atom.id,
            'atom_name': atom.name,
            'teaching_content': teaching_content,
            'videos': resources.get('videos', []),
            'images': resources.get('images', []),
            'phase': progress.phase,
            'mastery_score': float(progress.mastery_score),
            'current_pacing': current_pacing
        })
    
    def _adjust_for_pacing(self, base_level, pacing):
        """Adjust knowledge level based on pacing"""
        if pacing == 'sharp_slowdown':
            # Treat as more beginner
            if base_level == 'advanced':
                return 'intermediate'
            elif base_level == 'intermediate':
                return 'beginner'
            else:
                return 'zero'
        elif pacing == 'slow_down':
            # Slightly reduce level
            if base_level == 'advanced':
                return 'intermediate'
            elif base_level == 'intermediate':
                return 'beginner'
        elif pacing == 'speed_up':
            # Slightly increase level
            if base_level == 'beginner':
                return 'intermediate'
            elif base_level == 'intermediate':
                return 'advanced'
        
        return base_level


class GenerateQuestionsFromTeachingView(APIView):
    """Step 4: Generate questions after teaching with pacing consideration"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        session_id = request.data.get('session_id')
        atom_id = request.data.get('atom_id')
        force_new = bool(request.data.get('force_new', False))
        
        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
            atom = TeachingAtom.objects.get(id=atom_id)
        except (LearningSession.DoesNotExist, TeachingAtom.DoesNotExist):
            return Response({'error': 'Session or atom not found'}, status=404)
        
        # Get progress
        progress, _ = StudentProgress.objects.get_or_create(
            user=request.user,
            atom=atom
        )
        
        # Update phase
        progress.phase = 'diagnostic'
        progress.save()
        
        # Get current pacing
        session_data = session.session_data
        pacing_history = session_data.get('pacing_history', [])
        current_pacing = _normalize_pacing_value(pacing_history[-1], 'stay') if pacing_history else 'stay'
        
        # Always generate questions FROM teaching content for this flow
        generator = QuestionGenerator()

        # Determine question distribution based on knowledge level and pacing
        level_config = self._get_question_distribution(session.knowledge_level, current_pacing)

        # Ensure we have teaching content to ground the questions
        teaching_content = {
            'explanation': atom.explanation or '',
            'analogy': atom.analogy or '',
            'examples': atom.examples or []
        }

        if not teaching_content['explanation']:
            engine = AdaptiveLearningEngine()
            # Get quiz mastery for depth adaptation
            session_data = session.session_data or {}
            quiz_eval = session_data.get('initial_quiz_evaluation', {})
            quiz_running = session_data.get('quiz_running_state', {})
            quiz_mastery = float(quiz_eval.get('mastery', quiz_running.get('mastery', 0.0)))
            generated_teaching = engine.generate_teaching_content(
                atom_name=atom.name,
                subject=atom.concept.subject,
                concept=atom.concept.name,
                knowledge_level=session.knowledge_level,
                mastery_score=quiz_mastery
            )
            teaching_content = {
                'explanation': generated_teaching.get('explanation', ''),
                'analogy': generated_teaching.get('analogy', ''),
                'examples': [
                    generated_teaching.get('example', ''),
                    generated_teaching.get('practical_application', ''),
                    generated_teaching.get('misconception', '')
                ]
            }

        generated = generator.generate_questions_from_teaching(
            subject=atom.concept.subject,
            concept=atom.concept.name,
            atom=atom.name,
            teaching_content=teaching_content,
            need_easy=int(level_config.get('easy', 0) or 0),
            need_medium=int(level_config.get('medium', 0) or 0),
            need_hard=int(level_config.get('hard', 0) or 0),
            knowledge_level=session.knowledge_level
        )

        # Prepare response + session grading payload
        questions_data = []
        full_questions = []
        saved_db_ids = []
        for q_data in generated:
            adj_time = self._adjust_time_for_pacing(
                q_data['estimated_time'],
                current_pacing
            )
            questions_data.append({
                'difficulty': q_data['difficulty'],
                'cognitive_operation': q_data['cognitive_operation'],
                'estimated_time': adj_time,
                'question': q_data['question'],
                'options': q_data['options']
            })

            full_questions.append({
                'difficulty': q_data['difficulty'],
                'cognitive_operation': q_data['cognitive_operation'],
                'estimated_time': adj_time,
                'question': q_data['question'],
                'options': q_data['options'],
                'correct_index': q_data['correct_index']
            })

            # Persist to Question model so teachers can review
            try:
                db_q = Question.objects.create(
                    atom=atom,
                    difficulty=q_data['difficulty'],
                    cognitive_operation=q_data.get('cognitive_operation', 'apply'),
                    estimated_time=adj_time,
                    question_text=q_data['question'],
                    options=q_data['options'],
                    correct_index=q_data['correct_index'],
                )
                saved_db_ids.append(db_q.id)
            except Exception as save_err:
                print(f"Warning: failed to persist question to DB: {save_err}")
        
        # Update session
        session_data['current_phase'] = 'questions'
        session_data['questions'] = full_questions
        session.session_data = session_data
        session.save()
        
        return Response({
            'atom_id': atom.id,
            'atom_name': atom.name,
            'questions': questions_data,
            'total_questions': len(questions_data),
            'current_pacing': current_pacing
        })
    
    def _get_question_distribution(self, knowledge_level, pacing):
        """Get question distribution based on level and pacing"""
        base_configs = {
            'zero': {'easy': 4, 'medium': 0, 'hard': 0},
            'beginner': {'easy': 3, 'medium': 1, 'hard': 0},
            'intermediate': {'easy': 2, 'medium': 2, 'hard': 0},
            'advanced': {'easy': 1, 'medium': 2, 'hard': 1}
        }
        
        config = base_configs.get(knowledge_level, base_configs['intermediate']).copy()
        
        # Adjust based on pacing
        if pacing == 'sharp_slowdown':
            # More easy questions
            config['easy'] += 1
            if config['medium'] > 0:
                config['medium'] -= 1
        elif pacing == 'slow_down':
            # Shift towards easier
            if config['medium'] > 0 and config['easy'] < 4:
                config['medium'] -= 1
                config['easy'] += 1
        elif pacing == 'speed_up':
            # Add a challenge
            if config['hard'] < 2 and config['easy'] > 0:
                config['easy'] -= 1
                config['hard'] += 1
        
        return config
    
    def _adjust_time_for_pacing(self, base_time, pacing):
        """
        Adjust estimated time based on pacing decision
        """
        # Extract pacing value if it's a dictionary
        if isinstance(pacing, dict):
            pacing_value = pacing.get('pacing', 'stay')
        elif isinstance(pacing, str):
            pacing_value = pacing
        else:
            pacing_value = 'stay'
        
        multipliers = {
            'sharp_slowdown': 2.0,
            'slow_down': 1.5,
            'stay': 1.0,
            'speed_up': 0.7,
            'advance': 0.5,
            'reinforce': 1.8,
        }
        
        return int(base_time * multipliers.get(pacing_value, 1.0))


class SubmitAtomAnswerView(APIView):
    """Step 5: Submit answer and update mastery with pacing"""
    permission_classes = [IsAuthenticated]
    
    def _get_bkt_params_for_pacing(self, pacing):
        """Adjust BKT parameters based on pacing"""
        # Extract pacing value if it's a dictionary
        if isinstance(pacing, dict):
            pacing_value = pacing.get('pacing', 'stay')
        elif isinstance(pacing, str):
            pacing_value = pacing
        else:
            pacing_value = 'stay'
        
        params = {
            'sharp_slowdown': {'slip': 0.15, 'guess': 0.25, 'learn': 0.10},  # More cautious
            'slow_down': {'slip': 0.12, 'guess': 0.22, 'learn': 0.12},       # Slightly cautious
            'stay': {'slip': 0.10, 'guess': 0.20, 'learn': 0.15},             # Default
            'speed_up': {'slip': 0.08, 'guess': 0.18, 'learn': 0.18}          # Faster learning
        }
        return params.get(pacing_value, params['stay'])
    
    def post(self, request):
        try:
            data = request.data
            session_id = data.get('session_id')
            atom_id = data.get('atom_id')
            question_index = data.get('question_index')
            raw_selected = data.get('selected')
            time_taken = data.get('time_taken', 30)
            question_set = data.get('question_set', 'teaching')

            # Type-safe: ensure selected is an int
            try:
                selected = int(raw_selected) if raw_selected is not None else None
            except (TypeError, ValueError):
                return Response({'error': 'Invalid selected option'}, status=400)
            
            # Get session and progress
            from accounts.models import LearningSession, StudentProgress, TeachingAtom
            
            session = LearningSession.objects.get(id=session_id, user=request.user)
            atom = TeachingAtom.objects.get(id=atom_id)
            progress, _ = StudentProgress.objects.get_or_create(
                user=request.user,
                atom=atom,
                defaults={'mastery_score': 0.0, 'phase': 'not_started'}
            )
            
            # Get question from session data
            if question_set == 'final':
                questions = session.session_data.get('final_questions', [])
            else:
                questions = session.session_data.get('questions', [])
            try:
                question_index = int(question_index)
            except (TypeError, ValueError):
                return Response({'error': 'Invalid question index'}, status=400)

            if question_index < 0 or question_index >= len(questions):
                return Response({'error': 'Invalid question index'}, status=400)
            
            question = questions[question_index]
            
            # Create atom state
            atom_state = TeachingAtomState(
                id=atom.id,
                name=atom.name,
                mastery_score=float(progress.mastery_score),
                phase=progress.phase,
                streak=progress.streak,
                hint_usage=progress.hint_usage,
                error_history=progress.error_history or []
            )
            
            # Get theta from learning profile
            try:
                profile = request.user.learning_profile
            except LearningProfile.DoesNotExist:
                profile = LearningProfile.objects.create(user=request.user)

            theta = float(profile.overall_theta)
            
            # Get questions history
            history = session.session_data.get('answers', [])
            
            # Process with enhanced engine
            engine = AdaptiveLearningEngine()
            result = engine.process_answer(
                atom_state=atom_state,
                theta=theta,
                question=question,
                selected_answer=selected,
                time_taken=time_taken,
                knowledge_level=session.knowledge_level,
                questions_history=history
            )
            
            # Save updated values
            mastery_before = float(progress.mastery_score)
            new_mastery = result['updated_mastery']
            was_already_complete = (progress.phase == 'complete')

            # ── Update streak + error_history BEFORE state machine ──
            # (update_atom_state checks streak for completion decisions)
            progress.streak = result['streak']
            progress.error_history = atom_state.error_history

            # ── Use adaptive state machine for phase transitions ──
            AdaptiveLearningEngine.update_atom_state(
                progress, new_mastery, result['correct']
            )
            # update_atom_state already calls progress.save()

            # ── Detect fragile knowledge only on atoms that were ALREADY
            #    complete before this answer (not ones that just became complete) ──
            if was_already_complete:
                AdaptiveLearningEngine.detect_fragile_knowledge(
                    progress, result['correct'], time_taken,
                    estimated_time=float(question.get('estimated_time', 60))
                )
            
            # Update learning profile theta
            profile.overall_theta = result['updated_theta']
            profile.save()
            
            # Update session data
            if 'answers' not in session.session_data:
                session.session_data['answers'] = []
            
            session.session_data['answers'].append({
                'question_index': question_index,
                'correct': result['correct'],
                'error_type': result['error_type'],
                'time_taken': time_taken,
                'mastery_after': result['updated_mastery'],
                'pacing_decision': result['pacing_decision']
            })

            # Track final challenge answers separately
            if question_set == 'final':
                if 'final_answers' not in session.session_data:
                    session.session_data['final_answers'] = []
                session.session_data['final_answers'].append({
                    'question_index': question_index,
                    'correct': result['correct'],
                    'time_taken': time_taken,
                    'selected': selected,
                    'correct_index': question.get('correct_index')
                })

            # Keep a richer performance history for CompleteAtomView
            if 'performance_history' not in session.session_data:
                session.session_data['performance_history'] = []

            session.session_data['performance_history'].append({
                'atom_id': atom.id,
                'question_index': question_index,
                'correct': result['correct'],
                'time_taken': time_taken,
                'mastery_before': mastery_before,
                'mastery_after': result['updated_mastery'],
                'error_type': result['error_type']
            })
            
            session.questions_answered += 1
            if result['correct']:
                session.correct_answers += 1
                # Award XP for correct answer based on difficulty
                difficulty = question.get('difficulty', 'medium')
                xp_map = {'easy': 1, 'medium': 2, 'hard': 3}
                xp_amount = xp_map.get(difficulty, 2)
                xp_profile, _ = UserXP.objects.get_or_create(user=request.user)
                xp_profile.award_xp(xp_amount, category='questions')
            
            session.save()

            # ── Live cognitive load and session-shape ──
            from learning_engine.cognitive_load import compute_cognitive_load, get_session_shape_message
            elapsed_minutes = (timezone.now() - session.start_time).total_seconds() / 60.0
            answers = session.session_data.get('answers', [])
            last_5 = answers[-5:] if len(answers) >= 5 else answers
            recent_accuracy = (sum(1 for a in last_5 if a.get('correct')) / len(last_5)) if last_5 else (1.0 if result['correct'] else 0.0)
            hint_usage_ratio = (session.hints_used or 0) / max(1, session.questions_answered)
            expected_time = float(question.get('estimated_time', 60))
            fatigue_val = result.get('fatigue')
            fatigue_level_str = fatigue_val.get('level', 'fresh') if isinstance(fatigue_val, dict) else (fatigue_val or 'fresh')
            load_score, session_shape_action = compute_cognitive_load(
                elapsed_minutes,
                session.questions_answered,
                time_taken,
                expected_time,
                recent_accuracy,
                hint_usage_ratio,
                fatigue_level_str,
            )
            if 'cognitive_load_history' not in session.session_data:
                session.session_data['cognitive_load_history'] = []
            session.session_data['cognitive_load_history'].append({
                'timestamp': timezone.now().isoformat(),
                'score': load_score,
                'action': session_shape_action,
            })
            session_shape_message = get_session_shape_message(session_shape_action)
            session.save()
            
            # Determine next steps based on pacing
            explanation = ''
            if not result['correct']:
                teaching_for_feedback = {
                    'explanation': atom.explanation or '',
                    'misconception': '',
                }
                if atom.examples and len(atom.examples) > 2:
                    teaching_for_feedback['misconception'] = atom.examples[2]

                explanation = _friendly_wrong_explanation(
                    question,
                    teaching_content=teaching_for_feedback,
                    error_type=result.get('error_type')
                )

            response_data = {
                'correct': result['correct'],
                'error_type': result['error_type'],
                'updated_mastery': result['updated_mastery'],
                'updated_theta': result['updated_theta'],
                'pacing_decision': result['pacing_decision'],
                'next_action': result['next_action'],
                'next_difficulty': result['next_difficulty'],
                'message': result.get('message', ''),
                'atom_complete': result['atom_complete'],
                'metrics': result['metrics'],
                'correct_index': question.get('correct_index') if not result['correct'] else None,
                'explanation': explanation,
                # ── Enhanced pacing engine data ──
                'fatigue': result.get('fatigue', 'fresh'),
                'retention_action': result.get('retention_action'),
                'hint_warning': result.get('hint_warning'),
                'velocity_snapshot': result.get('velocity_snapshot'),
                'engagement_adjustment': result.get('engagement_adjustment'),
                'mastery_verdict': result.get('mastery_verdict'),
                # ── Cognitive load and session-shape ──
                'cognitive_load_score': load_score,
                'cognitive_load_action': session_shape_action,
                'session_shape_message': session_shape_message,
            }
            
            # Persist enriched data to session-level fatigue/velocity
            session.fatigue_level = result.get('fatigue', 'fresh')
            if result.get('velocity_snapshot'):
                vel_data = session.velocity_data or []
                vel_data.append(result['velocity_snapshot'])
                session.velocity_data = vel_data
            if result.get('engagement_adjustment'):
                session.engagement_score = result['engagement_adjustment'].get('score', session.engagement_score)
            
            # If atom complete, use ADAPTIVE ENGINE to find next best atom
            # atom_complete comes from pacing engine's should_exit_atom.
            # Only mark 'complete' if mastery genuinely meets the threshold;
            # otherwise the student just hit max-questions and must move on
            # without an artificial mastery boost.
            if result['atom_complete'] and progress.phase != 'complete':
                if float(progress.mastery_score) >= MASTERY_THRESHOLD:
                    progress.phase = 'complete'
                else:
                    # Max-questions reached but mastery is low — don't fake it
                    progress.phase = 'practice'
                progress.save()

            if result['atom_complete'] or progress.phase == 'complete':
                
                # Use adaptive engine to select next atom (weakest eligible)
                next_step = engine.get_next_learning_step(
                    request.user, atom.concept, session
                )
                
                if next_step.get('all_mastered'):
                    # All atoms complete — signal concept final challenge
                    response_data['concept_complete'] = True
                    response_data['concept_final_challenge_ready'] = True
                elif next_step.get('atom'):
                    next_atom_obj = next_step['atom']
                    # Get the actual next atom's progress for mastery info
                    try:
                        next_prog = StudentProgress.objects.get(
                            user=request.user,
                            atom=next_atom_obj
                        )
                        next_mastery = float(next_prog.mastery_score)
                    except StudentProgress.DoesNotExist:
                        next_mastery = 0.0
                    
                    response_data['next_atom'] = {
                        'id': next_atom_obj.id,
                        'name': next_atom_obj.name,
                        'mastery_score': next_mastery,
                        'phase': next_step.get('phase', 'not_started'),
                    }
                    response_data['next_action'] = 'next_atom'
                    response_data['adaptive_action'] = next_step.get('action', 'TEACH')
                else:
                    response_data['concept_complete'] = True
                    response_data['concept_final_challenge_ready'] = True
            
            # Sync response mastery with actual DB value
            # (may differ due to fragile decay or completion boost)
            response_data['updated_mastery'] = float(progress.mastery_score)

            return Response(response_data)
            
        except Exception as e:
            print(f"Error submitting answer: {e}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)   

class CompleteAtomView(APIView):
    """Step 6: Complete atom - CALCULATE EVERYTHING and DECIDE next action"""
    permission_classes = [IsAuthenticated]
    
    def _get_bkt_params_for_pacing(self, pacing):
        """Adjust BKT parameters based on pacing"""
        # Extract pacing value if it's a dictionary
        if isinstance(pacing, dict):
            pacing_value = pacing.get('pacing', 'stay')
        elif isinstance(pacing, str):
            pacing_value = pacing
        else:
            pacing_value = 'stay'
        
        params = {
            'sharp_slowdown': {'slip': 0.15, 'guess': 0.25, 'learn': 0.10},
            'slow_down': {'slip': 0.12, 'guess': 0.22, 'learn': 0.12},
            'stay': {'slip': 0.10, 'guess': 0.20, 'learn': 0.15},
            'speed_up': {'slip': 0.08, 'guess': 0.18, 'learn': 0.18}
        }
        return params.get(pacing_value, params['stay'])

    def _get_pacing_explanation(self, pacing, results):
        """Get detailed explanation for pacing decision"""
        accuracy = results.get('accuracy', 0)
        mastery = results.get('mastery', 0)
        
        if pacing == 'sharp_slowdown':
            return f"Critical: {accuracy:.0%} accuracy and {mastery:.0%} mastery indicate fundamental gaps"
        elif pacing == 'slow_down':
            return f"Caution: {accuracy:.0%} accuracy suggests need for more careful learning"
        elif pacing == 'stay':
            return f"Balanced: {accuracy:.0%} accuracy shows good progress at current pace"
        elif pacing == 'speed_up':
            return f"Excellent: {accuracy:.0%} accuracy shows readiness for faster pace"
        return "Continue at current pace"
    
    def _get_pacing_recommendation(self, pacing, accuracy, mastery):
        """Get human-readable recommendation"""
        recommendations = {
            'sharp_slowdown': f'⚠️ URGENT: Review required. Score: {accuracy:.0%}, Mastery: {mastery:.0%}',
            'slow_down': f'⏸️ Slow down and practice more. Score: {accuracy:.0%}',
            'stay': f'👉 Keep going at this pace. Score: {accuracy:.0%}',
            'speed_up': f'🚀 Accelerate! You\'re ready. Score: {accuracy:.0%}'
        }
        return recommendations.get(pacing, 'Continue learning')
    
    def _get_pacing_icon(self, pacing):
        icons = {
            'sharp_slowdown': '⚠️',
            'slow_down': '⏸️',
            'stay': '👉',
            'speed_up': '🚀'
        }
        return icons.get(pacing, '•')
    
    def _get_pacing_color(self, pacing):
        colors = {
            'sharp_slowdown': 'red',
            'slow_down': 'orange',
            'stay': 'blue',
            'speed_up': 'green'
        }
        return colors.get(pacing, 'gray')
    
    def post(self, request):
        session_id = request.data.get('session_id')
        atom_id = request.data.get('atom_id')
        
        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
            atom = TeachingAtom.objects.get(id=atom_id)
            progress = StudentProgress.objects.get(user=request.user, atom=atom)
        except (LearningSession.DoesNotExist, TeachingAtom.DoesNotExist, StudentProgress.DoesNotExist):
            return Response({'error': 'Session, atom, or progress not found'}, status=404)
        
        # ========== STEP 1: COLLECT ALL PERFORMANCE DATA ==========

        session_data = session.session_data or {}
        
        # Get current generated questions from session (source of truth for this flow)
        questions = session_data.get('questions', [])
        
        # Get performance history for this atom from session
        performance = session_data.get('performance_history', [])
        atom_performance = [p for p in performance if p.get('atom_id') == atom.id]
        
        # Calculate detailed metrics
        answered_questions = len(atom_performance)
        
        if answered_questions == 0:
            return Response({'error': 'No questions answered for this atom'}, status=400)
        
        # Basic metrics
        correct_count = sum(1 for p in atom_performance if p['correct'])
        accuracy = correct_count / answered_questions
        
        # Time metrics
        time_taken_list = [p.get('time_taken', 30) for p in atom_performance]
        avg_time_per_question = sum(time_taken_list) / len(time_taken_list)
        
        estimated_times = [q.get('estimated_time', 60) for q in questions]
        total_estimated_time = sum(estimated_times)
        total_time_taken = sum(time_taken_list)
        time_ratio = total_time_taken / total_estimated_time if total_estimated_time > 0 else 1.0
        
        # ========== STEP 2: CALCULATE BKT PARAMETERS ==========
        
        # Current mastery from BKT (already updated per question)
        current_mastery = progress.mastery_score
        
        # Calculate learning rate (how fast they improved)
        if len(atom_performance) >= 2:
            first_mastery = atom_performance[0].get('mastery_before', 0.0)
            last_mastery = atom_performance[-1].get('mastery_after', current_mastery)
            learning_rate = (last_mastery - first_mastery) / len(atom_performance)
        else:
            learning_rate = 0.15  # Default
        
        # Calculate slip probability (wrong when they know)
        # Look for patterns: correct then wrong on similar difficulty
        slip_events = 0
        for i, p in enumerate(atom_performance):
            if not p['correct'] and i > 0 and atom_performance[i-1]['correct']:
                # Wrong after being correct - possible slip
                slip_events += 1
        slip_prob = slip_events / max(answered_questions, 1)
        
        # Calculate guess probability (correct when they don't know)
        # Look for fast correct answers when mastery was low
        guess_events = 0
        for i, p in enumerate(atom_performance):
            if p['correct'] and p.get('mastery_before', 0.0) < 0.4 and p.get('time_taken', 30) < 10:
                # Fast correct when mastery low - possible guess
                guess_events += 1
        guess_prob = guess_events / max(answered_questions, 1)
        
        # ========== STEP 3: USE ALREADY-UPDATED THETA ==========
        
        # Theta was already incrementally updated per-question in
        # SubmitAtomAnswerView via process_answer(). Don't recalculate
        # here — just read the current value from the profile.
        current_theta = request.user.learning_profile.overall_theta
        final_theta = current_theta
        theta_change = 0.0  # Already accounted for per-question
        
        # ========== STEP 4: ANALYZE ERROR PATTERNS ==========
        
        # Classify error types
        error_types = progress.error_history[-10:]  # Last 10 errors
        
        conceptual_errors = sum(1 for e in error_types if e == 'conceptual')
        procedural_errors = sum(1 for e in error_types if e == 'procedural')
        factual_errors = sum(1 for e in error_types if e == 'factual')
        guessing_errors = sum(1 for e in error_types if e == 'guessing')
        
        # Calculate error severity
        error_severity = 'low'
        if conceptual_errors >= 2:
            error_severity = 'high'
        elif conceptual_errors >= 1 or procedural_errors >= 2:
            error_severity = 'medium'
        
        # ========== STEP 5: CALCULATE MASTERY CONFIDENCE ==========
        
        # Mastery confidence based on consistency
        if len(atom_performance) >= 3:
            recent_performance = atom_performance[-3:]
            recent_correct = sum(1 for p in recent_performance if p['correct'])
            consistency = recent_correct / 3
            
            if consistency >= 0.67 and current_mastery >= 0.7:
                mastery_confidence = 'high'
            elif consistency >= 0.5 or current_mastery >= 0.6:
                mastery_confidence = 'medium'
            else:
                mastery_confidence = 'low'
        else:
            mastery_confidence = 'low' if current_mastery < 0.6 else 'medium'
        
        # ========== STEP 6: DETERMINE PACING DECISION ==========
        
        # Prepare diagnostic results for pacing engine
        diagnostic_results = {
            'accuracy': accuracy,
            'mastery': current_mastery,
            'streak': progress.streak,
            'error_types': error_types[-3:],
            'time_ratio': time_ratio,
            'learning_rate': learning_rate,
            'theta_change': theta_change,
            'consistency': consistency if len(atom_performance) >= 3 else 0.5
        }
        
        engine = AdaptiveLearningEngine()
        pacing_full = engine.determine_pacing_full(
            diagnostic_results=diagnostic_results,
            knowledge_level=session.knowledge_level,
            session=session
        )
        pacing = pacing_full.get('pacing', 'stay')
        
        # Extract enriched pacing features
        fatigue_info = pacing_full.get('fatigue', 'fresh')
        retention_action = pacing_full.get('retention_action')
        velocity_snapshot = pacing_full.get('velocity_snapshot')
        mastery_verdict = pacing_full.get('mastery_verdict')
        engagement_adjustment = pacing_full.get('engagement_adjustment')
        
        # ========== STEP 7: MAKE AUTOMATIC DECISION ==========

        # Theta already updated per-question in SubmitAtomAnswerView — no overwrite needed.
        
        # Update session data
        completed = session_data.get('completed_atoms', [])
        if atom.id not in completed:
            completed.append(atom.id)
        session_data['completed_atoms'] = completed
        
        # Store all calculated metrics
        session_data['last_atom_metrics'] = {
            'atom_id': atom.id,
            'accuracy': accuracy,
            'final_mastery': current_mastery,
            'theta_before': current_theta,
            'theta_after': final_theta,
            'theta_change': theta_change,
            'avg_time': avg_time_per_question,
            'time_ratio': time_ratio,
            'learning_rate': learning_rate,
            'slip_prob': slip_prob,
            'guess_prob': guess_prob,
            'error_types': error_types[-5:],
            'mastery_confidence': mastery_confidence
        }
        
        # ---- Use adaptive engine to pick the BEST next atom ----
        engine = AdaptiveLearningEngine()
        next_step = engine.get_next_learning_step(request.user, atom.concept, session)
        next_atom = next_step.get('atom')          # TeachingAtom model instance or None
        adaptive_action = next_step.get('action')  # TEACH / PRACTICE / ADVANCE / SUBJECT_COMPLETE
        
        all_atoms = TeachingAtom.objects.filter(concept=atom.concept).count()
        all_completed = (adaptive_action == 'SUBJECT_COMPLETE') or next_step.get('all_mastered') or len(completed) >= all_atoms
        
        # ========== STEP 8: DETERMINE NEXT ACTION (AUTOMATIC) ==========
        
        next_action = 'unknown'
        action_reason = ''
        
        if all_completed:
            next_action = 'concept_complete'
            action_reason = 'All atoms in this concept have been mastered.'
        elif adaptive_action in ('TEACH', 'teach'):
            next_action = 'auto_advance'
            action_reason = f'Moving to {next_atom.name} — teaching phase.'
        elif adaptive_action in ('PRACTICE', 'practice'):
            next_action = 'auto_advance'
            action_reason = f'Moving to {next_atom.name} — practice phase.'
        elif adaptive_action in ('ADVANCE', 'advance'):
            next_action = 'auto_advance'
            action_reason = f'{next_atom.name} is ready — advancing.'
        else:
            # Fallback: use pacing heuristics
            if current_mastery < 0.5 or accuracy < 0.4 or conceptual_errors >= 2:
                next_action = 'review_current'
                action_reason = 'Mastery too low — review required before proceeding'
            elif current_mastery >= 0.7 and accuracy >= 0.75:
                next_action = 'final_challenge'
                action_reason = 'Great progress! Complete the final challenge to finish this atom.'
            else:
                next_action = 'user_choice'
                action_reason = 'Ready to continue?'
        
        # Store pacing decision
        pacing_history = session_data.get('pacing_history', [])
        pacing_history.append({
            'atom_id': atom.id,
            'pacing': pacing,
            'accuracy': accuracy,
            'mastery': current_mastery,
            'theta': final_theta,
            'next_action': next_action,
            'timestamp': str(timezone.now())
        })
        session_data['pacing_history'] = pacing_history
        session_data['last_pacing'] = pacing
        session.session_data = session_data
        session.save()
        
        # ========== STEP 9: BUILD COMPREHENSIVE RESPONSE ==========
        
        # Update progress phase — respect adaptive engine decisions.
        # Do NOT overwrite 'complete' if the atom was already mastered.
        if progress.phase == 'complete':
            pass  # Already mastered — don't regress
        elif next_action in ['review_current', 'recommend_review', 'recommend_practice']:
            progress.phase = 'reinforcement'
            progress.save()
        elif next_action == 'concept_complete':
            progress.phase = 'complete'
            progress.save()
        else:
            progress.phase = 'practice'
            progress.save()

        response_data = {
            # Atom completion status
            'atom_completed': True,
            'atom_id': atom.id,
            'atom_name': atom.name,
            
            # ===== ALL CALCULATED METRICS =====
            'metrics': {
                # Basic performance
                'accuracy': accuracy,
                'correct_count': correct_count,
                'total_questions': answered_questions,
                
                # BKT parameters
                'final_mastery': current_mastery,
                'mastery_improvement': current_mastery - session_data.get('initial_mastery', 0.0),
                'learning_rate': learning_rate,
                'slip_probability': slip_prob,
                'guess_probability': guess_prob,
                
                # IRT theta
                'theta_before': current_theta,
                'theta_after': final_theta,
                'theta_change': theta_change,
                
                # Time analysis
                'avg_time_per_question': avg_time_per_question,
                'total_time_taken': total_time_taken,
                'total_estimated_time': total_estimated_time,
                'time_ratio': time_ratio,
                'time_efficiency': 'fast' if time_ratio < 0.8 else 'normal' if time_ratio < 1.2 else 'slow',
                
                # Error analysis
                'error_count': len(error_types),
                'conceptual_errors': conceptual_errors,
                'procedural_errors': procedural_errors,
                'factual_errors': factual_errors,
                'guessing_errors': guessing_errors,
                'error_severity': error_severity,
                
                # Confidence
                'mastery_confidence': mastery_confidence,
                'consistency': consistency if len(atom_performance) >= 3 else None,
            },
            
            # ===== PACING DECISION =====
            'pacing': {
                'decision': pacing,
                'explanation': self._get_pacing_explanation(pacing, diagnostic_results),
                'recommendation': self._get_pacing_recommendation(pacing, accuracy, current_mastery),
                'icon': self._get_pacing_icon(pacing),
                'color': self._get_pacing_color(pacing)
            },
            
            # ===== ENHANCED PACING FEATURES =====
            'fatigue': fatigue_info,
            'retention_action': retention_action,
            'velocity_snapshot': velocity_snapshot,
            'mastery_verdict': mastery_verdict,
            'engagement_adjustment': engagement_adjustment,
            
            # ===== NEXT ACTION (AUTOMATIC) =====
            'next_action': {
                'action': next_action,
                'reason': action_reason,
                'auto_proceed': next_action in ['auto_advance', 'review_current', 'concept_complete'],
                'user_choice_required': next_action in ['user_choice', 'optional_continue', 'recommend_practice', 'recommend_review', 'recommend_advance']
            },
            
            # Next atom if applicable
            'next_atom': None,
            'all_completed': all_completed
        }
        
        # Add next atom info if exists
        if next_atom and not all_completed:
            next_progress, _ = StudentProgress.objects.get_or_create(
                user=request.user, atom=next_atom,
                defaults={'mastery_score': 0.0, 'phase': 'not_started'}
            )
            response_data['next_atom'] = {
                'id': next_atom.id,
                'name': next_atom.name,
                'phase': next_progress.phase,
                'order': next_atom.order,
                'current_mastery': next_progress.mastery_score,
                'mastery_score': next_progress.mastery_score,
                'adaptive_action': adaptive_action,
            }
        
        # Award XP for atom completion
        xp_profile, _ = UserXP.objects.get_or_create(user=request.user)
        atom_xp = 10 if current_mastery >= 0.8 else 5
        xp_profile.award_xp(atom_xp, category='atoms')
        response_data['xp_earned_atom'] = atom_xp

        # Add completion message
        if all_completed:
            response_data['completion_message'] = 'All atoms done! Complete the Concept Final Challenge to finish.'
            response_data['concept_final_challenge_ready'] = True
            
            # Calculate overall concept mastery (for display, XP awarded after concept final challenge)
            concept_atoms = TeachingAtom.objects.filter(concept=atom.concept)
            concept_mastery = sum(StudentProgress.objects.get(user=request.user, atom=a).mastery_score for a in concept_atoms) / len(concept_atoms)
            response_data['concept_mastery'] = concept_mastery
        
        return Response(response_data)


class GetNextLearningStepView(APIView):
    """Core adaptive endpoint — returns the best next atom + action for a student."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({'error': 'session_id required'}, status=400)
        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
        except LearningSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)

        concept = session.concept
        engine = AdaptiveLearningEngine()
        step = engine.get_next_learning_step(request.user, concept, session)

        atom = step.get('atom')
        if atom is None:
            return Response({
                'action': 'concept_complete',
                'reason': step.get('reason', 'All atoms mastered'),
                'atom': None,
            })

        progress, _ = StudentProgress.objects.get_or_create(
            user=request.user, atom=atom,
            defaults={'mastery_score': 0.0, 'phase': 'not_started'}
        )
        return Response({
            'action': step['action'],
            'reason': step.get('reason', ''),
            'atom': {
                'id': atom.id,
                'name': atom.name,
                'order': atom.order,
                'phase': progress.phase,
                'mastery_score': progress.mastery_score,
            }
        })


class GenerateConceptOverviewView(APIView):
    """Generate a beginner-friendly overview when knowledge_level is zero."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
        except LearningSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)

        concept = session.concept
        atoms = TeachingAtom.objects.filter(concept=concept).order_by('order')
        atom_names = [a.name for a in atoms]

        generator = QuestionGenerator()
        overview = generator.generate_concept_overview(
            subject=concept.subject,
            concept=concept.name,
            atoms=atom_names
        )

        # Store in session
        session_data = session.session_data or {}
        session_data['concept_overview'] = overview
        session_data['current_phase'] = 'concept_overview'
        session.session_data = session_data
        session.save()

        return Response({
            'overview': overview,
            'concept_name': concept.name,
            'subject': concept.subject,
            'atom_names': atom_names,
        })


class GenerateAtomSummaryView(APIView):
    """Generate end-of-atom summary with quick notes, must-remember, suggestions."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        atom_id = request.data.get('atom_id')

        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
            atom = TeachingAtom.objects.get(id=atom_id)
            progress = StudentProgress.objects.get(user=request.user, atom=atom)
        except (LearningSession.DoesNotExist, TeachingAtom.DoesNotExist, StudentProgress.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        teaching_content = {
            'explanation': atom.explanation or '',
            'analogy': atom.analogy or '',
            'examples': atom.examples or []
        }

        generator = QuestionGenerator()
        summary = generator.generate_atom_summary(
            subject=atom.concept.subject,
            concept=atom.concept.name,
            atom_name=atom.name,
            teaching_content=teaching_content,
            mastery_score=float(progress.mastery_score),
            error_types=progress.error_history or []
        )

        # Store in session
        session_data = session.session_data or {}
        atom_summaries = session_data.get('atom_summaries', {})
        atom_summaries[str(atom.id)] = summary
        session_data['atom_summaries'] = atom_summaries
        session.session_data = session_data
        session.save()

        return Response({
            'atom_id': atom.id,
            'atom_name': atom.name,
            'mastery_score': float(progress.mastery_score),
            'phase': progress.phase,
            'summary': summary,
        })


class AdaptiveReteachView(APIView):
    """Re-teach an atom with a DIFFERENT approach based on error history + mastery."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        atom_id = request.data.get('atom_id')

        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
            atom = TeachingAtom.objects.get(id=atom_id)
            progress = StudentProgress.objects.get(user=request.user, atom=atom)
        except (LearningSession.DoesNotExist, TeachingAtom.DoesNotExist, StudentProgress.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        engine = AdaptiveLearningEngine()

        # Force regen with error focus
        error_history = progress.error_history or []

        # Determine adjusted knowledge level based on mastery
        mastery = float(progress.mastery_score)
        if mastery < 0.3:
            adjusted_level = 'zero'
        elif mastery < 0.5:
            adjusted_level = 'beginner'
        elif mastery < 0.7:
            adjusted_level = 'intermediate'
        else:
            adjusted_level = session.knowledge_level

        teaching_content = engine.generate_teaching_content(
            atom_name=atom.name,
            subject=atom.concept.subject,
            concept=atom.concept.name,
            knowledge_level=adjusted_level,
            error_history=error_history,
            mastery_score=mastery
        )

        # Save updated content
        atom.explanation = teaching_content.get('explanation', '')
        atom.analogy = teaching_content.get('analogy', '')
        atom.examples = [teaching_content.get('example', '')]
        atom.save()

        # Reset progress phase to teaching for this reteach cycle
        progress.phase = 'teaching'
        progress.times_practiced = (progress.times_practiced or 0) + 1
        progress.save()

        # Fetch external resources
        from learning_engine.external_resources import ExternalResourceFetcher
        try:
            fetcher = ExternalResourceFetcher()
            resources = fetcher.get_resources_for_concept(
                subject=atom.concept.subject,
                concept=atom.concept.name,
                atom_name=atom.name
            )
        except Exception:
            resources = {'videos': [], 'images': []}

        return Response({
            'atom_id': atom.id,
            'atom_name': atom.name,
            'teaching_content': teaching_content,
            'videos': resources.get('videos', []),
            'images': resources.get('images', []),
            'adjusted_level': adjusted_level,
            'mastery_score': mastery,
            'reteach_count': progress.times_practiced,
            'message': f"Here's a fresh explanation of {atom.name}, adapted to address your specific difficulties."
        })


class GetAllAtomsMasteryView(APIView):
    """Get mastery overview for all atoms in a concept — used for end-of-concept dashboard."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        concept_id = request.data.get('concept_id')

        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
            concept = Concept.objects.get(id=concept_id)
        except (LearningSession.DoesNotExist, Concept.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        atoms = TeachingAtom.objects.filter(concept=concept).order_by('order')
        atom_data = []
        total_mastery = 0.0

        for atom in atoms:
            try:
                progress = StudentProgress.objects.get(user=request.user, atom=atom)
                mastery = float(progress.mastery_score)
                phase = progress.phase
                streak = progress.streak
                errors = len(progress.error_history or [])
            except StudentProgress.DoesNotExist:
                mastery = 0.0
                phase = 'not_started'
                streak = 0
                errors = 0

            total_mastery += mastery

            # Retrieve stored atom summary if available
            session_data = session.session_data or {}
            atom_summaries = session_data.get('atom_summaries', {})
            summary = atom_summaries.get(str(atom.id))

            atom_data.append({
                'id': atom.id,
                'name': atom.name,
                'order': atom.order,
                'mastery_score': round(mastery, 4),
                'phase': phase,
                'streak': streak,
                'error_count': errors,
                'summary': summary,
            })

        avg_mastery = total_mastery / max(len(atoms), 1)
        completed_count = sum(1 for a in atom_data if a['phase'] == 'complete')

        # Get user theta & total XP
        try:
            profile = request.user.learning_profile
            user_theta = float(profile.overall_theta)
        except Exception:
            user_theta = 0.0
        try:
            xp_profile = UserXP.objects.get(user=request.user)
            total_xp = xp_profile.total_xp
        except UserXP.DoesNotExist:
            total_xp = 0

        # Add 'mastery' alias on each atom for frontend compatibility
        for a in atom_data:
            a['mastery'] = a['mastery_score']

        # Suggestions based on overall performance
        weak_atoms = [a for a in atom_data if a['mastery_score'] < 0.6]
        strong_atoms = [a for a in atom_data if a['mastery_score'] >= 0.8]

        suggestions = []
        if weak_atoms:
            names = ", ".join([a['name'] for a in weak_atoms[:3]])
            suggestions.append(f"Focus on reviewing: {names}")
        if avg_mastery < 0.6:
            suggestions.append("Consider revisiting the concept overview before the final challenge.")
        if avg_mastery >= 0.8:
            suggestions.append("Excellent overall mastery! You're well prepared for the final challenge.")
        if not suggestions:
            suggestions.append("Good progress! Keep practicing the weaker areas.")

        return Response({
            'concept_name': concept.name,
            'subject': concept.subject,
            'atoms': atom_data,
            'avg_mastery': round(avg_mastery, 4),
            'overall_mastery': round(avg_mastery, 4),
            'total_atoms': len(atoms),
            'completed_atoms': completed_count,
            'atoms_mastered': completed_count,
            'theta': user_theta,
            'total_xp': total_xp,
            'strong_atoms': len(strong_atoms),
            'weak_atoms': len(weak_atoms),
            'suggestions': suggestions,
        })


class GenerateFinalChallengeView(APIView):
    """Generate 5 medium+hard questions as final challenge after mastery."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        atom_id = request.data.get('atom_id')

        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
            atom = TeachingAtom.objects.get(id=atom_id)
        except (LearningSession.DoesNotExist, TeachingAtom.DoesNotExist):
            return Response({'error': 'Session or atom not found'}, status=404)

        # Build teaching content context
        teaching_content = {
            'explanation': atom.explanation or '',
            'analogy': atom.analogy or '',
            'examples': atom.examples or []
        }

        generator = QuestionGenerator()
        final_questions = generator.generate_questions_from_teaching(
            subject=atom.concept.subject,
            concept=atom.concept.name,
            atom=atom.name,
            teaching_content=teaching_content,
            need_easy=0,
            need_medium=2,
            need_hard=3,
            knowledge_level=session.knowledge_level
        )

        # Store full questions for grading
        session_data = session.session_data
        session_data['final_questions'] = final_questions
        session_data['final_answers'] = []
        session_data['current_phase'] = 'final_challenge'
        session.session_data = session_data
        session.save()

        # Persist to Question model so teachers can review
        for q in final_questions:
            try:
                Question.objects.create(
                    atom=atom,
                    difficulty=q['difficulty'],
                    cognitive_operation=q.get('cognitive_operation', 'apply'),
                    estimated_time=q.get('estimated_time', 60),
                    question_text=q['question'],
                    options=q['options'],
                    correct_index=q['correct_index'],
                )
            except Exception as save_err:
                print(f"Warning: failed to persist final-challenge question to DB: {save_err}")

        # Return without correct_index
        questions_payload = []
        for q in final_questions:
            questions_payload.append({
                'difficulty': q['difficulty'],
                'cognitive_operation': q['cognitive_operation'],
                'estimated_time': q['estimated_time'],
                'question': q['question'],
                'options': q['options']
            })

        return Response({
            'questions': questions_payload,
            'total_questions': len(questions_payload)
        })


class CompleteFinalChallengeView(APIView):
    """Finalize final challenge, mark atom complete, and provide suggestions."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        atom_id = request.data.get('atom_id')

        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
            atom = TeachingAtom.objects.get(id=atom_id)
            progress = StudentProgress.objects.get(user=request.user, atom=atom)
        except (LearningSession.DoesNotExist, TeachingAtom.DoesNotExist, StudentProgress.DoesNotExist):
            return Response({'error': 'Session, atom, or progress not found'}, status=404)

        final_answers = session.session_data.get('final_answers', [])
        if not final_answers:
            return Response({'error': 'No final challenge answers'}, status=400)

        correct_count = sum(1 for a in final_answers if a.get('correct'))
        accuracy = correct_count / len(final_answers)

        try:
            profile = request.user.learning_profile
        except LearningProfile.DoesNotExist:
            profile = LearningProfile.objects.create(user=request.user)

        # Calculate pacing/suggestion from final challenge performance
        latest_error_types = []
        for entry in session.session_data.get('answers', [])[-5:]:
            if entry.get('error_type'):
                latest_error_types.append(entry.get('error_type'))

        pacing_engine = PacingEngine()
        pacing_context = PacingContext(
            accuracy=accuracy,
            mastery_score=float(progress.mastery_score),
            streak=progress.streak,
            error_types=latest_error_types,
            theta=float(profile.overall_theta),
            questions_answered=len(final_answers),
            knowledge_level=session.knowledge_level,
            phase='final_challenge'
        )
        pacing_result = pacing_engine.decide_pacing(pacing_context)
        pacing = pacing_result.decision
        _next_action = pacing_result.next_action
        _reasoning = pacing_result.reasoning
        pacing_value = pacing.value if hasattr(pacing, 'value') else pacing

        mastered = accuracy >= 0.7 and float(progress.mastery_score) >= 0.7

        # Mark atom complete only if final mastery check is passed
        if mastered:
            progress.phase = 'complete'
            progress.retention_verified = True
        else:
            progress.phase = 'reinforcement'
            progress.retention_verified = False
        progress.save()

        # Award XP for atom completion via final challenge
        if mastered:
            xp_profile, _ = UserXP.objects.get_or_create(user=request.user)
            atom_xp = 10 if float(progress.mastery_score) >= 0.8 else 5
            xp_profile.award_xp(atom_xp, category='atoms')

        # Determine next atom
        next_atom = TeachingAtom.objects.filter(
            concept=atom.concept,
            order__gt=atom.order
        ).order_by('order').first()

        all_atoms = TeachingAtom.objects.filter(concept=atom.concept).count()
        completed = StudentProgress.objects.filter(user=request.user, atom__concept=atom.concept, phase='complete').count()
        all_completed = completed >= all_atoms

        # Friendly recommendation
        if mastered and pacing_value in ['speed_up', 'stay']:
            recommendation = 'Excellent! You passed the final challenge and can move forward.'
        elif mastered:
            recommendation = 'Nice work! You passed, but keep a steady pace on the next atom.'
        elif accuracy >= 0.6:
            recommendation = 'Good effort. Let’s do one short review cycle and try again.'
        else:
            recommendation = 'Let’s review the teaching content and rebuild mastery before moving on.'

        next_action = 'advance_next_atom' if mastered else 'review_current'

        # Save pacing entry for final challenge
        session_data = session.session_data
        pacing_history = session_data.get('pacing_history', [])
        pacing_history.append({
            'phase': 'final_challenge',
            'atom_id': atom.id,
            'pacing': pacing_value,
            'accuracy': accuracy,
            'mastery': float(progress.mastery_score),
            'next_action': next_action,
            'timestamp': str(timezone.now())
        })
        session_data['pacing_history'] = pacing_history
        session_data['last_pacing'] = pacing_value
        session.session_data = session_data
        session.save()

        return Response({
            'accuracy': accuracy,
            'correct': correct_count,
            'total': len(final_answers),
            'recommendation': recommendation,
            'mastered': mastered,
            'pacing': pacing_value,
            'next_action': next_action,
            'next_atom': {
                'id': next_atom.id,
                'name': next_atom.name
            } if mastered and next_atom and not all_completed else None,
            'all_completed': all_completed,
            'concept_final_challenge_ready': all_completed,
        })
    
class GetLearningProgressView(APIView):
    """Get overall learning progress with pacing history and stats"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            profile = request.user.learning_profile
        except:
            profile = LearningProfile.objects.create(user=request.user)
        
        # Get all progress records
        progress_records = StudentProgress.objects.filter(
            user=request.user
        ).select_related('atom__concept')
        
        # Get all sessions
        all_sessions = LearningSession.objects.filter(user=request.user)
        
        # Session stats
        total_sessions = all_sessions.count()
        total_questions_answered = sum(s.questions_answered for s in all_sessions)
        total_correct_answers = sum(s.correct_answers for s in all_sessions)
        total_hints_used = sum(s.hints_used for s in all_sessions)

        # Recent sessions for pacing analysis
        recent_sessions = all_sessions.order_by('-start_time')[:5]
        
        pacing_trend = []
        for session in recent_sessions:
            session_data = session.session_data
            pacing_history = session_data.get('pacing_history', [])
            if pacing_history:
                pacing_trend.append({
                    'concept': session.concept.name,
                    'date': session.start_time,
                    'final_pacing': pacing_history[-1].get('pacing') if pacing_history else None
                })

        # Recent sessions list (for history display)
        recent_sessions_list = []
        for s in all_sessions.order_by('-start_time')[:10]:
            duration_mins = None
            if s.end_time and s.start_time:
                duration_mins = round((s.end_time - s.start_time).total_seconds() / 60, 1)
            recent_sessions_list.append({
                'concept_name': s.concept.name,
                'subject': s.concept.subject,
                'start_time': s.start_time.isoformat(),
                'end_time': s.end_time.isoformat() if s.end_time else None,
                'duration_mins': duration_mins,
                'questions_answered': s.questions_answered,
                'correct_answers': s.correct_answers,
                'accuracy': round(s.correct_answers / s.questions_answered, 2) if s.questions_answered > 0 else 0,
            })
        
        # Group by concept
        concepts_data = {}
        for p in progress_records:
            concept_name = p.atom.concept.name
            concept_id = p.atom.concept.id
            if concept_name not in concepts_data:
                concepts_data[concept_name] = {
                    'id': concept_id,
                    'name': concept_name,
                    'subject': p.atom.concept.subject,
                    'atoms': [],
                    'mastered_count': 0,
                    'total_count': 0
                }
            
            concepts_data[concept_name]['atoms'].append({
                'name': p.atom.name,
                'mastery': p.mastery_score,
                'phase': p.phase,
                'streak': p.streak,
                'hint_usage': p.hint_usage,
                'error_count': len(p.error_history),
                'last_practiced': p.last_practiced.isoformat() if p.last_practiced else None,
            })
            concepts_data[concept_name]['total_count'] += 1
            if p.phase == 'complete':
                concepts_data[concept_name]['mastered_count'] += 1

        # Compute per-concept mastery %
        for cdata in concepts_data.values():
            if cdata['total_count'] > 0:
                cdata['mastery_pct'] = round(
                    sum(a['mastery'] for a in cdata['atoms']) / cdata['total_count'] * 100
                )
            else:
                cdata['mastery_pct'] = 0
        
        # Calculate overall mastery
        if progress_records:
            overall_mastery = sum(p.mastery_score for p in progress_records) / len(progress_records)
        else:
            overall_mastery = 0

        # Completed atoms / concepts
        total_atoms = progress_records.count()
        mastered_atoms = progress_records.filter(phase='complete').count()

        concept_ids_started = set(p.atom.concept_id for p in progress_records)
        concepts_completed = 0
        for cid in concept_ids_started:
            c_atoms = TeachingAtom.objects.filter(concept_id=cid).count()
            c_mastered = progress_records.filter(atom__concept_id=cid, phase='complete').count()
            if c_atoms > 0 and c_mastered >= c_atoms:
                concepts_completed += 1

        # XP stats
        try:
            xp_profile = request.user.xp_profile
            xp_data = {
                'total_xp': xp_profile.total_xp,
                'questions_xp': xp_profile.questions_xp,
                'atoms_xp': xp_profile.atoms_xp,
                'concepts_xp': xp_profile.concepts_xp,
            }
        except:
            xp_data = {'total_xp': 0, 'questions_xp': 0, 'atoms_xp': 0, 'concepts_xp': 0}
        
        return Response({
            'overall_mastery': overall_mastery,
            'overall_theta': profile.overall_theta,
            'learning_streak': profile.learning_streak,
            'total_time_spent': profile.total_time_spent,
            'concepts': list(concepts_data.values()),
            'total_atoms': total_atoms,
            'mastered_atoms': mastered_atoms,
            'concepts_started': len(concept_ids_started),
            'concepts_completed': concepts_completed,
            'total_sessions': total_sessions,
            'total_questions_answered': total_questions_answered,
            'total_correct_answers': total_correct_answers,
            'total_hints_used': total_hints_used,
            'overall_accuracy': round(total_correct_answers / total_questions_answered, 2) if total_questions_answered > 0 else 0,
            'xp': xp_data,
            'recent_sessions': recent_sessions_list,
            'pacing_trend': pacing_trend,
            'recommended_pacing': self._get_recommended_pacing(pacing_trend)
        })
    
    def _get_recommended_pacing(self, pacing_trend):
        """Analyze pacing trend to give overall recommendation"""
        if not pacing_trend:
            return 'start'
        
        pacings = [p['final_pacing'] for p in pacing_trend if p['final_pacing']]
        if not pacings:
            return 'normal'
        
        # Count occurrences
        sharp_count = pacings.count('sharp_slowdown')
        slow_count = pacings.count('slow_down')
        speed_count = pacings.count('speed_up')
        
        if sharp_count > len(pacings) / 2:
            return 'needs_foundation'
        elif slow_count > len(pacings) / 2:
            return 'cautious'
        elif speed_count > len(pacings) / 2:
            return 'accelerated'
        else:
            return 'balanced'


# ==================== ENHANCED PACING ENGINE VIEWS ====================

class GetVelocityGraphView(APIView):
    """Return velocity snapshots for the current session (Feature 10)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({'error': 'session_id required'}, status=400)

        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
        except LearningSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)

        velocity_data = session.velocity_data or []

        # Also gather per-atom velocity snapshots from StudentProgress
        atom_velocities = {}
        progresses = StudentProgress.objects.filter(
            user=request.user,
            atom__concept=session.concept
        )
        for p in progresses:
            snaps = p.velocity_snapshots or []
            if snaps:
                atom_velocities[p.atom.name] = snaps

        return Response({
            'session_velocity': velocity_data,
            'atom_velocities': atom_velocities,
            'engagement_score': session.engagement_score,
        })


class GetFatigueStatusView(APIView):
    """Return current fatigue level and break recommendations (Feature 8)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({'error': 'session_id required'}, status=400)

        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
        except LearningSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)

        # Compute fatigue using PacingEngine
        pacing_engine = PacingEngine()
        elapsed = (timezone.now() - session.start_time).total_seconds() / 60.0

        # Build minimal context for fatigue computation
        perf_history = session.session_data.get('performance_history', [])
        time_history = [p.get('time_taken', 30) for p in perf_history]
        accuracy_trend = []
        window = []
        for p in perf_history:
            window.append(1.0 if p.get('correct') else 0.0)
            if len(window) >= 3:
                accuracy_trend.append(sum(window[-3:]) / 3.0)

        ctx = PacingContext(
            accuracy=sum(1 for p in perf_history if p.get('correct')) / max(len(perf_history), 1),
            mastery_score=0.5,
            streak=0,
            error_types=[],
            theta=0.0,
            questions_answered=len(perf_history),
            knowledge_level=session.knowledge_level,
            phase='practice',
            session_duration_minutes=elapsed,
            consecutive_skips=session.consecutive_skips,
            time_per_question_history=time_history,
            recent_accuracy_trend=accuracy_trend,
        )

        fatigue_rec = pacing_engine.get_fatigue_recommendation(
            pacing_engine._detect_fatigue(ctx)
        )

        return Response({
            'fatigue_level': session.fatigue_level,
            'break_count': session.break_count,
            'last_break_at': session.last_break_at,
            'session_duration_minutes': round(elapsed, 1),
            'recommendation': fatigue_rec,
        })


class RecordBreakView(APIView):
    """Record that the student took a break (Feature 8)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')

        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
        except LearningSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)

        session.break_count = (session.break_count or 0) + 1
        session.last_break_at = timezone.now()
        session.fatigue_level = 'fresh'  # Reset after break
        session.consecutive_skips = 0
        session.save()

        return Response({
            'break_count': session.break_count,
            'fatigue_level': 'fresh',
            'message': 'Break recorded. Fatigue reset.'
        })


class RetentionCheckView(APIView):
    """Trigger or record a retention check for an atom (Feature 6)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        atom_id = request.data.get('atom_id')
        passed = request.data.get('passed')  # True/False or None (request check)

        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
            atom = TeachingAtom.objects.get(id=atom_id)
            progress = StudentProgress.objects.get(user=request.user, atom=atom)
        except (LearningSession.DoesNotExist, TeachingAtom.DoesNotExist, StudentProgress.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        if passed is None:
            # Request: should we do a retention check?
            pacing_engine = PacingEngine()
            last_practiced = None
            if progress.next_review_at and progress.next_review_at <= timezone.now():
                should_review = True
            else:
                elapsed = (timezone.now() - (progress.next_review_at or session.start_time)).total_seconds() / 60.0
                ctx = PacingContext(
                    accuracy=0.5, mastery_score=float(progress.mastery_score),
                    streak=progress.streak, error_types=[],
                    theta=0.0, questions_answered=0,
                    knowledge_level=session.knowledge_level,
                    phase=progress.phase,
                    last_practiced_minutes_ago=abs(elapsed),
                    retention_score=float(progress.retention_score),
                )
                ret = pacing_engine.compute_retention_score(ctx)
                should_review = ret < 0.5

            return Response({
                'should_review': should_review,
                'retention_score': float(progress.retention_score),
                'next_review_at': progress.next_review_at,
            })

        # Record result
        if passed:
            progress.retention_checks_passed = (progress.retention_checks_passed or 0) + 1
            progress.retention_score = min(1.0, float(progress.retention_score) + 0.1)
        else:
            progress.retention_checks_failed = (progress.retention_checks_failed or 0) + 1
            progress.retention_score = max(0.0, float(progress.retention_score) - 0.15)

        # Schedule next review using Ebbinghaus spacing
        pacing_engine = PacingEngine()
        ctx = PacingContext(
            accuracy=0.5, mastery_score=float(progress.mastery_score),
            streak=progress.streak, error_types=[],
            theta=0.0, questions_answered=0,
            knowledge_level=session.knowledge_level,
            phase=progress.phase,
            retention_score=float(progress.retention_score),
            retention_checks_passed=progress.retention_checks_passed,
        )
        next_review_minutes = pacing_engine.schedule_next_review(ctx)
        progress.next_review_at = timezone.now() + timezone.timedelta(minutes=next_review_minutes)
        progress.save()

        return Response({
            'passed': passed,
            'retention_score': float(progress.retention_score),
            'next_review_at': progress.next_review_at,
            'retention_checks_passed': progress.retention_checks_passed,
            'retention_checks_failed': progress.retention_checks_failed,
        })


class RecordHintUsageView(APIView):
    """Track hint usage for adaptive hint depth (Feature 7)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        atom_id = request.data.get('atom_id')
        hint_level = request.data.get('hint_level', 1)  # 1=nudge, 2=worked example, 3=full solution

        try:
            atom = TeachingAtom.objects.get(id=atom_id)
            progress = StudentProgress.objects.get(user=request.user, atom=atom)
        except (TeachingAtom.DoesNotExist, StudentProgress.DoesNotExist):
            return Response({'error': 'Not found'}, status=404)

        progress.hint_usage = (progress.hint_usage or 0) + 1
        progress.save()

        # Determine hint depth warning
        pacing_engine = PacingEngine()
        ctx = PacingContext(
            accuracy=0.5, mastery_score=float(progress.mastery_score),
            streak=progress.streak, error_types=progress.error_history[-5:] if progress.error_history else [],
            theta=0.0, questions_answered=0,
            knowledge_level='intermediate',
            phase=progress.phase,
            hint_usage_count=progress.hint_usage,
        )
        result = pacing_engine.decide_pacing(ctx)
        hint_warning = result.hint_warning

        return Response({
            'hint_usage': progress.hint_usage,
            'hint_level': hint_level,
            'hint_warning': hint_warning,
            'mastery_score': float(progress.mastery_score),
        })


# Add to backend/accounts/views.py

from learning_engine.external_resources import ExternalResourceFetcher

class GetConceptResourcesView(APIView):
    """Get external resources (videos, images) for a concept"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            subject = request.data.get('subject')
            concept = request.data.get('concept')
            atom_name = request.data.get('atom_name')
            
            if not subject or not concept:
                return Response(
                    {'error': 'Subject and concept are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            fetcher = ExternalResourceFetcher()
            resources = fetcher.get_resources_for_concept(subject, concept, atom_name)
            
            return Response(resources, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching resources: {str(e)}")
            return Response(
                {'error': 'Failed to fetch resources'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==================== LEADERBOARD ====================

class LeaderboardView(APIView):
    """Get XP leaderboard"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Ensure current user has an XP profile
        UserXP.objects.get_or_create(user=request.user)

        leaderboard = UserXP.objects.select_related('user').order_by('-total_xp')[:50]
        data = []
        for rank, entry in enumerate(leaderboard, 1):
            data.append({
                'rank': rank,
                'username': entry.user.username,
                'first_name': entry.user.first_name,
                'last_name': entry.user.last_name,
                'total_xp': entry.total_xp,
                'questions_xp': entry.questions_xp,
                'atoms_xp': entry.atoms_xp,
                'concepts_xp': entry.concepts_xp,
                'is_current_user': entry.user.id == request.user.id,
            })

        # If current user not in top 50, add their entry
        current_in_list = any(d['is_current_user'] for d in data)
        if not current_in_list:
            user_xp = UserXP.objects.get(user=request.user)
            user_rank = UserXP.objects.filter(total_xp__gt=user_xp.total_xp).count() + 1
            data.append({
                'rank': user_rank,
                'username': request.user.username,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'total_xp': user_xp.total_xp,
                'questions_xp': user_xp.questions_xp,
                'atoms_xp': user_xp.atoms_xp,
                'concepts_xp': user_xp.concepts_xp,
                'is_current_user': True,
            })

        return Response(data)


class MyXPView(APIView):
    """Get current user's XP details"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        xp_profile, _ = UserXP.objects.get_or_create(user=request.user)
        rank = UserXP.objects.filter(total_xp__gt=xp_profile.total_xp).count() + 1
        total_users = UserXP.objects.count()
        return Response({
            'total_xp': xp_profile.total_xp,
            'questions_xp': xp_profile.questions_xp,
            'atoms_xp': xp_profile.atoms_xp,
            'concepts_xp': xp_profile.concepts_xp,
            'rank': rank,
            'total_users': total_users,
        })


# ==================== CONCEPT FINAL CHALLENGE ====================

class GenerateConceptFinalChallengeView(APIView):
    """Generate a final challenge spanning ALL atoms after all atoms are completed."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        concept_id = request.data.get('concept_id')

        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
            concept = Concept.objects.get(id=concept_id)
        except (LearningSession.DoesNotExist, Concept.DoesNotExist):
            return Response({'error': 'Session or concept not found'}, status=404)

        atoms = TeachingAtom.objects.filter(concept=concept).order_by('order')
        if not atoms.exists():
            return Response({'error': 'No atoms found for concept'}, status=400)

        generator = QuestionGenerator()
        all_questions = []

        # Generate 2 questions per atom (1 medium + 1 hard) for a comprehensive challenge
        for atom in atoms:
            teaching_content = {
                'explanation': atom.explanation or '',
                'analogy': atom.analogy or '',
                'examples': atom.examples or []
            }
            qs = generator.generate_questions_from_teaching(
                subject=concept.subject,
                concept=concept.name,
                atom=atom.name,
                teaching_content=teaching_content,
                need_easy=0,
                need_medium=1,
                need_hard=1,
                knowledge_level=session.knowledge_level
            )
            for q in qs:
                q['source_atom_id'] = atom.id
                q['source_atom_name'] = atom.name
            all_questions.extend(qs)

        # Store in session
        session_data = session.session_data
        session_data['concept_final_questions'] = all_questions
        session_data['concept_final_answers'] = []
        session_data['current_phase'] = 'concept_final_challenge'
        session.session_data = session_data
        session.save()

        # Build payload without correct_index
        questions_payload = []
        for q in all_questions:
            questions_payload.append({
                'difficulty': q.get('difficulty', 'medium'),
                'cognitive_operation': q.get('cognitive_operation', 'apply'),
                'estimated_time': q.get('estimated_time', 60),
                'question': q.get('question', ''),
                'options': q.get('options', []),
                'source_atom_name': q.get('source_atom_name', ''),
            })

        return Response({
            'questions': questions_payload,
            'total_questions': len(questions_payload),
            'concept_name': concept.name,
        })


class SubmitConceptFinalAnswerView(APIView):
    """Submit an individual answer during the concept final challenge."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        question_index = request.data.get('question_index')
        selected = request.data.get('selected')
        time_taken = request.data.get('time_taken', 30)

        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
        except LearningSession.DoesNotExist:
            return Response({'error': 'Session not found'}, status=404)

        questions = session.session_data.get('concept_final_questions', [])
        try:
            question_index = int(question_index)
        except (TypeError, ValueError):
            return Response({'error': 'Invalid question index'}, status=400)

        if question_index < 0 or question_index >= len(questions):
            return Response({'error': 'Invalid question index'}, status=400)

        question = questions[question_index]

        # Type-safe comparison: ensure both are ints
        try:
            selected_int = int(selected) if selected is not None else None
        except (TypeError, ValueError):
            selected_int = None
        stored_correct = question.get('correct_index')
        try:
            correct_index = int(stored_correct) if stored_correct is not None else None
        except (TypeError, ValueError):
            correct_index = None

        is_correct = (selected_int is not None and selected_int == correct_index)

        # Award XP for correct answer
        if is_correct:
            difficulty = question.get('difficulty', 'medium')
            xp_map = {'easy': 1, 'medium': 2, 'hard': 3}
            xp_amount = xp_map.get(difficulty, 2)
            xp_profile, _ = UserXP.objects.get_or_create(user=request.user)
            xp_profile.award_xp(xp_amount, category='questions')

        # Store answer
        if 'concept_final_answers' not in session.session_data:
            session.session_data['concept_final_answers'] = []
        session.session_data['concept_final_answers'].append({
            'question_index': question_index,
            'selected': selected_int,
            'correct': is_correct,
            'correct_index': correct_index,
            'time_taken': time_taken,
            'difficulty': question.get('difficulty', 'medium'),
        })
        session.save()

        explanation = ''
        if not is_correct:
            options = question.get('options', [])
            correct_option = options[correct_index] if isinstance(correct_index, int) and 0 <= correct_index < len(options) else None
            explanation = f"Correct answer: {correct_option}" if correct_option else "Review the concept and try again."

        return Response({
            'correct': is_correct,
            'correct_index': correct_index if not is_correct else None,
            'explanation': explanation,
        })


class CompleteConceptFinalChallengeView(APIView):
    """Finalize the concept final challenge, calculate mastery, and award XP."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        concept_id = request.data.get('concept_id')

        try:
            session = LearningSession.objects.get(id=session_id, user=request.user)
            concept = Concept.objects.get(id=concept_id)
        except (LearningSession.DoesNotExist, Concept.DoesNotExist):
            return Response({'error': 'Session or concept not found'}, status=404)

        final_answers = session.session_data.get('concept_final_answers', [])
        if not final_answers:
            return Response({'error': 'No concept final challenge answers'}, status=400)

        correct_count = sum(1 for a in final_answers if a.get('correct'))
        total = len(final_answers)
        accuracy = correct_count / total

        # Overall concept mastery from atoms
        concept_atoms = TeachingAtom.objects.filter(concept=concept)
        atom_masteries = []
        weakest_atom = None
        lowest_mastery = 1.0

        for atom in concept_atoms:
            try:
                prog = StudentProgress.objects.get(user=request.user, atom=atom)
                mastery = float(prog.mastery_score)
            except StudentProgress.DoesNotExist:
                mastery = 0.0
            atom_masteries.append(mastery)

            if mastery < lowest_mastery:
                lowest_mastery = mastery
                weakest_atom = atom

        concept_mastery = sum(atom_masteries) / max(len(atom_masteries), 1)

        # Blend atom mastery with final challenge accuracy
        final_mastery = (concept_mastery * 0.6) + (accuracy * 0.4)

        # Determine if passed
        passed = accuracy >= 0.6

        # Award concept XP
        xp_profile, _ = UserXP.objects.get_or_create(user=request.user)
        if passed:
            concept_xp = 50 if final_mastery >= 0.8 else 25
            xp_profile.award_xp(concept_xp, category='concepts')
        else:
            concept_xp = 0

        # Update session
        session.end_time = timezone.now()
        session_data = session.session_data
        session_data['concept_final_result'] = {
            'accuracy': accuracy,
            'correct': correct_count,
            'total': total,
            'concept_mastery': concept_mastery,
            'final_mastery': final_mastery,
            'passed': passed,
            'xp_earned': concept_xp,
            'weakest_atom': weakest_atom.name if weakest_atom else None,
            'lowest_mastery': lowest_mastery,
        }
        session.session_data = session_data
        session.save()
        if accuracy < 0.6 and weakest_atom:
            recommendation = (
                f" We recommend revising '{weakest_atom.name}' "
                f"(Mastery: {lowest_mastery:.0%}) before continuing."
            )

        elif passed:
            recommendation = f"🎉 Congratulations! You passed with {accuracy:.0%} accuracy and earned {concept_xp} XP!"
        elif accuracy >= 0.4:
            recommendation = f"Almost there! You scored {accuracy:.0%}. Review weaker atoms and try again."
        else:
            recommendation = f"You scored {accuracy:.0%}. Take some time to review the atoms before retrying."

        return Response({
            'passed': passed,
            'accuracy': accuracy,
            'correct': correct_count,
            'total': total,
            'concept_mastery': concept_mastery,
            'final_mastery': final_mastery,
            'concept_xp': concept_xp,
            'recommendation': recommendation,
            'weakest_atom': weakest_atom.name if weakest_atom else None,
            'lowest_mastery': lowest_mastery,
        })
    # ==================== AI Assistance ====================

class AIDoubtAssistantView(APIView):
    """
    AI-Based Doubt Solver
    Personalized explanation based on student mastery and accuracy
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = request.data.get("question")
        topic = request.data.get("topic")
        level = request.data.get("level")
        accuracy = request.data.get("accuracy")

        if not question or not topic:
            return Response(
                {"error": "Question and topic are required"},
                status=400
            )

        try:
            # Generate AI Response
            answer = generate_ai_response(
                question=question,
                topic=topic,
                level=level,
                accuracy=accuracy
            )

            # Optional: Save doubt to session or database
            # Example: Attach to LearningSession if needed

            return Response({
                "question": question,
                "topic": topic,
                "level_used": level,
                "ai_answer": answer,
                "timestamp": timezone.now(),
                "message": "AI explanation generated successfully"
            })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=500
            )


# ==================== TEACHER PERMISSION MIXIN ====================

class IsTeacher:
    """Check if user has a teacher profile"""
    @staticmethod
    def check(user):
        return hasattr(user, 'teacher_profile') and user.teacher_profile.is_active


# ==================== TEACHER AUTH VIEWS ====================

class TeacherRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TeacherRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'pending_approval': True,
                'message': 'Teacher account created successfully. Your account is pending admin approval. You will be able to login once approved.'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user:
            if not IsTeacher.check(user):
                return Response({'error': 'This account is not a teacher account'},
                                status=status.HTTP_403_FORBIDDEN)
            # Check if teacher is approved by admin
            try:
                profile = user.teacher_profile
                if not profile.is_active:
                    return Response({
                        'error': 'Your account is pending admin approval. Please wait for an administrator to activate your account.',
                        'pending_approval': True
                    }, status=status.HTTP_403_FORBIDDEN)
            except Exception:
                return Response({'error': 'Teacher profile not found'}, status=status.HTTP_403_FORBIDDEN)

            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
                'is_teacher': True,
                'teacher_profile': TeacherProfileSerializer(user.teacher_profile).data
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class TeacherDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        teacher = request.user
        profile = teacher.teacher_profile

        # Get all students (non-teachers)
        all_students = User.objects.filter(
            is_staff=False, is_superuser=False
        ).exclude(id=teacher.id)

        # Student count
        total_students = all_students.count()

        # Get all concepts (teacher should see full class data)
        teacher_concepts = Concept.objects.all().order_by('subject', 'order')

        # Class-level analytics: average mastery per concept
        class_analytics = []
        for concept in teacher_concepts:
            atoms = TeachingAtom.objects.filter(concept=concept)
            if not atoms.exists():
                continue
            progresses = StudentProgress.objects.filter(atom__in=atoms)
            if progresses.exists():
                avg_mastery = progresses.aggregate(
                    avg=models.Avg('mastery_score')
                )['avg'] or 0
                student_count = progresses.values('user').distinct().count()
                weak_count = progresses.filter(mastery_score__lt=0.5).values('user').distinct().count()
            else:
                avg_mastery = 0
                student_count = 0
                weak_count = 0

            class_analytics.append({
                'concept_id': concept.id,
                'concept_name': concept.name,
                'subject': concept.subject,
                'avg_mastery': round(avg_mastery, 3),
                'student_count': student_count,
                'weak_students': weak_count,
                'atom_count': atoms.count(),
            })

        # Pending question approvals
        pending_questions = QuestionApproval.objects.filter(
            status='pending'
        ).count()

        # Active overrides
        active_overrides = TeacherOverride.objects.filter(
            teacher=teacher, is_active=True
        ).count()

        # Active goals
        active_goals = TeacherGoal.objects.filter(
            teacher=teacher, status='active'
        ).count()

        # Struggling students (mastery < 0.4 on any atom)
        struggling_students = []
        for student in all_students[:50]:  # Limit for performance
            weak_progress = StudentProgress.objects.filter(
                user=student, mastery_score__lt=0.4
            ).select_related('atom__concept').order_by('mastery_score')[:3]
            if weak_progress.exists():
                struggling_students.append({
                    'student_id': student.id,
                    'student_name': student.get_full_name() or student.username,
                    'username': student.username,
                    'weak_areas': [{
                        'atom': p.atom.name,
                        'concept': p.atom.concept.name,
                        'mastery': round(p.mastery_score, 3),
                    } for p in weak_progress]
                })

        return Response({
            'teacher': TeacherProfileSerializer(profile).data,
            'stats': {
                'total_students': total_students,
                'total_concepts': teacher_concepts.count(),
                'pending_questions': pending_questions,
                'active_overrides': active_overrides,
                'active_goals': active_goals,
            },
            'class_analytics': class_analytics,
            'struggling_students': struggling_students[:20],
        })


# ==================== STUDENT ANALYTICS (for teacher) ====================

class TeacherStudentListView(APIView):
    """List all students with summary stats"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        students = User.objects.filter(
            is_staff=False, is_superuser=False
        ).order_by('username')

        student_data = []
        for student in students:
            progress = StudentProgress.objects.filter(user=student)
            total_atoms = progress.count()
            avg_mastery = progress.aggregate(avg=models.Avg('mastery_score'))['avg'] or 0
            completed_atoms = progress.filter(phase='complete').count()
            weak_count = progress.filter(mastery_score__lt=0.5).count()

            try:
                xp = student.xp_profile.total_xp
            except Exception:
                xp = 0

            sessions = LearningSession.objects.filter(user=student)
            total_questions = sessions.aggregate(total=models.Sum('questions_answered'))['total'] or 0
            total_correct = sessions.aggregate(total=models.Sum('correct_answers'))['total'] or 0

            student_data.append({
                'id': student.id,
                'username': student.username,
                'name': student.get_full_name() or student.username,
                'email': student.email,
                'total_atoms': total_atoms,
                'completed_atoms': completed_atoms,
                'avg_mastery': round(avg_mastery, 3),
                'weak_areas': weak_count,
                'total_xp': xp,
                'total_questions': total_questions,
                'total_correct': total_correct,
                'accuracy': round(total_correct / max(total_questions, 1), 3),
            })

        return Response(student_data)


class TeacherStudentDetailView(APIView):
    """Detailed view of a specific student"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response({'error': 'student_id required'}, status=400)

        try:
            student = User.objects.get(id=student_id)
        except User.DoesNotExist:
            return Response({'error': 'Student not found'}, status=404)

        serializer = StudentDetailSerializer(student)
        
        # Also include sessions
        sessions = LearningSession.objects.filter(user=student).select_related('concept').order_by('-start_time')[:20]
        session_data = [{
            'id': s.id,
            'concept': s.concept.name,
            'start_time': s.start_time,
            'end_time': s.end_time,
            'questions_answered': s.questions_answered,
            'correct_answers': s.correct_answers,
            'knowledge_level': s.knowledge_level,
            'fatigue_level': s.fatigue_level,
            'engagement_score': s.engagement_score,
        } for s in sessions]

        # Get overrides for this student
        overrides = TeacherOverride.objects.filter(
            student=student, teacher=request.user
        ).order_by('-created_at')[:10]

        return Response({
            'student': serializer.data,
            'sessions': session_data,
            'overrides': TeacherOverrideSerializer(overrides, many=True).data,
        })


# ==================== CONTENT MANAGEMENT ====================

class TeacherContentListView(APIView):
    """List and create teacher content"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        contents = TeacherContent.objects.filter(
            teacher=request.user
        ).select_related('atom__concept')

        serializer = TeacherContentSerializer(contents, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        serializer = TeacherContentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(teacher=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherContentDetailView(APIView):
    """Update or delete teacher content"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        content_id = request.data.get('content_id')
        try:
            content = TeacherContent.objects.get(id=content_id, teacher=request.user)
        except TeacherContent.DoesNotExist:
            return Response({'error': 'Content not found'}, status=404)

        serializer = TeacherContentSerializer(content, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        content_id = request.query_params.get('content_id')
        try:
            content = TeacherContent.objects.get(id=content_id, teacher=request.user)
        except TeacherContent.DoesNotExist:
            return Response({'error': 'Content not found'}, status=404)

        content.delete()
        return Response({'message': 'Content deleted'}, status=status.HTTP_204_NO_CONTENT)


# ==================== QUESTION MANAGEMENT ====================

class TeacherQuestionListView(APIView):
    """List all questions for teacher review"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        filter_status = request.query_params.get('status', 'all')
        concept_id = request.query_params.get('concept_id')

        questions = Question.objects.all().select_related('atom__concept')

        if concept_id:
            questions = questions.filter(atom__concept_id=concept_id)

        question_data = []
        for q in questions:
            approval = QuestionApproval.objects.filter(question=q).first()
            question_data.append({
                'id': q.id,
                'question_text': q.question_text,
                'options': q.options,
                'correct_index': q.correct_index,
                'difficulty': q.difficulty,
                'cognitive_operation': q.cognitive_operation,
                'atom_name': q.atom.name,
                'atom_id': q.atom.id,
                'concept_name': q.atom.concept.name,
                'concept_id': q.atom.concept.id,
                'subject': q.atom.concept.subject,
                'approval_status': approval.status if approval else 'pending',
                'approval_feedback': approval.feedback if approval else '',
            })

        if filter_status != 'all':
            question_data = [q for q in question_data if q['approval_status'] == filter_status]

        return Response(question_data)


class TeacherQuestionApproveView(APIView):
    """Approve, reject, edit, or disable a question"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        question_id = request.data.get('question_id')
        action = request.data.get('action')  # approve, reject, edit, disable
        feedback = request.data.get('feedback', '')

        if not question_id or not action:
            return Response({'error': 'question_id and action required'}, status=400)

        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response({'error': 'Question not found'}, status=404)

        approval, created = QuestionApproval.objects.get_or_create(
            question=question,
            defaults={'teacher': request.user, 'status': 'pending'}
        )

        if action == 'approve':
            approval.status = 'approved'
        elif action == 'reject':
            approval.status = 'rejected'
        elif action == 'disable':
            approval.status = 'disabled'
        elif action == 'edit':
            approval.status = 'edited'
            edited_text = request.data.get('edited_question_text')
            edited_options = request.data.get('edited_options')
            edited_correct = request.data.get('edited_correct_index')
            if edited_text:
                approval.edited_question_text = edited_text
                question.question_text = edited_text
            if edited_options:
                approval.edited_options = edited_options
                question.options = edited_options
            if edited_correct is not None:
                approval.edited_correct_index = edited_correct
                question.correct_index = edited_correct
            question.save()
        else:
            return Response({'error': 'Invalid action'}, status=400)

        approval.teacher = request.user
        approval.feedback = feedback
        approval.reviewed_at = timezone.now()
        approval.save()

        return Response({
            'message': f'Question {action}d successfully',
            'question_id': question.id,
            'status': approval.status,
        })


class TeacherAddQuestionView(APIView):
    """Teacher manually adds a question"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        atom_id = request.data.get('atom_id')
        question_text = request.data.get('question_text')
        options = request.data.get('options', [])
        correct_index = request.data.get('correct_index')
        difficulty = request.data.get('difficulty', 'medium')
        cognitive_operation = request.data.get('cognitive_operation', 'apply')

        if not all([atom_id, question_text, options, correct_index is not None]):
            return Response({'error': 'All fields required'}, status=400)

        try:
            atom = TeachingAtom.objects.get(id=atom_id)
        except TeachingAtom.DoesNotExist:
            return Response({'error': 'Atom not found'}, status=404)

        question = Question.objects.create(
            atom=atom,
            question_text=question_text,
            options=options,
            correct_index=correct_index,
            difficulty=difficulty,
            cognitive_operation=cognitive_operation,
        )

        # Auto-approve teacher-created questions
        QuestionApproval.objects.create(
            question=question,
            teacher=request.user,
            status='approved',
            feedback='Teacher-created question',
            reviewed_at=timezone.now(),
        )

        return Response({
            'message': 'Question created and approved',
            'question_id': question.id,
        }, status=status.HTTP_201_CREATED)


# ==================== STUDENT INTERVENTION ====================

class TeacherOverrideListView(APIView):
    """List and create teacher overrides"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        overrides = TeacherOverride.objects.filter(
            teacher=request.user
        ).select_related('student', 'atom', 'concept')

        return Response(TeacherOverrideSerializer(overrides, many=True).data)

    def post(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        student_id = request.data.get('student')
        action = request.data.get('action')
        atom_id = request.data.get('atom')
        concept_id = request.data.get('concept')
        parameters = request.data.get('parameters', {})
        reason = request.data.get('reason', '')

        if not student_id or not action:
            return Response({'error': 'student and action required'}, status=400)

        try:
            student = User.objects.get(id=student_id)
        except User.DoesNotExist:
            return Response({'error': 'Student not found'}, status=404)

        override = TeacherOverride.objects.create(
            teacher=request.user,
            student=student,
            atom_id=atom_id,
            concept_id=concept_id,
            action=action,
            parameters=parameters,
            reason=reason,
        )

        # Apply the override immediately
        if action == 'reset_mastery' and atom_id:
            try:
                progress = StudentProgress.objects.get(user=student, atom_id=atom_id)
                progress.mastery_score = 0.0
                progress.phase = 'not_started'
                progress.streak = 0
                progress.save()
            except StudentProgress.DoesNotExist:
                pass

        elif action == 'set_mastery' and atom_id:
            mastery_value = parameters.get('mastery', 0.5)
            try:
                progress = StudentProgress.objects.get(user=student, atom_id=atom_id)
                progress.mastery_score = mastery_value
                progress.save()
            except StudentProgress.DoesNotExist:
                pass

        elif action == 'force_review' and atom_id:
            try:
                progress = StudentProgress.objects.get(user=student, atom_id=atom_id)
                progress.phase = 'reinforcement'
                progress.retention_verified = False
                progress.save()
            except StudentProgress.DoesNotExist:
                pass

        return Response(TeacherOverrideSerializer(override).data, status=status.HTTP_201_CREATED)


class TeacherOverrideDeactivateView(APIView):
    """Deactivate an override"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        override_id = request.data.get('override_id')
        try:
            override = TeacherOverride.objects.get(id=override_id, teacher=request.user)
        except TeacherOverride.DoesNotExist:
            return Response({'error': 'Override not found'}, status=404)

        override.is_active = False
        override.save()
        return Response({'message': 'Override deactivated'})


# ==================== GOALS & DEADLINES ====================

class TeacherGoalListView(APIView):
    """List and create teacher goals"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        goals = TeacherGoal.objects.filter(
            teacher=request.user
        ).select_related('student', 'concept')

        return Response(TeacherGoalSerializer(goals, many=True).data)

    def post(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        serializer = TeacherGoalSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(teacher=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherGoalUpdateView(APIView):
    """Update goal status"""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        goal_id = request.data.get('goal_id')
        try:
            goal = TeacherGoal.objects.get(id=goal_id, teacher=request.user)
        except TeacherGoal.DoesNotExist:
            return Response({'error': 'Goal not found'}, status=404)

        new_status = request.data.get('status')
        if new_status:
            goal.status = new_status
        title = request.data.get('title')
        if title:
            goal.title = title
        deadline = request.data.get('deadline')
        if deadline:
            goal.deadline = deadline
        
        goal.save()
        return Response(TeacherGoalSerializer(goal).data)


# ==================== CLASS ANALYTICS ====================

class TeacherClassAnalyticsView(APIView):
    """Detailed class-level analytics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        from django.db.models import Avg, Count, Sum, Q

        teacher = request.user
        profile = teacher.teacher_profile

        # Get all concepts (teacher should see full class analytics)
        concepts = Concept.objects.all().order_by('subject', 'order')

        # Per-concept breakdown
        concept_analytics = []
        for concept in concepts:
            atoms = TeachingAtom.objects.filter(concept=concept)
            atom_analytics = []
            for atom in atoms:
                progresses = StudentProgress.objects.filter(atom=atom)
                if progresses.exists():
                    stats = progresses.aggregate(
                        avg_mastery=Avg('mastery_score'),
                        total_students=Count('user', distinct=True),
                        completed=Count('id', filter=Q(phase='complete')),
                        struggling=Count('id', filter=Q(mastery_score__lt=0.4)),
                    )
                else:
                    stats = {'avg_mastery': 0, 'total_students': 0, 'completed': 0, 'struggling': 0}

                atom_analytics.append({
                    'atom_id': atom.id,
                    'atom_name': atom.name,
                    'avg_mastery': round(stats['avg_mastery'] or 0, 3),
                    'total_students': stats['total_students'],
                    'completed': stats['completed'],
                    'struggling': stats['struggling'],
                })

            overall_mastery = sum(a['avg_mastery'] for a in atom_analytics) / max(len(atom_analytics), 1)
            concept_analytics.append({
                'concept_id': concept.id,
                'concept_name': concept.name,
                'subject': concept.subject,
                'overall_mastery': round(overall_mastery, 3),
                'atoms': atom_analytics,
            })

        # Overall class stats
        all_progress = StudentProgress.objects.all()
        overall_stats = all_progress.aggregate(
            avg_mastery=Avg('mastery_score'),
            total_completions=Count('id', filter=Q(phase='complete')),
        )

        total_sessions = LearningSession.objects.count()
        total_questions_answered = LearningSession.objects.aggregate(
            total=Sum('questions_answered')
        )['total'] or 0

        return Response({
            'concepts': concept_analytics,
            'overall': {
                'avg_mastery': round(overall_stats['avg_mastery'] or 0, 3),
                'total_completions': overall_stats['total_completions'],
                'total_sessions': total_sessions,
                'total_questions_answered': total_questions_answered,
            }
        })


# ==================== KNOWLEDGE GRAPH MANAGEMENT ====================

class TeacherConceptManageView(APIView):
    """Teacher creates/edits/deletes concepts and atoms"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all concepts with atoms for management"""
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        concepts = Concept.objects.filter(
            created_by=request.user
        ).prefetch_related('atoms')

        data = []
        for concept in concepts:
            atoms = concept.atoms.all().order_by('order')
            data.append({
                'id': concept.id,
                'name': concept.name,
                'subject': concept.subject,
                'description': concept.description,
                'difficulty': concept.difficulty,
                'order': concept.order,
                'atoms': [{
                    'id': a.id, 'name': a.name, 'order': a.order,
                    'explanation': a.explanation, 'analogy': a.analogy,
                    'examples': a.examples,
                    'question_count': a.questions.count(),
                } for a in atoms],
                'prerequisites': list(concept.prerequisites.values_list('id', flat=True)),
            })

        return Response(data)

    def post(self, request):
        """Create a new concept"""
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        name = request.data.get('name')
        subject = request.data.get('subject')
        description = request.data.get('description', '')
        difficulty = request.data.get('difficulty', 'medium')
        prerequisite_ids = request.data.get('prerequisites', [])

        if not name or not subject:
            return Response({'error': 'name and subject required'}, status=400)

        concept = Concept.objects.create(
            name=name,
            subject=subject,
            description=description,
            difficulty=difficulty,
            created_by=request.user,
        )

        if prerequisite_ids:
            concept.prerequisites.set(prerequisite_ids)

        return Response({
            'id': concept.id,
            'name': concept.name,
            'subject': concept.subject,
            'message': 'Concept created'
        }, status=status.HTTP_201_CREATED)

    def put(self, request):
        """Update a concept"""
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        concept_id = request.data.get('concept_id')
        try:
            concept = Concept.objects.get(id=concept_id, created_by=request.user)
        except Concept.DoesNotExist:
            return Response({'error': 'Concept not found'}, status=404)

        for field in ['name', 'subject', 'description', 'difficulty']:
            if field in request.data:
                setattr(concept, field, request.data[field])
        concept.save()

        prerequisite_ids = request.data.get('prerequisites')
        if prerequisite_ids is not None:
            concept.prerequisites.set(prerequisite_ids)

        return Response({'message': 'Concept updated'})

    def delete(self, request):
        """Delete a concept"""
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        concept_id = request.query_params.get('concept_id')
        try:
            concept = Concept.objects.get(id=concept_id, created_by=request.user)
        except Concept.DoesNotExist:
            return Response({'error': 'Concept not found'}, status=404)

        concept.delete()
        return Response({'message': 'Concept deleted'}, status=status.HTTP_204_NO_CONTENT)


class TeacherAtomManageView(APIView):
    """Teacher creates/edits/deletes atoms"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create atom"""
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        concept_id = request.data.get('concept_id')
        name = request.data.get('name')
        explanation = request.data.get('explanation', '')
        analogy = request.data.get('analogy', '')
        examples = request.data.get('examples', [])
        order = request.data.get('order', 0)

        if not concept_id or not name:
            return Response({'error': 'concept_id and name required'}, status=400)

        try:
            concept = Concept.objects.get(id=concept_id)
        except Concept.DoesNotExist:
            return Response({'error': 'Concept not found'}, status=404)

        atom = TeachingAtom.objects.create(
            concept=concept,
            name=name,
            explanation=explanation,
            analogy=analogy,
            examples=examples,
            order=order,
        )

        return Response({
            'id': atom.id,
            'name': atom.name,
            'message': 'Atom created'
        }, status=status.HTTP_201_CREATED)

    def put(self, request):
        """Update atom"""
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        atom_id = request.data.get('atom_id')
        try:
            atom = TeachingAtom.objects.get(id=atom_id)
        except TeachingAtom.DoesNotExist:
            return Response({'error': 'Atom not found'}, status=404)

        for field in ['name', 'explanation', 'analogy', 'examples', 'order']:
            if field in request.data:
                setattr(atom, field, request.data[field])
        atom.save()

        return Response({'message': 'Atom updated'})

    def delete(self, request):
        """Delete atom"""
        if not IsTeacher.check(request.user):
            return Response({'error': 'Not a teacher'}, status=403)

        atom_id = request.query_params.get('atom_id')
        try:
            atom = TeachingAtom.objects.get(id=atom_id)
        except TeachingAtom.DoesNotExist:
            return Response({'error': 'Atom not found'}, status=404)

        atom.delete()
        return Response({'message': 'Atom deleted'}, status=status.HTTP_204_NO_CONTENT)


# ==================== CHECK IF USER IS TEACHER ====================

class CheckTeacherView(APIView):
    """Check if the current user is a teacher"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_teacher = IsTeacher.check(request.user)
        data = {'is_teacher': is_teacher}
        if is_teacher:
            data['teacher_profile'] = TeacherProfileSerializer(request.user.teacher_profile).data
        return Response(data)



# ==================== PARENT PERMISSION ====================

class IsParent:
    """Check if user has a parent profile"""
    @staticmethod
    def check(user):
        return hasattr(user, 'parent_profile') and user.parent_profile.is_active


# ==================== PARENT AUTH VIEWS ====================

class ParentRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ParentRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Parent account created successfully. You can now log in.',
                'user': UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ParentLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user:
            if not IsParent.check(user):
                return Response({'error': 'This account is not a parent account'},
                                status=status.HTTP_403_FORBIDDEN)
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
                'is_parent': True,
                'parent_profile': ParentProfileSerializer(user.parent_profile).data,
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class CheckParentView(APIView):
    """Check if the current user is a parent"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        is_parent = IsParent.check(request.user)
        data = {'is_parent': is_parent}
        if is_parent:
            data['parent_profile'] = ParentProfileSerializer(request.user.parent_profile).data
        return Response(data)


# ==================== PARENT CHILDREN & LINKING ====================

class ParentChildrenView(APIView):
    """List linked children (and pending invite codes) for the parent"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsParent.check(request.user):
            return Response({'error': 'Not a parent'}, status=403)
        links = ParentChild.objects.filter(parent=request.user).select_related('child')
        # Return only linked children (child is not null) for the list; optionally include pending
        children_list = [link for link in links if link.child_id is not None]
        pending_list = [{'invite_code': link.invite_code} for link in links if link.child_id is None and link.invite_code]
        serializer = ParentChildSerializer(children_list, many=True)

        # Dashboard stats
        child_ids = [link.child_id for link in children_list]
        total_sessions_last_7_days = 0
        last_activity_at = None
        if child_ids:
            since = timezone.now() - timedelta(days=7)
            total_sessions_last_7_days = LearningSession.objects.filter(
                user_id__in=child_ids,
                start_time__gte=since,
            ).count()
            last_activity_at = LearningProfile.objects.filter(
                user_id__in=child_ids,
            ).aggregate(Max('last_active'))['last_active__max']

        stats = {
            'total_children': len(children_list),
            'total_sessions_last_7_days': total_sessions_last_7_days,
            'last_activity_at': last_activity_at.isoformat() if last_activity_at else None,
        }

        return Response({
            'children': serializer.data,
            'pending_invites': pending_list,
            'stats': stats,
        })


class ParentLinkChildView(APIView):
    """Parent generates an invite code to link a child. Creates ParentChild with child=null, invite_code set."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not IsParent.check(request.user):
            return Response({'error': 'Not a parent'}, status=403)
        code = secrets.token_hex(4).upper()[:8]  # 8-char code
        link = ParentChild.objects.create(parent=request.user, invite_code=code)
        return Response({'invite_code': code, 'message': 'Share this code with your child to link their account.'}, status=status.HTTP_201_CREATED)


class ParentInviteCodeView(APIView):
    """Return current pending invite code for the parent (if any)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not IsParent.check(request.user):
            return Response({'error': 'Not a parent'}, status=403)
        pending = ParentChild.objects.filter(parent=request.user, child__isnull=True).exclude(invite_code__isnull=True).exclude(invite_code='').first()
        if pending:
            return Response({'invite_code': pending.invite_code})
        return Response({'invite_code': None})


class LinkParentView(APIView):
    """Student links their account to a parent using an invite code"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        invite_code = (request.data.get('invite_code') or '').strip().upper()
        if not invite_code:
            return Response({'error': 'invite_code required'}, status=400)
        try:
            link = ParentChild.objects.get(invite_code=invite_code)
        except ParentChild.DoesNotExist:
            return Response({'error': 'Invalid or expired invite code.'}, status=400)
        if link.child_id is not None:
            if link.child_id == request.user.id:
                return Response({'message': 'Already linked to this parent.'})
            return Response({'error': 'This code has already been used.'}, status=400)
        link.child = request.user
        link.linked_at = timezone.now()
        link.invite_code = None
        link.save()
        return Response({'message': 'Successfully linked to parent.'})


# ==================== PARENT ADAPTIVE INSIGHTS ====================

def _parent_pacing_message(pacing_value):
    """Turn pacing enum into parent-facing message."""
    if not pacing_value:
        return 'steady', 'The system is gathering information about your child\'s pace.'
    p = (pacing_value.value if hasattr(pacing_value, 'value') else pacing_value) or 'stay'
    messages = {
        'speed_up': ('speeding_up', 'The system is moving at a faster pace for your child.'),
        'stay': ('steady', 'The system is moving at a steady pace for your child.'),
        'slow_down': ('slowing_down', 'The system has slowed down a bit to reinforce recent topics.'),
        'sharp_slowdown': ('slowing_down', 'The system has slowed down to give extra practice where needed.'),
    }
    return messages.get(p, ('steady', 'The system is adapting to your child\'s learning speed.'))


class ParentChildInsightsView(APIView):
    """Adaptive Learning Insights for one linked child."""
    permission_classes = [IsAuthenticated]

    def get(self, request, child_id):
        if not IsParent.check(request.user):
            return Response({'error': 'Not a parent'}, status=403)
        if not ParentChild.objects.filter(parent=request.user, child_id=child_id).exists():
            return Response({'error': 'Child not found or not linked to you'}, status=404)
        try:
            child = User.objects.get(id=child_id)
        except User.DoesNotExist:
            return Response({'error': 'Child not found'}, status=404)

        # Child summary
        progress_records = StudentProgress.objects.filter(user=child).select_related('atom__concept')
        overall_mastery = 0.0
        if progress_records.exists():
            overall_mastery = round(
                sum(p.mastery_score for p in progress_records) / progress_records.count(), 3
            )
        try:
            total_xp = child.xp_profile.total_xp
        except Exception:
            total_xp = 0
        try:
            last_active = child.learning_profile.last_active
        except Exception:
            last_active = None

        child_summary = {
            'id': child.id,
            'name': child.get_full_name() or child.username,
            'username': child.username,
            'last_active': last_active.isoformat() if last_active else None,
            'total_xp': total_xp,
            'overall_mastery': overall_mastery,
        }

        # Current pacing: from most recent session's pacing_history
        recent_sessions = LearningSession.objects.filter(user=child).select_related('concept').order_by('-start_time')[:5]
        current_pacing_value = None
        for session in recent_sessions:
            sh = (session.session_data or {}).get('pacing_history', [])
            if sh:
                current_pacing_value = _normalize_pacing_value(sh[-1])
                break
        pacing_label, pacing_message = _parent_pacing_message(current_pacing_value)
        current_pacing = {'pacing': current_pacing_value or 'stay', 'label': pacing_label, 'message': pacing_message}

        # Recent sessions
        sessions = LearningSession.objects.filter(user=child).select_related('concept').order_by('-start_time')[:20]
        recent_sessions_data = [{
            'id': s.id,
            'concept': s.concept.name,
            'subject': s.concept.subject,
            'start_time': s.start_time.isoformat(),
            'end_time': s.end_time.isoformat() if s.end_time else None,
            'questions_answered': s.questions_answered,
            'correct_answers': s.correct_answers,
            'accuracy': round(s.correct_answers / s.questions_answered, 2) if s.questions_answered > 0 else 0,
            'fatigue_level': s.fatigue_level,
            'engagement_score': s.engagement_score,
        } for s in sessions]

        # Mastery by concept/atom
        concepts_data = {}
        for p in progress_records:
            c = p.atom.concept
            if c.name not in concepts_data:
                concepts_data[c.name] = {
                    'concept_id': c.id,
                    'concept_name': c.name,
                    'subject': c.subject,
                    'atoms': [],
                }
            concepts_data[c.name]['atoms'].append({
                'atom_id': p.atom.id,
                'atom_name': p.atom.name,
                'mastery_score': round(p.mastery_score, 3),
                'phase': p.phase,
                'last_practiced': p.last_practiced.isoformat() if p.last_practiced else None,
            })

        # Weak areas
        weak_areas = [{
            'atom_id': p.atom.id,
            'atom_name': p.atom.name,
            'concept_name': p.atom.concept.name,
            'mastery_score': round(p.mastery_score, 3),
        } for p in progress_records.filter(mastery_score__lt=0.5).select_related('atom__concept').order_by('mastery_score')[:15]]

        # Insight messages (rule-based)
        insights = []
        if progress_records.exists():
            concepts_started = set(p.atom.concept.name for p in progress_records)
            for cname in list(concepts_started)[:3]:
                crecords = progress_records.filter(atom__concept__name=cname)
                avg = sum(r.mastery_score for r in crecords) / crecords.count()
                pct = int(round(avg * 100))
                insights.append(f"Your child is learning {cname} at a steady pace; mastery is about {pct}%.")
            mastered = progress_records.filter(phase='complete').count()
            total = progress_records.count()
            if total > 0:
                insights.append(f"They've mastered {mastered} of {total} topics so far.")
        if recent_sessions:
            last_s = recent_sessions[0]
            if last_s.questions_answered > 0:
                acc = int(round(100 * last_s.correct_answers / last_s.questions_answered))
                insights.append(f"Recent quiz accuracy in {last_s.concept.name} was {acc}%.")
            if getattr(last_s, 'fatigue_level', None) and last_s.fatigue_level not in ('fresh', 'mild', ''):
                insights.append("The system suggested a break during the last session (fatigue).")
        if weak_areas:
            names = [w['atom_name'] for w in weak_areas[:3]]
            insights.append(f"Extra practice recommended for: {', '.join(names)}.")
        if not insights:
            insights.append("Your child hasn't started any topics yet. Once they do, you'll see insights here.")

        # Optional: velocity snapshot (simple trend from session or progress)
        velocity_snapshots = []
        for s in sessions[:10]:
            vd = getattr(s, 'velocity_data', None) or []
            if vd:
                for entry in (vd[-3:] if isinstance(vd, list) else []):
                    if isinstance(entry, dict) and 'timestamp' in entry:
                        velocity_snapshots.append({'date': entry.get('timestamp'), 'value': entry.get('value')})
                    elif isinstance(entry, (int, float)):
                        velocity_snapshots.append({'date': s.start_time.isoformat(), 'value': entry})
        velocity_snapshots = velocity_snapshots[:10]

        # Weekly summary (last 7 days)
        since_7d = timezone.now() - timedelta(days=7)
        sessions_last_7 = LearningSession.objects.filter(
            user=child,
            start_time__gte=since_7d,
        ).count()
        weekly_summary = {
            'sessions_count': sessions_last_7,
            'summary': f"{sessions_last_7} session(s) in the last 7 days. Overall mastery: {int(round(overall_mastery * 100))}%.",
        }

        return Response({
            'child_summary': child_summary,
            'current_pacing': current_pacing,
            'recent_sessions': recent_sessions_data,
            'mastery_by_concept': list(concepts_data.values()),
            'weak_areas': weak_areas,
            'insight_messages': insights,
            'velocity_snapshots': velocity_snapshots,
            'weekly_summary': weekly_summary,
        })




class LearningCalendarView(APIView):
    """GET learning calendar for a month: sessions per day, review_due, suggested, streak_days."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now().date()
        try:
            year = int(request.query_params.get('year', now.year))
            month = int(request.query_params.get('month', now.month))
        except (TypeError, ValueError):
            year, month = now.year, now.month
        if month < 1 or month > 12:
            year, month = now.year, now.month
        first_day = date(year, month, 1)
        last_day = date(year, month, cal_module.monthrange(year, month)[1])

        user = request.user
        days = {}

        # Sessions in range: group by start_time date
        sessions = LearningSession.objects.filter(
            user=user,
            start_time__date__gte=first_day,
            start_time__date__lte=last_day,
        ).select_related('concept').order_by('start_time')

        streak_days = []
        for s in sessions:
            d = s.start_time.date()
            key = d.isoformat()
            if key not in streak_days:
                streak_days.append(key)
            if key not in days:
                days[key] = {'sessions': [], 'review_due': [], 'suggested': []}
            duration_mins = None
            if s.end_time and s.start_time:
                duration_mins = round((s.end_time - s.start_time).total_seconds() / 60, 1)
            days[key]['sessions'].append({
                'id': s.id,
                'concept_id': s.concept_id,
                'concept_name': s.concept.name,
                'subject': s.concept.subject,
                'start_time': s.start_time.isoformat(),
                'end_time': s.end_time.isoformat() if s.end_time else None,
                'questions_answered': s.questions_answered,
                'correct_answers': s.correct_answers,
                'duration_mins': duration_mins,
                'accuracy': round(s.correct_answers / s.questions_answered, 2) if s.questions_answered > 0 else 0,
            })

        # Review due: StudentProgress with next_review_at in range
        review_progress = StudentProgress.objects.filter(
            user=user,
            next_review_at__isnull=False,
            next_review_at__date__gte=first_day,
            next_review_at__date__lte=last_day,
        ).select_related('atom__concept')

        for p in review_progress:
            key = p.next_review_at.date().isoformat()
            if key not in days:
                days[key] = {'sessions': [], 'review_due': [], 'suggested': []}
            days[key]['review_due'].append({
                'atom_id': p.atom_id,
                'atom_name': p.atom.name,
                'concept_name': p.atom.concept.name,
                'concept_id': p.atom.concept_id,
                'mastery_score': round(p.mastery_score, 3),
            })
            days[key]['suggested'].append({
                'atom_id': p.atom_id,
                'atom_name': p.atom.name,
                'concept_name': p.atom.concept.name,
                'concept_id': p.atom.concept_id,
                'reason': 'review_due',
            })

        # Suggested "continue": atoms in practice/teaching for today
        today_key = now.isoformat()
        if first_day <= now <= last_day:
            continue_progress = StudentProgress.objects.filter(
                user=user,
                phase__in=('practice', 'teaching'),
                atom__concept__isnull=False,
            ).select_related('atom__concept').order_by('mastery_score', 'last_practiced')[:5]
            if today_key not in days:
                days[today_key] = {'sessions': [], 'review_due': [], 'suggested': []}
            for p in continue_progress:
                days[today_key]['suggested'].append({
                    'atom_id': p.atom_id,
                    'atom_name': p.atom.name,
                    'concept_name': p.atom.concept.name,
                    'concept_id': p.atom.concept_id,
                    'reason': 'continue',
                })

        # Streak: consecutive days with at least one session ending today
        distinct_dates_set = set(
            LearningSession.objects.filter(
                user=user,
                start_time__date__lte=now,
            ).values_list('start_time__date', flat=True).distinct()
        )
        streak_count = 0
        d = now
        while d in distinct_dates_set:
            streak_count += 1
            d -= timedelta(days=1)

        # This week summary (Mon–Sun)
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=6)
        sessions_this_week = LearningSession.objects.filter(
            user=user,
            start_time__date__gte=week_start,
            start_time__date__lte=week_end,
        ).count()
        review_due_this_week = StudentProgress.objects.filter(
            user=user,
            next_review_at__isnull=False,
            next_review_at__date__gte=week_start,
            next_review_at__date__lte=week_end,
        ).count()
        continue_today = StudentProgress.objects.filter(
            user=user,
            phase__in=('practice', 'teaching'),
            atom__concept__isnull=False,
        ).count() if now <= week_end else 0
        suggested_this_week = review_due_this_week + (continue_today if week_start <= now <= week_end else 0)
        this_week_summary = {
            'sessions': sessions_this_week,
            'suggested': suggested_this_week,
        }

        return Response({
            'year': year,
            'month': month,
            'days': days,
            'streak_days': streak_days,
            'streak_count': streak_count,
            'this_week_summary': this_week_summary,
        })
    
    
    # Planner View

class CreateStudyPlannerView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            data = request.data
            
            # Create the planner
            planner = StudyPlanner.objects.create(
                user=request.user,
                goal_type=data.get('goal_type', 'study'),
                day_option=data.get('day_option', 'mon_fri'),
                free_hours_per_day=data.get('free_hours_per_day', 2)
            )
            
            # Add subjects and generate topics for each
            subjects_data = data.get('subjects', [])
            subjects_with_topics = []
            
            for subject_data in subjects_data:
                subject_name = subject_data.get('subject_name')
                priority = subject_data.get('priority', 1)
                
                # Create the subject
                planner_subject = PlannerSubject.objects.create(
                    planner=planner,
                    subject_name=subject_name,
                    priority=priority
                )
                
                # Generate AI topics for this subject
                topics = generate_subtopics(
                    subject=subject_name,
                    goal=data.get('goal_type', 'study'),
                    num_topics=8  # Generate 8 topics per subject
                )
                
                subjects_with_topics.append({
                    "subject_name": subject_name,
                    "topics": topics,
                    "priority": priority
                })
            
            # Distribute topics across days
            schedule = distribute_topics(planner, subjects_with_topics)
            
            # Convert schedule to timetable format for storage
            timetable = {}
            for day_schedule in schedule:
                day_name = day_schedule['day']
                timetable[day_name] = []
                for session in day_schedule['sessions']:
                    timetable[day_name].append({
                        "hour": len(timetable[day_name]) + 1,
                        "subject": session['subject'],
                        "topic": session['topic'],
                        "hours": session['hours'],
                        "status": "pending"
                    })
            
            # Save the timetable
            planner.timetable = timetable
            planner.save()
            
            # Return the created planner with topics
            response_data = {
                'id': planner.id,
                'goal_type': planner.goal_type,
                'day_option': planner.day_option,
                'free_hours_per_day': planner.free_hours_per_day,
                'created_at': planner.created_at,
                'subjects': subjects_with_topics,
                'timetable': timetable
            }
            
            return Response(response_data, status=201)
            
        except Exception as e:
            print(f"Error creating planner: {str(e)}")
            return Response({'error': str(e)}, status=500)

# backend/accounts/views.py - Add this view

class TodayStudyView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            planner_id = request.query_params.get('planner_id')
            if not planner_id:
                return Response({'error': 'Planner ID required'}, status=400)
            
            # Get the planner
            planner = StudyPlanner.objects.get(id=planner_id, user=request.user)
            
            # Get today's day name
            today = datetime.now().strftime('%A')
            
            # Get today's schedule from planner timetable
            timetable = planner.timetable or {}
            today_schedule = timetable.get(today, [])
            
            # Build subjects with topics
            subjects = {}
            completed_subjects = {}
            total_topics = 0
            completed_topics = 0
            
            for session in today_schedule:
                subject_name = session.get('subject')
                topic_name = session.get('topic', f"Study {subject_name}")
                hour = session.get('hour')
                
                if subject_name not in subjects:
                    subjects[subject_name] = []
                
                # Check if this topic is completed
                is_completed = False  # You can track this in a separate model
                
                subjects[subject_name].append({
                    'id': hash(f"{subject_name}_{topic_name}") % 10000,  # Temporary ID
                    'name': topic_name,
                    'description': f"Study {topic_name}",
                    'difficulty': 'medium',  # Default
                    'estimated_time': session.get('hours', 1) * 60,  # Convert to minutes
                    'completed': is_completed,
                    'concept_id': hour,  # Use hour as temporary concept_id
                })
                
                total_topics += 1
                if is_completed:
                    completed_topics += 1
                    
                # Track completed hours
                if is_completed:
                    if subject_name not in completed_subjects:
                        completed_subjects[subject_name] = []
                    completed_subjects[subject_name].append(hour)
            
            response_data = {
                'total_topics': total_topics,
                'completed_topics': completed_topics,
                'completed_subjects': completed_subjects,
                'subjects': subjects,
                'date': today,
                'planner_id': planner.id,
                'schedule': today_schedule
            }
            
            return Response(response_data)
            
        except StudyPlanner.DoesNotExist:
            return Response({'error': 'Planner not found'}, status=404)
        except Exception as e:
            print(f"Error in TodayStudyView: {str(e)}")
            return Response({'error': str(e)}, status=500)

        
class GetMyPlannerView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        planner = StudyPlanner.objects.filter(user=request.user).first()

        if not planner:
            return Response({"message": "No planner found"}, status=404)

        return Response({
            "goal_type": planner.goal_type,
            "day_option": planner.day_option,
            "free_hours_per_day": planner.free_hours_per_day,
            "timetable": planner.timetable
        })
