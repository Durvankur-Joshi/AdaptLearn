// frontend/src/components/Learning/TeachingFirstFlow.jsx - COMPLETE ADAPTIVE FLOW

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLearning } from '../../context/LearningContext';
import TeachingModule from './TeachingModule';
import QuestionsFromTeaching from './QuestionsFromTeaching';
import AtomComplete from './AtomComplete';
import AtomReview from './AtomReview';
import FatigueIndicator from './FatigueIndicator';
import LearningVelocityGraph from './LearningVelocityGraph';
// Inline WeakTopicDetector component
import { AlertCircle, Target, TrendingUp, BookOpen, RefreshCw } from 'lucide-react';

const WeakTopicDetector = ({ conceptData, sessionId, onReviewStart }) => {
    const [showDetails, setShowDetails] = useState(false);
    const [analyzing, setAnalyzing] = useState(false);
    // NOTE: If you want to use fetchWeakTopics, weakTopics, loading from context, add:
    // const { fetchWeakTopics, weakTopics, loading } = useLearning();

    // Get color based on mastery score
    const getMasteryColor = (score) => {
        if (score >= 0.7) return 'text-emerald-500';
        if (score >= 0.5) return 'text-yellow-500';
        if (score >= 0.3) return 'text-orange-500';
        return 'text-error';
    };

    // Get background color based on mastery score
    const getMasteryBgColor = (score) => {
        if (score >= 0.7) return 'bg-emerald-500/10';
        if (score >= 0.5) return 'bg-yellow-500/10';
        if (score >= 0.3) return 'bg-orange-500/10';
        return 'bg-error/10';
    };

    // Get progress bar color
    const getProgressColor = (score) => {
        if (score >= 0.7) return 'bg-emerald-500';
        if (score >= 0.5) return 'bg-yellow-500';
        if (score >= 0.3) return 'bg-orange-500';
        return 'bg-error';
    };

    // If no concept data or no weakest atom, don't render
    if (!conceptData || !conceptData.weakest_atom) {
        return null;
    }

    const { weakest_atom, lowest_mastery, final_mastery, accuracy, passed } = conceptData;

    return (
        <div className="bg-surface rounded-theme-xl shadow-theme-lg border border-theme-border overflow-hidden animate-fade-in-up">
            {/* Header */}
            <div className="gradient-primary px-6 py-4 text-white flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Target className="w-6 h-6" />
                    <div>
                        <h3 className="font-semibold text-lg">Topic Mastery Analysis</h3>
                        <p className="text-sm text-white/80">Personalized learning insights</p>
                    </div>
                </div>
                <button
                    onClick={() => setShowDetails(!showDetails)}
                    className="px-3 py-1 bg-white/20 rounded-theme-lg text-sm font-medium hover:bg-white/30 transition-colors"
                >
                    {showDetails ? 'Hide Details' : 'View Details'}
                </button>
            </div>

            {/* Main Content */}
            <div className="p-6">
                {/* Overall Performance */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-surface-alt rounded-theme-lg p-4">
                        <p className="text-sm text-theme-text-muted mb-1">Final Mastery</p>
                        <p className="text-2xl font-bold text-theme-text">
                            {Math.round(final_mastery * 100)}%
                        </p>
                        <div className="w-full h-2 bg-theme-border rounded-full mt-2">
                            <div
                                className="h-full bg-primary rounded-full transition-all duration-500"
                                style={{ width: `${final_mastery * 100}%` }}
                            />
                        </div>
                    </div>

                    <div className="bg-surface-alt rounded-theme-lg p-4">
                        <p className="text-sm text-theme-text-muted mb-1">Challenge Accuracy</p>
                        <p className="text-2xl font-bold text-theme-text">
                            {Math.round(accuracy * 100)}%
                        </p>
                        <div className="flex items-center gap-2 mt-2">
                            <span className={`text-sm font-medium ${passed ? 'text-emerald-500' : 'text-error'}`}>
                                {passed ? '✓ Passed' : '✗ Needs Work'}
                            </span>
                        </div>
                    </div>

                    <div className="bg-surface-alt rounded-theme-lg p-4">
                        <p className="text-sm text-theme-text-muted mb-1">Concept Mastery</p>
                        <p className="text-2xl font-bold text-theme-text">
                            {Math.round(conceptData.concept_mastery * 100)}%
                        </p>
                        <p className="text-xs text-theme-text-muted mt-2">
                            Average of all atoms
                        </p>
                    </div>
                </div>

                {/* Weakest Topic Alert */}
                <div className={`${getMasteryBgColor(lowest_mastery)} rounded-theme-lg p-5 border ${getMasteryColor(lowest_mastery).replace('text', 'border')}/20`}>
                    <div className="flex items-start gap-4">
                        <div className={`p-3 rounded-full ${getMasteryBgColor(lowest_mastery)}`}>
                            <AlertCircle className={`w-6 h-6 ${getMasteryColor(lowest_mastery)}`} />
                        </div>

                        <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                                <h4 className="font-semibold text-theme-text">Weakest Topic Identified</h4>
                                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getMasteryBgColor(lowest_mastery)} ${getMasteryColor(lowest_mastery)}`}>
                                    Priority Review
                                </span>
                            </div>

                            <p className="text-lg font-bold text-theme-text mb-2">
                                {weakest_atom}
                            </p>

                            <div className="flex items-center gap-4 mb-3">
                                <div className="flex-1">
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-theme-text-muted">Current Mastery</span>
                                        <span className={`font-medium ${getMasteryColor(lowest_mastery)}`}>
                                            {Math.round(lowest_mastery * 100)}%
                                        </span>
                                    </div>
                                    <div className="w-full h-2 bg-theme-border rounded-full overflow-hidden">
                                        <div
                                            className={`h-full ${getProgressColor(lowest_mastery)} transition-all duration-500`}
                                            style={{ width: `${lowest_mastery * 100}%` }}
                                        />
                                    </div>
                                </div>

                                <button
                                    onClick={() => onReviewStart?.(weakest_atom)}
                                    className="px-4 py-2 gradient-primary text-white rounded-theme-lg text-sm font-medium hover:opacity-90 transition-opacity flex items-center gap-2"
                                >
                                    <RefreshCw className="w-4 h-4" />
                                    Review Now
                                </button>
                            </div>

                            {/* Recommendation */}
                            <div className="mt-4 p-3 bg-theme-bg rounded-theme-lg border border-theme-border">
                                <p className="text-sm text-theme-text">
                                    {conceptData.recommendation}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Detailed Analysis (Conditional) */}
                {showDetails && (
                    <div className="mt-6 animate-fade-in">
                        <h4 className="font-semibold text-theme-text mb-3 flex items-center gap-2">
                            <BookOpen className="w-4 h-4 text-primary" />
                            Learning Recommendations
                        </h4>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-surface-alt rounded-theme-lg p-4">
                                <h5 className="font-medium text-theme-text mb-2">Focus Areas</h5>
                                <ul className="space-y-2">
                                    <li className="flex items-start gap-2 text-sm text-theme-text-secondary">
                                        <span className="text-primary mt-1">•</span>
                                        <span>Review fundamental concepts of "{weakest_atom}"</span>
                                    </li>
                                    <li className="flex items-start gap-2 text-sm text-theme-text-secondary">
                                        <span className="text-primary mt-1">•</span>
                                        <span>Practice with targeted exercises</span>
                                    </li>
                                    <li className="flex items-start gap-2 text-sm text-theme-text-secondary">
                                        <span className="text-primary mt-1">•</span>
                                        <span>Watch video explanations for better understanding</span>
                                    </li>
                                </ul>
                            </div>

                            <div className="bg-surface-alt rounded-theme-lg p-4">
                                <h5 className="font-medium text-theme-text mb-2">Mastery Gap</h5>
                                <div className="space-y-3">
                                    <div>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="text-theme-text-muted">Current</span>
                                            <span className="text-orange-500">{Math.round(lowest_mastery * 100)}%</span>
                                        </div>
                                        <div className="w-full h-2 bg-theme-border rounded-full overflow-hidden">
                                            <div className="h-full bg-orange-500" style={{ width: `${lowest_mastery * 100}%` }} />
                                        </div>
                                    </div>
                                    <div>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="text-theme-text-muted">Target</span>
                                            <span className="text-emerald-500">70%</span>
                                        </div>
                                        <div className="w-full h-2 bg-theme-border rounded-full overflow-hidden">
                                            <div className="h-full bg-emerald-500" style={{ width: '70%' }} />
                                        </div>
                                    </div>
                                    <p className="text-xs text-theme-text-muted mt-2">
                                        Need to improve by {Math.max(0, 70 - lowest_mastery * 100).toFixed(0)}% to reach mastery
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
import ConceptOverview from './ConceptOverview';
import AtomSummary from './AtomSummary';

const TeachingFirstFlow = ({ conceptId, knowledgeLevel = 'intermediate' }) => {
    const navigate = useNavigate();

    // Core state
    const [currentAtomData, setCurrentAtomData] = useState(null);
    const [sessionStarted, setSessionStarted] = useState(false);
    const [flowState, setFlowState] = useState('initializing'); // initializing, concept_overview, initial_quiz, teaching, questions, review, atom_summary, all_atoms_mastery, final_challenge, concept_final_challenge, complete, concept_complete
    const [reviewMetrics, setReviewMetrics] = useState(null);
    const [error, setError] = useState(null);
    const [retryCount, setRetryCount] = useState(0);
    const [initialQuestions, setInitialQuestions] = useState([]);
    const [finalRecommendation, setFinalRecommendation] = useState('');
    const [nextAtomAfterFinal, setNextAtomAfterFinal] = useState(null);
    const [conceptFinalResult, setConceptFinalResult] = useState(null);
    const [pendingCompletionData, setPendingCompletionData] = useState(null);

    // Get all context values
    const {
        // State
        currentSession,
        currentAtom,
        showTeaching,
        setShowTeaching,
        currentQuestions,
        teachingContent,
        pacingDecision,
        nextAction,
        atomMastery,
        currentTheta,
        answers,
        metrics,
        loading,

        // Methods
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
        resetForNewAtom,

        // Enhanced pacing engine
        fatigueLevel,
        velocityData,
        retentionAction,
        hintWarning,
        engagementScore,
        masteryVerdict,
        recordBreak,
        checkRetention,
        recordHint,

        // Concept final challenge
        generateConceptFinalChallenge,
        submitConceptFinalAnswer,
        completeConceptFinalChallenge,

        // Adaptive flow
        generateConceptOverview,
        generateAtomSummary,
        adaptiveReteach,
        getAllAtomsMastery,
        conceptOverview,
        atomSummaries,
        allAtomsMastery,
    } = useLearning();

    const [currentSubject, setCurrentSubject] = useState('');
    const [currentConceptName, setCurrentConceptName] = useState('');

    // When starting the session, store the subject and concept
    useEffect(() => {
        if (currentSession) {
            setCurrentSubject(currentSession.subject || '');
            setCurrentConceptName(currentSession.concept_name || '');
        }
    }, [currentSession]);

    const [quizEvaluation, setQuizEvaluation] = useState(null);

    // Refs for tracking
    const sessionIdRef = useRef(null);
    const conceptIdRef = useRef(conceptId);
    const flowStateRef = useRef(flowState);

    // Update ref when flowState changes
    useEffect(() => {
        flowStateRef.current = flowState;
    }, [flowState]);

    // Initialize session
    useEffect(() => {
        const initSession = async () => {
            if (!conceptId || sessionStarted) return;

            setFlowState('initializing');
            setError(null);

            try {
                console.log('Starting teaching session for concept:', conceptId, 'level:', knowledgeLevel);
                const result = await startTeachingSession(conceptId, knowledgeLevel);

                if (result.success && result.data) {
                    console.log('Session started:', result.data);
                    sessionIdRef.current = result.data.session_id;
                    setSessionStarted(true);

                    // Prefer current_atom from backend, otherwise fallback to first atom in list
                    const firstAtom = result.data.current_atom
                        || (Array.isArray(result.data.atoms) && result.data.atoms.length > 0
                            ? result.data.atoms[0]
                            : null);

                    if (!firstAtom) {
                        setError('No atoms available for this concept');
                        setFlowState('error');
                        return;
                    }

                    setCurrentAtomData(firstAtom);

                    // ADAPTIVE BRANCHING: Check knowledge level
                    const level = knowledgeLevel || result.data.knowledge_level || 'intermediate';

                    if (level === 'zero') {
                        // Zero knowledge: Show concept overview first, then quiz
                        console.log('Zero knowledge detected — generating concept overview');
                        const overviewResult = await generateConceptOverview({
                            session_id: result.data.session_id
                        });

                        if (overviewResult.success) {
                            setFlowState('concept_overview');
                        } else {
                            // Fallback: skip overview and go directly to quiz
                            console.warn('Overview generation failed, falling back to quiz');
                            const quizResult = await generateInitialQuiz({
                                session_id: result.data.session_id
                            });
                            if (quizResult.success && quizResult.data?.questions?.length > 0) {
                                setInitialQuestions(quizResult.data.questions);
                                setFlowState('initial_quiz');
                            } else {
                                // Even quiz failed, go to teaching
                                const contentResult = await getTeachingContent({
                                    session_id: result.data.session_id,
                                    atom_id: firstAtom.id
                                });
                                if (contentResult.success) {
                                    setFlowState('teaching');
                                } else {
                                    setError('Failed to start learning session');
                                    setFlowState('error');
                                }
                            }
                        }
                    } else {
                        // Non-zero knowledge: go directly to diagnostic quiz
                        const quizResult = await generateInitialQuiz({
                            session_id: result.data.session_id
                        });

                        if (quizResult.success && quizResult.data?.questions?.length > 0) {
                            setInitialQuestions(quizResult.data.questions);
                            setFlowState('initial_quiz');
                        } else {
                            setError(quizResult.error || 'Failed to generate initial quiz');
                            setFlowState('error');
                        }
                    }
                } else {
                    setError(result.error || 'Failed to start session');
                    setFlowState('error');
                }
            } catch (err) {
                console.error('Error starting session:', err);
                setError('Failed to start learning session');
                setFlowState('error');
            }
        };

        initSession();
    }, [conceptId, sessionStarted, knowledgeLevel, startTeachingSession, generateInitialQuiz, getTeachingContent, generateConceptOverview]);

    // Handle starting an atom
    const handleStartAtom = useCallback(async (atom) => {
        if (!currentSession?.session_id) {
            console.error('No active session');
            return;
        }

        setFlowState('loading');
        setError(null);

        try {
            console.log('Getting teaching content for atom:', atom.id);
            const result = await getTeachingContent({
                session_id: currentSession.session_id,
                atom_id: atom.id
            });

            if (result.success) {
                setCurrentAtomData(atom);
                setFlowState('teaching');
            } else {
                setError(result.error || 'Failed to load teaching content');
                setFlowState('error');
            }
        } catch (err) {
            console.error('Error getting teaching content:', err);
            setError('Failed to load teaching content');
            setFlowState('error');
        }
    }, [currentSession, getTeachingContent]);

    // Handle concept overview continue → go to diagnostic quiz
    const handleConceptOverviewContinue = useCallback(async () => {
        if (!currentSession?.session_id) return;

        setFlowState('loading');
        setError(null);

        try {
            const quizResult = await generateInitialQuiz({
                session_id: currentSession.session_id
            });

            if (quizResult.success && quizResult.data?.questions?.length > 0) {
                setInitialQuestions(quizResult.data.questions);
                setFlowState('initial_quiz');
            } else {
                // If quiz generation fails, go directly to teaching
                console.warn('Quiz generation failed after overview, going to teaching');
                if (currentAtomData?.id) {
                    const contentResult = await getTeachingContent({
                        session_id: currentSession.session_id,
                        atom_id: currentAtomData.id
                    });
                    if (contentResult.success) {
                        setFlowState('teaching');
                    } else {
                        setError('Failed to load content');
                        setFlowState('error');
                    }
                } else {
                    setError('No atoms available');
                    setFlowState('error');
                }
            }
        } catch (err) {
            console.error('Error after concept overview:', err);
            setError('Failed to generate quiz');
            setFlowState('error');
        }
    }, [currentSession, currentAtomData, generateInitialQuiz, getTeachingContent]);

    // Handle continue to questions
    const handleContinueToQuestions = useCallback(async () => {
        if (!currentSession?.session_id || !currentAtomData?.id) {
            console.error('Missing session or atom data');
            return;
        }

        setFlowState('loading');
        setError(null);

        try {
            console.log('Generating questions for atom:', currentAtomData.id);
            const result = await generateQuestionsFromTeaching({
                session_id: currentSession.session_id,
                atom_id: currentAtomData.id
            });

            if (result.success && result.data.questions?.length > 0) {
                setFlowState('questions');
            } else {
                setError('No questions generated');
                setFlowState('error');
            }
        } catch (err) {
            console.error('Error generating questions:', err);
            setError('Failed to generate questions');
            setFlowState('error');
        }
    }, [currentSession, currentAtomData, generateQuestionsFromTeaching]);

    const handleInitialQuizComplete = useCallback(async () => {
        if (!currentSession?.session_id || !currentAtomData?.id) return;

        const result = await completeInitialQuiz({ session_id: currentSession.session_id });
        if (!result.success) {
            setError('Failed to complete initial quiz');
            setFlowState('error');
            return;
        }

        const evalData = result.data;
        setQuizEvaluation(evalData);

        console.log('Quiz evaluation:', evalData);

        // Adaptive routing based on quiz mastery
        const nextStep = evalData.next_step || 'normal_teaching';

        if (nextStep === 'skip_to_practice') {
            // High mastery — skip teaching, go directly to practice questions
            try {
                const qResult = await generateQuestionsFromTeaching({
                    session_id: currentSession.session_id,
                    atom_id: currentAtomData.id
                });
                if (qResult.success && qResult.data.questions?.length > 0) {
                    setFlowState('questions');
                    return;
                }
            } catch (err) {
                console.warn('Skip-to-practice failed, falling back to teaching:', err);
            }
        }

        // Default: load teaching content (adapted by backend based on mastery/pacing)
        const contentResult = await getTeachingContent({
            session_id: currentSession.session_id,
            atom_id: currentAtomData.id
        });

        if (contentResult.success) {
            setFlowState('teaching');
        } else {
            setError(contentResult.error || 'Failed to load teaching content');
            setFlowState('error');
        }
    }, [currentSession, currentAtomData, completeInitialQuiz, getTeachingContent, generateQuestionsFromTeaching]);

    // Handle back to teaching
    const handleBackToTeaching = useCallback(() => {
        setFlowState('teaching');
    }, []);

    // Handle answer submission (wrapped to work with QuestionsFromTeaching)
    const handleSubmitAnswer = useCallback(async (payload) => {
        if (!currentSession?.session_id || !currentAtomData?.id) {
            return { success: false, error: 'No active session' };
        }

        return await submitAtomAnswer({
            session_id: payload.session_id || currentSession.session_id,
            atom_id: payload.atom_id || currentAtomData.id,
            question_index: payload.question_index,
            selected: payload.selected,
            forceTimeTaken: payload.time_taken,
            question_set: payload.question_set || 'teaching'
        });
    }, [currentSession, currentAtomData, submitAtomAnswer]);

    // Handle questions complete — ALWAYS show compulsory review
    const handleQuestionsComplete = useCallback(async () => {
        if (!currentSession?.session_id || !currentAtomData?.id) return;

        console.log('Questions completed. Finalizing atom...');
        setFlowState('completing');

        try {
            const completeResult = await completeAtom({
                session_id: currentSession.session_id,
                atom_id: currentAtomData.id,
                continue_learning: true
            });

            if (!completeResult.success) {
                setError('Failed to complete atom');
                setFlowState('error');
                return;
            }

            const data = completeResult.data;

            // ALWAYS build review metrics (compulsory review after every atom)
            const totalAnswers = answers.length;
            const correctCount = answers.filter(a => a.correct).length;
            const accuracy = totalAnswers > 0 ? correctCount / totalAnswers : 0;

            const errorCounts = {
                conceptual: answers.filter(a => a.error_type === 'conceptual').length,
                procedural: answers.filter(a => a.error_type === 'procedural').length,
                factual: answers.filter(a => a.error_type === 'factual').length,
                guessing: answers.filter(a => a.error_type === 'guessing').length,
                attentional: answers.filter(a => a.error_type === 'attentional').length
            };

            // Use backend's authoritative mastery (fixes mastery inconsistency)
            const authoritativeMastery = data.metrics?.final_mastery ?? atomMastery;

            setReviewMetrics({
                accuracy,
                final_mastery: authoritativeMastery,
                error_count: totalAnswers - correctCount,
                conceptual_errors: errorCounts.conceptual,
                procedural_errors: errorCounts.procedural,
                factual_errors: errorCounts.factual,
                guessing_errors: errorCounts.guessing,
                attentional_errors: errorCounts.attentional,
                time_ratio: answers.length > 0
                    ? answers.reduce((sum, a) => sum + (a.time_taken / 60), 0) / answers.length
                    : 1.0,
                theta_change: data.metrics?.theta_change || metrics?.theta_change || 0
            });

            // Store completion data for navigation after compulsory review
            setPendingCompletionData(data);

            // ALWAYS show compulsory review page
            setFlowState('review');
        } catch (err) {
            console.error('Error completing atom:', err);
            setError('Failed to complete atom');
            setFlowState('error');
        }
    }, [currentSession, currentAtomData, answers, atomMastery, metrics, completeAtom]);

    // Launch concept final challenge (after all atoms done)
    const launchConceptFinalChallenge = useCallback(async () => {
        if (!currentSession?.session_id) return;
        setFlowState('loading');
        setError(null);
        resetForNewAtom(); // clear previous question state
        try {
            const result = await generateConceptFinalChallenge({
                session_id: currentSession.session_id,
                concept_id: conceptId,
            });
            if (result.success && result.data.questions?.length > 0) {
                setFlowState('concept_final_challenge');
            } else {
                setError('Failed to generate concept final challenge');
                setFlowState('error');
            }
        } catch (err) {
            console.error('Error launching concept final challenge:', err);
            setError('Failed to generate concept final challenge');
            setFlowState('error');
        }
    }, [currentSession, conceptId, generateConceptFinalChallenge, resetForNewAtom]);

    const handleFinalChallengeComplete = useCallback(async () => {
        if (!currentSession?.session_id || !currentAtomData?.id) return;

        const result = await completeFinalChallenge({
            session_id: currentSession.session_id,
            atom_id: currentAtomData.id
        });

        if (!result.success) {
            setError('Failed to complete final challenge');
            setFlowState('error');
            return;
        }

        if (result.data.all_completed || result.data.concept_final_challenge_ready) {
            // Generate atom summary before all_atoms_mastery
            try {
                await generateAtomSummary({
                    session_id: currentSession.session_id,
                    atom_id: currentAtomData.id
                });
            } catch (e) {
                console.warn('Atom summary failed:', e);
            }
            setFlowState('atom_summary');
            return;
        }

        if (!result.data.mastered || result.data.next_action === 'review_current') {
            setFinalRecommendation(result.data.recommendation || 'Let\'s review and retry this atom.');
            setFlowState('teaching');
            return;
        }

        // Generate atom summary before next atom
        setFinalRecommendation(result.data.recommendation || '');
        setNextAtomAfterFinal(result.data.next_atom || null);
        try {
            await generateAtomSummary({
                session_id: currentSession.session_id,
                atom_id: currentAtomData.id
            });
        } catch (e) {
            console.warn('Atom summary failed:', e);
        }
        setFlowState('atom_summary');
    }, [currentSession, currentAtomData, completeFinalChallenge, generateAtomSummary]);

    // Handle concept final challenge questions complete
    const handleConceptFinalChallengeComplete = useCallback(async () => {
        if (!currentSession?.session_id) return;
        setFlowState('completing');

        try {
            const result = await completeConceptFinalChallenge({
                session_id: currentSession.session_id,
                concept_id: conceptId,
            });

            if (!result.success) {
                setError('Failed to complete concept final challenge');
                setFlowState('error');
                return;
            }

            setConceptFinalResult(result.data);
            setFlowState('concept_complete');
        } catch (err) {
            console.error('Error completing concept final challenge:', err);
            setError('Failed to complete concept final challenge');
            setFlowState('error');
        }
    }, [currentSession, conceptId, completeConceptFinalChallenge]);

    // Handle review complete
    const handleReviewComplete = useCallback(async (action) => {
        if (!currentSession?.session_id || !currentAtomData?.id) return;

        console.log('Review complete with action:', action);

        if (action === 'reteach') {
            // Use adaptive reteach API for different teaching approach
            setFlowState('loading');

            try {
                const reteachResult = await adaptiveReteach({
                    session_id: currentSession.session_id,
                    atom_id: currentAtomData.id
                });

                if (reteachResult.success) {
                    setFlowState('teaching');
                } else {
                    // Fallback to regular teaching content
                    await getTeachingContent({
                        session_id: currentSession.session_id,
                        atom_id: currentAtomData.id
                    });
                    setFlowState('teaching');
                }
            } catch (err) {
                console.error('Error reteaching:', err);
                setError('Failed to load teaching content');
                setFlowState('error');
            }

        } else if (action === 'practice') {
            // Generate new practice questions
            setFlowState('loading');

            try {
                await generateQuestionsFromTeaching({
                    session_id: currentSession.session_id,
                    atom_id: currentAtomData.id,
                    force_new: true
                });
                setFlowState('questions');
            } catch (err) {
                console.error('Error generating practice questions:', err);
                setError('Failed to generate questions');
                setFlowState('error');
            }

        } else if (action === 'skip') {
            // Continue after compulsory review — use stored completion data
            const data = pendingCompletionData;
            setPendingCompletionData(null);

            if (!data) {
                // Fallback: no stored data
                setFlowState('concept_complete');
                return;
            }

            try {
                if (data.all_completed || data.next_action?.action === 'concept_complete' || data.concept_final_challenge_ready) {
                    // All atoms done — generate atom summary, then go to all_atoms_mastery
                    try {
                        await generateAtomSummary({
                            session_id: currentSession.session_id,
                            atom_id: currentAtomData.id
                        });
                    } catch (e) {
                        console.warn('Atom summary generation failed:', e);
                    }
                    setFlowState('atom_summary');
                    return;
                }

                const nextActionType = data.next_action?.action;

                if (nextActionType === 'final_challenge') {
                    setFlowState('loading');
                    const finalResult = await generateFinalChallenge({
                        session_id: currentSession.session_id,
                        atom_id: currentAtomData.id
                    });
                    if (finalResult.success) {
                        setFlowState('final_challenge');
                    } else {
                        setError('Failed to generate final challenge');
                        setFlowState('error');
                    }
                    return;
                }

                if (data.next_atom) {
                    // Generate atom summary before going to next atom
                    setNextAtomAfterFinal(data.next_atom);
                    try {
                        await generateAtomSummary({
                            session_id: currentSession.session_id,
                            atom_id: currentAtomData.id
                        });
                    } catch (e) {
                        console.warn('Atom summary generation failed:', e);
                    }
                    setFlowState('atom_summary');
                    return;
                }

                // Default fallback
                setFlowState('concept_complete');
            } catch (err) {
                console.error('Error continuing after review:', err);
                setError('Failed to continue');
                setFlowState('error');
            }
        }
    }, [currentSession, currentAtomData, conceptId, pendingCompletionData, getTeachingContent, generateQuestionsFromTeaching, adaptiveReteach, generateFinalChallenge, generateAtomSummary]);

    // Handle atom summary continue → next atom or all_atoms_mastery
    const handleAtomSummaryContinue = useCallback(async () => {
        if (!currentSession?.session_id) return;

        // Check if there's a next atom queued
        if (nextAtomAfterFinal) {
            setCurrentAtomData(nextAtomAfterFinal);
            setNextAtomAfterFinal(null);
            setFinalRecommendation('');
            resetForNewAtom();

            // Load teaching content for next atom
            setFlowState('loading');
            try {
                const contentResult = await getTeachingContent({
                    session_id: currentSession.session_id,
                    atom_id: nextAtomAfterFinal.id
                });
                if (contentResult.success) {
                    setFlowState('teaching');
                } else {
                    setError('Failed to load teaching content');
                    setFlowState('error');
                }
            } catch (err) {
                setError('Failed to load next atom');
                setFlowState('error');
            }
            return;
        }

        // No next atom — all atoms completed, show mastery overview
        setFlowState('loading');
        try {
            await getAllAtomsMastery({
                session_id: currentSession.session_id,
                concept_id: conceptId
            });
            setFlowState('all_atoms_mastery');
        } catch (err) {
            console.error('Error getting all atoms mastery:', err);
            // Fallback: go directly to concept final challenge
            await launchConceptFinalChallenge();
        }
    }, [currentSession, conceptId, nextAtomAfterFinal, resetForNewAtom, getTeachingContent, getAllAtomsMastery, launchConceptFinalChallenge]);

    // Handle all atoms mastery continue → concept final challenge
    const handleAllAtomsMasteryContinue = useCallback(async () => {
        await launchConceptFinalChallenge();
    }, [launchConceptFinalChallenge]);

    // Handle atom complete - continue or go to dashboard
    const handleAtomCompleteContinue = useCallback(() => {
        if (nextAtomAfterFinal) {
            setCurrentAtomData(nextAtomAfterFinal);
            setFlowState('teaching');
            setFinalRecommendation('');
            setNextAtomAfterFinal(null);
            resetForNewAtom();
        } else {
            navigate('/dashboard');
        }
    }, [nextAtomAfterFinal, navigate, resetForNewAtom]);

    // Handle retry after error
    const handleRetry = useCallback(() => {
        setRetryCount(prev => prev + 1);
        setError(null);
        setSessionStarted(false); // Force re-initialization
    }, []);

    // Handle back to dashboard
    const handleBackToDashboard = useCallback(() => {
        navigate('/dashboard');
    }, [navigate]);

    // Loading state
    if (flowState === 'initializing' || (loading && flowState !== 'error')) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <div className="text-center">
                    <div className="text-xl text-theme-text-secondary mb-4">Preparing your adaptive learning session...</div>
                    <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto"></div>
                    <p className="mt-4 text-sm text-theme-text-muted">Analyzing concept structure</p>
                </div>
            </div>
        );
    }

    // Error state
    if (flowState === 'error' && error) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <div className="text-center max-w-md p-8 bg-surface rounded-theme-xl shadow-theme-lg border border-theme-border">
                    <div className="text-5xl mb-4">😕</div>
                    <h2 className="text-2xl font-bold text-error mb-2">Something went wrong</h2>
                    <p className="text-theme-text-secondary mb-6">{error}</p>
                    <div className="space-y-3">
                        <button
                            onClick={handleRetry}
                            className="w-full px-4 py-2 gradient-primary text-white rounded-theme-lg hover:shadow-theme-lg transition-all"
                        >
                            Try Again
                        </button>
                        <button
                            onClick={handleBackToDashboard}
                            className="w-full px-4 py-2 bg-theme-bg text-theme-text-secondary rounded-theme-lg hover:bg-theme-border transition-colors"
                        >
                            Back to Dashboard
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // No session
    if (!currentSession) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <div className="text-center max-w-md p-8 bg-surface rounded-theme-xl shadow-theme-lg border border-theme-border">
                    <div className="text-5xl mb-4">🔍</div>
                    <h2 className="text-2xl font-bold text-theme-text mb-2">No Active Session</h2>
                    <p className="text-theme-text-secondary mb-6">We couldn't find an active learning session.</p>
                    <button
                        onClick={handleBackToDashboard}
                        className="px-4 py-2 gradient-primary text-white rounded-theme-lg hover:shadow-theme-lg transition-all"
                    >
                        Back to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-theme-bg py-8">
            <div className="max-w-4xl mx-auto px-4">
                {/* Session Header with Real-time Stats */}
                <div className="mb-6 bg-surface rounded-theme-xl shadow-theme border border-theme-border p-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-xl font-bold text-theme-text">
                                {currentSession.concept_name || 'Learning Session'}
                            </h1>
                            <p className="text-sm text-theme-text-muted">
                                {flowState === 'concept_overview' && '📘 Concept Overview'}
                                {flowState === 'initial_quiz' && '📝 Diagnostic Quiz'}
                                {flowState === 'teaching' && '📖 Learning new concept'}
                                {flowState === 'questions' && '✍️ Answering questions'}
                                {flowState === 'review' && '🔄 Reviewing material'}
                                {flowState === 'atom_summary' && '📋 Atom Summary'}
                                {flowState === 'all_atoms_mastery' && '🎯 All Atoms Mastery'}
                                {flowState === 'complete' && '✅ Atom complete'}
                                {flowState === 'concept_final_challenge' && '🏆 Concept Final Challenge'}
                                {flowState === 'concept_complete' && '🎉 Concept mastered!'}
                                {flowState === 'loading' && '⏳ Loading...'}
                            </p>
                        </div>

                        {/* Real-time Stats */}
                        <div className="flex space-x-4">
                            <div className="text-center">
                                <div className="text-xs text-theme-text-muted">Mastery</div>
                                <div className="text-xl font-bold text-primary">
                                    {Math.round(atomMastery * 100)}%
                                </div>
                                <div className="w-20 h-1 bg-theme-border rounded-full mt-1">
                                    <div
                                        className="h-1 gradient-primary rounded-full transition-all duration-300"
                                        style={{ width: `${atomMastery * 100}%` }}
                                    ></div>
                                </div>
                            </div>

                            <div className="text-center">
                                <div className="text-xs text-theme-text-muted">Ability (θ)</div>
                                <div className="text-xl font-bold text-violet-500">
                                    {currentTheta.toFixed(2)}
                                </div>
                            </div>

                            {pacingDecision && pacingDecision !== 'stay' && (
                                <div className="text-center">
                                    <div className="text-xs text-theme-text-muted">Pace</div>
                                    <div className={`text-sm font-bold px-2 py-1 rounded-theme ${pacingDecision === 'speed_up' ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' :
                                        pacingDecision === 'slow_down' ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400' :
                                            pacingDecision === 'sharp_slowdown' ? 'bg-error/10 text-error' :
                                                'bg-theme-bg text-theme-text'
                                        }`}>
                                        {pacingDecision === 'speed_up' && '⚡ Speed Up'}
                                        {pacingDecision === 'slow_down' && '🐢 Slow Down'}
                                        {pacingDecision === 'sharp_slowdown' && '⚠️ Careful'}
                                    </div>
                                </div>
                            )}

                            {answers.length > 0 && (
                                <div className="text-center">
                                    <div className="text-xs text-theme-text-muted">Questions</div>
                                    <div className="text-lg font-bold text-theme-text">
                                        {answers.length}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Fatigue indicator + Velocity graph row */}
                    <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                            <FatigueIndicator />
                            {retentionAction && (
                                <div className="mt-1 text-xs text-orange-500 font-medium">
                                    🔁 {typeof retentionAction === 'string' ? retentionAction : 'Retention review recommended'}
                                </div>
                            )}
                            {hintWarning && (
                                <div className="mt-1 text-xs text-amber-500 font-medium">
                                    💡 {hintWarning}
                                </div>
                            )}
                        </div>
                        <LearningVelocityGraph sessionId={currentSession?.session_id} />
                    </div>
                </div>

                {/* Main Content - Flow-based rendering */}
                <div className="transition-all duration-300">
                    {/* Concept Overview (zero knowledge) */}
                    {flowState === 'concept_overview' && conceptOverview && (
                        <ConceptOverview
                            overview={conceptOverview}
                            onContinue={handleConceptOverviewContinue}
                            loading={loading}
                        />
                    )}

                    {/* Initial Diagnostic Quiz */}
                    {flowState === 'initial_quiz' && initialQuestions.length > 0 && (
                        <QuestionsFromTeaching
                            questions={initialQuestions}
                            atomName={`${currentSession.concept_name} Diagnostic`}
                            sessionId={currentSession.session_id}
                            atomId={currentAtomData?.id}
                            onComplete={handleInitialQuizComplete}
                            onBackToTeaching={handleBackToDashboard}
                            onSubmitAnswer={submitInitialQuizAnswer}
                            showMetrics={false}
                        />
                    )}

                    {/* Quiz Evaluation Summary (shows above teaching/questions after quiz) */}
                    {quizEvaluation && (flowState === 'teaching' || flowState === 'questions') && (
                        <div className="mb-4 bg-surface rounded-theme-xl shadow-theme border border-theme-border p-4">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="text-sm font-semibold text-theme-text">
                                    📊 Diagnostic Quiz Results
                                </h3>
                                <button
                                    onClick={() => setQuizEvaluation(null)}
                                    className="text-xs text-theme-text-muted hover:text-theme-text"
                                >
                                    Dismiss
                                </button>
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
                                <div>
                                    <div className="text-xs text-theme-text-muted">Accuracy</div>
                                    <div className={`text-lg font-bold ${quizEvaluation.accuracy >= 0.7 ? 'text-emerald-500' :
                                        quizEvaluation.accuracy >= 0.4 ? 'text-amber-500' : 'text-error'
                                        }`}>
                                        {Math.round((quizEvaluation.accuracy || 0) * 100)}%
                                    </div>
                                </div>
                                <div>
                                    <div className="text-xs text-theme-text-muted">Mastery</div>
                                    <div className="text-lg font-bold text-primary">
                                        {Math.round((quizEvaluation.mastery || 0) * 100)}%
                                    </div>
                                </div>
                                <div>
                                    <div className="text-xs text-theme-text-muted">Ability</div>
                                    <div className="text-lg font-bold text-violet-500">
                                        {(quizEvaluation.theta || 0).toFixed(2)}
                                    </div>
                                </div>
                                <div>
                                    <div className="text-xs text-theme-text-muted">Pace</div>
                                    <div className={`text-sm font-bold ${quizEvaluation.initial_pacing === 'speed_up' ? 'text-emerald-500' :
                                        quizEvaluation.initial_pacing === 'slow_down' ? 'text-amber-500' :
                                            quizEvaluation.initial_pacing === 'sharp_slowdown' ? 'text-error' :
                                                'text-theme-text'
                                        }`}>
                                        {quizEvaluation.initial_pacing === 'speed_up' && '⚡ Speed Up'}
                                        {quizEvaluation.initial_pacing === 'slow_down' && '🐢 Slow Down'}
                                        {quizEvaluation.initial_pacing === 'sharp_slowdown' && '⚠️ Careful'}
                                        {quizEvaluation.initial_pacing === 'stay' && '➡️ Steady'}
                                    </div>
                                </div>
                            </div>
                            {quizEvaluation.next_step_message && (
                                <p className="mt-3 text-sm text-center text-theme-text-muted italic">
                                    {quizEvaluation.next_step_message}
                                </p>
                            )}
                            {quizEvaluation.error_analysis?.dominant_error && (
                                <p className="mt-1 text-xs text-center text-amber-500">
                                    Focus area: {quizEvaluation.error_analysis.dominant_error} errors detected
                                </p>
                            )}
                        </div>
                    )}

                    {/* Teaching Module */}
                    {flowState === 'teaching' && teachingContent && currentAtomData && (
                        <TeachingModule
                            atom={currentAtomData}
                            subject={currentSubject}  // Pass subject
                            concept={currentConceptName}
                            teachingContent={teachingContent}
                            onContinue={handleContinueToQuestions}
                            onBack={handleBackToDashboard}
                            showBackButton={true}
                            pacingDecision={pacingDecision}
                            currentMastery={atomMastery}
                        />
                    )}

                    {/* Questions Module */}
                    {flowState === 'questions' && currentQuestions?.length > 0 && currentAtomData && (
                        <QuestionsFromTeaching
                            questions={currentQuestions}
                            atomName={currentAtomData.name}
                            sessionId={currentSession.session_id}
                            atomId={currentAtomData.id}
                            onComplete={handleQuestionsComplete}
                            onBackToTeaching={handleBackToTeaching}
                            onSubmitAnswer={handleSubmitAnswer}
                            currentMastery={atomMastery}
                            pacingDecision={pacingDecision}
                        />
                    )}

                    {/* Review Module */}
                    {flowState === 'review' && reviewMetrics && currentAtomData && (
                        <AtomReview
                            atom={currentAtomData}
                            metrics={reviewMetrics}
                            onComplete={handleReviewComplete}
                            onSkip={() => handleReviewComplete('skip')}
                        />
                    )}

                    {/* Final Challenge */}
                    {flowState === 'final_challenge' && currentQuestions?.length > 0 && currentAtomData && (
                        <QuestionsFromTeaching
                            questions={currentQuestions}
                            atomName={`${currentAtomData.name} Final Challenge`}
                            sessionId={currentSession.session_id}
                            atomId={currentAtomData.id}
                            onComplete={handleFinalChallengeComplete}
                            onBackToTeaching={handleBackToTeaching}
                            onSubmitAnswer={(payload) => submitAtomAnswer({ ...payload, question_set: 'final' })}
                            showMetrics={false}
                        />
                    )}

                    {/* Atom Complete Module */}
                    {flowState === 'complete' && currentAtomData && (
                        <AtomComplete
                            atom={currentAtomData}
                            onContinue={handleAtomCompleteContinue}
                            recommendation={finalRecommendation}
                            mastery={atomMastery}
                            accuracy={answers.length > 0 ? answers.filter(a => a.correct).length / answers.length : 0}
                            totalQuestions={answers.length}
                        />
                    )}

                    {/* Atom Summary (after each atom) */}
                    {flowState === 'atom_summary' && currentAtomData && (
                        <AtomSummary
                            summary={atomSummaries[currentAtomData.id]}
                            atomName={currentAtomData.name}
                            masteryScore={atomMastery}
                            onContinue={handleAtomSummaryContinue}
                            isLastAtom={!nextAtomAfterFinal}
                            loading={loading}
                        />
                    )}

                    {/* All Atoms Mastery Overview */}
                    {flowState === 'all_atoms_mastery' && allAtomsMastery && (
                        <div className="max-w-3xl mx-auto space-y-6 animate-fade-in-up">
                            <div className="bg-gradient-to-r from-violet-600 to-purple-600 rounded-2xl p-6 text-white shadow-lg">
                                <h2 className="text-2xl font-bold mb-2">🎯 All Atoms Mastery Overview</h2>
                                <p className="text-violet-100">Here's how you performed across all atomic concepts</p>
                            </div>

                            {/* Overall stats */}
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                                <div className="bg-surface rounded-xl p-4 text-center border border-theme-border shadow">
                                    <div className="text-2xl font-bold text-primary">
                                        {Math.round((allAtomsMastery.overall_mastery || 0) * 100)}%
                                    </div>
                                    <div className="text-xs text-theme-text-muted">Overall Mastery</div>
                                </div>
                                <div className="bg-surface rounded-xl p-4 text-center border border-theme-border shadow">
                                    <div className="text-2xl font-bold text-emerald-500">
                                        {allAtomsMastery.atoms_mastered || 0}/{allAtomsMastery.total_atoms || 0}
                                    </div>
                                    <div className="text-xs text-theme-text-muted">Atoms Mastered</div>
                                </div>
                                <div className="bg-surface rounded-xl p-4 text-center border border-theme-border shadow">
                                    <div className="text-2xl font-bold text-violet-500">
                                        {(allAtomsMastery.theta || 0).toFixed(2)}
                                    </div>
                                    <div className="text-xs text-theme-text-muted">Ability (θ)</div>
                                </div>
                                <div className="bg-surface rounded-xl p-4 text-center border border-theme-border shadow">
                                    <div className="text-2xl font-bold text-amber-500">
                                        +{allAtomsMastery.total_xp || 0}
                                    </div>
                                    <div className="text-xs text-theme-text-muted">Total XP</div>
                                </div>
                            </div>

                            {/* Individual atom mastery */}
                            {allAtomsMastery.atoms && (
                                <div className="bg-surface rounded-xl p-6 border border-theme-border shadow">
                                    <h3 className="text-lg font-semibold text-theme-text mb-4">Atom-by-Atom Performance</h3>
                                    <div className="space-y-3">
                                        {allAtomsMastery.atoms.map((atom, i) => (
                                            <div key={atom.id || i} className="flex items-center gap-4">
                                                <span className="w-8 h-8 bg-primary/10 text-primary rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0">
                                                    {i + 1}
                                                </span>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex justify-between items-center mb-1">
                                                        <span className="text-sm font-medium text-theme-text truncate">{atom.name}</span>
                                                        <span className={`text-sm font-bold ${atom.mastery >= 0.8 ? 'text-emerald-500' :
                                                            atom.mastery >= 0.5 ? 'text-amber-500' : 'text-red-500'
                                                            }`}>
                                                            {Math.round((atom.mastery || 0) * 100)}%
                                                        </span>
                                                    </div>
                                                    <div className="w-full h-2 bg-theme-border rounded-full overflow-hidden">
                                                        <div
                                                            className={`h-full rounded-full transition-all ${atom.mastery >= 0.8 ? 'bg-emerald-500' :
                                                                atom.mastery >= 0.5 ? 'bg-amber-500' : 'bg-red-500'
                                                                }`}
                                                            style={{ width: `${(atom.mastery || 0) * 100}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Suggestions */}
                            {allAtomsMastery.suggestions && (
                                <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-xl p-6 border border-indigo-200 dark:border-indigo-700">
                                    <h3 className="text-lg font-semibold text-indigo-800 dark:text-indigo-300 mb-3">💡 Suggestions</h3>
                                    <p className="text-indigo-900 dark:text-indigo-200 whitespace-pre-line">
                                        {Array.isArray(allAtomsMastery.suggestions) ? allAtomsMastery.suggestions.join('\n') : allAtomsMastery.suggestions}
                                    </p>
                                </div>
                            )}

                            {/* Continue to final challenge */}
                            <div className="flex justify-center pt-4 pb-6">
                                <button
                                    onClick={handleAllAtomsMasteryContinue}
                                    disabled={loading}
                                    className="px-8 py-3 bg-gradient-to-r from-violet-600 to-purple-600 text-white font-semibold rounded-xl
                                        hover:from-violet-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl
                                        disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105"
                                >
                                    {loading ? 'Preparing Final Challenge...' : 'Take Final Challenge →'}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Concept Final Challenge */}
                    {flowState === 'concept_final_challenge' && currentQuestions?.length > 0 && (
                        <QuestionsFromTeaching
                            questions={currentQuestions}
                            atomName={`${currentSession.concept_name || 'Concept'} — Final Challenge`}
                            sessionId={currentSession.session_id}
                            atomId={null}
                            onComplete={handleConceptFinalChallengeComplete}
                            onBackToTeaching={handleBackToDashboard}
                            onSubmitAnswer={(payload) =>
                                submitConceptFinalAnswer({
                                    session_id: currentSession.session_id,
                                    question_index: payload.question_index,
                                    selected: payload.selected,
                                    time_taken: payload.time_taken,
                                })
                            }
                            showMetrics={false}
                        />
                    )}

                    {/* Concept Complete */}
                    {flowState === 'concept_complete' && (
                        <div className="bg-surface rounded-theme-xl shadow-theme-lg border border-theme-border p-12 text-center animate-scale-in">
                            <div className="text-6xl mb-4">{conceptFinalResult?.passed ? '🏆' : '📚'}</div>
                            <h2 className="text-3xl font-bold text-theme-text mb-2">
                                {conceptFinalResult?.passed ? 'Concept Mastered!' : 'Almost There!'}
                            </h2>
                            <p className="text-lg text-theme-text-secondary mb-6">
                                {conceptFinalResult?.recommendation || "You've completed all atoms in this concept."}
                            </p>

                            {/* Final Stats */}
                            {conceptFinalResult && (
                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-xl mx-auto mb-8">
                                    <div className="bg-primary/10 p-4 rounded-theme-lg">
                                        <div className="text-2xl font-bold text-primary">
                                            {Math.round((conceptFinalResult.accuracy || 0) * 100)}%
                                        </div>
                                        <div className="text-sm text-theme-text-muted">Challenge Score</div>
                                    </div>
                                    <div className="bg-emerald-500/10 p-4 rounded-theme-lg">
                                        <div className="text-2xl font-bold text-emerald-500">
                                            {conceptFinalResult.correct}/{conceptFinalResult.total}
                                        </div>
                                        <div className="text-sm text-theme-text-muted">Correct</div>
                                    </div>
                                    <div className="bg-violet-500/10 p-4 rounded-theme-lg">
                                        <div className="text-2xl font-bold text-violet-500">
                                            {Math.round((conceptFinalResult.final_mastery || 0) * 100)}%
                                        </div>
                                        <div className="text-sm text-theme-text-muted">Final Mastery</div>
                                    </div>
                                    <div className="bg-amber-500/10 p-4 rounded-theme-lg">
                                        <div className="text-2xl font-bold text-amber-500">
                                            +{conceptFinalResult.concept_xp || 0}
                                        </div>
                                        <div className="text-sm text-theme-text-muted">XP Earned</div>
                                    </div>
                                </div>
                            )}

                            {/* Weak Topic Detector - Mastery Analysis */}
                            <div className="max-w-3xl mx-auto my-8">
                                <WeakTopicDetector
                                    conceptData={conceptFinalResult}
                                    sessionId={currentSession?.session_id}
                                    onReviewStart={handleBackToTeaching}
                                />
                            </div>

                            {/* Certificate Card */}
                            <div className="max-w-3xl mx-auto space-y-6 animate-scale-in">
                                <div className="relative bg-gradient-to-br from-amber-50 via-white to-amber-50 dark:from-gray-800 dark:via-gray-900 dark:to-gray-800 rounded-2xl shadow-2xl border-2 border-amber-300 dark:border-amber-600 p-8 text-center overflow-hidden">
                                    {/* Decorative corners */}
                                    <div className="absolute top-0 left-0 w-16 h-16 border-t-4 border-l-4 border-amber-400 rounded-tl-2xl" />
                                    <div className="absolute top-0 right-0 w-16 h-16 border-t-4 border-r-4 border-amber-400 rounded-tr-2xl" />
                                    <div className="absolute bottom-0 left-0 w-16 h-16 border-b-4 border-l-4 border-amber-400 rounded-bl-2xl" />
                                    <div className="absolute bottom-0 right-0 w-16 h-16 border-b-4 border-r-4 border-amber-400 rounded-br-2xl" />

                                    <div className="text-6xl mb-3">
                                        {conceptFinalResult?.passed ? '🏆' : '📚'}
                                    </div>

                                    <p className="text-sm uppercase tracking-widest text-amber-600 dark:text-amber-400 font-semibold mb-1">
                                        Certificate of Completion
                                    </p>

                                    <h2 className="text-3xl font-bold text-theme-text mb-2">
                                        {conceptFinalResult?.passed ? 'Concept Mastered!' : 'Learning Complete!'}
                                    </h2>

                                    <p className="text-lg text-theme-text-secondary mb-1">
                                        {currentSession?.concept_name || 'Concept'}
                                    </p>
                                    <p className="text-sm text-theme-text-muted mb-6">
                                        {currentSubject || 'Subject'}
                                    </p>

                                    <p className="text-theme-text-secondary mb-6 max-w-md mx-auto">
                                        {conceptFinalResult?.recommendation || "Congratulations! You've completed all atoms in this concept."}
                                    </p>

                                    {/* Final Stats (again for certificate) */}
                                    {conceptFinalResult && (
                                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-xl mx-auto mb-6">
                                            <div className="bg-primary/10 p-4 rounded-xl">
                                                <div className="text-2xl font-bold text-primary">
                                                    {Math.round((conceptFinalResult.accuracy || 0) * 100)}%
                                                </div>
                                                <div className="text-xs text-theme-text-muted">Challenge Score</div>
                                            </div>
                                            <div className="bg-emerald-500/10 p-4 rounded-xl">
                                                <div className="text-2xl font-bold text-emerald-500">
                                                    {conceptFinalResult.correct}/{conceptFinalResult.total}
                                                </div>
                                                <div className="text-xs text-theme-text-muted">Correct</div>
                                            </div>
                                            <div className="bg-violet-500/10 p-4 rounded-xl">
                                                <div className="text-2xl font-bold text-violet-500">
                                                    {Math.round((conceptFinalResult.final_mastery || 0) * 100)}%
                                                </div>
                                                <div className="text-xs text-theme-text-muted">Final Mastery</div>
                                            </div>
                                            <div className="bg-amber-500/10 p-4 rounded-xl">
                                                <div className="text-2xl font-bold text-amber-500">
                                                    +{conceptFinalResult.concept_xp || 0}
                                                </div>
                                                <div className="text-xs text-theme-text-muted">XP Earned</div>
                                            </div>
                                        </div>
                                    )}

                                    {!conceptFinalResult && (
                                        <div className="grid grid-cols-3 gap-4 max-w-md mx-auto mb-6">
                                            <div className="bg-primary/10 p-4 rounded-xl">
                                                <div className="text-2xl font-bold text-primary">
                                                    {Math.round(atomMastery * 100)}%
                                                </div>
                                                <div className="text-xs text-theme-text-muted">Mastery</div>
                                            </div>
                                            <div className="bg-emerald-500/10 p-4 rounded-xl">
                                                <div className="text-2xl font-bold text-emerald-500">
                                                    {currentTheta.toFixed(2)}
                                                </div>
                                                <div className="text-xs text-theme-text-muted">Ability (θ)</div>
                                            </div>
                                            <div className="bg-violet-500/10 p-4 rounded-xl">
                                                <div className="text-2xl font-bold text-violet-500">
                                                    {answers.length}
                                                </div>
                                                <div className="text-xs text-theme-text-muted">Questions</div>
                                            </div>
                                        </div>
                                    )}

                                    <div className="text-xs text-theme-text-muted">
                                        {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
                                    </div>
                                </div>

                                <div className="flex justify-center space-x-4 pt-2">
                                    <button
                                        onClick={handleBackToDashboard}
                                        className="px-8 py-3 bg-emerald-500 text-white rounded-xl font-semibold hover:bg-emerald-600 transition-colors shadow-lg"
                                    >
                                        Return to Dashboard
                                    </button>
                                    <button
                                        onClick={() => navigate('/leaderboard')}
                                        className="px-8 py-3 bg-amber-500 text-white rounded-xl font-semibold hover:bg-amber-600 transition-colors shadow-lg"
                                    >
                                        🏆 Leaderboard
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Loading State for transitions */}
                    {flowState === 'loading' && (
                        <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-12 text-center">
                            <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                            <p className="text-theme-text-muted">Loading next content...</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default TeachingFirstFlow;