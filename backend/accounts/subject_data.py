# ─────────────────────────────────────────────────────────────────────
#  Curated subject list & subject → concept mappings
#  Used by SuggestSubjectsView and SuggestConceptsView in views.py
# ─────────────────────────────────────────────────────────────────────

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

# ─── Concept maps for every subject (offline, zero API calls) ───
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
