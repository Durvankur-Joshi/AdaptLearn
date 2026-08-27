import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

const Login = () => {
    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    
    const { login } = useAuth();
    const { theme, toggleTheme } = useTheme();
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const result = await login(formData.username, formData.password);
        
        if (result.success) {
            navigate('/dashboard');
        } else {
            setError(result.error);
        }
        
        setLoading(false);
    };

    return (
        <div className="min-h-screen bg-theme-bg flex">
            {/* Left panel - decorative */}
            <div className="hidden lg:flex lg:w-1/2 gradient-primary relative overflow-hidden">
                <div className="absolute inset-0 bg-black/10" />
                <div className="relative z-10 flex flex-col justify-center px-16 text-white">
                    <div className="w-12 h-12 gradient-primary rounded-xl flex items-center justify-center text-white font-bold text-2xl shadow-lg mb-8 border border-white/20">
                        A
                    </div>
                    <h1 className="text-4xl font-bold mb-4">Welcome back</h1>
                    <p className="text-white/80 text-lg leading-relaxed max-w-md">
                        Continue your adaptive learning journey. Your personalized path awaits.
                    </p>
                    <div className="mt-12 flex gap-8">
                        <div>
                            <div className="text-3xl font-bold">IRT</div>
                            <div className="text-white/60 text-sm">Adaptive Engine</div>
                        </div>
                        <div>
                            <div className="text-3xl font-bold">BKT</div>
                            <div className="text-white/60 text-sm">Knowledge Tracing</div>
                        </div>
                        <div>
                            <div className="text-3xl font-bold">XP</div>
                            <div className="text-white/60 text-sm">Gamified</div>
                        </div>
                    </div>
                </div>
                <div className="absolute -bottom-20 -right-20 w-96 h-96 rounded-full bg-white/5" />
                <div className="absolute top-20 -right-10 w-40 h-40 rounded-full bg-white/5" />
            </div>

            {/* Right panel - form */}
            <div className="flex-1 flex items-center justify-center px-4 sm:px-8 py-12">
                <div className="w-full max-w-md animate-fade-in-up">
                    {/* Theme toggle */}
                    <div className="flex justify-end mb-8">
                        <button
                            onClick={toggleTheme}
                            className="relative w-14 h-7 rounded-full bg-surface-alt border border-theme-border transition-colors duration-300"
                            aria-label="Toggle theme"
                        >
                            <span className={`absolute top-0.5 left-0.5 w-6 h-6 rounded-full transition-all duration-300 flex items-center justify-center text-sm ${
                                theme === 'dark'
                                    ? 'translate-x-7 bg-indigo-500 text-white'
                                    : 'translate-x-0 bg-yellow-400 text-yellow-900'
                            }`}>
                                {theme === 'dark' ? '🌙' : '☀️'}
                            </span>
                        </button>
                    </div>

                    <div className="mb-8">
                        <Link to="/" className="flex items-center gap-2 mb-8 group">
                            <div className="w-9 h-9 gradient-primary rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-lg">
                                A
                            </div>
                            <span className="text-lg font-bold text-theme-text">
                                Adapt<span className="text-gradient">Learn</span>
                            </span>
                        </Link>
                        <h2 className="text-3xl font-bold text-theme-text">
                            Sign in
                        </h2>
                        <p className="mt-2 text-theme-text-secondary">
                            Don't have an account?{' '}
                            <Link to="/register" className="text-primary font-semibold hover:text-primary-dark transition-colors">
                                Create one
                            </Link>
                        </p>
                    </div>
                    
                    {error && (
                        <div className="mb-6 p-4 rounded-theme bg-error/10 border border-error/20 text-error text-sm font-medium animate-scale-in" role="alert">
                            {error}
                        </div>
                    )}
                    
                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-theme-text mb-1.5">
                                Username or Email
                            </label>
                            <input
                                id="username"
                                name="username"
                                type="text"
                                required
                                className="w-full px-4 py-3 rounded-theme bg-surface border border-theme-border text-theme-text placeholder-theme-text-muted focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                                placeholder="Enter your username or email"
                                value={formData.username}
                                onChange={handleChange}
                            />
                        </div>
                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-theme-text mb-1.5">
                                Password
                            </label>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                required
                                className="w-full px-4 py-3 rounded-theme bg-surface border border-theme-border text-theme-text placeholder-theme-text-muted focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
                                placeholder="Enter your password"
                                value={formData.password}
                                onChange={handleChange}
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 gradient-primary text-white rounded-theme font-semibold hover:opacity-90 transition-all shadow-theme disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                    Signing in...
                                </span>
                            ) : 'Sign in'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default Login;