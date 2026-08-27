import React from 'react';

const ConceptOverview = ({ overview, onContinue, loading }) => {
    if (!overview) return null;

    return (
        <div className="max-w-3xl mx-auto space-y-6 animate-fade-in-up">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-6 text-white shadow-lg">
                <h2 className="text-2xl font-bold mb-2">📘 Concept Overview</h2>
                <p className="text-blue-100 text-sm">
                    Let's start with a quick introduction before we test your knowledge
                </p>
            </div>

            {/* Overview text */}
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-3 flex items-center gap-2">
                    <span>🔍</span> What is this about?
                </h3>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
                    {overview.overview}
                </p>
            </div>

            {/* Why it matters */}
            {overview.why_it_matters && (
                <div className="bg-amber-50 dark:bg-amber-900/20 rounded-xl p-6 shadow border border-amber-200 dark:border-amber-700">
                    <h3 className="text-lg font-semibold text-amber-800 dark:text-amber-300 mb-3 flex items-center gap-2">
                        <span>💡</span> Why does this matter?
                    </h3>
                    <p className="text-amber-900 dark:text-amber-200 leading-relaxed whitespace-pre-line">
                        {overview.why_it_matters}
                    </p>
                </div>
            )}

            {/* What you'll learn */}
            {overview.what_you_will_learn && (
                <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-6 shadow border border-green-200 dark:border-green-700">
                    <h3 className="text-lg font-semibold text-green-800 dark:text-green-300 mb-3 flex items-center gap-2">
                        <span>🎯</span> What you'll learn
                    </h3>
                    {Array.isArray(overview.what_you_will_learn) ? (
                        <ul className="space-y-2">
                            {overview.what_you_will_learn.map((item, i) => (
                                <li key={i} className="flex items-start gap-2 text-green-900 dark:text-green-200">
                                    <span className="mt-1 text-green-500">✓</span>
                                    <span>{item}</span>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-green-900 dark:text-green-200 leading-relaxed whitespace-pre-line">
                            {overview.what_you_will_learn}
                        </p>
                    )}
                </div>
            )}

            {/* Key terms */}
            {overview.key_terms && (
                <div className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-6 shadow border border-purple-200 dark:border-purple-700">
                    <h3 className="text-lg font-semibold text-purple-800 dark:text-purple-300 mb-3 flex items-center gap-2">
                        <span>📚</span> Key Terms to Know
                    </h3>
                    {Array.isArray(overview.key_terms) ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            {overview.key_terms.map((term, i) => (
                                <div key={i} className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-purple-100 dark:border-purple-800">
                                    {typeof term === 'object' ? (
                                        <>
                                            <span className="font-medium text-purple-700 dark:text-purple-300">{term.term || term.name}:</span>{' '}
                                            <span className="text-gray-600 dark:text-gray-400 text-sm">{term.definition || term.description}</span>
                                        </>
                                    ) : (
                                        <span className="text-purple-700 dark:text-purple-300">{term}</span>
                                    )}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-purple-900 dark:text-purple-200 leading-relaxed whitespace-pre-line">
                            {typeof overview.key_terms === 'string' ? overview.key_terms : JSON.stringify(overview.key_terms)}
                        </p>
                    )}
                </div>
            )}

            {/* Encouragement */}
            {overview.encouragement && (
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-5 shadow border border-blue-200 dark:border-blue-700 text-center">
                    <p className="text-blue-800 dark:text-blue-200 text-lg font-medium italic">
                        ✨ {overview.encouragement}
                    </p>
                </div>
            )}

            {/* Continue button */}
            <div className="flex justify-center pt-4">
                <button
                    onClick={onContinue}
                    disabled={loading}
                    className="px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-xl
                        hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl
                        disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105"
                >
                    {loading ? (
                        <span className="flex items-center gap-2">
                            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            Preparing Quiz...
                        </span>
                    ) : (
                        'Continue to Diagnostic Quiz →'
                    )}
                </button>
            </div>
        </div>
    );
};

export default ConceptOverview;
