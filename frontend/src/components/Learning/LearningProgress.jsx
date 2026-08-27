import React, { useEffect } from 'react';
import { useLearning } from '../../context/LearningContext';

const LearningProgress = ({ onContinue }) => {
    const { learningProgress, loadLearningProgress, loading } = useLearning();

    useEffect(() => {
        loadLearningProgress();
    }, [loadLearningProgress]);

    const getPhaseIcon = (phase) => {
        const icons = {
            'complete': '✅',
            'teaching': '📚',
            'diagnostic': '📝',
            'not_started': '⭕'
        };
        return icons[phase] || '📌';
    };

    const getPhaseColor = (phase) => {
        const colors = {
            'complete': 'text-emerald-500',
            'teaching': 'text-primary',
            'diagnostic': 'text-violet-500',
            'not_started': 'text-theme-text-muted'
        };
        return colors[phase] || 'text-theme-text-muted';
    };

    if (loading && !learningProgress) {
        return (
            <div className="text-center py-12">
                <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
                <p className="text-theme-text-muted">Loading progress...</p>
            </div>
        );
    }

    if (!learningProgress) {
        return (
            <div className="text-center py-12">
                <p className="text-error">Failed to load progress.</p>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-theme-text mb-8">Your Learning Progress</h2>

            {/* Stats Cards */}
            <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-8 mb-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-primary/10 p-4 rounded-theme-lg text-center">
                        <p className="text-2xl font-bold text-primary">
                            {Math.round(learningProgress.overall_mastery * 100)}%
                        </p>
                        <p className="text-sm text-theme-text-muted">Overall Mastery</p>
                    </div>
                    
                    <div className="bg-emerald-500/10 p-4 rounded-theme-lg text-center">
                        <p className="text-2xl font-bold text-emerald-500">
                            {learningProgress.total_atoms || 0}
                        </p>
                        <p className="text-sm text-theme-text-muted">Total Atoms</p>
                    </div>
                    
                    <div className="bg-orange-500/10 p-4 rounded-theme-lg text-center">
                        <p className="text-2xl font-bold text-orange-500">
                            {learningProgress.learning_streak || 0} 🔥
                        </p>
                        <p className="text-sm text-theme-text-muted">Learning Streak</p>
                    </div>
                </div>

                {/* Theta Score */}
                <div className="border-t border-theme-border pt-6">
                    <div className="flex justify-between items-center">
                        <span className="text-theme-text font-medium">Ability (θ):</span>
                        <span className="text-lg font-semibold text-violet-500">
                            {learningProgress.overall_theta?.toFixed(2) || '0.00'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Concepts */}
            <h3 className="text-xl font-bold text-theme-text mb-4">Concepts</h3>
            
            {learningProgress.concepts?.map((concept, idx) => (
                <div key={idx} className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-6 mb-4">
                    <div className="flex justify-between items-center mb-4">
                        <h4 className="text-lg font-semibold text-theme-text">{concept.name}</h4>
                        <span className="text-sm text-theme-text-muted">
                            {concept.mastered_count}/{concept.total_count} mastered
                        </span>
                    </div>

                    <div className="space-y-3">
                        {concept.atoms.map((atom, atomIdx) => (
                            <div key={atomIdx} className="flex items-center justify-between p-3 bg-theme-bg rounded-theme">
                                <div className="flex items-center">
                                    <span className="text-xl mr-3">{getPhaseIcon(atom.phase)}</span>
                                    <div>
                                        <p className="font-medium text-theme-text">{atom.name}</p>
                                        <p className="text-xs text-theme-text-muted">
                                            Mastery: {Math.round(atom.mastery * 100)}%
                                            {atom.streak > 0 && ` • Streak: ${atom.streak}`}
                                        </p>
                                    </div>
                                </div>
                                <span className={`text-sm font-medium ${getPhaseColor(atom.phase)}`}>
                                    {atom.phase === 'complete' ? 'Mastered' : 
                                     atom.phase === 'teaching' ? 'Learning' :
                                     atom.phase === 'diagnostic' ? 'In Progress' : 'Not Started'}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            ))}

            <div className="flex justify-center mt-8">
                <button
                    onClick={onContinue}
                    className="gradient-primary text-white px-8 py-3 rounded-theme-lg font-semibold hover:shadow-theme-lg transition-all duration-200"
                >
                    Continue Learning
                </button>
            </div>
        </div>
    );
};

export default LearningProgress;