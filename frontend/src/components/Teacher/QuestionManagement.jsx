import React, { useEffect, useState, useMemo } from 'react';
import { useTeacher } from '../../context/TeacherContext';
import TeacherNavbar from './TeacherNavbar';

const QuestionManagement = () => {
    const [questions, setQuestions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filterStatus, setFilterStatus] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');
    const [showAddForm, setShowAddForm] = useState(false);
    const [editingQuestion, setEditingQuestion] = useState(null);
    const [concepts, setConcepts] = useState([]);
    const [expandedSubjects, setExpandedSubjects] = useState({});
    const [expandedConcepts, setExpandedConcepts] = useState({});
    const [expandedAtoms, setExpandedAtoms] = useState({});
    const [addForm, setAddForm] = useState({
        atom_id: '', question_text: '', options: ['', '', '', ''],
        correct_index: 0, difficulty: 'medium', cognitive_operation: 'apply'
    });
    const [editForm, setEditForm] = useState({
        edited_question_text: '', edited_options: ['', '', '', ''], edited_correct_index: 0
    });
    const { teacherAxios } = useTeacher();

    useEffect(() => {
        fetchData();
    }, [filterStatus]);

    const fetchData = async () => {
        try {
            const [qRes, cRes] = await Promise.all([
                teacherAxios.get(`/auth/api/teacher/questions/?status=${filterStatus}`),
                teacherAxios.get('/auth/api/teacher/concepts/'),
            ]);
            setQuestions(qRes.data);
            setConcepts(cRes.data);
        } catch (err) {
            console.error('Failed to fetch:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleApprove = async (questionId, action, feedback = '') => {
        try {
            const payload = { question_id: questionId, action, feedback };
            if (action === 'edit' && editingQuestion) {
                payload.edited_question_text = editForm.edited_question_text;
                payload.edited_options = editForm.edited_options;
                payload.edited_correct_index = editForm.edited_correct_index;
            }
            await teacherAxios.post('/auth/api/teacher/question-approve/', payload);
            setEditingQuestion(null);
            fetchData();
        } catch (err) {
            console.error('Failed:', err);
        }
    };

    const handleAddQuestion = async () => {
        try {
            await teacherAxios.post('/auth/api/teacher/question-add/', {
                ...addForm,
                options: addForm.options.filter(o => o.trim()),
            });
            setShowAddForm(false);
            setAddForm({ atom_id: '', question_text: '', options: ['', '', '', ''], correct_index: 0, difficulty: 'medium', cognitive_operation: 'apply' });
            fetchData();
        } catch (err) {
            console.error('Failed to add question:', err);
        }
    };

    const startEditing = (q) => {
        setEditingQuestion(q.id);
        setEditForm({
            edited_question_text: q.question_text,
            edited_options: [...(q.options || [])],
            edited_correct_index: q.correct_index,
        });
    };

    // Build hierarchical tree: subject → concept → atom → questions
    const hierarchy = useMemo(() => {
        const filtered = questions.filter(q =>
            !searchTerm || q.question_text.toLowerCase().includes(searchTerm.toLowerCase()) ||
            q.atom_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            q.concept_name.toLowerCase().includes(searchTerm.toLowerCase())
        );

        const tree = {};
        filtered.forEach(q => {
            const subj = q.subject || 'Uncategorized';
            const concept = q.concept_name;
            const atom = q.atom_name;
            const atomId = q.atom_id;
            const conceptId = q.concept_id;

            if (!tree[subj]) tree[subj] = { concepts: {}, count: 0, statusCounts: {} };
            tree[subj].count++;
            tree[subj].statusCounts[q.approval_status] = (tree[subj].statusCounts[q.approval_status] || 0) + 1;

            if (!tree[subj].concepts[conceptId]) tree[subj].concepts[conceptId] = { name: concept, atoms: {}, count: 0 };
            tree[subj].concepts[conceptId].count++;

            if (!tree[subj].concepts[conceptId].atoms[atomId]) tree[subj].concepts[conceptId].atoms[atomId] = { name: atom, questions: [], count: 0 };
            tree[subj].concepts[conceptId].atoms[atomId].questions.push(q);
            tree[subj].concepts[conceptId].atoms[atomId].count++;
        });
        return tree;
    }, [questions, searchTerm]);

    const toggleSubject = (subj) => setExpandedSubjects(p => ({ ...p, [subj]: !p[subj] }));
    const toggleConcept = (id) => setExpandedConcepts(p => ({ ...p, [id]: !p[id] }));
    const toggleAtom = (id) => setExpandedAtoms(p => ({ ...p, [id]: !p[id] }));

    const expandAll = () => {
        const s = {}, c = {}, a = {};
        Object.keys(hierarchy).forEach(subj => {
            s[subj] = true;
            Object.entries(hierarchy[subj].concepts).forEach(([cId, concept]) => {
                c[cId] = true;
                Object.keys(concept.atoms).forEach(aId => { a[aId] = true; });
            });
        });
        setExpandedSubjects(s); setExpandedConcepts(c); setExpandedAtoms(a);
    };
    const collapseAll = () => { setExpandedSubjects({}); setExpandedConcepts({}); setExpandedAtoms({}); };

    const statusColors = {
        pending: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
        approved: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
        rejected: 'bg-error/10 text-error border-error/20',
        edited: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
        disabled: 'bg-surface-alt text-theme-text-muted border-theme-border',
    };

    const statusIcons = { pending: '⏳', approved: '✅', rejected: '❌', edited: '✏️', disabled: '🚫' };

    if (loading) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    const totalQ = questions.length;
    const pendingQ = questions.filter(q => q.approval_status === 'pending').length;
    const approvedQ = questions.filter(q => q.approval_status === 'approved').length;

    return (
        <div className="min-h-screen bg-theme-bg">
            <TeacherNavbar />
            <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-theme-text">❓ Question Management</h1>
                        <p className="text-theme-text-secondary mt-1">Organized by Subject → Concept → Atom</p>
                    </div>
                    <button onClick={() => setShowAddForm(!showAddForm)}
                        className="px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity shadow-theme">
                        + Add Question
                    </button>
                </div>

                {/* Stats Bar */}
                <div className="grid grid-cols-3 sm:grid-cols-5 gap-3 mb-6">
                    {[
                        { label: 'Total', value: totalQ, color: 'text-theme-text' },
                        { label: 'Pending', value: pendingQ, color: 'text-amber-500' },
                        { label: 'Approved', value: approvedQ, color: 'text-emerald-500' },
                        { label: 'Subjects', value: Object.keys(hierarchy).length, color: 'text-blue-500' },
                        { label: 'Concepts', value: [...new Set(questions.map(q => q.concept_id))].length, color: 'text-violet-500' },
                    ].map((s, i) => (
                        <div key={i} className="bg-surface rounded-xl border border-theme-border p-3 text-center">
                            <div className={`text-xl font-bold ${s.color}`}>{s.value}</div>
                            <div className="text-xs text-theme-text-muted">{s.label}</div>
                        </div>
                    ))}
                </div>

                {/* Filters & Controls */}
                <div className="flex flex-wrap items-center gap-3 mb-6">
                    <div className="flex-1 min-w-[200px]">
                        <input type="text" placeholder="Search questions, atoms, concepts..."
                            value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full px-4 py-2.5 rounded-lg bg-surface border border-theme-border text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50" />
                    </div>
                    <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}
                        className="px-3 py-2.5 rounded-lg bg-surface border border-theme-border text-theme-text text-sm">
                        <option value="all">All Status</option>
                        <option value="pending">⏳ Pending</option>
                        <option value="approved">✅ Approved</option>
                        <option value="rejected">❌ Rejected</option>
                        <option value="edited">✏️ Edited</option>
                        <option value="disabled">🚫 Disabled</option>
                    </select>
                    <div className="flex gap-1">
                        <button onClick={expandAll}
                            className="px-3 py-2.5 rounded-lg bg-surface-alt text-theme-text-secondary text-xs font-medium hover:bg-surface-alt/80 transition-colors">
                            Expand All
                        </button>
                        <button onClick={collapseAll}
                            className="px-3 py-2.5 rounded-lg bg-surface-alt text-theme-text-secondary text-xs font-medium hover:bg-surface-alt/80 transition-colors">
                            Collapse All
                        </button>
                    </div>
                </div>

                {/* Add Question Form */}
                {showAddForm && (
                    <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-theme-xl p-6 mb-6">
                        <h3 className="font-bold text-theme-text mb-4">➕ Add New Question</h3>
                        <div className="grid sm:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Atom</label>
                                <select value={addForm.atom_id} onChange={(e) => setAddForm({ ...addForm, atom_id: e.target.value })}
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm">
                                    <option value="">Select Atom</option>
                                    {concepts.map(c => (
                                        <optgroup key={c.id} label={`${c.subject} → ${c.name}`}>
                                            {c.atoms?.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                                        </optgroup>
                                    ))}
                                </select>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                                <div>
                                    <label className="block text-sm font-medium text-theme-text mb-1">Difficulty</label>
                                    <select value={addForm.difficulty} onChange={(e) => setAddForm({ ...addForm, difficulty: e.target.value })}
                                        className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm">
                                        <option value="easy">Easy</option>
                                        <option value="medium">Medium</option>
                                        <option value="hard">Hard</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-theme-text mb-1">Cognitive Level</label>
                                    <select value={addForm.cognitive_operation} onChange={(e) => setAddForm({ ...addForm, cognitive_operation: e.target.value })}
                                        className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm">
                                        <option value="recall">Recall</option>
                                        <option value="apply">Apply</option>
                                        <option value="analyze">Analyze</option>
                                    </select>
                                </div>
                            </div>
                            <div className="sm:col-span-2">
                                <label className="block text-sm font-medium text-theme-text mb-1">Question Text</label>
                                <textarea value={addForm.question_text} onChange={(e) => setAddForm({ ...addForm, question_text: e.target.value })}
                                    rows={2} placeholder="Enter the question..." className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" />
                            </div>
                            {addForm.options.map((opt, i) => (
                                <div key={i}>
                                    <label className="block text-sm font-medium text-theme-text mb-1">
                                        Option {String.fromCharCode(65 + i)} {i === addForm.correct_index && <span className="text-emerald-500">(Correct)</span>}
                                    </label>
                                    <div className="flex gap-2">
                                        <input value={opt}
                                            onChange={(e) => {
                                                const opts = [...addForm.options]; opts[i] = e.target.value;
                                                setAddForm({ ...addForm, options: opts });
                                            }}
                                            placeholder={`Option ${String.fromCharCode(65 + i)}`}
                                            className="flex-1 px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" />
                                        <button onClick={() => setAddForm({ ...addForm, correct_index: i })}
                                            className={`px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                                                i === addForm.correct_index ? 'bg-emerald-500 text-white' : 'bg-surface-alt text-theme-text-muted hover:bg-emerald-500/10 hover:text-emerald-500'
                                            }`}>
                                            ✓
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="mt-4 flex gap-2">
                            <button onClick={handleAddQuestion} className="px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-semibold hover:bg-emerald-600 transition-colors">Add Question</button>
                            <button onClick={() => setShowAddForm(false)} className="px-4 py-2 bg-surface-alt text-theme-text rounded-lg text-sm">Cancel</button>
                        </div>
                    </div>
                )}

                {/* Hierarchical Question Tree */}
                {Object.keys(hierarchy).length === 0 ? (
                    <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-12 text-center">
                        <div className="text-5xl mb-4">📋</div>
                        <h3 className="text-lg font-semibold text-theme-text">No questions found</h3>
                        <p className="text-theme-text-muted">Try changing the filter or add a new question</p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {Object.entries(hierarchy).sort(([a], [b]) => a.localeCompare(b)).map(([subject, subjData]) => (
                            <div key={subject} className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden">
                                {/* Subject Header */}
                                <button onClick={() => toggleSubject(subject)}
                                    className="w-full px-6 py-4 flex items-center justify-between hover:bg-surface-alt/30 transition-colors">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white text-lg">
                                            📚
                                        </div>
                                        <div className="text-left">
                                            <h3 className="font-bold text-theme-text">{subject}</h3>
                                            <p className="text-xs text-theme-text-muted">
                                                {Object.keys(subjData.concepts).length} concept{Object.keys(subjData.concepts).length !== 1 ? 's' : ''} · {subjData.count} question{subjData.count !== 1 ? 's' : ''}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="hidden sm:flex items-center gap-1.5">
                                            {Object.entries(subjData.statusCounts).map(([status, count]) => (
                                                <span key={status} className={`text-xs px-2 py-0.5 rounded-full border ${statusColors[status]}`}>
                                                    {statusIcons[status]} {count}
                                                </span>
                                            ))}
                                        </div>
                                        <svg className={`w-5 h-5 text-theme-text-muted transition-transform ${
                                            expandedSubjects[subject] ? 'rotate-180' : ''
                                        }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                        </svg>
                                    </div>
                                </button>

                                {/* Concepts under this subject */}
                                {expandedSubjects[subject] && (
                                    <div className="border-t border-theme-border">
                                        {Object.entries(subjData.concepts).map(([conceptId, conceptData]) => (
                                            <div key={conceptId} className="border-b border-theme-border/50 last:border-b-0">
                                                <button onClick={() => toggleConcept(conceptId)}
                                                    className="w-full pl-10 pr-6 py-3 flex items-center justify-between hover:bg-surface-alt/20 transition-colors">
                                                    <div className="flex items-center gap-2.5">
                                                        <div className="w-7 h-7 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-500 text-sm">
                                                            📘
                                                        </div>
                                                        <div className="text-left">
                                                            <span className="font-semibold text-theme-text text-sm">{conceptData.name}</span>
                                                            <span className="text-xs text-theme-text-muted ml-2">{conceptData.count} Q</span>
                                                        </div>
                                                    </div>
                                                    <svg className={`w-4 h-4 text-theme-text-muted transition-transform ${
                                                        expandedConcepts[conceptId] ? 'rotate-180' : ''
                                                    }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                    </svg>
                                                </button>

                                                {expandedConcepts[conceptId] && (
                                                    <div className="bg-surface-alt/10">
                                                        {Object.entries(conceptData.atoms).map(([atomId, atomData]) => (
                                                            <div key={atomId}>
                                                                <button onClick={() => toggleAtom(atomId)}
                                                                    className="w-full pl-16 pr-6 py-2.5 flex items-center justify-between hover:bg-surface-alt/30 transition-colors">
                                                                    <div className="flex items-center gap-2">
                                                                        <div className="w-6 h-6 rounded-md bg-emerald-500/10 flex items-center justify-center text-emerald-500 text-xs">
                                                                            ⚛️
                                                                        </div>
                                                                        <span className="text-sm text-theme-text font-medium">{atomData.name}</span>
                                                                        <span className="text-xs px-1.5 py-0.5 rounded-full bg-surface-alt text-theme-text-muted">{atomData.count}</span>
                                                                    </div>
                                                                    <svg className={`w-3.5 h-3.5 text-theme-text-muted transition-transform ${
                                                                        expandedAtoms[atomId] ? 'rotate-180' : ''
                                                                    }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                                    </svg>
                                                                </button>

                                                                {expandedAtoms[atomId] && (
                                                                    <div className="pl-20 pr-6 pb-3 space-y-3">
                                                                        {atomData.questions.map(q => (
                                                                            <div key={q.id} className="bg-surface rounded-xl border border-theme-border p-4">
                                                                                <div className="flex items-center gap-2 mb-2 flex-wrap">
                                                                                    <span className={`text-xs px-2 py-0.5 rounded-full border ${statusColors[q.approval_status]}`}>
                                                                                        {statusIcons[q.approval_status]} {q.approval_status}
                                                                                    </span>
                                                                                    <span className="text-xs px-2 py-0.5 rounded-full bg-surface-alt text-theme-text-muted">{q.difficulty}</span>
                                                                                    <span className="text-xs px-2 py-0.5 rounded-full bg-surface-alt text-theme-text-muted">{q.cognitive_operation}</span>
                                                                                </div>

                                                                                {editingQuestion === q.id ? (
                                                                                    <div className="space-y-3">
                                                                                        <textarea value={editForm.edited_question_text}
                                                                                            onChange={(e) => setEditForm({ ...editForm, edited_question_text: e.target.value })}
                                                                                            rows={2} className="w-full px-3 py-2 rounded-lg bg-surface-alt border border-theme-border text-theme-text text-sm" />
                                                                                        <div className="grid grid-cols-2 gap-2">
                                                                                            {editForm.edited_options.map((opt, i) => (
                                                                                                <div key={i} className="flex gap-1">
                                                                                                    <input value={opt}
                                                                                                        onChange={(e) => {
                                                                                                            const opts = [...editForm.edited_options]; opts[i] = e.target.value;
                                                                                                            setEditForm({ ...editForm, edited_options: opts });
                                                                                                        }}
                                                                                                        className="flex-1 px-2 py-1.5 rounded-lg bg-surface-alt border border-theme-border text-theme-text text-xs" />
                                                                                                    <button onClick={() => setEditForm({ ...editForm, edited_correct_index: i })}
                                                                                                        className={`px-2 py-1.5 rounded-lg text-xs transition-colors ${
                                                                                                            i === editForm.edited_correct_index ? 'bg-emerald-500 text-white' : 'bg-surface-alt text-theme-text-muted'
                                                                                                        }`}>✓</button>
                                                                                                </div>
                                                                                            ))}
                                                                                        </div>
                                                                                        <div className="flex gap-2">
                                                                                            <button onClick={() => handleApprove(q.id, 'edit')}
                                                                                                className="px-3 py-1.5 bg-blue-500 text-white rounded-lg text-xs font-semibold">Save Edit</button>
                                                                                            <button onClick={() => setEditingQuestion(null)}
                                                                                                className="px-3 py-1.5 bg-surface-alt text-theme-text rounded-lg text-xs">Cancel</button>
                                                                                        </div>
                                                                                    </div>
                                                                                ) : (
                                                                                    <>
                                                                                        <p className="text-theme-text font-medium text-sm mb-2">{q.question_text}</p>
                                                                                        <div className="grid grid-cols-2 gap-1.5">
                                                                                            {q.options?.map((opt, i) => (
                                                                                                <div key={i} className={`px-3 py-1.5 rounded-lg text-xs ${
                                                                                                    i === q.correct_index
                                                                                                        ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 font-medium'
                                                                                                        : 'bg-surface-alt text-theme-text-secondary'
                                                                                                }`}>
                                                                                                    {String.fromCharCode(65 + i)}. {opt}
                                                                                                </div>
                                                                                            ))}
                                                                                        </div>

                                                                                        <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-theme-border/50">
                                                                                            {q.approval_status !== 'approved' && (
                                                                                                <button onClick={() => handleApprove(q.id, 'approve')}
                                                                                                    className="px-2.5 py-1 bg-emerald-500/10 text-emerald-500 rounded-lg text-xs font-medium hover:bg-emerald-500/20 transition-colors">
                                                                                                    ✅ Approve
                                                                                                </button>
                                                                                            )}
                                                                                            {q.approval_status !== 'rejected' && (
                                                                                                <button onClick={() => handleApprove(q.id, 'reject')}
                                                                                                    className="px-2.5 py-1 bg-error/10 text-error rounded-lg text-xs font-medium hover:bg-error/20 transition-colors">
                                                                                                    ❌ Reject
                                                                                                </button>
                                                                                            )}
                                                                                            <button onClick={() => startEditing(q)}
                                                                                                className="px-2.5 py-1 bg-blue-500/10 text-blue-500 rounded-lg text-xs font-medium hover:bg-blue-500/20 transition-colors">
                                                                                                ✏️ Edit
                                                                                            </button>
                                                                                            {q.approval_status !== 'disabled' && (
                                                                                                <button onClick={() => handleApprove(q.id, 'disable')}
                                                                                                    className="px-2.5 py-1 bg-surface-alt text-theme-text-muted rounded-lg text-xs font-medium hover:opacity-80 transition-opacity">
                                                                                                    🚫 Disable
                                                                                                </button>
                                                                                            )}
                                                                                        </div>

                                                                                        {q.approval_feedback && (
                                                                                            <div className="mt-2 p-2 rounded-lg bg-surface-alt text-xs text-theme-text-muted">
                                                                                                <strong>Feedback:</strong> {q.approval_feedback}
                                                                                            </div>
                                                                                        )}
                                                                                    </>
                                                                                )}
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
};

export default QuestionManagement;
