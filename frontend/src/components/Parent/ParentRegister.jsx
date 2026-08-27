import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useParent } from '../../context/ParentContext';

const ParentRegister = () => {
    const [formData, setFormData] = useState({
        username: '', email: '', password: '', password2: '',
        first_name: '', last_name: '', display_name: '',
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { parentRegister } = useParent();
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        const result = await parentRegister(formData);
        if (result.success) {
            navigate('/parent/login');
        } else {
            const errData = result.error;
            if (typeof errData === 'object' && errData !== null) {
                const msg = Object.values(errData).flat().filter(Boolean).join(', ');
                setError(msg || 'Registration failed');
            } else {
                setError(typeof errData === 'string' ? errData : 'Registration failed');
            }
        }
        setLoading(false);
    };

    return (
        <div className="min-h-screen bg-theme-bg flex items-center justify-center px-4 py-8">
            <div className="max-w-lg w-full">
                <div className="text-center mb-8">
                    <div className="w-16 h-16 bg-gradient-to-br from-violet-500 to-indigo-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4 shadow-lg">
                        P
                    </div>
                    <h1 className="text-3xl font-bold text-theme-text">Create Parent Account</h1>
                    <p className="text-theme-text-secondary mt-2">Join to see your child&apos;s adaptive learning insights</p>
                </div>

                <div className="bg-surface rounded-theme-xl shadow-theme border border-theme-border p-8">
                    {error && (
                        <div className="mb-4 p-3 rounded-lg bg-error/10 border border-error/20 text-error text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">First Name</label>
                                <input type="text" name="first_name" value={formData.first_name} onChange={handleChange}
                                    className="w-full px-3 py-2 rounded-lg bg-surface-alt border border-theme-border text-theme-text focus:outline-none focus:ring-2 focus:ring-violet-500/50" required />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Last Name</label>
                                <input type="text" name="last_name" value={formData.last_name} onChange={handleChange}
                                    className="w-full px-3 py-2 rounded-lg bg-surface-alt border border-theme-border text-theme-text focus:outline-none focus:ring-2 focus:ring-violet-500/50" required />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-theme-text mb-1">Username</label>
                            <input type="text" name="username" value={formData.username} onChange={handleChange}
                                className="w-full px-3 py-2 rounded-lg bg-surface-alt border border-theme-border text-theme-text focus:outline-none focus:ring-2 focus:ring-violet-500/50" required />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-theme-text mb-1">Email</label>
                            <input type="email" name="email" value={formData.email} onChange={handleChange}
                                className="w-full px-3 py-2 rounded-lg bg-surface-alt border border-theme-border text-theme-text focus:outline-none focus:ring-2 focus:ring-violet-500/50" required />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-theme-text mb-1">Display name (optional)</label>
                            <input type="text" name="display_name" value={formData.display_name} onChange={handleChange}
                                placeholder="How your child sees you"
                                className="w-full px-3 py-2 rounded-lg bg-surface-alt border border-theme-border text-theme-text focus:outline-none focus:ring-2 focus:ring-violet-500/50" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Password</label>
                                <input type="password" name="password" value={formData.password} onChange={handleChange}
                                    className="w-full px-3 py-2 rounded-lg bg-surface-alt border border-theme-border text-theme-text focus:outline-none focus:ring-2 focus:ring-violet-500/50" required />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-theme-text mb-1">Confirm Password</label>
                                <input type="password" name="password2" value={formData.password2} onChange={handleChange}
                                    className="w-full px-3 py-2 rounded-lg bg-surface-alt border border-theme-border text-theme-text focus:outline-none focus:ring-2 focus:ring-violet-500/50" required />
                            </div>
                        </div>
                        <button type="submit" disabled={loading}
                            className="w-full py-2.5 bg-gradient-to-r from-violet-500 to-indigo-600 text-white rounded-lg font-semibold hover:opacity-90 transition-opacity disabled:opacity-50">
                            {loading ? 'Creating Account...' : 'Create Parent Account'}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-sm text-theme-text-muted">
                            Already have an account?{' '}
                            <Link to="/parent/login" className="text-violet-500 hover:underline font-medium">Sign in</Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ParentRegister;
