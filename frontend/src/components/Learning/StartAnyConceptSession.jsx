import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useLearning } from '../../context/LearningContext';
import axios from '../../axiosConfig';

/* ─── vast local subject list (no API needed) ─── */
const ALL_SUBJECTS = [
    // CS & IT
    "Computer Science", "Data Structures", "Algorithms", "Operating Systems",
    "Database Management", "DBMS", "Computer Networks", "Compiler Design",
    "Theory of Computation", "Computer Architecture", "Computer Organization",
    "Software Engineering", "Object Oriented Programming", "OOP",
    "Computer Graphics", "Distributed Systems", "Parallel Computing",
    "System Design", "Design Patterns", "API Design",
    // Programming
    "Python Programming", "Java Programming", "C Programming",
    "C++ Programming", "JavaScript", "TypeScript", "Rust Programming",
    "Go Programming", "Kotlin Programming", "Swift Programming",
    "Ruby Programming", "PHP Programming", "R Programming",
    "Scala Programming", "Haskell", "Assembly Language", "SQL", "Shell Scripting", "MATLAB",
    // Web & Mobile
    "Web Development", "Frontend Development", "Backend Development",
    "Full Stack Development", "React", "Angular", "Vue.js", "Next.js",
    "Node.js", "Django", "Flask", "Spring Boot", "Express.js",
    "HTML and CSS", "REST API", "GraphQL", "WebSockets",
    "Mobile App Development", "Android Development", "iOS Development",
    "React Native", "Flutter", "Progressive Web Apps",
    // AI / ML / Data
    "Machine Learning", "Artificial Intelligence", "Deep Learning",
    "Natural Language Processing", "Computer Vision", "Reinforcement Learning",
    "Neural Networks", "Data Science", "Data Analytics", "Big Data",
    "Data Mining", "Data Engineering", "MLOps",
    "Generative AI", "Large Language Models", "Prompt Engineering",
    "TensorFlow", "PyTorch", "Scikit-learn",
    // Cloud & DevOps
    "Cloud Computing", "AWS", "Microsoft Azure", "Google Cloud Platform",
    "Docker", "Kubernetes", "DevOps", "CI/CD",
    "Terraform", "Ansible", "Jenkins", "Linux Administration",
    "Microservices Architecture", "Serverless Computing",
    // Cyber Security
    "Cyber Security", "Ethical Hacking", "Penetration Testing",
    "Cryptography", "Network Security", "Information Security",
    "Web Security", "Digital Forensics",
    // Networking & Hardware
    "Networking", "Embedded Systems", "Internet of Things", "IoT",
    "Microprocessor", "Microcontroller", "Digital Electronics",
    "Analog Electronics", "Signal Processing", "VLSI Design",
    "Communication Systems", "Control Systems",
    "Power Electronics", "Electrical Machines",
    // Mathematics
    "Mathematics", "Calculus", "Linear Algebra", "Discrete Mathematics",
    "Probability", "Statistics", "Number Theory", "Real Analysis",
    "Complex Analysis", "Abstract Algebra", "Topology",
    "Differential Equations", "Numerical Methods", "Mathematical Logic",
    "Graph Theory", "Combinatorics", "Optimization",
    "Operations Research", "Game Theory", "Stochastic Processes",
    // Physics
    "Physics", "Classical Mechanics", "Quantum Mechanics",
    "Thermodynamics", "Electromagnetism", "Optics",
    "Nuclear Physics", "Astrophysics", "Relativity",
    "Solid State Physics", "Fluid Mechanics", "Nanotechnology",
    // Chemistry
    "Chemistry", "Organic Chemistry", "Inorganic Chemistry",
    "Physical Chemistry", "Analytical Chemistry", "Biochemistry",
    "Polymer Chemistry", "Electrochemistry", "Spectroscopy",
    // Biology
    "Biology", "Cell Biology", "Molecular Biology", "Genetics",
    "Microbiology", "Biotechnology", "Bioinformatics",
    "Ecology", "Zoology", "Botany", "Human Anatomy",
    "Physiology", "Immunology", "Neuroscience",
    // Engineering
    "Electrical Engineering", "Mechanical Engineering",
    "Civil Engineering", "Electronics Engineering",
    "Chemical Engineering", "Aerospace Engineering",
    "Biomedical Engineering", "Industrial Engineering",
    "Environmental Engineering", "Materials Science",
    "Structural Analysis", "Strength of Materials", "Engineering Mechanics",
    // Emerging Tech
    "Blockchain", "Cryptocurrency", "Smart Contracts", "Web3",
    "Quantum Computing", "Augmented Reality", "Virtual Reality",
    "3D Printing", "Robotics", "Drone Technology",
    // Business
    "Economics", "Microeconomics", "Macroeconomics",
    "Business Analytics", "Financial Accounting",
    "Marketing", "Digital Marketing", "Entrepreneurship",
    "Project Management", "Supply Chain Management",
    "Stock Market", "Investment Banking",
    // Social Sciences
    "Psychology", "Sociology", "Philosophy",
    "Political Science", "History", "Geography",
    "English Literature", "Creative Writing", "Journalism",
    // Tools & DBs
    "Power BI", "Tableau", "Git", "MongoDB", "PostgreSQL", "Redis",
    "Elasticsearch", "Apache Spark", "Hadoop", "Kafka",
    // Testing
    "Software Testing", "Automation Testing", "Selenium",
    "Test Driven Development", "Agile Methodology", "Scrum",
    // Competitive
    "Competitive Programming", "Data Structures and Algorithms",
    "Aptitude and Reasoning", "Logical Reasoning", "Quantitative Aptitude",
];

/* ─── tiny debounce helper ─── */
function useDebounce(value, delay = 300) {
    const [debounced, setDebounced] = useState(value);
    useEffect(() => {
        const t = setTimeout(() => setDebounced(value), delay);
        return () => clearTimeout(t);
    }, [value, delay]);
    return debounced;
}

/* ─── reusable autocomplete dropdown ─── */
const SuggestionDropdown = ({ suggestions, loading, visible, onSelect, highlightIndex }) => {
    if (!visible || (!loading && suggestions.length === 0)) return null;
    return (
        <div className="absolute z-50 left-0 right-0 mt-1 max-h-56 overflow-y-auto bg-surface border border-theme-border rounded-theme-lg shadow-theme-lg animate-fade-in-up">
            {loading ? (
                <div className="px-4 py-3 text-sm text-theme-text-muted flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4 text-primary" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                    </svg>
                    Loading suggestions…
                </div>
            ) : (
                suggestions.map((item, idx) => (
                    <button
                        key={item}
                        type="button"
                        onMouseDown={(e) => { e.preventDefault(); onSelect(item); }}
                        className={`w-full text-left px-4 py-2.5 text-sm transition-colors ${
                            idx === highlightIndex
                                ? 'bg-primary/15 text-primary font-medium'
                                : 'text-theme-text hover:bg-primary/10'
                        }`}
                    >
                        {item}
                    </button>
                ))
            )}
        </div>
    );
};

const StartAnyConceptSession = () => {
    const location = useLocation();
    const [formData, setFormData] = useState({
        subject: '',
        concept: '',
        knowledge_level: 'intermediate'
    });
    // Autofill subject/concept if passed from navigation state
    useEffect(() => {
        if (location.state) {
            setFormData(prev => ({
                ...prev,
                subject: location.state.subject || prev.subject,
                concept: location.state.topic || prev.concept
            }));
        }
    }, [location.state]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [generatedAtoms, setGeneratedAtoms] = useState(null);

    /* ─── suggestion state ─── */
    const [subjectSuggestions, setSubjectSuggestions] = useState([]);
    const [conceptSuggestions, setConceptSuggestions] = useState([]);
    const [subjectLoading, setSubjectLoading] = useState(false);
    const [conceptLoading, setConceptLoading] = useState(false);
    const [showSubjectDropdown, setShowSubjectDropdown] = useState(false);
    const [showConceptDropdown, setShowConceptDropdown] = useState(false);
    const [subjectHighlight, setSubjectHighlight] = useState(-1);
    const [conceptHighlight, setConceptHighlight] = useState(-1);

    const subjectRef = useRef(null);
    const conceptRef = useRef(null);

    const debouncedConcept = useDebounce(formData.concept, 500);

    const navigate = useNavigate();
    const { generateConcept } = useLearning();

    /* ─── AbortController ref for concept requests only ─── */
    const conceptAbort = useRef(null);

    /* ─── subject suggestions — purely local, instant filtering ─── */
    const filteredSubjects = useMemo(() => {
        const q = formData.subject.trim().toLowerCase();
        if (!q) return ALL_SUBJECTS.slice(0, 20);
        return ALL_SUBJECTS.filter(s => s.toLowerCase().includes(q)).slice(0, 20);
    }, [formData.subject]);

    // Update subject suggestions whenever the filter changes
    useEffect(() => {
        setSubjectSuggestions(filteredSubjects);
    }, [filteredSubjects]);

    /* ─── fetch concept suggestions only after complete word or on subject change ─── */
    useEffect(() => {
        if (!formData.subject.trim()) {
            setConceptSuggestions([]);
            return;
        }
        const trimmedQ = debouncedConcept.trim();
        // Only call API if: query is empty (show base list), OR ends with a space (word complete)
        const endsWithSpace = debouncedConcept.length > 0 && debouncedConcept.endsWith(' ');
        if (trimmedQ.length > 0 && !endsWithSpace) return;

        conceptAbort.current?.abort();
        const controller = new AbortController();
        conceptAbort.current = controller;

        const fetchConcepts = async () => {
            setConceptLoading(true);
            try {
                const res = await axios.get('/auth/api/suggest-concepts/', {
                    params: { subject: formData.subject, q: trimmedQ },
                    signal: controller.signal,
                });
                setConceptSuggestions(res.data.suggestions || []);
            } catch (err) {
                if (!axios.isCancel?.(err) && err?.name !== 'CanceledError') {
                    setConceptSuggestions([]);
                }
            }
            if (!controller.signal.aborted) setConceptLoading(false);
        };
        fetchConcepts();

        return () => controller.abort();
    }, [formData.subject, debouncedConcept]);

    /* ─── keyboard navigation ─── */
    const handleKeyDown = useCallback((e, suggestions, highlightIdx, setHighlight, onSelect, setShow) => {
        if (!suggestions.length) return;
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setHighlight(prev => Math.min(prev + 1, suggestions.length - 1));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setHighlight(prev => Math.max(prev - 1, 0));
        } else if (e.key === 'Enter' && highlightIdx >= 0 && highlightIdx < suggestions.length) {
            e.preventDefault();
            onSelect(suggestions[highlightIdx]);
            setShow(false);
        } else if (e.key === 'Escape') {
            setShow(false);
        }
    }, []);

    const handleChange = (e) => {
        const { name, value } = e.target;
        if (name === 'subject') {
            setFormData(prev => ({ ...prev, subject: value, concept: '' }));
            setShowSubjectDropdown(true);
            setSubjectHighlight(-1);
            setConceptSuggestions([]);
        } else if (name === 'concept') {
            setFormData(prev => ({ ...prev, concept: value }));
            setShowConceptDropdown(true);
            setConceptHighlight(-1);
        } else {
            setFormData(prev => ({ ...prev, [name]: value }));
        }
    };

    const selectSubject = (val) => {
        setFormData(prev => ({ ...prev, subject: val, concept: '' }));
        setShowSubjectDropdown(false);
        setSubjectHighlight(-1);
        setTimeout(() => conceptRef.current?.focus(), 100);
    };

    const selectConcept = (val) => {
        setFormData(prev => ({ ...prev, concept: val }));
        setShowConceptDropdown(false);
        setConceptHighlight(-1);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const result = await generateConcept(
            formData.subject,
            formData.concept,
            formData.knowledge_level
        );

        if (result.success) {
            setGeneratedAtoms(result.data);
        } else {
            setError(result.error || 'Failed to generate concept');
        }
        setLoading(false);
    };

    const handleStartLearning = () => {
        if (generatedAtoms) {
            navigate(`/learn/${generatedAtoms.concept_id}`, {
                state: { knowledge_level: formData.knowledge_level }
            });
        }
    };

    const knowledgeLevels = [
        { value: 'zero', label: 'Zero Knowledge (Complete Beginner)' },
        { value: 'beginner', label: 'Beginner (Some basic understanding)' },
        { value: 'intermediate', label: 'Intermediate (Comfortable with basics)' },
        { value: 'advanced', label: 'Advanced (Strong understanding)' }
    ];

    return (
        <div className="min-h-screen bg-theme-bg py-12">
            <div className="max-w-2xl mx-auto px-4">
                <div className="bg-surface rounded-theme-xl shadow-theme-lg border border-theme-border p-8 animate-fade-in-up">
                    <h1 className="text-2xl font-bold text-theme-text mb-6">
                        Start New Learning Session
                    </h1>

                    {!generatedAtoms ? (
                        <form onSubmit={handleSubmit} className="space-y-6">
                            {/* ── Subject with autocomplete ── */}
                            <div className="relative">
                                <label className="block text-sm font-medium text-theme-text-secondary mb-2">
                                    Subject *
                                </label>
                                <input
                                    ref={subjectRef}
                                    type="text"
                                    name="subject"
                                    value={formData.subject}
                                    onChange={handleChange}
                                    onFocus={() => setShowSubjectDropdown(true)}
                                    onBlur={() => setTimeout(() => setShowSubjectDropdown(false), 200)}
                                    onKeyDown={(e) => handleKeyDown(e, subjectSuggestions, subjectHighlight, setSubjectHighlight, selectSubject, setShowSubjectDropdown)}
                                    required
                                    autoComplete="off"
                                    placeholder="e.g., Microprocessor, Mathematics, Physics"
                                    className="w-full px-4 py-2 bg-theme-bg border border-theme-border rounded-theme-lg focus:ring-2 focus:ring-primary/50 focus:border-primary text-theme-text placeholder:text-theme-text-muted transition-colors"
                                    readOnly={!!location.state && !!location.state.subject}
                                />
                                <SuggestionDropdown
                                    suggestions={subjectSuggestions}
                                    loading={subjectLoading}
                                    visible={showSubjectDropdown}
                                    onSelect={selectSubject}
                                    highlightIndex={subjectHighlight}
                                />
                            </div>

                            {/* ── Concept with autocomplete ── */}
                            <div className="relative">
                                <label className="block text-sm font-medium text-theme-text-secondary mb-2">
                                    Concept *
                                </label>
                                <input
                                    ref={conceptRef}
                                    type="text"
                                    name="concept"
                                    value={formData.concept}
                                    onChange={handleChange}
                                    onFocus={() => { if (formData.subject.trim()) setShowConceptDropdown(true); }}
                                    onBlur={() => setTimeout(() => setShowConceptDropdown(false), 200)}
                                    onKeyDown={(e) => handleKeyDown(e, conceptSuggestions, conceptHighlight, setConceptHighlight, selectConcept, setShowConceptDropdown)}
                                    required
                                    autoComplete="off"
                                    placeholder={formData.subject ? `Concepts in ${formData.subject}…` : 'Enter a subject first'}
                                    disabled={!formData.subject.trim()}
                                    className="w-full px-4 py-2 bg-theme-bg border border-theme-border rounded-theme-lg focus:ring-2 focus:ring-primary/50 focus:border-primary text-theme-text placeholder:text-theme-text-muted transition-colors disabled:opacity-50"
                                    // placeholder="e.g., Memory Organization, Calculus, Quantum Mechanics"
                                    // className="w-full px-4 py-2 bg-theme-bg border border-theme-border rounded-theme-lg focus:ring-2 focus:ring-primary/50 focus:border-primary text-theme-text placeholder:text-theme-text-muted transition-colors"
                                    readOnly={!!location.state && !!location.state.topic}
                                />
                                {formData.subject.trim() && (
                                    <SuggestionDropdown
                                        suggestions={conceptSuggestions}
                                        loading={conceptLoading}
                                        visible={showConceptDropdown}
                                        onSelect={selectConcept}
                                        highlightIndex={conceptHighlight}
                                    />
                                )}
                                {!formData.subject.trim() && (
                                    <p className="text-xs text-theme-text-muted mt-1">
                                        Type a subject above to see concept suggestions
                                    </p>
                                )}
                            </div>

                            {/* Knowledge Level */}
                            <div>
                                <label className="block text-sm font-medium text-theme-text-secondary mb-2">
                                    Your Knowledge Level *
                                </label>
                                <select
                                    name="knowledge_level"
                                    value={formData.knowledge_level}
                                    onChange={handleChange}
                                    className="w-full px-4 py-2 bg-theme-bg border border-theme-border rounded-theme-lg focus:ring-2 focus:ring-primary/50 focus:border-primary text-theme-text transition-colors"
                                >
                                    {knowledgeLevels.map(level => (
                                        <option key={level.value} value={level.value}>
                                            {level.label}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {error && (
                                <div className="bg-error/10 border border-error/30 text-error px-4 py-3 rounded-theme-lg">
                                    {error}
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full gradient-primary text-white font-bold py-3 px-4 rounded-theme-lg hover:shadow-theme-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? 'Generating atoms...' : 'Generate Learning Path'}
                            </button>

                            <button
                                type="button"
                                onClick={() => navigate('/dashboard')}
                                className="w-full bg-theme-bg hover:bg-theme-border text-theme-text-secondary font-bold py-3 px-4 rounded-theme-lg transition-colors"
                            >
                                Back to Dashboard
                            </button>
                        </form>
                    ) : (
                        <div className="space-y-6">
                            {/* Success message */}
                            <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-theme-lg p-6">
                                <h3 className="text-lg font-semibold text-emerald-600 dark:text-emerald-400 mb-2">
                                    ✓ Learning Path Generated!
                                </h3>
                                <p className="text-emerald-600 dark:text-emerald-400">
                                    We've created {generatedAtoms.atoms.length} atomic concepts for "{generatedAtoms.concept_name}".
                                </p>
                            </div>

                            {/* Atoms list */}
                            <div>
                                <h4 className="font-medium text-theme-text-secondary mb-3">Atomic Concepts:</h4>
                                <div className="space-y-2">
                                    {generatedAtoms.atoms.map((atom, index) => (
                                        <div
                                            key={atom.id}
                                            className="flex items-center p-3 bg-theme-bg rounded-theme-lg"
                                        >
                                            <span className="w-8 h-8 bg-primary/10 text-primary rounded-full flex items-center justify-center font-bold mr-3">
                                                {index + 1}
                                            </span>
                                            <span className="text-theme-text">{atom.name}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Start learning button */}
                            <button
                                onClick={handleStartLearning}
                                className="w-full bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-3 px-4 rounded-theme-lg transition-colors"
                            >
                                Start Learning Now
                            </button>

                            {/* Note */}
                            <p className="text-sm text-theme-text-muted text-center">
                                You'll learn each concept one by one, with teaching followed by assessment.
                            </p>
                        </div>
                    )}
                </div>
            </div>

        </div>
    );
};

export default StartAnyConceptSession;