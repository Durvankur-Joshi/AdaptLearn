import React, { useEffect, useState } from 'react';
import { useTeacher } from '../../context/TeacherContext';
import TeacherNavbar from './TeacherNavbar';

const GoalsManagement = () => {
    const [goals, setGoals] = useState([]);
    const [students, setStudents] = useState([]);
    const [concepts, setConcepts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [formData, setFormData] = useState({
        title: '', description: '', student: '', concept: '',
        deadline: '', target_mastery: 0.8, is_class_wide: false
    });
    const { teacherAxios } = useTeacher();

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [goalsRes, studentsRes, conceptsRes] = await Promise.all([
                teacherAxios.get('/auth/api/teacher/goals/'),
                teacherAxios.get('/auth/api/teacher/students/'),
                teacherAxios.get('/auth/api/teacher/concepts/'),
            ]);
            setGoals(goalsRes.data);
            setStudents(studentsRes.data);
            setConcepts(conceptsRes.data);
        } catch (err) {
            console.error('Failed to fetch:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateGoal = async () => {
        try {
            const payload = {
                ...formData,
                student: formData.is_class_wide ? null : formData.student || null,
                concept: formData.concept || null,
                deadline: formData.deadline || null,
            };
            await teacherAxios.post('/auth/api/teacher/goals/', payload);
            setShowForm(false);
            setFormData({ title: '', description: '', student: '', concept: '', deadline: '', target_mastery: 0.8, is_class_wide: false });
            fetchData();
        } catch (err) {
            console.error('Failed to create goal:', err);
        }
    };

    const handleUpdateStatus = async (goalId, newStatus) => {
        try {
            await teacherAxios.put('/auth/api/teacher/goal-update/', { goal_id: goalId, status: newStatus });
            fetchData();
        } catch (err) {
            console.error('Failed to update:', err);
        }
    };

    const statusColors = {
        active: 'bg-emerald-500/10 text-emerald-500',
        completed: 'bg-blue-500/10 text-blue-500',
        overdue: 'bg-error/10 text-error',
        cancelled: 'bg-surface-alt text-theme-text-muted',
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    const activeGoals = goals.filter(g => g.status === 'active');
    const completedGoals = goals.filter(g => g.status !== 'active');

    return (
        <div className="min-h-screen bg-theme-bg">
            <TeacherNavbar />
            <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-theme-text">🎯 Goals & Deadlines</h1>
                        <p className="text-theme-text-secondary mt-1">Assign goals and deadlines to students</p>
                    </div>
                    <button onClick={() => setShowForm(!showForm)}
                        className="px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-lg text-sm font-semibold hover:opacity-90">
                        + New Goal
                    </button>
                </div>

                {/* Create Goal Form */}
                {showForm && (
                    <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-theme-xl p-6 mb-6">
                        <h3 className="font-bold text-theme-text mb-4">🎯 Create New Goal</h3>
                        <div className="grid sm:grid-cols-2 gap-4">
                            <div className="sm:col-span-2">
                                <label className="block text-sm font-medium text-theme-text mb-1">Goal Title</label>
                                <input value={formData.title} onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                    placeholder="e.g., Complete Chapter 3 by Friday"
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" />
                            </div>
                            <div className="sm:col-span-2">
                                <label className="block text-sm font-medium text-theme-text mb-1">Description</label>
                                <textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    rows={2} className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" />
                            </div>
                            <div className="sm:col-span-2 flex items-center gap-2">
                                <input type="checkbox" checked={formData.is_class_wide}
                                    onChange={(e) => setFormData({ ...formData, is_class_wide: e.target.checked })}
                                    className="rounded" />
                                <label className="text-sm text-theme-text">Apply to all students (class-wide)</label>
                            </div>
                            {!formData.is_class_wide && (
                                <div>
                                    <label className="block text-sm font-medium text-theme-text mb-1">Student</label>
                                    <select value={formData.student} onChange={(e) => setFormData({ ...formData, student: e.target.value })}
                                        className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm">
                                        <option value="">Select Student</option>
                                        {students.map(s => <option key={s.id} value={s.id}>{s.name} (@{s.username})</option>)}
                                    </select>
                                </div>
                            )}
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Concept (optional)</label>
                                <select value={formData.concept} onChange={(e) => setFormData({ ...formData, concept: e.target.value })}
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm">
                                    <option value="">Select Concept</option>
                                    {concepts.map(c => <option key={c.id} value={c.id}>{c.name} ({c.subject})</option>)}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Deadline</label>
                                <input type="datetime-local" value={formData.deadline}
                                    onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Target Mastery</label>
                                <input type="number" step="0.1" min="0" max="1" value={formData.target_mastery}
                                    onChange={(e) => setFormData({ ...formData, target_mastery: parseFloat(e.target.value) })}
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" />
                            </div>
                        </div>
                        <div className="mt-4 flex gap-2">
                            <button onClick={handleCreateGoal} className="px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-semibold">Create Goal</button>
                            <button onClick={() => setShowForm(false)} className="px-4 py-2 bg-surface-alt text-theme-text rounded-lg text-sm">Cancel</button>
                        </div>
                    </div>
                )}

                {/* Active Goals */}
                <div className="mb-6">
                    <h2 className="text-lg font-bold text-theme-text mb-4">Active Goals ({activeGoals.length})</h2>
                    {activeGoals.length === 0 ? (
                        <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-8 text-center">
                            <p className="text-theme-text-muted">No active goals. Create one above!</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {activeGoals.map(goal => (
                                <div key={goal.id} className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-5">
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[goal.status]}`}>
                                                    {goal.status}
                                                </span>
                                                {goal.is_class_wide && (
                                                    <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500">Class-wide</span>
                                                )}
                                                {goal.concept_name && (
                                                    <span className="text-xs text-theme-text-muted">{goal.concept_name}</span>
                                                )}
                                            </div>
                                            <h3 className="font-bold text-theme-text">{goal.title}</h3>
                                            {goal.description && (
                                                <p className="text-sm text-theme-text-secondary mt-1">{goal.description}</p>
                                            )}
                                            <div className="flex items-center gap-4 mt-2 text-xs text-theme-text-muted">
                                                <span>👤 {goal.student_name || 'All Students'}</span>
                                                <span>🎯 Target: {(goal.target_mastery * 100).toFixed(0)}%</span>
                                                {goal.deadline && (
                                                    <span>📅 Due: {new Date(goal.deadline).toLocaleDateString()}</span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="flex gap-2 ml-4">
                                            <button onClick={() => handleUpdateStatus(goal.id, 'completed')}
                                                className="px-3 py-1.5 bg-emerald-500/10 text-emerald-500 rounded-lg text-xs font-semibold hover:bg-emerald-500/20">
                                                ✅ Complete
                                            </button>
                                            <button onClick={() => handleUpdateStatus(goal.id, 'cancelled')}
                                                className="px-3 py-1.5 bg-surface-alt text-theme-text-muted rounded-lg text-xs hover:bg-error/10 hover:text-error">
                                                Cancel
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Completed/Cancelled Goals */}
                {completedGoals.length > 0 && (
                    <div>
                        <h2 className="text-lg font-bold text-theme-text mb-4">Past Goals ({completedGoals.length})</h2>
                        <div className="space-y-3">
                            {completedGoals.map(goal => (
                                <div key={goal.id} className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-5 opacity-70">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[goal.status]}`}>
                                            {goal.status}
                                        </span>
                                        {goal.concept_name && (
                                            <span className="text-xs text-theme-text-muted">{goal.concept_name}</span>
                                        )}
                                    </div>
                                    <h3 className="font-medium text-theme-text">{goal.title}</h3>
                                    <p className="text-xs text-theme-text-muted mt-1">
                                        👤 {goal.student_name || 'All Students'} · Created {new Date(goal.created_at).toLocaleDateString()}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
};

export default GoalsManagement;
