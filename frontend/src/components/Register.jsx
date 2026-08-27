import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';

const Register = () => {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        first_name: '',
        last_name: '',
        password: '',
        password2: ''
    });
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);
    
    const { register } = useAuth();
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
        setErrors({});
        setLoading(true);

        const result = await register(formData);
        
        if (result.success) {
            navigate('/login', { state: { message: 'Registration successful! Please login.' } });
        } else {
            setErrors(result.error);
        }
        
        setLoading(false);
    };

    const inputClass = "w-full px-4 py-3 rounded-theme bg-surface border border-theme-border text-theme-text placeholder-theme-text-muted focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all";

    return (
        <div className="min-h-screen bg-theme-bg flex">
            {/* Left panel - decorative */}
            <div className="hidden lg:flex lg:w-1/2 gradient-primary relative overflow-hidden">
                <div className="absolute inset-0 bg-black/10" />
                <div className="relative z-10 flex flex-col justify-center px-16 text-white">
                    <div className="w-12 h-12 gradient-primary rounded-xl flex items-center justify-center text-white font-bold text-2xl shadow-lg mb-8 border border-white/20">
                        A
                    </div>
                    <h1 className="text-4xl font-bold mb-4">Start your journey</h1>
                    <p className="text-white/80 text-lg leading-relaxed max-w-md">
                        Join our adaptive learning platform and experience education that evolves with you.
                    </p>
                    <div className="mt-12 space-y-4">
                        {['Personalized learning paths', 'Real-time mastery tracking', 'AI-powered question generation'].map((item, i) => (
                            <div key={i} className="flex items-center gap-3">
                                <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center">
                                    <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                    </svg>
                                </div>
                                <span className="text-white/90">{item}</span>
                            </div>
                        ))}
                    </div>
                </div>
                <div className="absolute -bottom-20 -right-20 w-96 h-96 rounded-full bg-white/5" />
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
                            Create account
                        </h2>
                        <p className="mt-2 text-theme-text-secondary">
                            Already registered?{' '}
                            <Link to="/login" className="text-primary font-semibold hover:text-primary-dark transition-colors">
                                Sign in
                            </Link>
                        </p>
                    </div>
                    
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-theme-text mb-1.5">
                                Username
                            </label>
                            <input id="username" name="username" type="text" required className={inputClass}
                                placeholder="Choose a username" value={formData.username} onChange={handleChange} />
                            {errors.username && <p className="mt-1.5 text-sm text-error">{errors.username[0]}</p>}
                        </div>

                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-theme-text mb-1.5">
                                Email
                            </label>
                            <input id="email" name="email" type="email" required className={inputClass}
                                placeholder="you@example.com" value={formData.email} onChange={handleChange} />
                            {errors.email && <p className="mt-1.5 text-sm text-error">{errors.email[0]}</p>}
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label htmlFor="first_name" className="block text-sm font-medium text-theme-text mb-1.5">
                                    First Name
                                </label>
                                <input id="first_name" name="first_name" type="text" required className={inputClass}
                                    placeholder="First" value={formData.first_name} onChange={handleChange} />
                            </div>
                            <div>
                                <label htmlFor="last_name" className="block text-sm font-medium text-theme-text mb-1.5">
                                    Last Name
                                </label>
                                <input id="last_name" name="last_name" type="text" required className={inputClass}
                                    placeholder="Last" value={formData.last_name} onChange={handleChange} />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-theme-text mb-1.5">
                                Password
                            </label>
                            <input id="password" name="password" type="password" required className={inputClass}
                                placeholder="Create a password" value={formData.password} onChange={handleChange} />
                            {errors.password && <p className="mt-1.5 text-sm text-error">{errors.password[0]}</p>}
                        </div>

                        <div>
                            <label htmlFor="password2" className="block text-sm font-medium text-theme-text mb-1.5">
                                Confirm Password
                            </label>
                            <input id="password2" name="password2" type="password" required className={inputClass}
                                placeholder="Confirm password" value={formData.password2} onChange={handleChange} />
                        </div>

                        {errors.non_field_errors && (
                            <div className="p-4 rounded-theme bg-error/10 border border-error/20 text-error text-sm font-medium">
                                {errors.non_field_errors[0]}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 gradient-primary text-white rounded-theme font-semibold hover:opacity-90 transition-all shadow-theme disabled:opacity-50 disabled:cursor-not-allowed mt-2"
                        >
                            {loading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24" fill="none">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                    </svg>
                                    Creating account...
                                </span>
                            ) : 'Create account'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default Register;