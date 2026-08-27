// frontend/src/components/Learning/QuestionsFromTeaching.jsx - Enhanced version

import React, { useState, useEffect } from 'react';
import { useLearning } from '../../context/LearningContext';

const QuestionsFromTeaching = ({ 
    questions, 
    atomName,
    sessionId,
    atomId,
    onComplete,
    onBackToTeaching,
    onSubmitAnswer,
    showMetrics = true
}) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [selectedOption, setSelectedOption] = useState(null);
    const [isSubmitted, setIsSubmitted] = useState(false);
    const [feedback, setFeedback] = useState(null);
    const [startTime, setStartTime] = useState(Date.now());
    const [showPacingAlert, setShowPacingAlert] = useState(false);
    
    const { 
        submitAtomAnswer, 
        nextQuestion,
        atomMastery, 
        currentTheta,
        pacingDecision,
        nextAction,
        metrics,
        loading,
        cognitiveLoadScore,
        sessionShapeAction,
        sessionShapeMessage,
    } = useLearning();

    const submitFn = onSubmitAnswer || submitAtomAnswer;

    const currentQuestion = questions[currentIndex];

    // Reset timer when question changes
    useEffect(() => {
        setStartTime(Date.now());
        setSelectedOption(null);
        setIsSubmitted(false);
        setFeedback(null);
        setShowPacingAlert(false);
    }, [currentIndex]);

    // Handle pacing decision alerts
    useEffect(() => {
        if (pacingDecision && isSubmitted) {
            setShowPacingAlert(true);
            
            // Auto-hide after 3 seconds
            const timer = setTimeout(() => {
                setShowPacingAlert(false);
            }, 3000);
            
            return () => clearTimeout(timer);
        }
    }, [pacingDecision, isSubmitted]);

    const handleOptionSelect = (index) => {
        if (!isSubmitted) {
            setSelectedOption(index);
        }
    };

    const handleSubmit = async () => {
        if (selectedOption === null) return;
        
        const timeTaken = Math.round((Date.now() - startTime) / 1000);
        
        const result = await submitFn({
            session_id: sessionId,
            atom_id: atomId,
            question_index: currentIndex,
            selected: selectedOption,
            time_taken: timeTaken
        });
        
        if (result.success) {
            const data = result.data;
            setIsSubmitted(true);
            
            // Set feedback based on result
            setFeedback({
                correct: data.correct,
                error_type: data.error_type,
                message: data.correct ? '✅ Correct!' : '❌ Not quite right',
                mastery_change: data.metrics?.mastery_change?.toFixed(2) || '0',
                theta_change: data.metrics?.theta_change?.toFixed(2) || '0',
                explanation: data.explanation || '',
                correct_index: data.correct_index
            });
        }
    };

    const handleNext = () => {
        if (currentIndex < questions.length - 1) {
            setCurrentIndex(prev => prev + 1);
            nextQuestion();
        } else {
            // All questions completed
            onComplete();
        }
    };

    const getPacingMessage = () => {
        switch(pacingDecision) {
            case 'speed_up':
                return '⚡ You\'re doing great! Ready for a challenge!';
            case 'slow_down':
                return '🐢 Let\'s take it a bit slower.';
            case 'sharp_slowdown':
                return '⚠️ Let\'s review the basics.';
            case 'stay':
            default:
                return '👍 Keep going at this pace.';
        }
    };

    const getPacingColor = () => {
        switch(pacingDecision) {
            case 'speed_up': return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30';
            case 'slow_down': return 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30';
            case 'sharp_slowdown': return 'bg-error/10 text-error border-error/30';
            default: return 'bg-primary/10 text-primary border-primary/30';
        }
    };

    if (!currentQuestion) {
        return (
            <div className="text-center py-8">
                <p className="text-theme-text-muted">No questions available.</p>
            </div>
        );
    }

    const correctIndex = feedback?.correct_index ?? currentQuestion.correct_index;

    return (
        <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-6">
            {/* Real-time Mastery Display */}
            {showMetrics && (
            <div className="mb-6 bg-primary/5 p-4 rounded-theme-lg border border-primary/20">
                <div className="flex justify-between items-center">
                    <div>
                        <h3 className="text-sm font-semibold text-theme-text-muted tracking-wider">REAL-TIME MASTERY</h3>
                        <div className="flex items-center space-x-4 mt-2">
                            <div>
                                <span className="text-2xl font-bold text-primary">
                                    {Math.round(atomMastery * 100)}%
                                </span>
                                <span className="text-sm text-theme-text-muted ml-2">mastery</span>
                            </div>
                            <div className="w-px h-8 bg-theme-border"></div>
                            <div>
                                <span className="text-xl font-semibold text-violet-500">
                                    θ = {currentTheta.toFixed(2)}
                                </span>
                                <span className="text-sm text-theme-text-muted ml-2">ability</span>
                            </div>
                        </div>
                    </div>
                    
                    {/* Pacing Badge */}
                    {showMetrics && pacingDecision && (
                        <div className={`px-3 py-1 rounded-full border ${getPacingColor()}`}>
                            <span className="text-sm font-medium">
                                {pacingDecision.replace('_', ' ').toUpperCase()}
                            </span>
                        </div>
                    )}
                </div>
                
                {/* Progress Bar */}
                <div className="mt-3">
                    <div className="w-full bg-theme-border rounded-full h-2.5">
                        <div 
                            className="gradient-primary h-2.5 rounded-full transition-all duration-300"
                            style={{ width: `${atomMastery * 100}%` }}
                        ></div>
                    </div>
                </div>
            </div>
            )}

            {/* Pacing Alert */}
            {showMetrics && showPacingAlert && (
                <div className={`mb-4 p-3 rounded-lg border ${getPacingColor()} animate-pulse`}>
                    <p className="text-sm font-medium">{getPacingMessage()}</p>
                </div>
            )}

            {/* Session-shape message (cognitive load) */}
            {isSubmitted && sessionShapeMessage && (
                <div className={`mb-4 p-3 rounded-lg border ${
                    sessionShapeAction === 'suggest_end' || sessionShapeAction === 'suggest_break'
                        ? 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30'
                        : sessionShapeAction === 'offer_one_more'
                        ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/30'
                        : 'bg-primary/10 text-primary border-primary/30'
                }`}>
                    <p className="text-sm font-medium">{sessionShapeMessage}</p>
                </div>
            )}

            {/* Load indicator (optional) */}
            {showMetrics && isSubmitted && cognitiveLoadScore != null && (
                <div className="mb-4 flex items-center gap-2 text-xs text-theme-text-muted">
                    <span>Focus:</span>
                    <span className={`font-medium ${
                        cognitiveLoadScore < 0.4 ? 'text-emerald-500' :
                        cognitiveLoadScore < 0.7 ? 'text-amber-500' : 'text-amber-600 dark:text-amber-400'
                    }`}>
                        {cognitiveLoadScore < 0.4 ? 'Low load' : cognitiveLoadScore < 0.7 ? 'Medium' : 'High load'}
                    </span>
                </div>
            )}

            {/* Question Header */}
            <div className="mb-4 flex justify-between items-center">
                <div>
                    <span className="text-sm text-theme-text-muted">
                        Question {currentIndex + 1} of {questions.length}
                    </span>
                    <h2 className="text-xl font-bold text-theme-text mt-1">{atomName}</h2>
                </div>
                <div className="flex space-x-2">
                    <span className={`px-2 py-1 rounded-theme text-xs font-semibold ${
                        currentQuestion.difficulty === 'easy' ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400' :
                        currentQuestion.difficulty === 'medium' ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400' :
                        'bg-error/10 text-error'
                    }`}>
                        {currentQuestion.difficulty?.toUpperCase()}
                    </span>
                    <span className="px-2 py-1 bg-violet-500/10 text-violet-600 dark:text-violet-400 rounded-theme text-xs font-semibold">
                        {currentQuestion.cognitive_operation?.toUpperCase()}
                    </span>
                </div>
            </div>

            {/* Question Text */}
            <div className="mb-6 p-4 bg-theme-bg rounded-theme-lg">
                <p className="text-lg text-theme-text">{currentQuestion.question}</p>
            </div>

            {/* Options */}
            <div className="space-y-3 mb-6">
                {currentQuestion.options?.map((option, index) => (
                    <button
                        key={index}
                        onClick={() => handleOptionSelect(index)}
                        disabled={isSubmitted}
                        className={`w-full text-left p-4 rounded-theme-lg border-2 transition text-theme-text ${
                            selectedOption === index
                                ? 'border-primary bg-primary/10'
                                : 'border-theme-border hover:border-primary/40 hover:bg-theme-bg'
                        } ${
                            isSubmitted && index === correctIndex
                                ? 'border-emerald-500 bg-emerald-500/10'
                                : isSubmitted && selectedOption === index && selectedOption !== correctIndex
                                ? 'border-error bg-error/10'
                                : ''
                        }`}
                    >
                        <span className="font-medium mr-2">
                            {String.fromCharCode(65 + index)}.
                        </span>
                        {option}
                    </button>
                ))}
            </div>

            {/* Feedback Section */}
            {feedback && (
                <div className={`mb-4 p-4 rounded-theme-lg ${
                    feedback.correct ? 'bg-emerald-500/10 border border-emerald-500/30' : 'bg-error/10 border border-error/30'
                }`}>
                    <div className="flex justify-between items-center">
                        <div>
                            <p className={`font-semibold ${
                                feedback.correct ? 'text-emerald-600 dark:text-emerald-400' : 'text-error'
                            }`}>
                                {feedback.message}
                            </p>
                            {!feedback.correct && feedback.error_type && (
                                <p className="text-sm text-theme-text-secondary mt-1">
                                    Error type: <span className="font-medium capitalize">{feedback.error_type}</span>
                                </p>
                            )}
                            {!feedback.correct && feedback.explanation && (
                                <p className="text-sm text-theme-text-secondary mt-1">
                                    {feedback.explanation}
                                </p>
                            )}
                        </div>
                        <div className="text-right">
                            {showMetrics && (
                                <>
                                    <p className="text-sm text-theme-text-muted">
                                        Mastery: <span className="font-bold text-primary">{feedback.mastery_change}</span>
                                    </p>
                                    <p className="text-sm text-theme-text-muted">
                                        θ: <span className="font-bold text-violet-500">{feedback.theta_change}</span>
                                    </p>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-between">
                <button
                    onClick={onBackToTeaching}
                    className="px-4 py-2 bg-theme-bg text-theme-text-secondary rounded-theme-lg hover:bg-theme-border transition-colors"
                >
                    ← Back to Teaching
                </button>
                
                {!isSubmitted ? (
                    <button
                        onClick={handleSubmit}
                        disabled={selectedOption === null || loading}
                        className="px-6 py-2 gradient-primary text-white rounded-theme-lg hover:shadow-theme-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Submitting...' : 'Submit Answer'}
                    </button>
                ) : (
                    <div className="flex items-center gap-2">
                        {sessionShapeAction === 'suggest_end' && (
                            <button
                                onClick={() => onComplete?.()}
                                className="px-4 py-2 bg-amber-500/20 text-amber-700 dark:text-amber-400 border border-amber-500/40 rounded-theme-lg hover:bg-amber-500/30 transition-colors"
                            >
                                End session
                            </button>
                        )}
                        <button
                            onClick={handleNext}
                            className="px-6 py-2 bg-emerald-500 text-white rounded-theme-lg hover:bg-emerald-600 transition-colors"
                        >
                            {currentIndex < questions.length - 1 ? 'Next Question →' : 'Complete Atom →'}
                        </button>
                    </div>
                )}
            </div>

            {/* Learning Metrics */}
            {showMetrics && Object.keys(metrics).length > 0 && (
                <div className="mt-6 pt-4 border-t border-theme-border">
                    <h4 className="text-sm font-semibold text-theme-text-muted mb-2">Learning Metrics</h4>
                    <div className="grid grid-cols-4 gap-2 text-xs">
                        <div className="bg-theme-bg p-2 rounded-theme">
                            <span className="text-theme-text-muted">Confidence:</span>
                            <span className="ml-1 font-bold text-theme-text">{(metrics.confidence * 100).toFixed(0)}%</span>
                        </div>
                        <div className="bg-theme-bg p-2 rounded-theme">
                            <span className="text-theme-text-muted">Quality:</span>
                            <span className="ml-1 font-bold text-theme-text">{metrics.performance_quality?.toFixed(2)}</span>
                        </div>
                        <div className="bg-theme-bg p-2 rounded-theme">
                            <span className="text-theme-text-muted">Learning rate:</span>
                            <span className="ml-1 font-bold text-theme-text">{metrics.learning_rate?.toFixed(2)}</span>
                        </div>
                        <div className="bg-theme-bg p-2 rounded-theme">
                            <span className="text-theme-text-muted">Next:</span>
                            <span className="ml-1 font-bold text-theme-text capitalize">{nextAction?.replace('_', ' ')}</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default QuestionsFromTeaching;