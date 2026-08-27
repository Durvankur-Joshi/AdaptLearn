// frontend/src/components/Planner/StudyPlanner.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import axios from '../../axiosConfig';
import {
    Calendar, Clock, BookOpen, Target, Plus, Trash2,
    ChevronDown, ChevronUp, Loader2, CheckCircle, X,
    Sparkles, Brain, Zap, Save, Edit2
} from 'lucide-react';

const StudyPlanner = () => {
    const { user } = useAuth();
    const navigate = useNavigate();

    // State for planners list and active planner
    const [planners, setPlanners] = useState([]);
    const [activePlanner, setActivePlanner] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // UI state
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [creatingPlanner, setCreatingPlanner] = useState(false);
    const [expandedDays, setExpandedDays] = useState({});
    const [selectedDay, setSelectedDay] = useState(null);
    const [showTopicsModal, setShowTopicsModal] = useState(false);

    // Form state for creating new planner
    const [formData, setFormData] = useState({
        goal_type: 'study',
        day_option: 'mon_fri',
        free_hours_per_day: 2,
        subjects: [
            { subject_name: '', priority: 1 }
        ]
    });

    // Fetch user's planners on mount with delay
    useEffect(() => {
        const timer = setTimeout(() => {
            fetchPlanners();
        }, 800); // 800ms delay
        return () => clearTimeout(timer);
    }, []);

    const fetchPlanners = async () => {
        setLoading(true);
        setError('');
        try {
            const response = await axios.get('/auth/my-planner/');
            console.log('Planners response:', response.data);

            // Handle different response formats
            let plannersData = [];
            if (Array.isArray(response.data)) {
                plannersData = response.data;
            } else if (response.data && Array.isArray(response.data.results)) {
                plannersData = response.data.results;
            } else if (response.data && typeof response.data === 'object') {
                plannersData = [response.data];
            }

            setPlanners(plannersData);
            if (plannersData.length > 0) {
                setActivePlanner(plannersData[0]);
            }
        } catch (error) {
            console.error('Failed to fetch planners:', error);
            setError('Failed to load planners. Please try again.');
            setPlanners([]);
        } finally {
            setLoading(false);
        }
    };

    // Handle form input changes
    const handleInputChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    // Handle subject changes
    const handleSubjectChange = (index, field, value) => {
        const updatedSubjects = [...formData.subjects];
        updatedSubjects[index][field] = value;
        setFormData({ ...formData, subjects: updatedSubjects });
    };

    // Add new subject field
    const addSubject = () => {
        setFormData({
            ...formData,
            subjects: [...formData.subjects, { subject_name: '', priority: 1 }]
        });
    };

    // Remove subject field
    const removeSubject = (index) => {
        if (formData.subjects.length > 1) {
            const updatedSubjects = formData.subjects.filter((_, i) => i !== index);
            setFormData({ ...formData, subjects: updatedSubjects });
        }
    };

    // Create new planner and delete old one automatically
    const handleCreatePlanner = async (e) => {
        e.preventDefault();
        setCreatingPlanner(true);
        setError('');

        try {
            // Delete previous planner if exists
            if (activePlanner && activePlanner.id) {
                try {
                    await axios.delete(`/auth/delete-planner/${activePlanner.id}/`);
                } catch (delErr) {
                    console.error('Failed to delete previous planner:', delErr);
                    // Optionally show error, but continue
                }
            }

            // Add delay before creating new planner
            await new Promise(resolve => setTimeout(resolve, 800));

            const response = await axios.post('/auth/create-planner/', formData);
            console.log('Create planner response:', response.data);

            // Add new planner to list
            const currentPlanners = Array.isArray(planners) ? planners : [];
            const newPlanner = response.data;

            const updatedPlanners = [newPlanner]; // Only new planner
            setPlanners(updatedPlanners);
            setActivePlanner(newPlanner);
            setShowCreateForm(false);
            resetForm();

            setError('');
        } catch (error) {
            console.error('Failed to create planner:', error);
            setError(error.response?.data?.error || 'Failed to create planner. Please try again.');
        } finally {
            setCreatingPlanner(false);
        }
    };

    // Reset form
    const resetForm = () => {
        setFormData({
            goal_type: 'study',
            day_option: 'mon_fri',
            free_hours_per_day: 2,
            subjects: [{ subject_name: '', priority: 1 }]
        });
    };

    // Toggle day expansion
    const toggleDay = (day) => {
        setExpandedDays(prev => ({
            ...(prev || {}),
            [day]: !(prev?.[day] || false)
        }));
    };

    // View topics for a specific day
    const viewDayTopics = (day, sessions) => {
        setSelectedDay({ name: day, sessions });
        setShowTopicsModal(true);
    };

    // Switch between planners
    const switchPlanner = (planner) => {
        setActivePlanner(planner);
        setExpandedDays({}); // Reset expanded days
    };

    // Get current day name
    const getCurrentDay = () => {
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        return days[new Date().getDay()];
    };

    // Get day name
    const getDayName = (day) => {
        const days = {
            'Monday': 'Monday',
            'Tuesday': 'Tuesday',
            'Wednesday': 'Wednesday',
            'Thursday': 'Thursday',
            'Friday': 'Friday',
            'Saturday': 'Saturday',
            'Sunday': 'Sunday'
        };
        return days[day] || day;
    };

    // Format goal type for display
    const formatGoalType = (goal) => {
        const goals = {
            'study': 'Regular Study',
            'exam': 'Exam Preparation',
            'exam_preparation': 'Exam Preparation',
            'other': 'Other'
        };
        return goals[goal] || goal;
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-theme-text-secondary">Loading your study plans...</p>
                </div>
            </div>
        );
    }

    const currentDay = getCurrentDay();

    return (
        <div className="min-h-screen bg-theme-bg py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Header with Create Button */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-theme-text flex items-center gap-2">
                            <Brain className="w-8 h-8 text-primary" />
                            AI Study Planner
                        </h1>
                        <p className="text-theme-text-secondary mt-1">
                            Create personalized study plans with AI-generated topics
                        </p>
                    </div>

                    {!showCreateForm && (
                        <button
                            onClick={() => {
                                resetForm();
                                setShowCreateForm(true);
                            }}
                            className="px-4 py-2 gradient-primary text-white rounded-lg font-semibold hover:opacity-90 transition-opacity flex items-center gap-2 shadow-lg hover:shadow-xl"
                        >
                            <Plus className="w-4 h-4" />
                            Create New Plan
                        </button>
                    )}
                </div>

                {/* Error Message */}
                {error && (
                    <div className="mb-6 p-4 bg-error/10 border border-error/20 rounded-theme-lg text-error flex items-center justify-between">
                        <span>{error}</span>
                        <button onClick={() => setError('')} className="text-error hover:text-error/80">
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                )}

                {/* Create Plan Form */}
                {showCreateForm && (
                    <div className="bg-surface rounded-theme-xl shadow-theme-lg border border-theme-border p-6 mb-8 animate-fade-in-up">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold text-theme-text flex items-center gap-2">
                                <Sparkles className="w-5 h-5 text-primary" />
                                Create New Study Plan
                            </h2>
                            <button
                                onClick={() => setShowCreateForm(false)}
                                className="p-2 hover:bg-surface-alt rounded-lg transition-colors"
                            >
                                <X className="w-5 h-5 text-theme-text-secondary" />
                            </button>
                        </div>

                        <form onSubmit={handleCreatePlanner}>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                                {/* Goal Type */}
                                <div>
                                    <label className="block text-sm font-medium text-theme-text-secondary mb-2">
                                        Goal Type
                                    </label>
                                    <select
                                        name="goal_type"
                                        value={formData.goal_type}
                                        onChange={handleInputChange}
                                        className="w-full px-3 py-2 bg-theme-bg border border-theme-border rounded-lg text-theme-text focus:ring-2 focus:ring-primary/50"
                                    >
                                        <option value="study">Regular Study</option>
                                        <option value="exam">Exam Preparation</option>
                                        <option value="other">Other</option>
                                    </select>
                                </div>

                                {/* Day Option */}
                                <div>
                                    <label className="block text-sm font-medium text-theme-text-secondary mb-2">
                                        Study Days
                                    </label>
                                    <select
                                        name="day_option"
                                        value={formData.day_option}
                                        onChange={handleInputChange}
                                        className="w-full px-3 py-2 bg-theme-bg border border-theme-border rounded-lg text-theme-text focus:ring-2 focus:ring-primary/50"
                                    >
                                        <option value="mon_fri">Monday to Friday</option>
                                        <option value="mon_sun">Monday to Sunday</option>
                                    </select>
                                </div>

                                {/* Free Hours Per Day */}
                                <div>
                                    <label className="block text-sm font-medium text-theme-text-secondary mb-2">
                                        Free Hours Per Day
                                    </label>
                                    <input
                                        type="number"
                                        name="free_hours_per_day"
                                        value={formData.free_hours_per_day}
                                        onChange={handleInputChange}
                                        min="1"
                                        max="12"
                                        className="w-full px-3 py-2 bg-theme-bg border border-theme-border rounded-lg text-theme-text focus:ring-2 focus:ring-primary/50"
                                    />
                                </div>
                            </div>

                            {/* Subjects */}
                            <div className="mb-6">
                                <label className="block text-sm font-medium text-theme-text-secondary mb-3">
                                    Subjects to Study
                                </label>

                                {formData.subjects.map((subject, index) => (
                                    <div key={index} className="flex gap-3 mb-3">
                                        <input
                                            type="text"
                                            value={subject.subject_name}
                                            onChange={(e) => handleSubjectChange(index, 'subject_name', e.target.value)}
                                            placeholder="e.g., Data Structures and Algorithms"
                                            className="flex-1 px-3 py-2 bg-theme-bg border border-theme-border rounded-lg text-theme-text focus:ring-2 focus:ring-primary/50"
                                            required
                                        />
                                        <select
                                            value={subject.priority}
                                            onChange={(e) => handleSubjectChange(index, 'priority', parseInt(e.target.value))}
                                            className="w-32 px-3 py-2 bg-theme-bg border border-theme-border rounded-lg text-theme-text focus:ring-2 focus:ring-primary/50"
                                        >
                                            <option value={1}>High</option>
                                            <option value={2}>Medium</option>
                                            <option value={3}>Low</option>
                                        </select>
                                        <button
                                            type="button"
                                            onClick={() => removeSubject(index)}
                                            className="p-2 text-error hover:bg-error/10 rounded-lg transition-colors"
                                            disabled={formData.subjects.length === 1}
                                        >
                                            <Trash2 className="w-5 h-5" />
                                        </button>
                                    </div>
                                ))}

                                <button
                                    type="button"
                                    onClick={addSubject}
                                    className="mt-2 px-3 py-1.5 text-primary border border-primary/20 rounded-lg text-sm font-medium hover:bg-primary/5 transition-colors flex items-center gap-1"
                                >
                                    <Plus className="w-4 h-4" />
                                    Add Another Subject
                                </button>
                            </div>

                            {/* Form Actions */}
                            <div className="flex gap-3">
                                <button
                                    type="submit"
                                    disabled={creatingPlanner}
                                    className="px-6 py-2 gradient-primary text-white rounded-lg font-semibold hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                >
                                    {creatingPlanner && <Loader2 className="w-4 h-4 animate-spin" />}
                                    <Save className="w-4 h-4" />
                                    Generate AI Study Plan
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setShowCreateForm(false)}
                                    disabled={creatingPlanner}
                                    className="px-6 py-2 bg-surface-alt text-theme-text rounded-lg font-semibold hover:bg-surface-alt/80 transition-colors disabled:opacity-50"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {/* Planner Tabs (if multiple planners) */}
                {!showCreateForm && planners.length > 1 && (
                    <div className="mb-6">
                        <h2 className="text-sm font-medium text-theme-text-secondary mb-3">Your Study Plans</h2>
                        <div className="flex gap-2 flex-wrap">
                            {planners.map((planner) => (
                                <button
                                    key={planner.id}
                                    onClick={() => switchPlanner(planner)}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activePlanner?.id === planner.id
                                            ? 'gradient-primary text-white shadow-md'
                                            : 'bg-surface-alt text-theme-text-secondary hover:text-theme-text hover:bg-surface-alt/80'
                                        }`}
                                >
                                    {formatGoalType(planner.goal_type)} • {new Date(planner.created_at).toLocaleDateString()}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Active Planner Display */}
                {!showCreateForm && activePlanner && (
                    <div className="space-y-6">
                        {/* Planner Header */}
                        <div className="bg-surface rounded-theme-xl shadow-theme-lg border border-theme-border overflow-hidden">
                            <div className="gradient-primary px-6 py-4 text-white">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h2 className="text-xl font-bold flex items-center gap-2">
                                            <Sparkles className="w-5 h-5" />
                                            {formatGoalType(activePlanner.goal_type)}
                                        </h2>
                                        <p className="text-sm text-white/80">
                                            Created on {new Date(activePlanner.created_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className="flex items-center gap-1 bg-white/20 px-3 py-1.5 rounded-lg">
                                            <Clock className="w-4 h-4" />
                                            <span className="text-sm font-medium">{activePlanner.free_hours_per_day} hrs/day</span>
                                        </div>
                                        <div className="flex items-center gap-1 bg-white/20 px-3 py-1.5 rounded-lg">
                                            <Calendar className="w-4 h-4" />
                                            <span className="text-sm font-medium">
                                                {activePlanner.day_option === 'mon_fri' ? 'Mon-Fri' : 'Mon-Sun'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Subjects Overview */}
                            <div className="p-6 border-b border-theme-border">
                                <h3 className="font-semibold text-theme-text mb-4 flex items-center gap-2">
                                    <BookOpen className="w-4 h-4 text-primary" />
                                    Your Subjects with AI-Generated Topics
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {activePlanner.subjects?.map((subject, idx) => (
                                        <div key={idx} className="bg-surface-alt rounded-lg p-4 hover:shadow-md transition-shadow">
                                            <div className="flex items-center justify-between mb-3">
                                                <h4 className="font-medium text-theme-text">{subject.subject_name}</h4>
                                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${subject.priority === 1 ? 'bg-red-500/10 text-red-500' :
                                                        subject.priority === 2 ? 'bg-yellow-500/10 text-yellow-500' :
                                                            'bg-green-500/10 text-green-500'
                                                    }`}>
                                                    Priority {subject.priority}
                                                </span>
                                            </div>
                                            <div className="flex flex-wrap gap-2">
                                                {subject.topics?.map((topic, i) => (
                                                    <span key={i} className="text-xs px-2 py-1 bg-primary/10 text-primary rounded-full">
                                                        {topic}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Weekly Schedule */}
                            <div className="p-6">
                                <h3 className="font-semibold text-theme-text mb-4 flex items-center gap-2">
                                    <Calendar className="w-4 h-4 text-primary" />
                                    Weekly Study Schedule
                                </h3>
                                <div className="space-y-3">
                                    {Object.entries(activePlanner.timetable || {}).map(([day, sessions]) => {
                                        const isToday = day === currentDay;

                                        return (
                                            <div key={day} className="border border-theme-border rounded-lg overflow-hidden">
                                                <button
                                                    onClick={() => toggleDay(day)}
                                                    className={`w-full px-4 py-3 flex items-center justify-between ${isToday ? 'bg-primary/5' : 'bg-surface-alt/50'
                                                        } hover:bg-surface-alt transition-colors`}
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <h4 className={`font-medium ${isToday ? 'text-primary' : 'text-theme-text'}`}>
                                                            {getDayName(day)}
                                                        </h4>
                                                        {isToday && (
                                                            <span className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-full">
                                                                Today
                                                            </span>
                                                        )}
                                                    </div>
                                                    <div className="flex items-center gap-4">
                                                        <span className="text-sm text-theme-text-secondary">
                                                            {sessions.length} sessions
                                                        </span>
                                                        {expandedDays[day] ? (
                                                            <ChevronUp className="w-4 h-4 text-theme-text-muted" />
                                                        ) : (
                                                            <ChevronDown className="w-4 h-4 text-theme-text-muted" />
                                                        )}
                                                    </div>
                                                </button>

                                                {expandedDays[day] && (
                                                    <div className="p-4 space-y-3 animate-fade-in">
                                                        {sessions.map((session, idx) => (
                                                            <div
                                                                key={idx}
                                                                className="flex items-center justify-between p-3 bg-surface-alt rounded-lg cursor-pointer hover:bg-surface-alt/80 transition-colors group"
                                                                onClick={() => viewDayTopics(day, [session])}
                                                            >
                                                                <div className="flex items-center gap-3 flex-1">
                                                                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold group-hover:bg-primary/20 transition-colors">
                                                                        {session.hour}
                                                                    </div>
                                                                    <div className="flex-1">
                                                                        <h5 className="font-medium text-theme-text">{session.subject}</h5>
                                                                        <p className="text-sm text-theme-text-secondary flex items-center gap-1">
                                                                            <BookOpen className="w-3 h-3" />
                                                                            {session.topic}
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                                <div className="flex items-center gap-3">
                                                                    <span className="text-xs text-theme-text-muted">
                                                                        {session.hours} hrs
                                                                    </span>
                                                                    {session.status === 'completed' && (
                                                                        <CheckCircle className="w-4 h-4 text-emerald-500" />
                                                                    )}
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>

                        {/* AI Tips */}
                        <div className="bg-gradient-to-br from-primary/5 to-accent/5 rounded-theme-xl p-6 border border-theme-border">
                            <div className="flex items-start gap-4">
                                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                                    <Zap className="w-5 h-5 text-primary" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-theme-text mb-2">AI-Generated Learning Path</h3>
                                    <p className="text-sm text-theme-text-secondary mb-3">
                                        Your study plan has been personalized based on your subjects and goals.
                                        Each topic is carefully selected to build your knowledge progressively.
                                    </p>
                                    <div className="flex gap-4 text-xs text-theme-text-muted">
                                        <span>✓ {activePlanner.subjects?.reduce((acc, s) => acc + (s.topics?.length || 0), 0)} total topics</span>
                                        <span>✓ {Object.keys(activePlanner.timetable || {}).length} study days</span>
                                        <span>✓ {activePlanner.free_hours_per_day} hours per day</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Empty State - No Planners */}
                {!showCreateForm && planners.length === 0 && (
                    <div className="text-center py-12">
                        <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Calendar className="w-10 h-10 text-primary" />
                        </div>
                        <h3 className="text-xl font-bold text-theme-text mb-2">No Study Plans Yet</h3>
                        <p className="text-theme-text-secondary mb-6">
                            Create your first AI-powered study plan to get personalized learning topics
                        </p>
                        <button
                            onClick={() => {
                                resetForm();
                                setShowCreateForm(true);
                            }}
                            className="px-6 py-3 gradient-primary text-white rounded-lg font-semibold hover:opacity-90 transition-opacity inline-flex items-center gap-2"
                        >
                            <Plus className="w-4 h-4" />
                            Create Your First Plan
                        </button>
                    </div>
                )}

                {/* Topics Modal */}
                {showTopicsModal && selectedDay && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                        <div className="bg-surface rounded-theme-xl shadow-theme-xl max-w-lg w-full max-h-[80vh] overflow-hidden animate-scale-in">
                            <div className="gradient-primary px-6 py-4 text-white flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <BookOpen className="w-5 h-5" />
                                    <h3 className="font-semibold text-lg">{selectedDay.name}'s Topics</h3>
                                </div>
                                <button
                                    onClick={() => setShowTopicsModal(false)}
                                    className="p-1 hover:bg-white/20 rounded-lg transition-colors"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
                                <div className="space-y-4">
                                    {selectedDay.sessions.map((session, idx) => (
                                        <div key={idx} className="bg-surface-alt rounded-lg p-4">
                                            <div className="flex items-center justify-between mb-2">
                                                <h4 className="font-semibold text-theme-text">{session.subject}</h4>
                                                <span className="text-xs px-2 py-1 bg-primary/10 text-primary rounded-full">
                                                    Hour {session.hour}
                                                </span>
                                            </div>
                                            <p className="text-theme-text-secondary mb-3">{session.topic}</p>
                                            <div className="flex items-center justify-between text-sm">
                                                <span className="text-theme-text-muted flex items-center gap-1">
                                                    <Clock className="w-3 h-3" />
                                                    {session.hours} hours
                                                </span>
                                                <button
                                                    onClick={() => {
                                                        setShowTopicsModal(false);
                                                        navigate('/learn/start', {
                                                            state: {
                                                                subject: session.subject,
                                                                topic: session.topic,
                                                                planner_id: activePlanner?.id
                                                            }
                                                        });
                                                    }}
                                                    className="px-3 py-1.5 gradient-primary text-white rounded-lg text-xs font-medium hover:opacity-90 transition-opacity"
                                                >
                                                    Start Learning
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="px-6 py-4 border-t border-theme-border bg-surface-alt/30">
                                <button
                                    onClick={() => setShowTopicsModal(false)}
                                    className="w-full px-4 py-2 bg-surface text-theme-text rounded-lg font-medium hover:bg-surface-alt transition-colors"
                                >
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default StudyPlanner;