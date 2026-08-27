import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from './Navbar';
import axios from '../axiosConfig';

const Dashboard = () => {
    const [concepts, setConcepts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedSubject, setSelectedSubject] = useState('');
    const [subjects, setSubjects] = useState([]);
    const [parentInviteCode, setParentInviteCode] = useState('');
    const [linkParentLoading, setLinkParentLoading] = useState(false);
    const [linkParentMessage, setLinkParentMessage] = useState({ type: '', text: '' });

    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLinkParent = async (e) => {
        e.preventDefault();
        const code = (parentInviteCode || '').trim();
        if (!code) return;
        setLinkParentMessage({ type: '', text: '' });
        setLinkParentLoading(true);
        try {
            await axios.post('/auth/api/link-parent/', { invite_code: code });
            setLinkParentMessage({ type: 'success', text: 'Successfully linked to parent.' });
            setParentInviteCode('');
        } catch (err) {
            setLinkParentMessage({
                type: 'error',
                text: err.response?.data?.error || 'Invalid or expired code. Please try again.',
            });
        } finally {
            setLinkParentLoading(false);
        }
    };

    const fetchConcepts = useCallback(async () => {
        try {
            const response = await axios.get('/auth/api/concepts/');
            setConcepts(response.data);
            
            const uniqueSubjects = [...new Set(response.data.map(c => c.subject))];
            setSubjects(uniqueSubjects);
        } catch (err) {
            console.error('Failed to fetch concepts:', err);
            setError('Failed to load concepts');
            
            if (err.response?.status === 401) {
                logout();
                navigate('/login');
            }
        } finally {
            setLoading(false);
        }
    }, [logout, navigate]);

    useEffect(() => {
        fetchConcepts();
    }, [fetchConcepts]);

    const handleStartLearning = (conceptId) => {
        navigate(`/learn/${conceptId}`);
    };

    const filteredConcepts = selectedSubject
        ? concepts.filter(c => c.subject === selectedSubject)
        : concepts;

    if (loading) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <div className="text-center animate-fade-in">
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-theme-text-secondary font-medium">Loading your dashboard...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-theme-bg">
            <Navbar />

            <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                {/* Welcome section */}
                <div className="mb-8 animate-fade-in-up">
                    <h1 className="text-3xl font-bold text-theme-text">
                        Welcome back, {user?.first_name || user?.username}
                    </h1>
                    <p className="text-theme-text-secondary mt-1">Ready to continue learning?</p>
                </div>

                {/* Error */}
                {error && (
                    <div className="mb-6 p-4 rounded-theme bg-error/10 border border-error/20 text-error text-sm font-medium animate-scale-in">
                        {error}
                    </div>
                )}

                {/* Quick Actions */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8 stagger">
                    {[
                        { label: 'New Session', icon: '▶️', color: 'from-emerald-500 to-teal-600', onClick: () => navigate('/learn/start') },
                        { label: 'Progress', icon: '📊', color: 'from-violet-500 to-purple-600', onClick: () => navigate('/progress') },
                        { label: 'Leaderboard', icon: '🏆', color: 'from-amber-500 to-orange-600', onClick: () => navigate('/leaderboard') },
                        { label: 'Refresh', icon: '🔄', color: 'from-blue-500 to-indigo-600', onClick: () => window.location.reload() },
                    ].map((action, i) => (
                        <button
                            key={i}
                            onClick={action.onClick}
                            className={`bg-gradient-to-br ${action.color} text-white rounded-theme-xl p-5 text-center shadow-theme hover:shadow-theme-lg hover:-translate-y-0.5 transition-all duration-200`}
                        >
                            <span className="text-2xl block mb-2">{action.icon}</span>
                            <span className="font-semibold text-sm">{action.label}</span>
                        </button>
                    ))}
                </div>

                {/* Concepts Section */}
                <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                    <div className="px-6 py-5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-theme-border">
                        <div>
                            <h2 className="text-xl font-bold text-theme-text">Available Concepts</h2>
                            <p className="text-sm text-theme-text-muted mt-0.5">Select a concept to start learning</p>
                        </div>
                        
                        {subjects.length > 0 && (
                            <select
                                value={selectedSubject}
                                onChange={(e) => setSelectedSubject(e.target.value)}
                                className="px-4 py-2 rounded-theme bg-surface-alt border border-theme-border text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                            >
                                <option value="">All Subjects</option>
                                {subjects.map(subject => (
                                    <option key={subject} value={subject}>{subject}</option>
                                ))}
                            </select>
                        )}
                    </div>
                    
                    {filteredConcepts.length === 0 ? (
                        <div className="text-center py-16 px-4">
                            <div className="text-5xl mb-4">📖</div>
                            <h3 className="text-lg font-semibold text-theme-text mb-2">No concepts yet</h3>
                            <p className="text-theme-text-muted mb-6">Start a new session to create your first concept!</p>
                            <button
                                onClick={() => navigate('/learn/start')}
                                className="px-6 py-2.5 gradient-primary text-white rounded-theme font-semibold hover:opacity-90 transition-opacity shadow-theme"
                            >
                                Start New Session
                            </button>
                        </div>
                    ) : (
                        <div className="divide-y divide-theme-border">
                            {filteredConcepts.map((concept, idx) => (
                                <div
                                    key={concept.id}
                                    className="px-6 py-4 flex items-center justify-between hover:bg-surface-alt/50 transition-colors group"
                                    style={{ animationDelay: `${idx * 0.05}s` }}
                                >
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center text-white font-bold text-sm shadow-sm flex-shrink-0">
                                                {concept.name.charAt(0)}
                                            </div>
                                            <div className="min-w-0">
                                                <p className="font-semibold text-theme-text truncate">
                                                    {concept.name}
                                                </p>
                                                <div className="flex items-center gap-2 text-xs text-theme-text-muted mt-0.5">
                                                    <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">{concept.subject}</span>
                                                    <span className="capitalize">
                                                        {concept.difficulty}
                                                    </span>
                                                    {concept.description && (
                                                        <span className="hidden sm:inline truncate max-w-xs">
                                                            · {concept.description}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => handleStartLearning(concept.id)}
                                        className="ml-4 px-4 py-2 rounded-theme bg-primary/10 text-primary font-semibold text-sm hover:bg-primary hover:text-white transition-all duration-200 flex-shrink-0"
                                    >
                                        Learn →
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Link to parent */}
                <div className="mt-6 bg-surface rounded-theme-xl border border-theme-border p-5 animate-fade-in-up" style={{ animationDelay: '0.25s' }}>
                    <h3 className="text-base font-semibold text-theme-text mb-2">Link your account to a parent</h3>
                    <p className="text-sm text-theme-text-secondary mb-3">
                        If a parent gave you an invite code, enter it below so they can see your learning insights.
                    </p>
                    <form onSubmit={handleLinkParent} className="flex flex-wrap items-center gap-2">
                        <input
                            type="text"
                            value={parentInviteCode}
                            onChange={(e) => setParentInviteCode(e.target.value)}
                            placeholder="Enter invite code"
                            className="px-3 py-2 rounded-theme bg-surface-alt border border-theme-border text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 w-40"
                        />
                        <button
                            type="submit"
                            disabled={linkParentLoading}
                            className="px-4 py-2 rounded-theme bg-violet-500/20 text-violet-600 dark:text-violet-400 font-medium text-sm hover:bg-violet-500/30 disabled:opacity-50"
                        >
                            {linkParentLoading ? 'Linking...' : 'Link'}
                        </button>
                    </form>
                    {linkParentMessage.text && (
                        <p className={`mt-2 text-sm ${linkParentMessage.type === 'success' ? 'text-emerald-600 dark:text-emerald-400' : 'text-error'}`}>
                            {linkParentMessage.text}
                        </p>
                    )}
                </div>

                {/* Tip */}
                <div className="mt-6 bg-info/5 border border-info/20 p-4 rounded-theme-lg flex items-start gap-3 animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
                    <span className="text-info mt-0.5">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                        </svg>
                    </span>
                    <p className="text-sm text-info/80">
                        <strong>How it works:</strong> For each concept, you'll learn one atomic piece at a time, 
                        then take a short quiz. The system adapts to your pace and mastery level.
                    </p>
                </div>
            </main>
        </div>
    );
};

export default Dashboard;