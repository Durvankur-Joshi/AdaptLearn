import React from 'react';

const AtomReview = ({ atom, metrics, onComplete, onSkip }) => {
    const isHighPerformance = metrics.accuracy >= 0.8 && metrics.final_mastery >= 0.7;

    return (
        <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-6 animate-fade-in-up">
            <h2 className="text-2xl font-bold text-theme-text mb-4">
                {isHighPerformance ? `Great Work: ${atom.name}` : `Review Required: ${atom.name}`}
            </h2>
            
            {/* Performance Summary */}
            <div className={`${isHighPerformance ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-error/10 border-error/20'} border rounded-theme-lg p-4 mb-6`}>
                <h3 className={`font-semibold ${isHighPerformance ? 'text-emerald-600 dark:text-emerald-400' : 'text-error'} mb-2`}>Performance Analysis</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <p className="text-theme-text-muted">Accuracy</p>
                        <p className={`text-xl font-bold ${metrics.accuracy >= 0.8 ? 'text-emerald-500' : metrics.accuracy >= 0.6 ? 'text-amber-500' : 'text-error'}`}>
                            {Math.round(metrics.accuracy * 100)}%
                        </p>
                    </div>
                    <div>
                        <p className="text-theme-text-muted">Mastery</p>
                        <p className={`text-xl font-bold ${metrics.final_mastery >= 0.7 ? 'text-emerald-500' : metrics.final_mastery >= 0.5 ? 'text-orange-500' : 'text-error'}`}>
                            {Math.round(metrics.final_mastery * 100)}%
                        </p>
                    </div>
                    <div>
                        <p className="text-theme-text-muted">Time Ratio</p>
                        <p className="text-xl font-bold text-primary">
                            {metrics.time_ratio.toFixed(2)}x
                        </p>
                    </div>
                    <div>
                        <p className="text-theme-text-muted">θ Change</p>
                        <p className={`text-xl font-bold ${metrics.theta_change > 0 ? 'text-emerald-500' : 'text-error'}`}>
                            {metrics.theta_change > 0 ? '+' : ''}{metrics.theta_change.toFixed(2)}
                        </p>
                    </div>
                </div>
            </div>

            {/* Error Analysis */}
            {metrics.error_count > 0 && (
                <div className="mb-6">
                    <h3 className="font-semibold text-theme-text mb-2">Error Types:</h3>
                    <div className="space-y-2">
                        {metrics.conceptual_errors > 0 && (
                            <div className="bg-violet-500/10 p-2.5 rounded-theme text-theme-text">
                                <span className="font-medium">Conceptual:</span> {metrics.conceptual_errors} errors
                            </div>
                        )}
                        {metrics.procedural_errors > 0 && (
                            <div className="bg-primary/10 p-2.5 rounded-theme text-theme-text">
                                <span className="font-medium">Procedural:</span> {metrics.procedural_errors} errors
                            </div>
                        )}
                        {metrics.factual_errors > 0 && (
                            <div className="bg-emerald-500/10 p-2.5 rounded-theme text-theme-text">
                                <span className="font-medium">Factual:</span> {metrics.factual_errors} errors
                            </div>
                        )}
                        {metrics.guessing_errors > 0 && (
                            <div className="bg-amber-500/10 p-2.5 rounded-theme text-theme-text">
                                <span className="font-medium">Guessing:</span> {metrics.guessing_errors} errors
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Review Options */}
            <div className="space-y-3">
                <button
                    onClick={() => onComplete('reteach')}
                    className="w-full gradient-primary text-white py-3 rounded-theme font-semibold hover:opacity-90 transition-opacity"
                >
                    Review Teaching Material
                </button>
                <button
                    onClick={() => onComplete('practice')}
                    className="w-full bg-emerald-500 text-white py-3 rounded-theme font-semibold hover:bg-emerald-600 transition-colors"
                >
                    Practice with New Questions
                </button>
                <button
                    onClick={onSkip}
                    className="w-full bg-theme-bg text-theme-text-secondary py-3 rounded-theme font-semibold border border-theme-border hover:bg-surface-alt transition-colors"
                >
                    Continue to Next Step →
                </button>
            </div>
        </div>
    );
};

export default AtomReview;