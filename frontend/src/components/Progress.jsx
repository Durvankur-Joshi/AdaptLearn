import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from './Navbar';
import axios from '../axiosConfig';

const Progress = () => {
    const [progress, setProgress] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { user } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        const fetchProgress = async () => {
            try {
                const res = await axios.get('/auth/api/progress/');
                setProgress(res.data);
            } catch (err) {
                console.error('Failed to fetch progress:', err);
                setError('Failed to load progress data');
            } finally {
                setLoading(false);
            }
        };
        fetchProgress();
    }, []);

    const getPhaseIcon = (phase) => {
        const icons = { complete: '✅', teaching: '📚', diagnostic: '📝', not_started: '⭕' };
        return icons[phase] || '📌';
    };

    const getPhaseLabel = (phase) => {
        const labels = { complete: 'Mastered', teaching: 'Learning', diagnostic: 'In Progress', not_started: 'Not Started' };
        return labels[phase] || phase;
    };

    const getPhaseColor = (phase) => {
        const colors = { complete: 'text-emerald-500', teaching: 'text-blue-500', diagnostic: 'text-violet-500', not_started: 'text-theme-text-muted' };
        return colors[phase] || 'text-theme-text-muted';
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <div className="text-center animate-fade-in">
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-theme-text-secondary font-medium">Loading your progress...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <div className="bg-surface rounded-theme-xl shadow-theme-lg p-8 text-center border border-theme-border">
                    <p className="text-error text-lg mb-4">{error}</p>
                    <button onClick={() => navigate('/dashboard')} className="gradient-primary text-white px-6 py-2.5 rounded-theme font-semibold hover:opacity-90 transition-opacity">
                        Back to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    const p = progress;
    const masteryPct = Math.round((p.overall_mastery || 0) * 100);

    return (
        <div className="min-h-screen bg-theme-bg">
            <Navbar />

            <main className="max-w-5xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="mb-8 animate-fade-in-up">
                    <h1 className="text-3xl font-bold text-theme-text">Your Learning Progress</h1>
                    <p className="text-theme-text-secondary mt-1">Track your mastery, XP, and study stats</p>
                </div>

                {/* XP Summary Card */}
                <div className="bg-gradient-to-br from-amber-500 via-orange-500 to-rose-500 rounded-theme-xl shadow-theme-lg p-6 mb-8 text-white animate-fade-in-up">
                    <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
                        <h2 className="text-xl font-bold flex items-center gap-2">⚡ Experience Points</h2>
                        <span className="text-3xl font-extrabold">{p.xp?.total_xp || 0} XP</span>
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                        {[
                            { val: p.xp?.questions_xp || 0, label: 'Questions XP' },
                            { val: p.xp?.atoms_xp || 0, label: 'Atoms XP' },
                            { val: p.xp?.concepts_xp || 0, label: 'Concepts XP' },
                        ].map((item, i) => (
                            <div key={i} className="bg-white/15 backdrop-blur rounded-theme p-3 text-center">
                                <p className="text-2xl font-bold">{item.val}</p>
                                <p className="text-xs text-white/80">{item.label}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Overview Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8 stagger">
                    {/* Mastery Ring */}
                    <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-5 text-center">
                        <div className="relative inline-flex items-center justify-center w-16 h-16 mb-2">
                            <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                                <circle cx="18" cy="18" r="15.9" fill="none" className="stroke-theme-border" strokeWidth="3" />
                                <circle cx="18" cy="18" r="15.9" fill="none" className="stroke-primary" strokeWidth="3"
                                    strokeDasharray={`${masteryPct} ${100 - masteryPct}`} strokeLinecap="round" />
                            </svg>
                            <span className="absolute text-sm font-bold text-primary">{masteryPct}%</span>
                        </div>
                        <p className="text-xs text-theme-text-muted font-medium">Overall Mastery</p>
                    </div>

                    {/* Streak */}
                    <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-5 text-center">
                        <p className="text-3xl font-bold text-orange-500 mb-1">{p.learning_streak || 0} 🔥</p>
                        <p className="text-xs text-theme-text-muted font-medium">Day Streak</p>
                    </div>

                    {/* Ability */}
                    <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-5 text-center">
                        <p className="text-3xl font-bold text-violet-500 mb-1">{p.overall_theta?.toFixed(2) || '0.00'}</p>
                        <p className="text-xs text-theme-text-muted font-medium">Ability (θ)</p>
                    </div>

                    {/* Accuracy */}
                    <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-5 text-center">
                        <p className="text-3xl font-bold text-emerald-500 mb-1">{Math.round((p.overall_accuracy || 0) * 100)}%</p>
                        <p className="text-xs text-theme-text-muted font-medium">Overall Accuracy</p>
                    </div>
                </div>

                {/* Study Stats */}
                <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-6 mb-8 animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
                    <h2 className="text-lg font-bold text-theme-text mb-4 flex items-center gap-2">
                        📊 Study Statistics
                    </h2>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                        {[
                            { label: 'Sessions', value: p.total_sessions || 0, color: 'text-blue-500', bg: 'bg-blue-500/10' },
                            { label: 'Questions', value: p.total_questions_answered || 0, color: 'text-indigo-500', bg: 'bg-indigo-500/10' },
                            { label: 'Correct', value: p.total_correct_answers || 0, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
                            { label: 'Hints Used', value: p.total_hints_used || 0, color: 'text-amber-500', bg: 'bg-amber-500/10' },
                            { label: 'Time Spent', value: `${Math.round((p.total_time_spent || 0) / 60)}m`, color: 'text-rose-500', bg: 'bg-rose-500/10' },
                        ].map((stat, i) => (
                            <div key={i} className={`${stat.bg} rounded-theme p-3 text-center`}>
                                <p className={`text-xl font-bold ${stat.color}`}>{stat.value}</p>
                                <p className="text-xs text-theme-text-muted">{stat.label}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Atoms & Concepts Overview */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 stagger">
                    <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-6">
                        <h3 className="text-lg font-bold text-theme-text mb-3 flex items-center gap-2">🧩 Atoms</h3>
                        <div className="flex items-end gap-3">
                            <span className="text-4xl font-extrabold text-primary">{p.mastered_atoms || 0}</span>
                            <span className="text-theme-text-muted text-lg mb-1">/ {p.total_atoms || 0} mastered</span>
                        </div>
                        {p.total_atoms > 0 && (
                            <div className="mt-3 w-full bg-primary/10 rounded-full h-3">
                                <div className="gradient-primary h-3 rounded-full transition-all" style={{ width: `${Math.round((p.mastered_atoms / p.total_atoms) * 100)}%` }} />
                            </div>
                        )}
                    </div>
                    <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-6">
                        <h3 className="text-lg font-bold text-theme-text mb-3 flex items-center gap-2">📦 Concepts</h3>
                        <div className="flex items-end gap-3">
                            <span className="text-4xl font-extrabold text-emerald-500">{p.concepts_completed || 0}</span>
                            <span className="text-theme-text-muted text-lg mb-1">/ {p.concepts_started || 0} completed</span>
                        </div>
                        {p.concepts_started > 0 && (
                            <div className="mt-3 w-full bg-emerald-500/10 rounded-full h-3">
                                <div className="bg-emerald-500 h-3 rounded-full transition-all" style={{ width: `${Math.round((p.concepts_completed / p.concepts_started) * 100)}%` }} />
                            </div>
                        )}
                    </div>
                </div>

                {/* Per-Concept Breakdown */}
                {p.concepts && p.concepts.length > 0 && (
                    <div className="mb-8">
                        <h2 className="text-lg font-bold text-theme-text mb-4 flex items-center gap-2">📚 Concept Breakdown</h2>
                        <div className="space-y-4">
                            {p.concepts.map((concept, idx) => (
                                <div key={idx} className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-6 animate-fade-in-up" style={{ animationDelay: `${idx * 0.05}s` }}>
                                    <div className="flex items-center justify-between mb-3">
                                        <div>
                                            <h4 className="font-semibold text-theme-text">{concept.name}</h4>
                                            <p className="text-xs text-theme-text-muted">{concept.subject}</p>
                                        </div>
                                        <div className="text-right">
                                            <span className="text-lg font-bold text-primary">{concept.mastery_pct || 0}%</span>
                                            <p className="text-xs text-theme-text-muted">{concept.mastered_count}/{concept.total_count} atoms</p>
                                        </div>
                                    </div>
                                    {/* Mastery bar */}
                                    <div className="w-full bg-primary/10 rounded-full h-2 mb-4">
                                        <div className="gradient-primary h-2 rounded-full transition-all" style={{ width: `${concept.mastery_pct || 0}%` }} />
                                    </div>
                                    {/* Atoms */}
                                    <div className="space-y-2">
                                        {concept.atoms.map((atom, aIdx) => (
                                            <div key={aIdx} className="flex items-center justify-between px-3 py-2.5 bg-theme-bg rounded-theme">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-lg">{getPhaseIcon(atom.phase)}</span>
                                                    <div>
                                                        <p className="text-sm font-medium text-theme-text">{atom.name}</p>
                                                        <p className="text-xs text-theme-text-muted">
                                                            {Math.round(atom.mastery * 100)}% mastery
                                                            {atom.streak > 0 && ` · ${atom.streak} streak`}
                                                            {atom.error_count > 0 && ` · ${atom.error_count} errors`}
                                                            {atom.last_practiced && ` · Last: ${new Date(atom.last_practiced).toLocaleDateString()}`}
                                                        </p>
                                                    </div>
                                                </div>
                                                <span className={`text-xs font-semibold ${getPhaseColor(atom.phase)}`}>
                                                    {getPhaseLabel(atom.phase)}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Recent Sessions */}
                {p.recent_sessions && p.recent_sessions.length > 0 && (
                    <div className="mb-8">
                        <h2 className="text-lg font-bold text-theme-text mb-4 flex items-center gap-2">🕒 Recent Sessions</h2>
                        <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead className="bg-theme-bg text-theme-text-muted text-xs uppercase">
                                        <tr>
                                            <th className="px-4 py-3 text-left font-semibold">Concept</th>
                                            <th className="px-4 py-3 text-left font-semibold">Subject</th>
                                            <th className="px-4 py-3 text-center font-semibold">Questions</th>
                                            <th className="px-4 py-3 text-center font-semibold">Accuracy</th>
                                            <th className="px-4 py-3 text-center font-semibold">Duration</th>
                                            <th className="px-4 py-3 text-right font-semibold">Date</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-theme-border">
                                        {p.recent_sessions.map((s, idx) => (
                                            <tr key={idx} className="hover:bg-surface-alt/50 transition-colors">
                                                <td className="px-4 py-3 font-medium text-theme-text">{s.concept_name}</td>
                                                <td className="px-4 py-3 text-theme-text-muted">{s.subject || '—'}</td>
                                                <td className="px-4 py-3 text-center">
                                                    <span className="text-emerald-500 font-medium">{s.correct_answers}</span>
                                                    <span className="text-theme-text-muted">/{s.questions_answered}</span>
                                                </td>
                                                <td className="px-4 py-3 text-center">
                                                    <span className={`font-medium ${s.accuracy >= 0.8 ? 'text-emerald-500' : s.accuracy >= 0.5 ? 'text-amber-500' : 'text-error'}`}>
                                                        {Math.round(s.accuracy * 100)}%
                                                    </span>
                                                </td>
                                                <td className="px-4 py-3 text-center text-theme-text-muted">
                                                    {s.duration_mins ? `${s.duration_mins}m` : '—'}
                                                </td>
                                                <td className="px-4 py-3 text-right text-theme-text-muted text-xs">
                                                    {new Date(s.start_time).toLocaleDateString()}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {/* Empty state */}
                {(!p.concepts || p.concepts.length === 0) && (
                    <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-12 text-center mb-8 animate-fade-in-up">
                        <p className="text-5xl mb-4">📖</p>
                        <h3 className="text-xl font-bold text-theme-text mb-2">No learning data yet</h3>
                        <p className="text-theme-text-muted mb-6">Start a learning session to track your progress!</p>
                        <button onClick={() => navigate('/learn/start')} className="gradient-primary text-white px-8 py-3 rounded-theme font-semibold hover:opacity-90 transition-opacity shadow-theme">
                            Start Learning
                        </button>
                    </div>
                )}

                {/* Bottom actions */}
                <div className="flex justify-center gap-4 pb-8">
                    <button onClick={() => navigate('/learn/start')} className="gradient-primary text-white px-8 py-3 rounded-theme font-semibold hover:opacity-90 transition-opacity shadow-theme">
                        Continue Learning
                    </button>
                    <button onClick={() => navigate('/leaderboard')} className="bg-surface text-theme-text px-8 py-3 rounded-theme font-semibold border border-theme-border hover:shadow-theme transition-shadow">
                        View Leaderboard
                    </button>
                </div>
            </main>
        </div>
    );
};

export default Progress;
