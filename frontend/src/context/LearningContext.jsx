// frontend/src/context/LearningContext.jsx - Enhanced version

import React, { createContext, useCallback, useMemo, useState, useContext, useRef } from 'react';
import axios from '../axiosConfig';

const LearningContext = createContext(null);

export const LearningProvider = ({ children }) => {
    const [currentSession, setCurrentSession] = useState(null);
    const [currentAtom, setCurrentAtom] = useState(null);
    const [learningProgress, setLearningProgress] = useState(null);
    const [loading, setLoading] = useState(false);
    const [knowledgeLevel, setKnowledgeLevel] = useState('intermediate');
    
    // Real-time tracking
    const [currentQuestions, setCurrentQuestions] = useState([]);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [answers, setAnswers] = useState([]);
    const [atomMastery, setAtomMastery] = useState(0.0);
    const [currentTheta, setCurrentTheta] = useState(0.0);
    const [pacingDecision, setPacingDecision] = useState('stay');
    const [nextAction, setNextAction] = useState('continue_practice');
    const [showTeaching, setShowTeaching] = useState(false);
    const [teachingContent, setTeachingContent] = useState(null);
    const [metrics, setMetrics] = useState({});

    // Enhanced pacing engine state
    const [fatigueLevel, setFatigueLevel] = useState('fresh');
    const [velocityData, setVelocityData] = useState([]);
    const [retentionAction, setRetentionAction] = useState(null);
    const [hintWarning, setHintWarning] = useState(null);
    const [engagementScore, setEngagementScore] = useState(0.7);
    const [masteryVerdict, setMasteryVerdict] = useState(null);
    const [showBreakModal, setShowBreakModal] = useState(false);

    // Cognitive load and session-shape (live)
    const [cognitiveLoadScore, setCognitiveLoadScore] = useState(0);
    const [sessionShapeAction, setSessionShapeAction] = useState('continue');
    const [sessionShapeMessage, setSessionShapeMessage] = useState('');

    // Adaptive flow state
    const [conceptOverview, setConceptOverview] = useState(null);
    const [atomSummaries, setAtomSummaries] = useState({});
    const [allAtomsMastery, setAllAtomsMastery] = useState(null);
    
    // Timers
    const questionStartTime = useRef(null);
    const [timeSpent, setTimeSpent] = useState(0);

    // Race-condition guard: track latest generation request
    const latestQuestionGenId = useRef(0);

    // Generate atoms for a concept (no questions)
    const generateConcept = useCallback(async (subject, concept, knowledgeLevel = 'intermediate') => {
        setLoading(true);
        try {
            const response = await axios.post('/auth/api/generate-concept/', {
                subject: subject,
                concept: concept,
                knowledge_level: knowledgeLevel
            });
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to generate concept'
            };
        } finally {
            setLoading(false);
        }
    }, []);

    // Start teaching session for a concept
    const startTeachingSession = useCallback(async (conceptId, level = 'intermediate') => {
        setLoading(true);
        setKnowledgeLevel(level);
        setAnswers([]);
        setAtomMastery(0.0);
        setPacingDecision('stay');
        
        try {
            const response = await axios.post('/auth/api/start-teaching-session/', {
                concept_id: conceptId,
                knowledge_level: level
            });
            
            setCurrentSession(response.data);
            
            // If there's a current atom, set it
            if (response.data.current_atom) {
                setCurrentAtom(response.data.current_atom);
            }
            
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to start session'
            };
        } finally {
            setLoading(false);
        }
    }, []);

    // Get teaching content for an atom
    const getTeachingContent = useCallback(async ({ session_id, atom_id }) => {
        setLoading(true);
        setShowTeaching(true);
        try {
            const response = await axios.post('/auth/api/teaching-content/', {
                session_id: session_id,
                atom_id: atom_id
            });

            // Normalize payload: backend may nest under teaching_content
            const raw = response.data?.teaching_content || response.data || {};
            const examples = Array.isArray(raw.examples) ? raw.examples : [];

            const normalized = {
                explanation: raw.explanation || '',
                example: raw.example || examples[0] || '',
                analogy: raw.analogy || '',
                misconception: raw.misconception || examples[2] || '',
                practical_application: raw.practical_application || examples[1] || '',
                examples: examples,
                videos: Array.isArray(response.data?.videos) ? response.data.videos : [],
                images: Array.isArray(response.data?.images) ? response.data.images : [],
            };

            setTeachingContent(normalized);
            setCurrentAtom({
                id: atom_id,
                name: response.data?.atom_name || response.data?.name || raw.atom_name || raw.name,
            });

            // Sync mastery from backend so new atoms start at their real value
            if (response.data?.mastery_score !== undefined) {
                setAtomMastery(response.data.mastery_score);
            }
            
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to get teaching content'
            };
        } finally {
            setLoading(false);
        }
    }, []);

    // Generate questions based on teaching content
    const generateQuestionsFromTeaching = useCallback(async ({ session_id, atom_id, force_new = false }) => {
        setLoading(true);
        const requestId = ++latestQuestionGenId.current;
        try {
            const response = await axios.post('/auth/api/generate-questions-from-teaching/', {
                session_id: session_id,
                atom_id: atom_id,
                force_new: force_new
            });
            
            // Only apply state if this is still the latest request (prevents race condition)
            if (requestId === latestQuestionGenId.current) {
                setCurrentQuestions(response.data.questions || []);
                setCurrentQuestionIndex(0);
                
                // Start timer for first question
                questionStartTime.current = Date.now();
            }
            
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to generate questions'
            };
        } finally {
            if (requestId === latestQuestionGenId.current) {
                setLoading(false);
            }
        }
    }, []);

    // Generate initial diagnostic quiz
    const generateInitialQuiz = useCallback(async ({ session_id }) => {
        setLoading(true);
        try {
            const response = await axios.post('/auth/api/initial-quiz/', {
                session_id: session_id
            });
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to generate initial quiz'
            };
        } finally {
            setLoading(false);
        }
    }, []);

    const submitInitialQuizAnswer = useCallback(async ({ session_id, question_index, selected, time_taken }) => {
        try {
            const response = await axios.post('/auth/api/submit-initial-quiz-answer/', {
                session_id,
                question_index,
                selected,
                time_taken
            });

            const data = response.data;

            // Real-time mastery & theta update from initial quiz
            if (data.updated_mastery !== undefined) {
                setAtomMastery(data.updated_mastery);
            }
            if (data.updated_theta !== undefined) {
                setCurrentTheta(data.updated_theta);
            }

            return { success: true, data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to submit initial quiz answer'
            };
        }
    }, []);

    const completeInitialQuiz = useCallback(async ({ session_id }) => {
        try {
            const response = await axios.post('/auth/api/complete-initial-quiz/', {
                session_id
            });
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to complete initial quiz'
            };
        }
    }, []);

    const generateFinalChallenge = useCallback(async ({ session_id, atom_id }) => {
        setLoading(true);
        const requestId = ++latestQuestionGenId.current;
        try {
            const response = await axios.post('/auth/api/final-challenge/', {
                session_id,
                atom_id
            });
            if (requestId === latestQuestionGenId.current) {
                setCurrentQuestions(response.data.questions || []);
                setCurrentQuestionIndex(0);
                questionStartTime.current = Date.now();
            }
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to generate final challenge'
            };
        } finally {
            if (requestId === latestQuestionGenId.current) {
                setLoading(false);
            }
        }
    }, []);

    const completeFinalChallenge = useCallback(async ({ session_id, atom_id }) => {
        try {
            const response = await axios.post('/auth/api/complete-final-challenge/', {
                session_id,
                atom_id
            });
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to complete final challenge'
            };
        }
    }, []);

    // ── Concept Final Challenge ──

    const generateConceptFinalChallenge = useCallback(async ({ session_id, concept_id }) => {
        setLoading(true);
        const requestId = ++latestQuestionGenId.current;
        try {
            const response = await axios.post('/auth/api/concept-final-challenge/', {
                session_id,
                concept_id
            });
            if (requestId === latestQuestionGenId.current) {
                setCurrentQuestions(response.data.questions || []);
                setCurrentQuestionIndex(0);
                questionStartTime.current = Date.now();
            }
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to generate concept final challenge'
            };
        } finally {
            if (requestId === latestQuestionGenId.current) {
                setLoading(false);
            }
        }
    }, []);

    const submitConceptFinalAnswer = useCallback(async ({ session_id, question_index, selected, time_taken }) => {
        let timeTaken = time_taken;
        if (timeTaken === undefined && questionStartTime.current) {
            timeTaken = Math.round((Date.now() - questionStartTime.current) / 1000);
        } else if (timeTaken === undefined) {
            timeTaken = 30;
        }
        try {
            const response = await axios.post('/auth/api/submit-concept-final-answer/', {
                session_id,
                question_index,
                selected,
                time_taken: timeTaken
            });
            const data = response.data;
            const newAnswer = {
                question_index,
                selected,
                correct: data.correct,
                time_taken: timeTaken,
            };
            setAnswers(prev => [...prev, newAnswer]);
            return { success: true, data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to submit concept final answer'
            };
        }
    }, []);

    const completeConceptFinalChallenge = useCallback(async ({ session_id, concept_id }) => {
        try {
            const response = await axios.post('/auth/api/complete-concept-final-challenge/', {
                session_id,
                concept_id
            });
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to complete concept final challenge'
            };
        }
    }, []);

    // Submit answer for an atom question with REAL-TIME updates
    const submitAtomAnswer = useCallback(async ({ 
        session_id, 
        atom_id, 
        question_index, 
        selected,
        forceTimeTaken = null,
        question_set = 'teaching'
    }) => {
        // Calculate time taken if not provided
        let time_taken = forceTimeTaken;
        if (time_taken === null && questionStartTime.current) {
            time_taken = Math.round((Date.now() - questionStartTime.current) / 1000);
        } else if (time_taken === null) {
            time_taken = 30; // Default fallback
        }
        
        try {
            const response = await axios.post('/auth/api/submit-atom-answer/', {
                session_id: session_id,
                atom_id: atom_id,
                question_index: question_index,
                selected: selected,
                time_taken: time_taken,
                question_set: question_set
            });
            
            const data = response.data;
            
            // REAL-TIME UI UPDATES based on response
            setAtomMastery(data.updated_mastery);
            setCurrentTheta(data.updated_theta);
            setPacingDecision(data.pacing_decision);
            setNextAction(data.next_action);
            setMetrics(data.metrics || {});

            // Enhanced pacing engine updates
            const fatigueVal = data.fatigue;
            if (fatigueVal) setFatigueLevel(typeof fatigueVal === 'object' ? fatigueVal.level : fatigueVal);
            if (data.retention_action) setRetentionAction(data.retention_action);
            if (data.cognitive_load_score != null) setCognitiveLoadScore(data.cognitive_load_score);
            if (data.cognitive_load_action) setSessionShapeAction(data.cognitive_load_action);
            if (data.session_shape_message != null) setSessionShapeMessage(data.session_shape_message);
            if (data.hint_warning) setHintWarning(data.hint_warning);
            if (data.engagement_adjustment) setEngagementScore(data.engagement_adjustment.score ?? engagementScore);
            if (data.mastery_verdict) setMasteryVerdict(data.mastery_verdict);
            if (data.velocity_snapshot) setVelocityData(prev => [...prev, data.velocity_snapshot]);

            // Auto-show break modal on high fatigue
            if (data.fatigue === 'high' || data.fatigue === 'critical') {
                setShowBreakModal(true);
            }
            
            // Store answer
            const newAnswer = {
                question_index,
                selected,
                correct: data.correct,
                error_type: data.error_type,
                time_taken,
                mastery_after: data.updated_mastery,
                pacing_decision: data.pacing_decision
            };
            
            setAnswers(prev => [...prev, newAnswer]);
            
            // Check if atom is complete
            if (data.atom_complete) {
                // Move to next atom or show completion
                if (data.next_atom) {
                    setCurrentAtom(prev => ({
                        ...prev,
                        next_atom: data.next_atom
                    }));
                }
            }
            
            // Update session data with pacing info
            setCurrentSession(prev => {
                if (!prev) return prev;
                return {
                    ...prev,
                    last_pacing: data.pacing_decision,
                    current_mastery: data.updated_mastery,
                    current_theta: data.updated_theta
                };
            });
            
            return { success: true, data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to submit answer'
            };
        }
    }, []);

    // Start next question with timer
    const nextQuestion = useCallback(() => {
        if (currentQuestionIndex < currentQuestions.length - 1) {
            setCurrentQuestionIndex(prev => prev + 1);
            questionStartTime.current = Date.now();
        }
    }, [currentQuestionIndex, currentQuestions.length]);

    // Complete atom and determine next action
    const completeAtom = useCallback(async ({ session_id, atom_id, continue_learning }) => {
        try {
            const response = await axios.post('/auth/api/complete-atom/', {
                session_id: session_id,
                atom_id: atom_id,
                continue_learning: continue_learning
            });
            
            const data = response.data;

            // Sync mastery with backend's authoritative value
            if (data.metrics?.final_mastery !== undefined) {
                setAtomMastery(data.metrics.final_mastery);
            }
            
            // Handle next steps based on pacing
            if (data.next_action === 'next_atom' && data.next_atom) {
                setCurrentAtom(data.next_atom);
                setShowTeaching(true); // Show teaching for next atom
                setCurrentQuestions([]);
                setAnswers([]);
            } else if (data.concept_complete) {
                // All atoms complete
                setCurrentAtom(null);
                setCurrentSession(null);
            }
            
            return { success: true, data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to complete atom'
            };
        }
    }, []);

    // Load learning progress
    const loadLearningProgress = useCallback(async () => {
        setLoading(true);
        try {
            const response = await axios.get('/auth/api/progress/');
            setLearningProgress(response.data);
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to load progress'
            };
        } finally {
            setLoading(false);
        }
    }, []);

    // ── Enhanced pacing engine API methods ──

    const fetchVelocityGraph = useCallback(async (sessionId) => {
        try {
            const response = await axios.get('/auth/api/velocity-graph/', {
                params: { session_id: sessionId }
            });
            setVelocityData(response.data.session_velocity || []);
            setEngagementScore(response.data.engagement_score ?? 0.7);
            return { success: true, data: response.data };
        } catch (error) {
            return { success: false, error: error.response?.data?.error || 'Failed to fetch velocity' };
        }
    }, []);

    const fetchFatigueStatus = useCallback(async (sessionId) => {
        try {
            const response = await axios.get('/auth/api/fatigue-status/', {
                params: { session_id: sessionId }
            });
            setFatigueLevel(response.data.fatigue_level || 'fresh');
            return { success: true, data: response.data };
        } catch (error) {
            return { success: false, error: error.response?.data?.error || 'Failed to fetch fatigue' };
        }
    }, []);

    const recordBreak = useCallback(async (sessionId) => {
        try {
            const response = await axios.post('/auth/api/record-break/', {
                session_id: sessionId
            });
            setFatigueLevel('fresh');
            setShowBreakModal(false);
            return { success: true, data: response.data };
        } catch (error) {
            return { success: false, error: error.response?.data?.error || 'Failed to record break' };
        }
    }, []);

    const checkRetention = useCallback(async ({ session_id, atom_id, passed = null }) => {
        try {
            const response = await axios.post('/auth/api/retention-check/', {
                session_id, atom_id, passed
            });
            if (passed !== null) {
                setRetentionAction(null); // Clear after recording
            }
            return { success: true, data: response.data };
        } catch (error) {
            return { success: false, error: error.response?.data?.error || 'Failed retention check' };
        }
    }, []);

    const recordHint = useCallback(async ({ atom_id, hint_level = 1 }) => {
        try {
            const response = await axios.post('/auth/api/record-hint/', {
                atom_id, hint_level
            });
            setHintWarning(response.data.hint_warning);
            return { success: true, data: response.data };
        } catch (error) {
            return { success: false, error: error.response?.data?.error || 'Failed to record hint' };
        }
    }, []);

    // ── Adaptive flow API methods ──

    const generateConceptOverview = useCallback(async ({ session_id }) => {
        setLoading(true);
        try {
            const response = await axios.post('/auth/api/concept-overview/', {
                session_id
            });
            setConceptOverview(response.data.overview);
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to generate concept overview'
            };
        } finally {
            setLoading(false);
        }
    }, []);

    const generateAtomSummary = useCallback(async ({ session_id, atom_id }) => {
        setLoading(true);
        try {
            const response = await axios.post('/auth/api/atom-summary/', {
                session_id,
                atom_id
            });
            const summary = response.data.summary;
            setAtomSummaries(prev => ({ ...prev, [atom_id]: summary }));
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to generate atom summary'
            };
        } finally {
            setLoading(false);
        }
    }, []);

    const adaptiveReteach = useCallback(async ({ session_id, atom_id }) => {
        setLoading(true);
        try {
            const response = await axios.post('/auth/api/adaptive-reteach/', {
                session_id,
                atom_id
            });
            // Update teaching content with reteach content
            const raw = response.data?.teaching_content || {};
            const examples = Array.isArray(raw.examples) ? raw.examples : [];
            const normalized = {
                explanation: raw.explanation || '',
                example: raw.example || examples[0] || '',
                analogy: raw.analogy || '',
                misconception: raw.misconception || examples[2] || '',
                practical_application: raw.practical_application || examples[1] || '',
                examples: examples,
                videos: [],
                images: [],
            };
            setTeachingContent(normalized);
            if (response.data.updated_mastery !== undefined) {
                setAtomMastery(response.data.updated_mastery);
            }
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to reteach'
            };
        } finally {
            setLoading(false);
        }
    }, []);

    const getAllAtomsMastery = useCallback(async ({ session_id, concept_id }) => {
        setLoading(true);
        try {
            const response = await axios.post('/auth/api/all-atoms-mastery/', {
                session_id,
                concept_id
            });
            setAllAtomsMastery(response.data);
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Failed to get atoms mastery'
            };
        } finally {
            setLoading(false);
        }
    }, []);

    // Reset for new atom
    const resetForNewAtom = useCallback(() => {
        setCurrentQuestions([]);
        setCurrentQuestionIndex(0);
        setAnswers([]);
        setAtomMastery(0.0);          // <-- critical: reset mastery for new atom
        setShowTeaching(true);
        setPacingDecision('stay');
        setCognitiveLoadScore(0);
        setSessionShapeAction('continue');
        setSessionShapeMessage('');
        questionStartTime.current = null;
    }, []);

    const value = useMemo(() => ({
        // State
        currentSession,
        currentAtom,
        learningProgress,
        loading,
        knowledgeLevel,
        
        // Real-time tracking
        currentQuestions,
        currentQuestionIndex,
        answers,
        atomMastery,
        currentTheta,
        pacingDecision,
        nextAction,
        showTeaching,
        teachingContent,
        metrics,
        timeSpent,

        // Enhanced pacing engine state
        fatigueLevel,
        velocityData,
        retentionAction,
        hintWarning,
        engagementScore,
        masteryVerdict,
        showBreakModal,
        cognitiveLoadScore,
        sessionShapeAction,
        sessionShapeMessage,

        // Adaptive flow state
        conceptOverview,
        atomSummaries,
        allAtomsMastery,
        
        // Setters
        setKnowledgeLevel,
        setShowTeaching,
        setShowBreakModal,
        
        // Core methods
        generateConcept,
        startTeachingSession,
        getTeachingContent,
        generateQuestionsFromTeaching,
        generateInitialQuiz,
        submitInitialQuizAnswer,
        completeInitialQuiz,
        generateFinalChallenge,
        completeFinalChallenge,
        submitAtomAnswer,
        completeAtom,
        loadLearningProgress,
        nextQuestion,
        resetForNewAtom,

        // Enhanced pacing engine methods
        fetchVelocityGraph,
        fetchFatigueStatus,
        recordBreak,
        checkRetention,
        recordHint,

        // Concept final challenge methods
        generateConceptFinalChallenge,
        submitConceptFinalAnswer,
        completeConceptFinalChallenge,

        // Adaptive flow methods
        generateConceptOverview,
        generateAtomSummary,
        adaptiveReteach,
        getAllAtomsMastery,
        
    }), [
        currentSession,
        currentAtom,
        learningProgress,
        loading,
        knowledgeLevel,
        currentQuestions,
        currentQuestionIndex,
        answers,
        atomMastery,
        currentTheta,
        pacingDecision,
        nextAction,
        showTeaching,
        teachingContent,
        metrics,
        timeSpent,
        fatigueLevel,
        velocityData,
        retentionAction,
        hintWarning,
        engagementScore,
        masteryVerdict,
        showBreakModal,
        cognitiveLoadScore,
        sessionShapeAction,
        sessionShapeMessage,
        conceptOverview,
        atomSummaries,
        allAtomsMastery,
        generateConcept,
        startTeachingSession,
        getTeachingContent,
        generateQuestionsFromTeaching,
        generateInitialQuiz,
        submitInitialQuizAnswer,
        completeInitialQuiz,
        generateFinalChallenge,
        completeFinalChallenge,
        submitAtomAnswer,
        completeAtom,
        loadLearningProgress,
        nextQuestion,
        resetForNewAtom,
        fetchVelocityGraph,
        fetchFatigueStatus,
        recordBreak,
        checkRetention,
        recordHint,
        generateConceptFinalChallenge,
        submitConceptFinalAnswer,
        completeConceptFinalChallenge,
        generateConceptOverview,
        generateAtomSummary,
        adaptiveReteach,
        getAllAtomsMastery,
    ]);

    return (
        <LearningContext.Provider value={value}>
            {children}
        </LearningContext.Provider>
    );
};

export const useLearning = () => {
    const context = useContext(LearningContext);
    if (!context) {
        throw new Error('useLearning must be used within a LearningProvider');
    }
    return context;
};