import React, { useEffect, useState } from 'react';
import { useTeacher } from '../../context/TeacherContext';
import TeacherNavbar from './TeacherNavbar';

const ContentManagement = () => {
    const [contents, setContents] = useState([]);
    const [concepts, setConcepts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editingContent, setEditingContent] = useState(null);
    const [formData, setFormData] = useState({
        atom: '', explanation: '', analogy: '', examples: '[]', tips: '', status: 'published', priority: true
    });
    const [conceptForm, setConceptForm] = useState({ name: '', subject: '', description: '', difficulty: 'medium' });
    const [atomForm, setAtomForm] = useState({ concept_id: '', name: '', explanation: '', analogy: '', examples: '[]', order: 0 });
    const [showConceptForm, setShowConceptForm] = useState(false);
    const [showAtomForm, setShowAtomForm] = useState(false);
    const { teacherAxios } = useTeacher();

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [contentRes, conceptRes] = await Promise.all([
                teacherAxios.get('/auth/api/teacher/content/'),
                teacherAxios.get('/auth/api/teacher/concepts/'),
            ]);
            setContents(contentRes.data);
            setConcepts(conceptRes.data);
        } catch (err) {
            console.error('Failed to fetch data:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveContent = async () => {
        try {
            let examplesData;
            try {
                examplesData = JSON.parse(formData.examples);
            } catch { examplesData = []; }

            const payload = { ...formData, examples: examplesData };
            if (editingContent) {
                await teacherAxios.put('/auth/api/teacher/content-detail/', { content_id: editingContent.id, ...payload });
            } else {
                await teacherAxios.post('/auth/api/teacher/content/', payload);
            }
            setShowForm(false);
            setEditingContent(null);
            setFormData({ atom: '', explanation: '', analogy: '', examples: '[]', tips: '', status: 'published', priority: true });
            fetchData();
        } catch (err) {
            console.error('Failed to save content:', err);
        }
    };

    const handleDeleteContent = async (contentId) => {
        if (!confirm('Delete this content?')) return;
        try {
            await teacherAxios.delete(`/auth/api/teacher/content-detail/?content_id=${contentId}`);
            fetchData();
        } catch (err) {
            console.error('Failed to delete:', err);
        }
    };

    const handleEditContent = (content) => {
        setEditingContent(content);
        setFormData({
            atom: content.atom,
            explanation: content.explanation,
            analogy: content.analogy,
            examples: JSON.stringify(content.examples || []),
            tips: content.tips,
            status: content.status,
            priority: content.priority,
        });
        setShowForm(true);
    };

    const handleCreateConcept = async () => {
        try {
            await teacherAxios.post('/auth/api/teacher/concepts/', conceptForm);
            setShowConceptForm(false);
            setConceptForm({ name: '', subject: '', description: '', difficulty: 'medium' });
            fetchData();
        } catch (err) {
            console.error('Failed to create concept:', err);
        }
    };

    const handleCreateAtom = async () => {
        try {
            let examples;
            try { examples = JSON.parse(atomForm.examples); } catch { examples = []; }
            await teacherAxios.post('/auth/api/teacher/atoms/', { ...atomForm, examples });
            setShowAtomForm(false);
            setAtomForm({ concept_id: '', name: '', explanation: '', analogy: '', examples: '[]', order: 0 });
            fetchData();
        } catch (err) {
            console.error('Failed to create atom:', err);
        }
    };

    const handleDeleteConcept = async (conceptId) => {
        if (!confirm('Delete this concept and all its atoms?')) return;
        try {
            await teacherAxios.delete(`/auth/api/teacher/concepts/?concept_id=${conceptId}`);
            fetchData();
        } catch (err) {
            console.error('Failed to delete concept:', err);
        }
    };

    const handleDeleteAtom = async (atomId) => {
        if (!confirm('Delete this atom?')) return;
        try {
            await teacherAxios.delete(`/auth/api/teacher/atoms/?atom_id=${atomId}`);
            fetchData();
        } catch (err) {
            console.error('Failed to delete atom:', err);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-theme-bg">
            <TeacherNavbar />
            <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-theme-text">📝 Content Management</h1>
                        <p className="text-theme-text-secondary mt-1">Manage knowledge graph, atoms, and teaching content</p>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={() => setShowConceptForm(!showConceptForm)}
                            className="px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 text-white rounded-lg text-sm font-semibold hover:opacity-90">
                            + New Concept
                        </button>
                        <button onClick={() => setShowAtomForm(!showAtomForm)}
                            className="px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-lg text-sm font-semibold hover:opacity-90">
                            + New Atom
                        </button>
                        <button onClick={() => { setShowForm(!showForm); setEditingContent(null); }}
                            className="px-4 py-2 bg-gradient-to-r from-violet-500 to-purple-600 text-white rounded-lg text-sm font-semibold hover:opacity-90">
                            + Teaching Content
                        </button>
                    </div>
                </div>

                {/* Create Concept Form */}
                {showConceptForm && (
                    <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-theme-xl p-6 mb-6">
                        <h3 className="font-bold text-theme-text mb-4">📚 Create New Concept</h3>
                        <div className="grid sm:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Concept Name</label>
                                <input value={conceptForm.name} onChange={(e) => setConceptForm({ ...conceptForm, name: e.target.value })}
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" placeholder="e.g., Loops" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Subject</label>
                                <input value={conceptForm.subject} onChange={(e) => setConceptForm({ ...conceptForm, subject: e.target.value })}
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" placeholder="e.g., Python" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Description</label>
                                <input value={conceptForm.description} onChange={(e) => setConceptForm({ ...conceptForm, description: e.target.value })}
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Difficulty</label>
                                <select value={conceptForm.difficulty} onChange={(e) => setConceptForm({ ...conceptForm, difficulty: e.target.value })}
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm">
                                    <option value="easy">Easy</option>
                                    <option value="medium">Medium</option>
                                    <option value="hard">Hard</option>
                                </select>
                            </div>
                        </div>
                        <div className="mt-4 flex gap-2">
                            <button onClick={handleCreateConcept} className="px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-semibold">Create Concept</button>
                            <button onClick={() => setShowConceptForm(false)} className="px-4 py-2 bg-surface-alt text-theme-text rounded-lg text-sm">Cancel</button>
                        </div>
                    </div>
                )}

                {/* Create Atom Form */}
                {showAtomForm && (
                    <div className="bg-blue-500/5 border border-blue-500/20 rounded-theme-xl p-6 mb-6">
                        <h3 className="font-bold text-theme-text mb-4">⚛️ Create New Atom</h3>
                        <div className="grid sm:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Concept</label>
                                <select value={atomForm.concept_id} onChange={(e) => setAtomForm({ ...atomForm, concept_id: e.target.value })}
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm">
                                    <option value="">Select Concept</option>
                                    {concepts.map(c => <option key={c.id} value={c.id}>{c.name} ({c.subject})</option>)}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Atom Name</label>
                                <input value={atomForm.name} onChange={(e) => setAtomForm({ ...atomForm, name: e.target.value })}
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" placeholder="e.g., while loop" />
                            </div>
                            <div className="sm:col-span-2">
                                <label className="block text-sm font-medium text-theme-text mb-1">Explanation</label>
                                <textarea value={atomForm.explanation} onChange={(e) => setAtomForm({ ...atomForm, explanation: e.target.value })}
                                    rows={3} className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Analogy</label>
                                <textarea value={atomForm.analogy} onChange={(e) => setAtomForm({ ...atomForm, analogy: e.target.value })}
                                    rows={2} className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Order</label>
                                <input type="number" value={atomForm.order} onChange={(e) => setAtomForm({ ...atomForm, order: parseInt(e.target.value) })}
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" />
                            </div>
                        </div>
                        <div className="mt-4 flex gap-2">
                            <button onClick={handleCreateAtom} className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-semibold">Create Atom</button>
                            <button onClick={() => setShowAtomForm(false)} className="px-4 py-2 bg-surface-alt text-theme-text rounded-lg text-sm">Cancel</button>
                        </div>
                    </div>
                )}

                {/* Teaching Content Form */}
                {showForm && (
                    <div className="bg-violet-500/5 border border-violet-500/20 rounded-theme-xl p-6 mb-6">
                        <h3 className="font-bold text-theme-text mb-4">
                            {editingContent ? '✏️ Edit Teaching Content' : '📝 New Teaching Content'}
                        </h3>
                        <div className="grid sm:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Atom</label>
                                <select value={formData.atom} onChange={(e) => setFormData({ ...formData, atom: e.target.value })}
                                    disabled={!!editingContent}
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm">
                                    <option value="">Select Atom</option>
                                    {concepts.flatMap(c => c.atoms?.map(a => (
                                        <option key={a.id} value={a.id}>{c.name} → {a.name}</option>
                                    )))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Status</label>
                                <select value={formData.status} onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm">
                                    <option value="published">Published</option>
                                    <option value="draft">Draft</option>
                                    <option value="archived">Archived</option>
                                </select>
                            </div>
                            <div className="sm:col-span-2">
                                <label className="block text-sm font-medium text-theme-text mb-1">Explanation</label>
                                <textarea value={formData.explanation} onChange={(e) => setFormData({ ...formData, explanation: e.target.value })}
                                    rows={3} placeholder="Your custom explanation (better than AI!)"
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Analogy</label>
                                <textarea value={formData.analogy} onChange={(e) => setFormData({ ...formData, analogy: e.target.value })}
                                    rows={2} placeholder="e.g., Loop is like solving 10 math problems using same method"
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Tips</label>
                                <textarea value={formData.tips} onChange={(e) => setFormData({ ...formData, tips: e.target.value })}
                                    rows={2} placeholder="Teaching tips for students"
                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm" />
                            </div>
                            <div className="sm:col-span-2 flex items-center gap-2">
                                <input type="checkbox" checked={formData.priority}
                                    onChange={(e) => setFormData({ ...formData, priority: e.target.checked })}
                                    className="rounded" />
                                <label className="text-sm text-theme-text">Priority (show before AI content)</label>
                            </div>
                        </div>
                        <div className="mt-4 flex gap-2">
                            <button onClick={handleSaveContent} className="px-4 py-2 bg-violet-500 text-white rounded-lg text-sm font-semibold">
                                {editingContent ? 'Update' : 'Create'} Content
                            </button>
                            <button onClick={() => { setShowForm(false); setEditingContent(null); }} className="px-4 py-2 bg-surface-alt text-theme-text rounded-lg text-sm">Cancel</button>
                        </div>
                    </div>
                )}

                {/* Knowledge Graph */}
                <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden mb-6">
                    <div className="px-6 py-4 border-b border-theme-border">
                        <h2 className="text-lg font-bold text-theme-text">🧠 Knowledge Graph (Your Concepts)</h2>
                        <p className="text-sm text-theme-text-muted">Concepts and their atomic units</p>
                    </div>
                    <div className="p-6 space-y-4">
                        {concepts.length === 0 ? (
                            <p className="text-theme-text-muted text-center py-8">No concepts yet. Create your first concept above!</p>
                        ) : (
                            concepts.map(concept => (
                                <div key={concept.id} className="border border-theme-border rounded-lg p-4">
                                    <div className="flex items-center justify-between mb-3">
                                        <div>
                                            <h3 className="font-bold text-theme-text">{concept.name}</h3>
                                            <p className="text-xs text-theme-text-muted">{concept.subject} · {concept.difficulty} · {concept.atoms?.length || 0} atoms</p>
                                        </div>
                                        <button onClick={() => handleDeleteConcept(concept.id)}
                                            className="text-xs px-2 py-1 rounded-lg text-error hover:bg-error/10 transition-colors">
                                            Delete
                                        </button>
                                    </div>
                                    {concept.atoms?.length > 0 && (
                                        <div className="space-y-1 ml-4">
                                            {concept.atoms.map(atom => (
                                                <div key={atom.id} className="flex items-center justify-between py-1.5 px-3 rounded-lg hover:bg-surface-alt/50">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-emerald-500">├──</span>
                                                        <span className="text-sm text-theme-text">{atom.name}</span>
                                                        <span className="text-xs text-theme-text-muted">({atom.question_count} questions)</span>
                                                    </div>
                                                    <button onClick={() => handleDeleteAtom(atom.id)}
                                                        className="text-xs px-2 py-0.5 text-error hover:bg-error/10 rounded transition-colors">
                                                        ×
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* Teaching Contents */}
                <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden">
                    <div className="px-6 py-4 border-b border-theme-border">
                        <h2 className="text-lg font-bold text-theme-text">📝 Your Teaching Content</h2>
                        <p className="text-sm text-theme-text-muted">Custom content that overrides AI-generated content</p>
                    </div>
                    <div className="divide-y divide-theme-border">
                        {contents.length === 0 ? (
                            <p className="text-theme-text-muted text-center py-8">No custom content yet</p>
                        ) : (
                            contents.map(content => (
                                <div key={content.id} className="px-6 py-4">
                                    <div className="flex items-center justify-between mb-2">
                                        <div>
                                            <span className="font-medium text-theme-text">{content.atom_name}</span>
                                            <span className="ml-2 text-xs text-theme-text-muted">in {content.concept_name}</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                                                content.status === 'published' ? 'bg-emerald-500/10 text-emerald-500' :
                                                content.status === 'draft' ? 'bg-amber-500/10 text-amber-500' :
                                                'bg-surface-alt text-theme-text-muted'
                                            }`}>{content.status}</span>
                                            {content.priority && <span className="text-xs text-violet-500">⭐ Priority</span>}
                                            <button onClick={() => handleEditContent(content)}
                                                className="text-xs px-2 py-1 text-blue-500 hover:bg-blue-500/10 rounded-lg transition-colors">Edit</button>
                                            <button onClick={() => handleDeleteContent(content.id)}
                                                className="text-xs px-2 py-1 text-error hover:bg-error/10 rounded-lg transition-colors">Delete</button>
                                        </div>
                                    </div>
                                    {content.explanation && <p className="text-sm text-theme-text-secondary line-clamp-2">{content.explanation}</p>}
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default ContentManagement;
