import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTeacher } from '../../context/TeacherContext';
import TeacherNavbar from './TeacherNavbar';

const TeacherDashboard = () => {
    const [dashData, setDashData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const { teacher, teacherAxios } = useTeacher();
    const navigate = useNavigate();

    useEffect(() => {
        fetchDashboard();
    }, []);

    const fetchDashboard = async () => {
        try {
            const res = await teacherAxios.get('/auth/api/teacher/dashboard/');
            setDashData(res.data);
        } catch (err) {
            setError('Failed to load dashboard');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <div className="text-center animate-fade-in">
                    <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-theme-text-secondary font-medium">Loading teacher dashboard...</p>
                </div>
            </div>
        );
    }

    const stats = dashData?.stats || {};
    const classAnalytics = dashData?.class_analytics || [];
    const struggling = dashData?.struggling_students || [];

    return (
        <div className="min-h-screen bg-theme-bg">
            <TeacherNavbar />

            <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                {/* Welcome */}
                <div className="mb-8 animate-fade-in-up">
                    <h1 className="text-3xl font-bold text-theme-text">
                        Teacher Dashboard
                    </h1>
                    <p className="text-theme-text-secondary mt-1">
                        Welcome back, {dashData?.teacher?.first_name || dashData?.teacher?.username || 'Teacher'}
                    </p>
                </div>

                {error && (
                    <div className="mb-6 p-4 rounded-theme bg-error/10 border border-error/20 text-error text-sm font-medium">
                        {error}
                    </div>
                )}

                {/* Quick Stats */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-8">
                    {[
                        { label: 'Students', value: stats.total_students || 0, icon: '👥', color: 'from-blue-500 to-indigo-600' },
                        { label: 'Concepts', value: stats.total_concepts || 0, icon: '📚', color: 'from-emerald-500 to-teal-600' },
                        { label: 'Pending Reviews', value: stats.pending_questions || 0, icon: '❓', color: 'from-amber-500 to-orange-600' },
                        { label: 'Active Overrides', value: stats.active_overrides || 0, icon: '🔧', color: 'from-violet-500 to-purple-600' },
                        { label: 'Active Goals', value: stats.active_goals || 0, icon: '🎯', color: 'from-rose-500 to-pink-600' },
                    ].map((stat, i) => (
                        <div key={i} className={`bg-gradient-to-br ${stat.color} text-white rounded-theme-xl p-5 shadow-theme`}>
                            <div className="text-2xl mb-1">{stat.icon}</div>
                            <div className="text-2xl font-bold">{stat.value}</div>
                            <div className="text-sm text-white/70">{stat.label}</div>
                        </div>
                    ))}
                </div>

                {/* Quick Actions */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
                    {[
                        { label: 'View Students', icon: '👥', onClick: () => navigate('/teacher/students') },
                        { label: 'Review Questions', icon: '❓', onClick: () => navigate('/teacher/questions') },
                        { label: 'Manage Content', icon: '📝', onClick: () => navigate('/teacher/content') },
                        { label: 'Class Analytics', icon: '📈', onClick: () => navigate('/teacher/analytics') },
                    ].map((action, i) => (
                        <button
                            key={i}
                            onClick={action.onClick}
                            className="bg-surface rounded-theme-xl border border-theme-border p-5 text-center shadow-theme hover:shadow-theme-lg hover:-translate-y-0.5 transition-all duration-200"
                        >
                            <span className="text-2xl block mb-2">{action.icon}</span>
                            <span className="font-semibold text-sm text-theme-text">{action.label}</span>
                        </button>
                    ))}
                </div>

                <div className="grid lg:grid-cols-2 gap-6">
                    {/* Class Mastery Overview */}
                    <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden">
                        <div className="px-6 py-4 border-b border-theme-border">
                            <h2 className="text-lg font-bold text-theme-text">📊 Class Mastery Overview</h2>
                            <p className="text-sm text-theme-text-muted">Average mastery per concept</p>
                        </div>
                        <div className="p-6 space-y-4 max-h-96 overflow-y-auto">
                            {classAnalytics.length === 0 ? (
                                <p className="text-theme-text-muted text-center py-8">No concepts yet</p>
                            ) : (
                                classAnalytics.map((c, i) => (
                                    <div key={i} className="space-y-2">
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <span className="font-medium text-theme-text text-sm">{c.concept_name}</span>
                                                <span className="ml-2 text-xs text-theme-text-muted">({c.subject})</span>
                                            </div>
                                            <div className="flex items-center gap-3 text-xs">
                                                <span className="text-theme-text-muted">{c.student_count} students</span>
                                                {c.weak_students > 0 && (
                                                    <span className="text-error font-medium">{c.weak_students} struggling</span>
                                                )}
                                                <span className="font-bold text-theme-text">{(c.avg_mastery * 100).toFixed(0)}%</span>
                                            </div>
                                        </div>
                                        <div className="w-full bg-surface-alt rounded-full h-2.5">
                                            <div
                                                className={`h-2.5 rounded-full transition-all duration-500 ${
                                                    c.avg_mastery >= 0.7 ? 'bg-emerald-500' :
                                                    c.avg_mastery >= 0.4 ? 'bg-amber-500' : 'bg-error'
                                                }`}
                                                style={{ width: `${Math.max(c.avg_mastery * 100, 2)}%` }}
                                            />
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Struggling Students */}
                    <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden">
                        <div className="px-6 py-4 border-b border-theme-border">
                            <h2 className="text-lg font-bold text-theme-text">🚨 Students Needing Help</h2>
                            <p className="text-sm text-theme-text-muted">Students with mastery below 40%</p>
                        </div>
                        <div className="divide-y divide-theme-border max-h-96 overflow-y-auto">
                            {struggling.length === 0 ? (
                                <p className="text-theme-text-muted text-center py-8">No struggling students! 🎉</p>
                            ) : (
                                struggling.map((s, i) => (
                                    <div key={i} className="px-6 py-4 hover:bg-surface-alt/50 transition-colors">
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="flex items-center gap-2">
                                                <div className="w-8 h-8 rounded-full bg-error/10 flex items-center justify-center text-error text-xs font-bold">
                                                    {s.student_name[0].toUpperCase()}
                                                </div>
                                                <div>
                                                    <span className="font-medium text-theme-text text-sm">{s.student_name}</span>
                                                    <span className="ml-2 text-xs text-theme-text-muted">@{s.username}</span>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => navigate(`/teacher/students?student=${s.student_id}`)}
                                                className="text-xs px-3 py-1 rounded-lg bg-emerald-500/10 text-emerald-500 font-medium hover:bg-emerald-500/20 transition-colors"
                                            >
                                                View →
                                            </button>
                                        </div>
                                        <div className="flex flex-wrap gap-2">
                                            {s.weak_areas.map((w, j) => (
                                                <span key={j} className="text-xs px-2 py-1 rounded-full bg-error/10 text-error">
                                                    {w.atom} ({(w.mastery * 100).toFixed(0)}%)
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default TeacherDashboard;
