import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useParent } from '../../context/ParentContext';

const ParentLogin = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { parentLogin } = useParent();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        const result = await parentLogin(username, password);
        if (result.success) {
            navigate('/parent/dashboard');
        } else {
            setError(result.error);
        }
        setLoading(false);
    };

    return (
        <div className="min-h-screen bg-theme-bg flex items-center justify-center px-4">
            <div className="max-w-md w-full">
                <div className="text-center mb-8">
                    <div className="w-16 h-16 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4 shadow-lg">
                        P
                    </div>
                    <h1 className="text-3xl font-bold text-theme-text">Parent Portal</h1>
                    <p className="text-theme-text-secondary mt-2">Sign in to view your child&apos;s learning insights</p>
                </div>

                <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-8">
                    {error && (
                        <div className="mb-4 p-3 rounded-lg bg-error/10 border border-error/20 text-error text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="block text-sm font-medium text-theme-text mb-1.5">Username</label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full px-4 py-2.5 rounded-lg bg-surface-alt border border-theme-border text-theme-text focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-theme-text mb-1.5">Password</label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-4 py-2.5 rounded-lg bg-surface-alt border border-theme-border text-theme-text focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                                required
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-2.5 bg-gradient-to-r from-violet-500 to-indigo-600 text-white rounded-lg font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
                        >
                            {loading ? 'Signing in...' : 'Sign In as Parent'}
                        </button>
                    </form>

                    <div className="mt-6 text-center space-y-2">
                        <p className="text-sm text-theme-text-muted">
                            Don&apos;t have an account?{' '}
                            <Link to="/parent/register" className="text-violet-500 hover:underline font-medium">
                                Register here
                            </Link>
                        </p>
                        <p className="text-sm text-theme-text-muted">
                            <Link to="/login" className="text-primary hover:underline">
                                Student Login →
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ParentLogin;
