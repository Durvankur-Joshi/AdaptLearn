import React from 'react';

const AtomList = ({ atoms, onStartAtom, conceptName, completedCount }) => {
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

    return (
        <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-8 animate-fade-in-up">
            <h2 className="text-2xl font-bold text-theme-text mb-2">{conceptName}</h2>
            <p className="text-theme-text-secondary mb-6">
                Completed {completedCount} of {atoms.length} concepts
            </p>

            <div className="space-y-3 mb-8">
                {atoms.map((atom, idx) => (
                    <div
                        key={atom.id}
                        className={`flex items-center justify-between p-4 rounded-theme-lg border transition-colors ${
                            atom.phase === 'not_started'
                                ? 'border-theme-border bg-theme-bg'
                                : atom.phase === 'complete'
                                ? 'border-emerald-500/20 bg-emerald-500/5'
                                : 'border-primary/20 bg-primary/5'
                        }`}
                    >
                        <div className="flex items-center">
                            <span className="text-2xl mr-4">{getPhaseIcon(atom.phase)}</span>
                            <div>
                                <p className="font-medium text-lg text-theme-text">{atom.name}</p>
                                <p className={`text-sm ${getPhaseColor(atom.phase)}`}>
                                    {atom.phase === 'complete' && '✓ Mastered'}
                                    {atom.phase === 'teaching' && '📖 Learning in progress'}
                                    {atom.phase === 'diagnostic' && '📝 Questions ready'}
                                    {atom.phase === 'not_started' && '⏳ Not started'}
                                </p>
                                {atom.mastery_score > 0 && (
                                    <p className="text-xs text-theme-text-muted mt-1">
                                        Mastery: {Math.round(atom.mastery_score * 100)}%
                                    </p>
                                )}
                            </div>
                        </div>
                        
                        {atom.phase === 'not_started' && (
                            <button
                                onClick={() => onStartAtom(atom)}
                                className="px-4 py-2 gradient-primary text-white rounded-theme font-medium hover:opacity-90 transition-opacity shadow-sm"
                            >
                                Start Learning
                            </button>
                        )}
                        
                        {atom.phase === 'teaching' && (
                            <button
                                onClick={() => onStartAtom(atom)}
                                className="px-4 py-2 bg-violet-500 text-white rounded-theme font-medium hover:bg-violet-600 transition-colors"
                            >
                                Continue
                            </button>
                        )}
                        
                        {atom.phase === 'complete' && (
                            <span className="text-emerald-500 font-medium">✓ Completed</span>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default AtomList;