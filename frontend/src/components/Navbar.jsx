import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

const ThemeToggle = () => {
    const { theme, toggleTheme } = useTheme();
    return (
        <button
            onClick={toggleTheme}
            className="relative w-14 h-7 rounded-full bg-surface-alt border border-theme-border transition-colors duration-300 focus-ring"
            aria-label="Toggle theme"
        >
            <span
                className={`absolute top-0.5 left-0.5 w-6 h-6 rounded-full transition-all duration-300 flex items-center justify-center text-sm ${theme === 'dark'
                        ? 'translate-x-7 bg-indigo-500 text-white'
                        : 'translate-x-0 bg-yellow-400 text-yellow-900'
                    }`}
            >
                {theme === 'dark' ? '🌙' : '☀️'}
            </span>
        </button>
    );
};

const Navbar = ({ variant = 'default' }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [mobileOpen, setMobileOpen] = useState(false);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const isActive = (path) => location.pathname === path;

    const navLinks = user
        ? [
            { path: '/dashboard', label: 'Dashboard', icon: '🏠' },
            { path: '/progress', label: 'Progress', icon: '📊' },
            { path: '/calendar', label: 'Calendar', icon: '📅' },
            { path: '/leaderboard', label: 'Leaderboard', icon: '🏆' },
            { path: '/learn/start', label: 'New Session', icon: '▶️' },
            { path: '/planner', label: 'Planner', icon: '🧠' },
        ]
        : [];

    return (
        <nav className="sticky top-0 z-50 glass-strong w-full">
            <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8">
                <div className="flex justify-between h-16 items-center">
                    {/* Logo */}
                    <Link to={user ? '/dashboard' : '/'} className="flex items-center gap-2 group">
                        <div className="w-9 h-9 gradient-primary rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-lg group-hover:scale-105 transition-transform">
                            A
                        </div>
                        <span className="text-lg font-bold text-theme-text hidden sm:block">
                            Adapt<span className="text-gradient">Learn</span>
                        </span>
                    </Link>

                    {/* Desktop Nav Links */}
                    {user && (
                        <div className="hidden md:flex items-center gap-1">
                            {navLinks.map(link => (
                                <Link
                                    key={link.path}
                                    to={link.path}
                                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${isActive(link.path)
                                            ? 'bg-primary/10 text-primary'
                                            : 'text-theme-text-secondary hover:text-theme-text hover:bg-surface-alt'
                                        }`}
                                    tabIndex={0}
                                >
                                    <span className="mr-1.5">{link.icon}</span>
                                    {link.label}
                                </Link>
                            ))}
                        </div>
                    )}

                    {/* Right section */}
                    <div className="flex items-center gap-3">
                        <ThemeToggle />

                        {user ? (
                            <>
                                <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-alt">
                                    <div className="w-7 h-7 gradient-primary rounded-full flex items-center justify-center text-white text-xs font-bold">
                                        {(user.first_name || user.username || '?')[0].toUpperCase()}
                                    </div>
                                    <span className="text-sm font-medium text-theme-text">
                                        {user.first_name || user.username}
                                    </span>
                                </div>
                                <button
                                    onClick={handleLogout}
                                    className="px-3 py-1.5 rounded-lg text-sm font-medium text-error hover:bg-error/10 transition-colors"
                                >
                                    Logout
                                </button>
                            </>
                        ) : (
                            variant !== 'auth' && (
                                <div className="flex items-center gap-2">
                                    <Link
                                        to="/login"
                                        className="px-4 py-2 rounded-lg text-sm font-medium text-theme-text-secondary hover:text-theme-text transition-colors"
                                    >
                                        Sign In
                                    </Link>
                                    <Link
                                        to="/register"
                                        className="px-4 py-2 gradient-primary text-white rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity shadow-theme"
                                    >
                                        Get Started
                                    </Link>
                                </div>
                            )
                        )}

                        {/* Mobile hamburger */}
                        {user && (
                            <button
                                className="md:hidden p-2 rounded-lg text-theme-text-secondary hover:bg-surface-alt focus:outline-none focus:ring-2 focus:ring-primary"
                                onClick={() => setMobileOpen(!mobileOpen)}
                                aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
                                aria-expanded={mobileOpen}
                                aria-controls="mobile-menu"
                            >
                                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    {mobileOpen ? (
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    ) : (
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                    )}
                                </svg>
                            </button>
                        )}
                    </div>
                </div>

                {/* Mobile nav with backdrop */}
                {mobileOpen && user && (
                    <>
                        <div className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm md:hidden" onClick={() => setMobileOpen(false)} aria-hidden="true"></div>
                        <div id="mobile-menu" className="md:hidden fixed top-0 right-0 w-4/5 max-w-xs h-full bg-surface shadow-lg z-50 animate-slide-in flex flex-col pt-6 pb-8 px-6 gap-2">
                            <div className="flex justify-between items-center mb-6">
                                <span className="text-lg font-bold text-theme-text">Menu</span>
                                <button onClick={() => setMobileOpen(false)} aria-label="Close menu" className="p-2 rounded-lg hover:bg-surface-alt">
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>
                            <div className="flex flex-col gap-2">
                                {navLinks.map(link => (
                                    <Link
                                        key={link.path}
                                        to={link.path}
                                        onClick={() => setMobileOpen(false)}
                                        className={`px-4 py-3 rounded-lg text-base font-medium transition-colors ${isActive(link.path)
                                                ? 'bg-primary/10 text-primary'
                                                : 'text-theme-text-secondary hover:bg-surface-alt'
                                            }`}
                                        tabIndex={0}
                                    >
                                        <span className="mr-2">{link.icon}</span>
                                        {link.label}
                                    </Link>
                                ))}
                            </div>
                            <div className="mt-auto flex flex-col gap-2 pt-8">
                                <button
                                    onClick={handleLogout}
                                    className="w-full px-4 py-3 rounded-lg text-base font-medium text-error hover:bg-error/10 transition-colors"
                                >
                                    Logout
                                </button>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </nav>
    );
};

export { ThemeToggle };
export default Navbar;
