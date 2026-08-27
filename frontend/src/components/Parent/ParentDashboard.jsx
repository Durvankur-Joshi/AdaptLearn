import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useParent } from '../../context/ParentContext';
import ParentNavbar from './ParentNavbar';

const ParentDashboard = () => {
    const { parent, parentChildren, parentAxios, fetchChildren } = useParent();
    const [inviteCode, setInviteCode] = useState('');
    const [loadingCode, setLoadingCode] = useState(false);
    const [codeError, setCodeError] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        fetchChildren();
    }, [fetchChildren]);

    const handleGenerateCode = async () => {
        setCodeError('');
        setLoadingCode(true);
        try {
            const res = await parentAxios.post('/auth/api/parent/link-child/');
            setInviteCode(res.data.invite_code || '');
        } catch (err) {
            setCodeError(err.response?.data?.error || 'Failed to generate code');
        } finally {
            setLoadingCode(false);
        }
    };

    const children = parentChildren?.children || [];
    const pendingInvites = parentChildren?.pending_invites || [];
    const stats = parentChildren?.stats;

    return (
        <div className="min-h-screen bg-theme-bg">
            <ParentNavbar />

            <main className="max-w-5xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                <div className="mb-8 animate-fade-in-up">
                    <h1 className="text-3xl font-bold text-theme-text">Parent Dashboard</h1>
                    <p className="text-theme-text-secondary mt-1">
                        Welcome back, {parent?.first_name || parent?.username || 'Parent'}
                    </p>
                </div>

                {/* Quick stats cards */}
                {stats && (
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                        <div className="bg-surface rounded-theme-xl border border-theme-border p-4 shadow-theme">
                            <p className="text-sm font-medium text-theme-text-muted">Linked children</p>
                            <p className="text-2xl font-bold text-theme-text mt-1">{stats.total_children ?? 0}</p>
                        </div>
                        <div className="bg-surface rounded-theme-xl border border-theme-border p-4 shadow-theme">
                            <p className="text-sm font-medium text-theme-text-muted">Sessions this week (all children)</p>
                            <p className="text-2xl font-bold text-primary mt-1">{stats.total_sessions_last_7_days ?? 0}</p>
                        </div>
                        <div className="bg-surface rounded-theme-xl border border-theme-border p-4 shadow-theme">
                            <p className="text-sm font-medium text-theme-text-muted">Last activity</p>
                            <p className="text-lg font-semibold text-theme-text mt-1">
                                {stats.last_activity_at ? new Date(stats.last_activity_at).toLocaleDateString(undefined, { dateStyle: 'short' }) : '—'}
                            </p>
                        </div>
                    </div>
                )}

                {/* Add child: generate invite code */}
                <section className="mb-8 bg-surface rounded-theme-xl border border-theme-border p-6 shadow-theme">
                    <h2 className="text-lg font-semibold text-theme-text mb-3">Link a child&apos;s account</h2>
                    <p className="text-theme-text-secondary text-sm mb-4">
                        Generate a code and have your child enter it on their dashboard to link their account.
                    </p>
                    {codeError && (
                        <div className="mb-3 p-2 rounded-lg bg-error/10 text-error text-sm">{codeError}</div>
                    )}
                    <div className="flex flex-wrap items-center gap-3">
                        <button
                            type="button"
                            onClick={handleGenerateCode}
                            disabled={loadingCode}
                            className="px-4 py-2 bg-gradient-to-r from-violet-500 to-indigo-600 text-white rounded-lg font-medium hover:opacity-90 disabled:opacity-50"
                        >
                            {loadingCode ? 'Generating...' : 'Generate invite code'}
                        </button>
                        {inviteCode && (
                            <div className="flex items-center gap-2 px-4 py-2 bg-violet-500/10 rounded-lg border border-violet-500/30">
                                <span className="text-theme-text-secondary text-sm">Code:</span>
                                <span className="font-mono font-bold text-violet-600 dark:text-violet-400">{inviteCode}</span>
                            </div>
                        )}
                    </div>
                    {pendingInvites.length > 0 && !inviteCode && (
                        <p className="mt-2 text-sm text-theme-text-muted">
                            You have a pending code. Share it with your child or generate a new one above.
                        </p>
                    )}
                </section>

                {/* Linked children */}
                <section>
                    <h2 className="text-lg font-semibold text-theme-text mb-4">Linked children</h2>
                    {children.length === 0 ? (
                        <div className="bg-surface rounded-theme-xl border border-theme-border p-8 text-center text-theme-text-secondary">
                            <p>No linked children yet.</p>
                            <p className="text-sm mt-2">Generate an invite code above and have your child enter it on their dashboard.</p>
                        </div>
                    ) : (
                        <div className="grid gap-4 sm:grid-cols-2">
                            {children.map((c) => (
                                <div
                                    key={c.id}
                                    className="bg-surface rounded-theme-xl border border-theme-border p-5 shadow-theme hover:border-violet-500/30 transition-colors"
                                >
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="font-semibold text-theme-text">{c.child_name || c.child_username}</h3>
                                            <p className="text-sm text-theme-text-muted">
                                                Mastery: {c.overall_mastery != null ? `${Math.round(c.overall_mastery * 100)}%` : '—'} · XP: {c.total_xp ?? '—'}
                                            </p>
                                            {c.last_active && (
                                                <p className="text-xs text-theme-text-muted mt-1">
                                                    Last active: {new Date(c.last_active).toLocaleDateString()}
                                                </p>
                                            )}
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => navigate(`/parent/child/${c.child_id}/insights`)}
                                            className="px-3 py-1.5 text-sm font-medium text-violet-600 dark:text-violet-400 hover:bg-violet-500/10 rounded-lg transition-colors"
                                        >
                                            View insights
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </section>
            </main>
        </div>
    );
};

export default ParentDashboard;
