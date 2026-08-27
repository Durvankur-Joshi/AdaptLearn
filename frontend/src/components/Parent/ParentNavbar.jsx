import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useParent } from '../../context/ParentContext';
import { ThemeToggle } from '../Navbar';

const ParentNavbar = () => {
    const { parent, parentLogout } = useParent();
    const location = useLocation();
    const [mobileOpen, setMobileOpen] = useState(false);

    const isActive = (path) => location.pathname === path;

    const navLinks = [
        { path: '/parent/dashboard', label: 'Dashboard', icon: '🏠' },
    ];

    return (
        <nav className="sticky top-0 z-50 glass-strong border-b border-violet-500/20">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16 items-center">
                    <Link to="/parent/dashboard" className="flex items-center gap-2 group">
                        <div className="w-9 h-9 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-lg group-hover:scale-105 transition-transform">
                            P
                        </div>
                        <span className="text-lg font-bold text-theme-text hidden sm:block">
                            Adapt<span className="text-violet-500">Learn</span>
                            <span className="text-xs ml-1 px-1.5 py-0.5 bg-violet-500/10 text-violet-500 rounded-full font-medium">Parent</span>
                        </span>
                    </Link>

                    <div className="hidden lg:flex items-center gap-1">
                        {navLinks.map(link => (
                            <Link
                                key={link.path}
                                to={link.path}
                                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                                    isActive(link.path)
                                        ? 'bg-violet-500/10 text-violet-500'
                                        : 'text-theme-text-secondary hover:text-theme-text hover:bg-surface-alt'
                                }`}
                            >
                                <span className="mr-1.5">{link.icon}</span>
                                {link.label}
                            </Link>
                        ))}
                    </div>

                    <div className="flex items-center gap-3">
                        <ThemeToggle />
                        {parent && (
                            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-alt">
                                <div className="w-7 h-7 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                                    {(parent?.first_name || parent?.display_name || parent?.username || 'P')[0].toUpperCase()}
                                </div>
                                <span className="text-sm font-medium text-theme-text">
                                    {parent?.first_name || parent?.display_name || parent?.username}
                                </span>
                            </div>
                        )}
                        <button
                            onClick={parentLogout}
                            className="px-3 py-1.5 rounded-lg text-sm font-medium text-error hover:bg-error/10 transition-colors"
                        >
                            Logout
                        </button>

                        <button
                            className="lg:hidden p-2 rounded-lg text-theme-text-secondary hover:bg-surface-alt"
                            onClick={() => setMobileOpen(!mobileOpen)}
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                {mobileOpen ? (
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                ) : (
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                )}
                            </svg>
                        </button>
                    </div>
                </div>

                {mobileOpen && (
                    <div className="lg:hidden pb-4 pt-2 border-t border-theme-border">
                        <div className="flex flex-col gap-1">
                            {navLinks.map(link => (
                                <Link
                                    key={link.path}
                                    to={link.path}
                                    onClick={() => setMobileOpen(false)}
                                    className={`px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                                        isActive(link.path)
                                            ? 'bg-violet-500/10 text-violet-500'
                                            : 'text-theme-text-secondary hover:bg-surface-alt'
                                    }`}
                                >
                                    <span className="mr-2">{link.icon}</span>
                                    {link.label}
                                </Link>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </nav>
    );
};

export default ParentNavbar;
