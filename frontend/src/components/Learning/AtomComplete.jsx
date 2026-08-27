// frontend/src/components/Learning/AtomComplete.jsx

import React from 'react';
import { useLearning } from '../../context/LearningContext';

const AtomComplete = ({ atom, onContinue, recommendation = '' }) => {
    const { atomMastery, currentTheta, answers } = useLearning();

    // Calculate stats
    const totalQuestions = answers.length;
    const correctCount = answers.filter(a => a.correct).length;
    const accuracy = totalQuestions > 0 ? (correctCount / totalQuestions) * 100 : 0;
    const avgTime = answers.length > 0 
        ? Math.round(answers.reduce((sum, a) => sum + a.time_taken, 0) / answers.length) 
        : 0;

    return (
        <div className="bg-surface rounded-theme-xl shadow-theme-lg p-8 text-center border border-theme-border animate-scale-in">
            {/* Success Icon */}
            <div className="mb-6">
                <div className="inline-flex items-center justify-center w-24 h-24 bg-emerald-500/10 rounded-full">
                    <span className="text-5xl">🎉</span>
                </div>
            </div>

            <h2 className="text-3xl font-bold text-theme-text mb-2">Atom Complete!</h2>
            <p className="text-xl text-emerald-500 mb-8">You've mastered: {atom?.name}</p>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8 stagger">
                <div className="bg-primary/10 p-4 rounded-theme-lg">
                    <div className="text-2xl font-bold text-primary">
                        {Math.round(atomMastery * 100)}%
                    </div>
                    <div className="text-sm text-theme-text-muted">Final Mastery</div>
                </div>
                
                <div className="bg-violet-500/10 p-4 rounded-theme-lg">
                    <div className="text-2xl font-bold text-violet-500">
                        {accuracy.toFixed(0)}%
                    </div>
                    <div className="text-sm text-theme-text-muted">Accuracy</div>
                </div>
                
                <div className="bg-emerald-500/10 p-4 rounded-theme-lg">
                    <div className="text-2xl font-bold text-emerald-500">
                        {correctCount}/{totalQuestions}
                    </div>
                    <div className="text-sm text-theme-text-muted">Correct</div>
                </div>
                
                <div className="bg-orange-500/10 p-4 rounded-theme-lg">
                    <div className="text-2xl font-bold text-orange-500">
                        {avgTime}s
                    </div>
                    <div className="text-sm text-theme-text-muted">Avg Time</div>
                </div>
            </div>

            {/* Theta Change */}
            <div className="mb-8 p-4 bg-theme-bg rounded-theme-lg">
                <div className="text-sm text-theme-text-muted">Ability (θ) Progress</div>
                <div className="text-2xl font-bold text-theme-text">
                    {currentTheta.toFixed(2)}
                </div>
            </div>

            {recommendation && (
                <div className="mb-6 p-4 bg-info/10 border border-info/20 rounded-theme-lg text-info">
                    {recommendation}
                </div>
            )}

            {/* Continue Button */}
            <button
                onClick={onContinue}
                className="px-8 py-3 bg-emerald-500 text-white rounded-theme font-semibold hover:bg-emerald-600 transition-colors shadow-theme"
            >
                Continue to Next Atom →
            </button>

            <p className="mt-4 text-sm text-theme-text-muted">
                You're making great progress! Keep going.
            </p>
        </div>
    );
};

export default AtomComplete;