// frontend/src/components/Learning/TeachingModule.jsx — Full-page structured teaching view

import React, { useState, useMemo } from 'react';
import { useLearning } from '../../context/LearningContext';

/* ───── helper: convert a normal YouTube URL to an embeddable one ───── */
const toEmbedUrl = (url = '') => {
    try {
        const shortMatch = url.match(/youtu\.be\/([^?&]+)/);
        if (shortMatch) return `https://www.youtube.com/embed/${shortMatch[1]}`;
        const idMatch = url.match(/[?&]v=([^&]+)/);
        if (idMatch) return `https://www.youtube.com/embed/${idMatch[1]}`;
        if (url.includes('/embed/')) return url;
    } catch { /* fall through */ }
    return url;
};

/* ───── helper: render explanation with markdown-ish bullets ───── */
const FormattedText = ({ text }) => {
    if (!text) return null;
    const lines = text.split(/\n/).filter(Boolean);
    const isList = lines.some(l => /^\s*[-*•]\s|^\s*\d+[.)]\s/.test(l));

    if (!isList) return <p className="text-theme-text leading-relaxed whitespace-pre-line">{text}</p>;

    return (
        <ul className="list-disc list-inside space-y-2 text-theme-text leading-relaxed">
            {lines.map((line, i) => {
                const cleaned = line.replace(/^\s*[-*•]\s*/, '').replace(/^\s*\d+[.)]\s*/, '');
                return <li key={i}>{cleaned || line}</li>;
            })}
        </ul>
    );
};

/* ═══════════════════════════════════════════════════════════════ */

const TeachingModule = ({
    atom,
    subject,
    concept,
    teachingContent,
    onContinue,
    onBack,
    showBackButton = true,
}) => {
    const { currentSession, pacingDecision, atomMastery, currentTheta } = useLearning();
    const [expandedImage, setExpandedImage] = useState(null);

    const displaySubject = subject || currentSession?.subject || '';
    const displayConcept = concept || currentSession?.concept_name || '';

    /* destructure teaching payload */
    const {
        explanation = '',
        example = '',
        analogy = '',
        misconception = '',
        practical_application = '',
        videos = [],
        images = [],
    } = teachingContent || {};

    /* embed-ready video list */
    const embedVideos = useMemo(
        () => videos.map(v => ({ ...v, embedUrl: toEmbedUrl(v.url) })),
        [videos],
    );

    /* adaptive message */
    const adaptiveMsg = (() => {
        if (pacingDecision === 'sharp_slowdown') return "Let's really focus on the fundamentals here. Take your time.";
        if (pacingDecision === 'slow_down') return "We'll go through this carefully. No rush.";
        if (pacingDecision === 'speed_up') return "You're ready for this! Let's move efficiently.";
        return "Let's master this concept step by step.";
    })();

    /* loading guard */
    if (!teachingContent) {
        return (
            <div className="flex items-center justify-center py-20">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-theme-text-muted">Preparing your lesson…</p>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full min-h-screen bg-theme-bg">
            {/* ─── HERO BANNER ─── */}
            <div className="relative bg-gradient-to-br from-primary/20 via-violet-500/10 to-emerald-500/10 border-b border-theme-border">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
                    <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
                        <div className="flex-1">
                            {displaySubject && (
                                <span className="inline-block px-3 py-1 text-xs font-semibold rounded-full bg-primary/10 text-primary mb-2">
                                    {displaySubject} &middot; {displayConcept}
                                </span>
                            )}
                            <h1 className="text-3xl sm:text-4xl font-extrabold text-theme-text leading-tight">
                                {atom?.name}
                            </h1>
                            <p className="mt-2 text-theme-text-secondary text-sm sm:text-base max-w-xl">
                                {adaptiveMsg}
                            </p>
                        </div>

                        {/* mastery / theta chips */}
                        <div className="flex sm:flex-col gap-3 flex-shrink-0">
                            <div className="bg-surface/80 backdrop-blur rounded-theme-lg px-4 py-2 border border-theme-border text-center">
                                <div className="text-xs text-theme-text-muted">Mastery</div>
                                <div className="text-2xl font-bold text-primary leading-none mt-1">
                                    {Math.round(atomMastery * 100)}%
                                </div>
                            </div>
                            <div className="bg-surface/80 backdrop-blur rounded-theme-lg px-4 py-2 border border-theme-border text-center">
                                <div className="text-xs text-theme-text-muted">Ability θ</div>
                                <div className="text-2xl font-bold text-violet-500 leading-none mt-1">
                                    {currentTheta.toFixed(2)}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* pacing chip */}
                    {pacingDecision && pacingDecision !== 'stay' && (
                        <div className={`mt-4 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border
                            ${pacingDecision === 'speed_up'
                                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30'
                                : pacingDecision === 'slow_down'
                                    ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30'
                                    : 'bg-error/10 text-error border-error/30'}`}
                        >
                            {pacingDecision === 'speed_up' && '⚡ Accelerated pace'}
                            {pacingDecision === 'slow_down' && '🐢 Slower pace — building foundation'}
                            {pacingDecision === 'sharp_slowdown' && '⚠️ Deep focus on basics'}
                        </div>
                    )}
                </div>
            </div>

            {/* ─── MAIN CONTENT ─── */}
            <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-10">

                {/* ── Section 1: Explanation ── */}
                <section className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden">
                    <div className="px-6 py-4 border-b border-theme-border flex items-center gap-2 bg-primary/5">
                        <span className="text-xl">📖</span>
                        <h2 className="text-lg font-bold text-theme-text">Explanation</h2>
                    </div>
                    <div className="px-6 py-5">
                        <FormattedText text={explanation} />
                    </div>
                </section>

                {/* ── Section 2: Watch & Learn (videos) ── */}
                {embedVideos.length > 0 && (
                    <section className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden">
                        <div className="px-6 py-4 border-b border-theme-border flex items-center gap-2 bg-violet-500/5">
                            <span className="text-xl">🎬</span>
                            <h2 className="text-lg font-bold text-theme-text">Watch &amp; Learn</h2>
                        </div>
                        <div className="px-6 py-5 space-y-6">
                            {embedVideos.map((video, idx) => (
                                <div key={idx}>
                                    <div className="aspect-video w-full rounded-theme-lg overflow-hidden border border-theme-border shadow-sm">
                                        <iframe
                                            src={video.embedUrl}
                                            title={video.title || `Video ${idx + 1}`}
                                            className="w-full h-full"
                                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                            allowFullScreen
                                        />
                                    </div>
                                    <div className="mt-2 flex items-center gap-3 text-sm text-theme-text-muted">
                                        <span className="font-medium text-theme-text truncate max-w-sm">
                                            {video.title || 'Untitled video'}
                                        </span>
                                        {video.channel && <span className="shrink-0">📺 {video.channel}</span>}
                                        {video.duration && <span className="shrink-0">⏱ {video.duration}</span>}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>
                )}

                {/* ── Section 3: Visual Diagrams (images) ── */}
                {images.length > 0 && (
                    <section className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden">
                        <div className="px-6 py-4 border-b border-theme-border flex items-center gap-2 bg-emerald-500/5">
                            <span className="text-xl">🖼️</span>
                            <h2 className="text-lg font-bold text-theme-text">Visual Diagrams</h2>
                        </div>
                        <div className="px-6 py-5">
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {images.map((img, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => setExpandedImage(img)}
                                        className="group relative border border-theme-border rounded-theme-lg overflow-hidden hover:shadow-theme-lg transition-shadow focus:outline-none focus:ring-2 focus:ring-primary/50"
                                    >
                                        <img
                                            src={img.thumbnail || img.url}
                                            alt={img.title || `Diagram ${idx + 1}`}
                                            className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
                                            onError={(e) => {
                                                e.target.onerror = null;
                                                e.target.src = 'https://via.placeholder.com/300x200?text=Image+Not+Available';
                                            }}
                                        />
                                        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-3">
                                            <span className="text-white text-xs font-medium truncate">{img.title}</span>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </section>
                )}

                {/* ── Section 4: Example ── */}
                {example && (
                    <section className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden">
                        <div className="px-6 py-4 border-b border-theme-border flex items-center gap-2 bg-emerald-500/5">
                            <span className="text-xl">💡</span>
                            <h2 className="text-lg font-bold text-theme-text">Example</h2>
                        </div>
                        <div className="px-6 py-5">
                            <FormattedText text={example} />
                        </div>
                    </section>
                )}

                {/* ── Section 5: Analogy ── */}
                {analogy && (
                    <section className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden">
                        <div className="px-6 py-4 border-b border-theme-border flex items-center gap-2 bg-violet-500/5">
                            <span className="text-xl">🔄</span>
                            <h2 className="text-lg font-bold text-theme-text">Think of It Like…</h2>
                        </div>
                        <div className="px-6 py-5">
                            <p className="text-theme-text-secondary leading-relaxed italic">"{analogy}"</p>
                        </div>
                    </section>
                )}

                {/* ── Section 6: Common Misconception ── */}
                {misconception && (
                    <section className="bg-surface rounded-theme-xl shadow-theme border border-error/20 overflow-hidden">
                        <div className="px-6 py-4 border-b border-error/20 flex items-center gap-2 bg-error/5">
                            <span className="text-xl">⚠️</span>
                            <h2 className="text-lg font-bold text-error">Common Misconception</h2>
                        </div>
                        <div className="px-6 py-5">
                            <p className="text-theme-text-secondary leading-relaxed">{misconception}</p>
                        </div>
                    </section>
                )}

                {/* ── Section 7: Why This Matters ── */}
                {practical_application && (
                    <section className="bg-surface rounded-theme-xl shadow-theme border border-theme-border overflow-hidden">
                        <div className="px-6 py-4 border-b border-theme-border flex items-center gap-2 bg-orange-500/5">
                            <span className="text-xl">🚀</span>
                            <h2 className="text-lg font-bold text-theme-text">Why This Matters</h2>
                        </div>
                        <div className="px-6 py-5">
                            <p className="text-theme-text-secondary leading-relaxed">{practical_application}</p>
                        </div>
                    </section>
                )}

                {/* ── Mastery progress bar ── */}
                <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-6">
                    <div className="flex justify-between text-sm text-theme-text-muted mb-2">
                        <span>Your understanding so far</span>
                        <span>Target: 70 %</span>
                    </div>
                    <div className="w-full bg-theme-border rounded-full h-3">
                        <div
                            className="gradient-primary h-3 rounded-full transition-all duration-500"
                            style={{ width: `${Math.min(100, atomMastery * 100)}%` }}
                        />
                    </div>
                </div>

                {/* ── Action buttons ── */}
                <div className="flex justify-between items-center pt-2 pb-8">
                    {showBackButton && (
                        <button
                            onClick={onBack}
                            className="px-5 py-2.5 bg-theme-bg text-theme-text-secondary rounded-theme-lg hover:bg-theme-border transition-colors text-sm"
                        >
                            ← Back
                        </button>
                    )}
                    <button
                        onClick={onContinue}
                        className="ml-auto px-8 py-3 bg-emerald-500 text-white rounded-theme-lg font-semibold hover:bg-emerald-600 hover:shadow-theme-lg transition-all text-base"
                    >
                        Continue to Questions →
                    </button>
                </div>

                {/* tip */}
                <p className="text-center text-xs text-theme-text-muted pb-4">
                    ✨ Read carefully — questions will be based on this material
                </p>
            </div>

            {/* ─── LIGHTBOX for expanded image ─── */}
            {expandedImage && (
                <div
                    className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
                    onClick={() => setExpandedImage(null)}
                >
                    <div
                        className="relative max-w-4xl w-full bg-surface rounded-theme-xl overflow-hidden shadow-2xl border border-theme-border"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <button
                            onClick={() => setExpandedImage(null)}
                            className="absolute top-3 right-3 z-10 bg-black/50 hover:bg-black/70 text-white w-8 h-8 rounded-full flex items-center justify-center transition-colors"
                        >
                            ✕
                        </button>
                        <img
                            src={expandedImage.url || expandedImage.thumbnail}
                            alt={expandedImage.title || 'Expanded diagram'}
                            className="w-full max-h-[80vh] object-contain"
                            onError={(e) => {
                                e.target.onerror = null;
                                e.target.src = 'https://via.placeholder.com/600x400?text=Image+Not+Available';
                            }}
                        />
                        {expandedImage.title && (
                            <div className="px-4 py-3 border-t border-theme-border">
                                <p className="text-sm text-theme-text">{expandedImage.title}</p>
                                {expandedImage.source && (
                                    <p className="text-xs text-theme-text-muted mt-0.5">Source: {expandedImage.source}</p>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default TeachingModule;