import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useParent } from '../../context/ParentContext';
import ParentNavbar from './ParentNavbar';

const pacingLabels = {
    steady: 'Steady pace',
    speeding_up: 'Speeding up',
    slowing_down: 'Slowing down',
};

const ParentChildInsights = () => {
    const { parentAxios } = useParent();
    const { childId } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!childId) return;
        const fetchInsights = async () => {
            try {
                const res = await parentAxios.get(`/auth/api/parent/child/${childId}/insights/`);
                setData(res.data);
            } catch (err) {
                setError(err.response?.data?.error || 'Failed to load insights');
            } finally {
                setLoading(false);
            }
        };
        fetchInsights();
    }, [childId, parentAxios]);

    if (loading) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <ParentNavbar />
                <div className="text-center animate-fade-in mt-20">
                    <div className="w-12 h-12 border-4 border-violet-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-theme-text-secondary font-medium">Loading insights...</p>
                </div>
            </div>
        );
    }

    if (error || !data) {
        return (
            <div className="min-h-screen bg-theme-bg">
                <ParentNavbar />
                <main className="max-w-2xl mx-auto py-12 px-4 text-center">
                    <p className="text-error mb-4">{error || 'No data'}</p>
                    <button
                        type="button"
                        onClick={() => navigate('/parent/dashboard')}
                        className="px-4 py-2 bg-violet-500 text-white rounded-lg font-medium hover:opacity-90"
                    >
                        Back to Dashboard
                    </button>
                </main>
            </div>
        );
    }

    const summary = data.child_summary || {};
    const pacing = data.current_pacing || {};
    const insights = data.insight_messages || [];
    const recentSessions = data.recent_sessions || [];
    const masteryByConcept = data.mastery_by_concept || [];
    const weakAreas = data.weak_areas || [];
    const weeklySummary = data.weekly_summary;

    return (
        <div className="min-h-screen bg-theme-bg">
            <ParentNavbar />

            <main className="max-w-5xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                <button
                    type="button"
                    onClick={() => navigate('/parent/dashboard')}
                    className="text-violet-500 hover:underline text-sm font-medium mb-6 inline-block"
                >
                    ← Back to Dashboard
                </button>

                {/* Child header */}
                <div className="mb-8 animate-fade-in-up">
                    <h1 className="text-3xl font-bold text-theme-text">{summary.name || summary.username || 'Child'}</h1>
                    <p className="text-theme-text-secondary mt-1">
                        Last active: {summary.last_active ? new Date(summary.last_active).toLocaleString() : '—'} · 
                        Total XP: {summary.total_xp ?? '—'} · 
                        Overall mastery: {summary.overall_mastery != null ? `${Math.round(summary.overall_mastery * 100)}%` : '—'}
                    </p>
                </div>

                {/* This week / Last 7 days */}
                {weeklySummary && (
                    <section className="mb-8 bg-primary/5 rounded-theme-xl border border-primary/20 p-6 shadow-theme">
                        <h2 className="text-lg font-semibold text-theme-text mb-2">Last 7 days</h2>
                        <p className="text-theme-text">{weeklySummary.summary ?? `${weeklySummary.sessions_count ?? 0} session(s) in the last 7 days.`}</p>
                    </section>
                )}

                {/* Current pace */}
                <section className="mb-8 bg-surface rounded-theme-xl border border-theme-border p-6 shadow-theme">
                    <h2 className="text-lg font-semibold text-theme-text mb-2">Current pace</h2>
                    <p className="text-theme-text-secondary mb-1">
                        {pacingLabels[pacing.label] || pacing.label || 'Steady pace'}
                    </p>
                    <p className="text-theme-text">{pacing.message}</p>
                </section>

                {/* Insights */}
                {insights.length > 0 && (
                    <section className="mb-8 bg-surface rounded-theme-xl border border-theme-border p-6 shadow-theme">
                        <h2 className="text-lg font-semibold text-theme-text mb-3">Insights</h2>
                        <ul className="space-y-2">
                            {insights.map((msg, i) => (
                                <li
                                    key={i}
                                    className="bg-surface rounded-theme border border-theme-border px-4 py-3 text-theme-text"
                                >
                                    {msg}
                                </li>
                            ))}
                        </ul>
                    </section>
                )}

                {/* Recent quiz activity */}
                {recentSessions.length > 0 && (
                    <section className="mb-8 bg-surface rounded-theme-xl border border-theme-border overflow-hidden shadow-theme">
                        <h2 className="text-lg font-semibold text-theme-text mb-3 p-6 pb-0">Recent quiz activity</h2>
                        <div className="overflow-hidden">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b border-theme-border bg-surface-alt">
                                        <th className="text-left py-3 px-4 font-medium text-theme-text">Concept</th>
                                        <th className="text-left py-3 px-4 font-medium text-theme-text">Date</th>
                                        <th className="text-right py-3 px-4 font-medium text-theme-text">Questions</th>
                                        <th className="text-right py-3 px-4 font-medium text-theme-text">Correct</th>
                                        <th className="text-right py-3 px-4 font-medium text-theme-text">Accuracy</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {recentSessions.slice(0, 10).map((s) => (
                                        <tr key={s.id} className="border-b border-theme-border last:border-0">
                                            <td className="py-2 px-4 text-theme-text">{s.concept}</td>
                                            <td className="py-2 px-4 text-theme-text-secondary">
                                                {s.start_time ? new Date(s.start_time).toLocaleDateString() : '—'}
                                            </td>
                                            <td className="py-2 px-4 text-right">{s.questions_answered ?? '—'}</td>
                                            <td className="py-2 px-4 text-right">{s.correct_answers ?? '—'}</td>
                                            <td className="py-2 px-4 text-right">
                                                {s.accuracy != null ? `${Math.round(s.accuracy * 100)}%` : '—'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </section>
                )}

                {/* Mastery by concept */}
                {masteryByConcept.length > 0 && (
                    <section className="mb-8 bg-surface rounded-theme-xl border border-theme-border p-6 shadow-theme">
                        <h2 className="text-lg font-semibold text-theme-text mb-3">Mastery by concept</h2>
                        <div className="space-y-4">
                            {masteryByConcept.map((concept) => (
                                <div
                                    key={concept.concept_id}
                                    className="bg-surface rounded-theme-xl border border-theme-border p-4 shadow-theme"
                                >
                                    <h3 className="font-medium text-theme-text">{concept.concept_name}</h3>
                                    <p className="text-sm text-theme-text-muted mb-2">{concept.subject}</p>
                                    <ul className="space-y-1">
                                        {(concept.atoms || []).map((a) => (
                                            <li key={a.atom_id} className="flex justify-between text-sm">
                                                <span className="text-theme-text">{a.atom_name}</span>
                                                <span className="text-theme-text-secondary">
                                                    {Math.round((a.mastery_score || 0) * 100)}% · {a.phase || '—'}
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            ))}
                        </div>
                    </section>
                )}

                {/* Areas that need more practice */}
                {weakAreas.length > 0 && (
                    <section className="mb-8 bg-amber-500/10 dark:bg-amber-500/20 rounded-theme-xl border border-amber-500/30 p-6 shadow-theme">
                        <h2 className="text-lg font-semibold text-theme-text mb-3">Areas that need more practice</h2>
                        <div>
                            <p className="text-sm text-theme-text-secondary mb-2">Extra practice recommended for these topics.</p>
                            <ul className="space-y-1">
                                {weakAreas.map((w) => (
                                    <li key={`${w.concept_name}-${w.atom_id}`} className="text-theme-text text-sm">
                                        {w.atom_name} ({w.concept_name}) — {Math.round((w.mastery_score || 0) * 100)}%
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </section>
                )}
            </main>
        </div>
    );
};

export default ParentChildInsights;
