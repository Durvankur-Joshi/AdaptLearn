import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from './Navbar';
import axios from '../axiosConfig';

const Leaderboard = () => {
    const [leaderboard, setLeaderboard] = useState([]);
    const [myXP, setMyXP] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { user } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [lbRes, xpRes] = await Promise.all([
                    axios.get('/auth/api/leaderboard/'),
                    axios.get('/auth/api/my-xp/'),
                ]);
                setLeaderboard(lbRes.data);
                setMyXP(xpRes.data);
            } catch (err) {
                console.error('Failed to fetch leaderboard:', err);
                setError('Failed to load leaderboard');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const getRankBadge = (rank) => {
        if (rank === 1) return '🥇';
        if (rank === 2) return '🥈';
        if (rank === 3) return '🥉';
        return `#${rank}`;
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <div className="text-center animate-fade-in">
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-theme-text-secondary font-medium">Loading leaderboard...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-theme-bg">
            <Navbar />

            <main className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                {/* Page header */}
                <div className="mb-8 animate-fade-in-up">
                    <h1 className="text-3xl font-bold text-theme-text flex items-center gap-3">
                        <span className="text-3xl">🏆</span> Leaderboard
                    </h1>
                    <p className="text-theme-text-secondary mt-1">See how you rank among other learners</p>
                </div>

                {error && (
                    <div className="mb-6 p-4 rounded-theme bg-error/10 border border-error/20 text-error text-sm font-medium animate-scale-in">
                        {error}
                    </div>
                )}

                {/* My XP Card */}
                {myXP && (
                    <div className="gradient-primary rounded-theme-xl shadow-theme-lg p-6 mb-6 text-white animate-fade-in-up">
                        <div className="flex items-center justify-between flex-wrap gap-4">
                            <div>
                                <p className="text-white/70 text-sm font-medium">Your XP</p>
                                <p className="text-4xl font-bold">{myXP.total_xp} XP</p>
                                <p className="text-white/60 mt-1">
                                    Rank #{myXP.rank} of {myXP.total_users} learners
                                </p>
                            </div>
                            <div className="text-right space-y-1 text-sm">
                                <div>
                                    <span className="text-white/60">Questions:</span>{' '}
                                    <span className="font-semibold">{myXP.questions_xp} XP</span>
                                </div>
                                <div>
                                    <span className="text-white/60">Atoms:</span>{' '}
                                    <span className="font-semibold">{myXP.atoms_xp} XP</span>
                                </div>
                                <div>
                                    <span className="text-white/60">Concepts:</span>{' '}
                                    <span className="font-semibold">{myXP.concepts_xp} XP</span>
                                </div>
                            </div>
                        </div>

                        {/* XP Breakdown Bar */}
                        <div className="mt-5">
                            <div className="flex h-3 rounded-full overflow-hidden bg-white/20">
                                {myXP.total_xp > 0 && (
                                    <>
                                        <div className="bg-emerald-400 transition-all" style={{ width: `${(myXP.questions_xp / myXP.total_xp) * 100}%` }} title="Questions XP" />
                                        <div className="bg-amber-400 transition-all" style={{ width: `${(myXP.atoms_xp / myXP.total_xp) * 100}%` }} title="Atoms XP" />
                                        <div className="bg-pink-400 transition-all" style={{ width: `${(myXP.concepts_xp / myXP.total_xp) * 100}%` }} title="Concepts XP" />
                                    </>
                                )}
                            </div>
                            <div className="flex justify-between text-xs mt-1.5 text-white/60">
                                <span>🟢 Questions</span>
                                <span>🟡 Atoms</span>
                                <span>🩷 Concepts</span>
                            </div>
                        </div>
                    </div>
                )}

                {/* XP Rules */}
                <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-5 mb-6 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
                    <h3 className="font-semibold text-theme-text mb-3">How to earn XP</h3>
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-center text-sm">
                        {[
                            { xp: '+1 XP', label: 'Easy Q', color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
                            { xp: '+2 XP', label: 'Medium Q', color: 'text-amber-500', bg: 'bg-amber-500/10' },
                            { xp: '+3 XP', label: 'Hard Q', color: 'text-rose-500', bg: 'bg-rose-500/10' },
                            { xp: '+5/10 XP', label: 'Atom ✓', color: 'text-blue-500', bg: 'bg-blue-500/10' },
                            { xp: '+25/50 XP', label: 'Concept ✓', color: 'text-violet-500', bg: 'bg-violet-500/10' },
                        ].map((item, i) => (
                            <div key={i} className={`${item.bg} rounded-theme p-2.5`}>
                                <div className={`font-bold ${item.color}`}>{item.xp}</div>
                                <div className="text-theme-text-muted text-xs">{item.label}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Leaderboard Table */}
                <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                    <div className="px-6 py-4 border-b border-theme-border">
                        <h2 className="text-lg font-bold text-theme-text">Top Learners</h2>
                    </div>

                    {leaderboard.length === 0 ? (
                        <div className="text-center py-16 px-4">
                            <div className="text-5xl mb-4">🏅</div>
                            <p className="text-theme-text-muted">No learners yet. Be the first to earn XP!</p>
                        </div>
                    ) : (
                        <ul className="divide-y divide-theme-border">
                            {leaderboard.map((entry, idx) => (
                                <li
                                    key={entry.username}
                                    className={`flex items-center justify-between px-6 py-4 transition-colors border-l-4 ${
                                        entry.is_current_user
                                            ? 'bg-primary/5 border-primary'
                                            : entry.rank <= 3
                                                ? 'border-amber-400/50 bg-amber-500/5'
                                                : 'border-transparent hover:bg-surface-alt/50'
                                    }`}
                                >
                                    <div className="flex items-center space-x-4">
                                        <span className="text-2xl w-10 text-center flex-shrink-0">
                                            {getRankBadge(entry.rank)}
                                        </span>
                                        <div>
                                            <p className={`font-semibold ${entry.is_current_user ? 'text-primary' : 'text-theme-text'}`}>
                                                {entry.first_name || entry.username}
                                                {entry.last_name ? ` ${entry.last_name}` : ''}
                                                {entry.is_current_user && (
                                                    <span className="ml-2 text-xs bg-primary/15 text-primary px-2 py-0.5 rounded-full font-medium">
                                                        You
                                                    </span>
                                                )}
                                            </p>
                                            <p className="text-xs text-theme-text-muted mt-0.5">
                                                Q: {entry.questions_xp} · A: {entry.atoms_xp} · C: {entry.concepts_xp}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="text-right flex-shrink-0">
                                        <span className="text-xl font-bold text-theme-text">
                                            {entry.total_xp}
                                        </span>
                                        <span className="text-sm text-theme-text-muted ml-1">XP</span>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </main>
        </div>
    );
};

export default Leaderboard;
