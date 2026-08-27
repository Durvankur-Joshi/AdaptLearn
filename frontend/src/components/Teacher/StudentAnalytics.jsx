import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTeacher } from '../../context/TeacherContext';
import TeacherNavbar from './TeacherNavbar';

const StudentAnalytics = () => {
    const [students, setStudents] = useState([]);
    const [selectedStudent, setSelectedStudent] = useState(null);
    const [studentDetail, setStudentDetail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [detailLoading, setDetailLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [sortBy, setSortBy] = useState('name');
    const [showIntervention, setShowIntervention] = useState(false);
    const [interventionData, setInterventionData] = useState({ action: 'reset_mastery', atom: '', reason: '', parameters: {} });
    const { teacherAxios } = useTeacher();
    const [searchParams] = useSearchParams();

    useEffect(() => {
        fetchStudents();
    }, []);

    useEffect(() => {
        const studentId = searchParams.get('student');
        if (studentId && students.length > 0) {
            const student = students.find(s => s.id === parseInt(studentId));
            if (student) {
                selectStudent(student);
            }
        }
    }, [searchParams, students]);

    const fetchStudents = async () => {
        try {
            const res = await teacherAxios.get('/auth/api/teacher/students/');
            setStudents(res.data);
        } catch (err) {
            console.error('Failed to fetch students:', err);
        } finally {
            setLoading(false);
        }
    };

    const selectStudent = async (student) => {
        setSelectedStudent(student);
        setDetailLoading(true);
        try {
            const res = await teacherAxios.get(`/auth/api/teacher/student-detail/?student_id=${student.id}`);
            setStudentDetail(res.data);
        } catch (err) {
            console.error('Failed to fetch student detail:', err);
        } finally {
            setDetailLoading(false);
        }
    };

    const handleIntervention = async () => {
        if (!selectedStudent) return;
        try {
            await teacherAxios.post('/auth/api/teacher/overrides/', {
                student: selectedStudent.id,
                action: interventionData.action,
                atom: interventionData.atom || null,
                reason: interventionData.reason,
                parameters: interventionData.parameters,
            });
            setShowIntervention(false);
            setInterventionData({ action: 'reset_mastery', atom: '', reason: '', parameters: {} });
            selectStudent(selectedStudent);
        } catch (err) {
            console.error('Failed to create intervention:', err);
        }
    };

    const sortedStudents = [...students]
        .filter(s => s.name.toLowerCase().includes(searchTerm.toLowerCase()) || s.username.toLowerCase().includes(searchTerm.toLowerCase()))
        .sort((a, b) => {
            if (sortBy === 'name') return a.name.localeCompare(b.name);
            if (sortBy === 'mastery') return a.avg_mastery - b.avg_mastery;
            if (sortBy === 'xp') return b.total_xp - a.total_xp;
            if (sortBy === 'weak') return b.weak_areas - a.weak_areas;
            return 0;
        });

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
                <div className="mb-6">
                    <h1 className="text-3xl font-bold text-theme-text">👥 Student Analytics</h1>
                    <p className="text-theme-text-secondary mt-1">Monitor and intervene in student progress</p>
                </div>

                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Student List */}
                    <div className="lg:col-span-1 bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden">
                        <div className="p-4 border-b border-theme-border space-y-3">
                            <input
                                type="text"
                                placeholder="Search students..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full px-3 py-2 rounded-lg bg-surface-alt border border-theme-border text-theme-text text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                            />
                            <select
                                value={sortBy}
                                onChange={(e) => setSortBy(e.target.value)}
                                className="w-full px-3 py-2 rounded-lg bg-surface-alt border border-theme-border text-theme-text text-sm"
                            >
                                <option value="name">Sort by Name</option>
                                <option value="mastery">Sort by Mastery (Low → High)</option>
                                <option value="xp">Sort by XP (High → Low)</option>
                                <option value="weak">Sort by Weak Areas (Most → Least)</option>
                            </select>
                        </div>
                        <div className="divide-y divide-theme-border max-h-[calc(100vh-320px)] overflow-y-auto">
                            {sortedStudents.map(student => (
                                <button
                                    key={student.id}
                                    onClick={() => selectStudent(student)}
                                    className={`w-full px-4 py-3 text-left hover:bg-surface-alt/50 transition-colors ${
                                        selectedStudent?.id === student.id ? 'bg-emerald-500/5 border-l-2 border-emerald-500' : ''
                                    }`}
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2 min-w-0">
                                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                                                student.avg_mastery >= 0.7 ? 'bg-emerald-500' :
                                                student.avg_mastery >= 0.4 ? 'bg-amber-500' : 'bg-error'
                                            }`}>
                                                {student.name[0]?.toUpperCase()}
                                            </div>
                                            <div className="min-w-0">
                                                <p className="font-medium text-theme-text text-sm truncate">{student.name}</p>
                                                <p className="text-xs text-theme-text-muted">@{student.username}</p>
                                            </div>
                                        </div>
                                        <div className="text-right flex-shrink-0">
                                            <p className="text-sm font-bold text-theme-text">{(student.avg_mastery * 100).toFixed(0)}%</p>
                                            {student.weak_areas > 0 && (
                                                <p className="text-xs text-error">{student.weak_areas} weak</p>
                                            )}
                                        </div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Student Detail */}
                    <div className="lg:col-span-2 space-y-6">
                        {!selectedStudent ? (
                            <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-12 text-center">
                                <div className="text-5xl mb-4">👈</div>
                                <h3 className="text-lg font-semibold text-theme-text">Select a student</h3>
                                <p className="text-theme-text-muted">Click on a student to view their detailed progress</p>
                            </div>
                        ) : detailLoading ? (
                            <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-12 text-center">
                                <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto" />
                            </div>
                        ) : studentDetail && (
                            <>
                                {/* Student Header */}
                                <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-6">
                                    <div className="flex items-center justify-between flex-wrap gap-4">
                                        <div className="flex items-center gap-4">
                                            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-white text-xl font-bold">
                                                {studentDetail.student.first_name?.[0] || studentDetail.student.username[0]}
                                            </div>
                                            <div>
                                                <h2 className="text-xl font-bold text-theme-text">
                                                    {studentDetail.student.first_name} {studentDetail.student.last_name}
                                                </h2>
                                                <p className="text-sm text-theme-text-muted">@{studentDetail.student.username} · {studentDetail.student.email}</p>
                                            </div>
                                        </div>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => setShowIntervention(!showIntervention)}
                                                className="px-4 py-2 rounded-lg bg-amber-500/10 text-amber-500 font-semibold text-sm hover:bg-amber-500/20 transition-colors"
                                            >
                                                🔧 Intervene
                                            </button>
                                        </div>
                                    </div>

                                    {/* Quick Stats */}
                                    <div className="grid grid-cols-3 gap-4 mt-6">
                                        <div className="bg-surface-alt rounded-lg p-3 text-center">
                                            <p className="text-2xl font-bold text-emerald-500">{studentDetail.student.total_xp}</p>
                                            <p className="text-xs text-theme-text-muted">Total XP</p>
                                        </div>
                                        <div className="bg-surface-alt rounded-lg p-3 text-center">
                                            <p className="text-2xl font-bold text-theme-text">{selectedStudent.completed_atoms}/{selectedStudent.total_atoms}</p>
                                            <p className="text-xs text-theme-text-muted">Atoms Completed</p>
                                        </div>
                                        <div className="bg-surface-alt rounded-lg p-3 text-center">
                                            <p className="text-2xl font-bold text-theme-text">{(selectedStudent.accuracy * 100).toFixed(0)}%</p>
                                            <p className="text-xs text-theme-text-muted">Accuracy</p>
                                        </div>
                                    </div>
                                </div>

                                {/* Intervention Panel */}
                                {showIntervention && (
                                    <div className="bg-amber-500/5 border border-amber-500/20 rounded-theme-xl p-6">
                                        <h3 className="font-bold text-theme-text mb-4">🔧 Create Intervention</h3>
                                        <div className="grid sm:grid-cols-2 gap-4">
                                            <div>
                                                <label className="block text-sm font-medium text-theme-text mb-1">Action</label>
                                                <select
                                                    value={interventionData.action}
                                                    onChange={(e) => setInterventionData({ ...interventionData, action: e.target.value })}
                                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm"
                                                >
                                                    <option value="reset_mastery">Reset Mastery</option>
                                                    <option value="assign_atom">Assign Specific Atom</option>
                                                    <option value="force_review">Force Review</option>
                                                    <option value="set_mastery">Set Mastery Level</option>
                                                    <option value="assign_remedial">Assign Remedial Content</option>
                                                    <option value="skip_atom">Skip Atom</option>
                                                </select>
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-theme-text mb-1">Atom ID (optional)</label>
                                                <input
                                                    type="number"
                                                    value={interventionData.atom}
                                                    onChange={(e) => setInterventionData({ ...interventionData, atom: e.target.value })}
                                                    placeholder="Enter atom ID"
                                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm"
                                                />
                                            </div>
                                            {interventionData.action === 'set_mastery' && (
                                                <div>
                                                    <label className="block text-sm font-medium text-theme-text mb-1">Mastery Value (0-1)</label>
                                                    <input
                                                        type="number"
                                                        step="0.1"
                                                        min="0"
                                                        max="1"
                                                        value={interventionData.parameters.mastery || 0.5}
                                                        onChange={(e) => setInterventionData({
                                                            ...interventionData,
                                                            parameters: { ...interventionData.parameters, mastery: parseFloat(e.target.value) }
                                                        })}
                                                        className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm"
                                                    />
                                                </div>
                                            )}
                                            <div className="sm:col-span-2">
                                                <label className="block text-sm font-medium text-theme-text mb-1">Reason</label>
                                                <textarea
                                                    value={interventionData.reason}
                                                    onChange={(e) => setInterventionData({ ...interventionData, reason: e.target.value })}
                                                    placeholder="Why are you intervening?"
                                                    rows={2}
                                                    className="w-full px-3 py-2 rounded-lg bg-surface border border-theme-border text-theme-text text-sm"
                                                />
                                            </div>
                                        </div>
                                        <div className="mt-4 flex gap-2">
                                            <button
                                                onClick={handleIntervention}
                                                className="px-4 py-2 bg-amber-500 text-white rounded-lg font-semibold text-sm hover:bg-amber-600 transition-colors"
                                            >
                                                Apply Intervention
                                            </button>
                                            <button
                                                onClick={() => setShowIntervention(false)}
                                                className="px-4 py-2 bg-surface-alt text-theme-text rounded-lg text-sm hover:bg-surface-alt/80 transition-colors"
                                            >
                                                Cancel
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {/* Weak Areas */}
                                {studentDetail.student.weak_areas?.length > 0 && (
                                    <div className="bg-surface rounded-theme-xl shadow-theme border border-error/20 p-6">
                                        <h3 className="font-bold text-theme-text mb-4">🚨 Weak Areas</h3>
                                        <div className="grid sm:grid-cols-2 gap-3">
                                            {studentDetail.student.weak_areas.map((w, i) => (
                                                <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-error/5 border border-error/10">
                                                    <div>
                                                        <p className="font-medium text-theme-text text-sm">{w.atom_name}</p>
                                                        <p className="text-xs text-theme-text-muted">{w.concept_name} · Phase: {w.phase}</p>
                                                    </div>
                                                    <span className="text-error font-bold text-sm">{(w.mastery_score * 100).toFixed(0)}%</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Progress Table - Grouped by Subject */}
                                <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden">
                                    <div className="px-6 py-4 border-b border-theme-border">
                                        <h3 className="font-bold text-theme-text">📊 Mastery Per Atom</h3>
                                        <p className="text-xs text-theme-text-muted mt-1">Grouped by subject — click to expand</p>
                                    </div>
                                    {(() => {
                                        const progress = studentDetail.student.progress || [];
                                        // Group by subject → concept → atoms
                                        const grouped = {};
                                        progress.forEach(p => {
                                            const subj = p.subject || 'Uncategorized';
                                            const concept = p.concept_name || 'Unknown';
                                            if (!grouped[subj]) grouped[subj] = {};
                                            if (!grouped[subj][concept]) grouped[subj][concept] = [];
                                            grouped[subj][concept].push(p);
                                        });

                                        const subjects = Object.keys(grouped).sort();
                                        if (subjects.length === 0) {
                                            return (
                                                <div className="p-8 text-center text-theme-text-muted text-sm">No progress data yet</div>
                                            );
                                        }

                                        return (
                                            <div className="divide-y divide-theme-border">
                                                {subjects.map(subject => {
                                                    const concepts = grouped[subject];
                                                    const allAtoms = Object.values(concepts).flat();
                                                    const avgMastery = allAtoms.reduce((s, p) => s + p.mastery_score, 0) / allAtoms.length;
                                                    const completedCount = allAtoms.filter(p => p.phase === 'complete').length;

                                                    return (
                                                        <details key={subject} className="group">
                                                            <summary className="px-6 py-4 cursor-pointer hover:bg-surface-alt/50 transition-colors list-none flex items-center justify-between">
                                                                <div className="flex items-center gap-3">
                                                                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-white text-sm font-bold ${
                                                                        avgMastery >= 0.7 ? 'bg-emerald-500' : avgMastery >= 0.4 ? 'bg-amber-500' : 'bg-error'
                                                                    }`}>
                                                                        {(avgMastery * 100).toFixed(0)}%
                                                                    </div>
                                                                    <div>
                                                                        <h4 className="font-semibold text-theme-text text-sm">{subject}</h4>
                                                                        <p className="text-xs text-theme-text-muted">
                                                                            {Object.keys(concepts).length} concept{Object.keys(concepts).length !== 1 ? 's' : ''} · {allAtoms.length} atom{allAtoms.length !== 1 ? 's' : ''} · {completedCount} completed
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                                <div className="flex items-center gap-3">
                                                                    <div className="w-24 bg-surface-alt rounded-full h-2 hidden sm:block">
                                                                        <div className={`h-2 rounded-full ${
                                                                            avgMastery >= 0.7 ? 'bg-emerald-500' : avgMastery >= 0.4 ? 'bg-amber-500' : 'bg-error'
                                                                        }`} style={{ width: `${Math.max(avgMastery * 100, 4)}%` }} />
                                                                    </div>
                                                                    <svg className="w-4 h-4 text-theme-text-muted transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                                    </svg>
                                                                </div>
                                                            </summary>
                                                            <div className="border-t border-theme-border">
                                                                {Object.entries(concepts).map(([conceptName, atoms]) => (
                                                                    <div key={conceptName}>
                                                                        <div className="px-6 py-2 bg-surface-alt/40 flex items-center gap-2">
                                                                            <span className="text-xs font-semibold text-theme-text-secondary">📘 {conceptName}</span>
                                                                            <span className="text-xs text-theme-text-muted">({atoms.length} atom{atoms.length !== 1 ? 's' : ''})</span>
                                                                        </div>
                                                                        <div className="overflow-x-auto">
                                                                            <table className="w-full text-sm">
                                                                                <thead>
                                                                                    <tr className="bg-surface-alt/20">
                                                                                        <th className="text-left px-6 py-2 font-medium text-theme-text-muted text-xs">Atom</th>
                                                                                        <th className="text-left px-4 py-2 font-medium text-theme-text-muted text-xs">Phase</th>
                                                                                        <th className="text-left px-4 py-2 font-medium text-theme-text-muted text-xs">Mastery</th>
                                                                                        <th className="text-left px-4 py-2 font-medium text-theme-text-muted text-xs">Streak</th>
                                                                                    </tr>
                                                                                </thead>
                                                                                <tbody className="divide-y divide-theme-border/50">
                                                                                    {atoms.map((p, i) => (
                                                                                        <tr key={i} className="hover:bg-surface-alt/30">
                                                                                            <td className="px-6 py-2.5 text-theme-text font-medium text-sm">{p.atom_name}</td>
                                                                                            <td className="px-4 py-2.5">
                                                                                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                                                                                                    p.phase === 'complete' ? 'bg-emerald-500/10 text-emerald-500' :
                                                                                                    p.phase === 'mastery_check' ? 'bg-blue-500/10 text-blue-500' :
                                                                                                    'bg-amber-500/10 text-amber-500'
                                                                                                }`}>
                                                                                                    {p.phase}
                                                                                                </span>
                                                                                            </td>
                                                                                            <td className="px-4 py-2.5">
                                                                                                <div className="flex items-center gap-2">
                                                                                                    <div className="w-16 bg-surface-alt rounded-full h-2">
                                                                                                        <div className={`h-2 rounded-full ${
                                                                                                            p.mastery_score >= 0.7 ? 'bg-emerald-500' :
                                                                                                            p.mastery_score >= 0.4 ? 'bg-amber-500' : 'bg-error'
                                                                                                        }`} style={{ width: `${Math.max(p.mastery_score * 100, 4)}%` }} />
                                                                                                    </div>
                                                                                                    <span className="text-theme-text font-medium text-xs">{(p.mastery_score * 100).toFixed(0)}%</span>
                                                                                                </div>
                                                                                            </td>
                                                                                            <td className="px-4 py-2.5 text-theme-text text-sm">{p.streak}</td>
                                                                                        </tr>
                                                                                    ))}
                                                                                </tbody>
                                                                            </table>
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </details>
                                                    );
                                                })}
                                            </div>
                                        );
                                    })()}
                                </div>

                                {/* Recent Sessions */}
                                {studentDetail.sessions?.length > 0 && (
                                    <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden">
                                        <div className="px-6 py-4 border-b border-theme-border">
                                            <h3 className="font-bold text-theme-text">📅 Recent Sessions</h3>
                                        </div>
                                        <div className="divide-y divide-theme-border">
                                            {studentDetail.sessions.map((s, i) => (
                                                <div key={i} className="px-6 py-3 flex items-center justify-between text-sm">
                                                    <div>
                                                        <span className="font-medium text-theme-text">{s.concept}</span>
                                                        <span className="ml-2 text-xs text-theme-text-muted">
                                                            {new Date(s.start_time).toLocaleDateString()}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-3 text-xs">
                                                        <span className="text-theme-text">{s.correct_answers}/{s.questions_answered} correct</span>
                                                        <span className={`px-2 py-0.5 rounded-full ${
                                                            s.fatigue_level === 'fresh' ? 'bg-emerald-500/10 text-emerald-500' :
                                                            s.fatigue_level === 'mild' ? 'bg-amber-500/10 text-amber-500' :
                                                            'bg-error/10 text-error'
                                                        }`}>
                                                            {s.fatigue_level}
                                                        </span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Active Overrides */}
                                {studentDetail.overrides?.length > 0 && (
                                    <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden">
                                        <div className="px-6 py-4 border-b border-theme-border">
                                            <h3 className="font-bold text-theme-text">🔧 Active Overrides</h3>
                                        </div>
                                        <div className="divide-y divide-theme-border">
                                            {studentDetail.overrides.map((o, i) => (
                                                <div key={i} className="px-6 py-3 flex items-center justify-between text-sm">
                                                    <div>
                                                        <span className="font-medium text-theme-text">{o.action}</span>
                                                        {o.atom_name && <span className="ml-2 text-theme-text-muted">on {o.atom_name}</span>}
                                                    </div>
                                                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                                                        o.is_active ? 'bg-emerald-500/10 text-emerald-500' : 'bg-surface-alt text-theme-text-muted'
                                                    }`}>
                                                        {o.is_active ? 'Active' : 'Inactive'}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default StudentAnalytics;
