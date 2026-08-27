import React from 'react';
import { Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { useState } from 'react';

const Home = () => {
    const { theme, toggleTheme } = useTheme();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);


    const features = [
        {
            icon: '🧠',
            title: 'Adaptive Learning',
            desc: 'AI-powered system that adapts to your pace, mastery level, and learning style in real-time.',
        },
        {
            icon: '📊',
            title: 'IRT-Based Assessment',
            desc: 'Item Response Theory ensures precise measurement of your ability with calibrated questions.',
        },
        {
            icon: '⚡',
            title: 'Smart Pacing',
            desc: 'Fatigue detection, break recommendations, and velocity tracking keep you in the optimal learning zone.',
        },
    ];

    return (
        <div className="min-h-screen bg-theme-bg overflow-hidden">
            {/* Navbar */}
            <nav className="sticky top-0 z-50 glass-strong">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between h-16 items-center">
                        {/* Logo - Always visible */}
                        <Link to="/" className="flex items-center gap-2 group shrink-0">
                            <div className="w-8 h-8 sm:w-9 sm:h-9 gradient-primary rounded-xl flex items-center justify-center text-white font-bold text-base sm:text-lg shadow-lg group-hover:scale-105 transition-transform">
                                A
                            </div>
                            <span className="text-base sm:text-lg font-bold text-theme-text">
                                Adapt<span className="text-gradient">Learn</span>
                            </span>
                        </Link>

                        {/* Desktop Navigation - Hidden on mobile, visible on md+ */}
                        <div className="hidden md:flex items-center gap-3">
                            {/* Theme Toggle */}
                            <button
                                onClick={toggleTheme}
                                className="relative w-14 h-7 rounded-full bg-surface-alt border border-theme-border transition-colors duration-300"
                                aria-label="Toggle theme"
                            >
                                <span className={`absolute top-0.5 left-0.5 w-6 h-6 rounded-full transition-all duration-300 flex items-center justify-center text-sm ${theme === 'dark'
                                        ? 'translate-x-7 bg-indigo-500 text-white'
                                        : 'translate-x-0 bg-yellow-400 text-yellow-900'
                                    }`}>
                                    {theme === 'dark' ? '🌙' : '☀️'}
                                </span>
                            </button>

                            <Link to="/teacher/login" className="px-3 py-2 rounded-lg text-sm font-medium text-emerald-500 hover:bg-emerald-500/10 transition-colors">
                                🎓 Teacher
                            </Link>
                            <Link to="/parent/login" className="px-3 py-2 rounded-lg text-sm font-medium text-violet-500 hover:bg-violet-500/10 transition-colors">
                                👨‍👩‍👧 Parent
                            </Link>
                            <Link to="/login" className="px-4 py-2 rounded-lg text-sm font-medium text-theme-text-secondary hover:text-theme-text transition-colors">
                                Sign In
                            </Link>
                            <Link to="/register" className="px-4 py-2 gradient-primary text-white rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity shadow-theme">
                                Get Started
                            </Link>
                        </div>

                        {/* Mobile Menu Button and Theme Toggle - Visible on mobile */}
                        <div className="flex md:hidden items-center gap-2">
                            {/* Theme Toggle - Mobile version */}
                            <button
                                onClick={toggleTheme}
                                className="relative w-12 h-6 rounded-full bg-surface-alt border border-theme-border transition-colors duration-300"
                                aria-label="Toggle theme"
                            >
                                <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full transition-all duration-300 flex items-center justify-center text-xs ${theme === 'dark'
                                        ? 'translate-x-6 bg-indigo-500 text-white'
                                        : 'translate-x-0 bg-yellow-400 text-yellow-900'
                                    }`}>
                                    {theme === 'dark' ? '🌙' : '☀️'}
                                </span>
                            </button>

                            {/* Mobile Menu Button */}
                            <button
                                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                                className="p-2 rounded-lg text-theme-text-secondary hover:text-theme-text hover:bg-theme-border/20 transition-colors"
                                aria-label="Toggle menu"
                            >
                                <svg
                                    className="w-6 h-6"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                >
                                    {isMobileMenuOpen ? (
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    ) : (
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                    )}
                                </svg>
                            </button>
                        </div>
                    </div>

                    {/* Mobile Menu Dropdown */}
                    {isMobileMenuOpen && (
                        <div className="md:hidden py-3 border-t border-theme-border/30 mt-2 animate-slideDown">
                            <div className="flex flex-col space-y-2">
                                <Link
                                    to="/teacher/login"
                                    className="px-4 py-3 rounded-lg text-sm font-medium text-emerald-500 hover:bg-emerald-500/10 transition-colors flex items-center gap-2"
                                    onClick={() => setIsMobileMenuOpen(false)}
                                >
                                    <span>🎓</span> Teacher Portal
                                </Link>
                                <Link
                                    to="/parent/login"
                                    className="px-4 py-3 rounded-lg text-sm font-medium text-violet-500 hover:bg-violet-500/10 transition-colors flex items-center gap-2"
                                    onClick={() => setIsMobileMenuOpen(false)}
                                >
                                    <span>👨‍👩‍👧</span> Parent Portal
                                </Link>
                                <div className="border-t border-theme-border/30 my-2"></div>
                                <Link
                                    to="/login"
                                    className="px-4 py-3 rounded-lg text-sm font-medium text-theme-text-secondary hover:text-theme-text hover:bg-theme-border/20 transition-colors"
                                    onClick={() => setIsMobileMenuOpen(false)}
                                >
                                    Sign In
                                </Link>
                                <Link
                                    to="/register"
                                    className="px-4 py-3 gradient-primary text-white rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity shadow-theme text-center"
                                    onClick={() => setIsMobileMenuOpen(false)}
                                >
                                    Get Started
                                </Link>
                            </div>
                        </div>
                    )}
                </div>
            </nav>

            {/* Hero */}
            <section className="relative pt-20 pb-32 px-4">
                {/* Background decoration */}
                <div className="absolute inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute -top-40 -right-40 w-[600px] h-[600px] rounded-full bg-primary/5 blur-3xl" />
                    <div className="absolute -bottom-40 -left-40 w-[500px] h-[500px] rounded-full bg-accent/5 blur-3xl" />
                </div>

                <div className="max-w-5xl mx-auto text-center relative z-10">
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-medium mb-8 animate-fade-in-up">
                        <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                        AI-Powered Adaptive Learning
                    </div>

                    <h1 className="text-5xl sm:text-6xl md:text-7xl font-extrabold tracking-tight mb-6 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
                        Learn Smarter,
                        <br />
                        <span className="text-gradient">Not Harder</span>
                    </h1>

                    <p className="text-lg sm:text-xl text-theme-text-secondary max-w-2xl mx-auto mb-10 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                        Experience personalized education powered by cognitive science. Our system adapts to your unique learning pattern, ensuring maximum retention with minimum effort.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
                        <Link
                            to="/register"
                            className="px-8 py-3.5 gradient-primary text-white rounded-xl text-lg font-semibold hover:opacity-90 transition-all shadow-theme-lg hover:shadow-theme-xl"
                        >
                            Start Learning Free
                        </Link>
                        <Link
                            to="/login"
                            className="px-8 py-3.5 bg-surface border border-theme-border text-theme-text rounded-xl text-lg font-semibold hover:bg-surface-alt transition-all shadow-theme"
                        >
                            Sign In
                        </Link>
                    </div>
                </div>
            </section>

            {/* Features */}
            <section className="py-20 px-4 bg-surface-alt/50">
                <div className="max-w-6xl mx-auto">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl sm:text-4xl font-bold text-theme-text mb-4">
                            Why AdaptLearn?
                        </h2>
                        <p className="text-theme-text-secondary max-w-xl mx-auto">
                            Built on proven learning science, designed for real results.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 stagger">
                        {features.map((f, i) => (
                            <div
                                key={i}
                                className="bg-surface rounded-theme-xl p-8 shadow-theme hover:shadow-theme-lg transition-all duration-300 border border-theme-border hover:-translate-y-1"
                            >
                                <div className="w-14 h-14 gradient-primary rounded-2xl flex items-center justify-center text-2xl mb-5 shadow-lg">
                                    {f.icon}
                                </div>
                                <h3 className="text-xl font-bold text-theme-text mb-2">{f.title}</h3>
                                <p className="text-theme-text-secondary leading-relaxed">{f.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Stats */}
            <section className="py-20 px-4">
                <div className="max-w-5xl mx-auto">
                    <div className="gradient-primary rounded-theme-xl p-10 sm:p-14 text-white text-center shadow-theme-xl">
                        <h2 className="text-3xl font-bold mb-10">Built for Effective Learning</h2>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                            {[
                                { val: 'IRT', label: 'Adaptive Engine' },
                                { val: 'BKT', label: 'Knowledge Tracing' },
                                { val: 'Real-time', label: 'Pacing Control' },
                                { val: 'XP', label: 'Gamified Progress' },
                            ].map((s, i) => (
                                <div key={i}>
                                    <div className="text-3xl font-extrabold mb-1">{s.val}</div>
                                    <div className="text-white/70 text-sm">{s.label}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-8 px-4 border-t border-theme-border">
                <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
                    <span className="text-sm text-theme-text-muted">
                        AdaptLearn — Adaptive Learning System
                    </span>
                    <span className="text-sm text-theme-text-muted">
                        Built with AI & Cognitive Science
                    </span>
                </div>
            </footer>
        </div>
    );
};

export default Home;