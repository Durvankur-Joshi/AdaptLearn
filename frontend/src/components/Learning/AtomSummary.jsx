import React from 'react';

const AtomSummary = ({ summary, atomName, masteryScore, onContinue, isLastAtom, loading }) => {
    if (!summary) return null;

    const masteryPercent = Math.round((masteryScore || 0) * 100);

    return (
        <div className="max-w-3xl mx-auto space-y-6 animate-fade-in-up">
            {/* Header with mastery */}
            <div className="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-2xl p-6 text-white shadow-lg">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-2xl font-bold mb-1">🎓 Atom Complete!</h2>
                        <p className="text-emerald-100">{atomName}</p>
                    </div>
                    <div className="text-center">
                        <div className={`text-3xl font-bold ${masteryPercent >= 80 ? 'text-green-200' : masteryPercent >= 50 ? 'text-yellow-200' : 'text-red-200'}`}>
                            {masteryPercent}%
                        </div>
                        <div className="text-sm text-emerald-200">Mastery</div>
                    </div>
                </div>
                {/* Mastery bar */}
                <div className="mt-4 bg-emerald-800/50 rounded-full h-3 overflow-hidden">
                    <div
                        className={`h-full rounded-full transition-all duration-1000 ${
                            masteryPercent >= 80 ? 'bg-green-300' :
                            masteryPercent >= 50 ? 'bg-yellow-300' : 'bg-red-300'
                        }`}
                        style={{ width: `${masteryPercent}%` }}
                    />
                </div>
            </div>

            {/* Summary */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3 flex items-center gap-2">
                    <span>📝</span> Summary
                </h3>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                    {summary.summary}
                </p>
            </div>

            {/* Quick Notes */}
            {summary.quick_notes && (
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-6 shadow border border-blue-200 dark:border-blue-700">
                    <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-300 mb-3 flex items-center gap-2">
                        <span>⚡</span> Quick Notes
                    </h3>
                    {Array.isArray(summary.quick_notes) ? (
                        <ul className="space-y-2">
                            {summary.quick_notes.map((note, i) => (
                                <li key={i} className="flex items-start gap-2 text-blue-900 dark:text-blue-200">
                                    <span className="mt-1 text-blue-500 font-bold">{i + 1}.</span>
                                    <span>{note}</span>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-blue-900 dark:text-blue-200 whitespace-pre-line">{summary.quick_notes}</p>
                    )}
                </div>
            )}

            {/* Must Remember */}
            {summary.must_remember && (
                <div className="bg-red-50 dark:bg-red-900/20 rounded-xl p-6 shadow border border-red-200 dark:border-red-700">
                    <h3 className="text-lg font-semibold text-red-800 dark:text-red-300 mb-3 flex items-center gap-2">
                        <span>🔴</span> Must Remember
                    </h3>
                    {Array.isArray(summary.must_remember) ? (
                        <ul className="space-y-2">
                            {summary.must_remember.map((item, i) => (
                                <li key={i} className="flex items-start gap-2 text-red-900 dark:text-red-200">
                                    <span className="mt-1">⚠️</span>
                                    <span className="font-medium">{item}</span>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-red-900 dark:text-red-200 font-medium whitespace-pre-line">{summary.must_remember}</p>
                    )}
                </div>
            )}

            {/* Common Pitfalls */}
            {summary.common_pitfalls && (
                <div className="bg-orange-50 dark:bg-orange-900/20 rounded-xl p-6 shadow border border-orange-200 dark:border-orange-700">
                    <h3 className="text-lg font-semibold text-orange-800 dark:text-orange-300 mb-3 flex items-center gap-2">
                        <span>⚠️</span> Common Pitfalls
                    </h3>
                    {Array.isArray(summary.common_pitfalls) ? (
                        <ul className="space-y-2">
                            {summary.common_pitfalls.map((pitfall, i) => (
                                <li key={i} className="flex items-start gap-2 text-orange-900 dark:text-orange-200">
                                    <span className="mt-1">❌</span>
                                    <span>{pitfall}</span>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-orange-900 dark:text-orange-200 whitespace-pre-line">{summary.common_pitfalls}</p>
                    )}
                </div>
            )}

            {/* Suggestions */}
            {summary.suggestions && (
                <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-xl p-6 shadow border border-indigo-200 dark:border-indigo-700">
                    <h3 className="text-lg font-semibold text-indigo-800 dark:text-indigo-300 mb-3 flex items-center gap-2">
                        <span>💡</span> What to explore next
                    </h3>
                    <p className="text-indigo-900 dark:text-indigo-200 whitespace-pre-line">
                        {Array.isArray(summary.suggestions) ? summary.suggestions.join('\n') : summary.suggestions}
                    </p>
                </div>
            )}

            {/* Confidence boost */}
            {summary.confidence_boost && (
                <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-5 shadow border border-emerald-200 dark:border-emerald-700 text-center">
                    <p className="text-emerald-800 dark:text-emerald-200 text-lg font-medium italic">
                        🌟 {summary.confidence_boost}
                    </p>
                </div>
            )}

            {/* Continue button */}
            <div className="flex justify-center pt-4 pb-6">
                <button
                    onClick={onContinue}
                    disabled={loading}
                    className="px-8 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-semibold rounded-xl
                        hover:from-emerald-700 hover:to-teal-700 transition-all shadow-lg hover:shadow-xl
                        disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105"
                >
                    {loading ? (
                        <span className="flex items-center gap-2">
                            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            Loading...
                        </span>
                    ) : isLastAtom ? (
                        'View All Atoms Mastery →'
                    ) : (
                        'Continue to Next Atom →'
                    )}
                </button>
            </div>
        </div>
    );
};

export default AtomSummary;
