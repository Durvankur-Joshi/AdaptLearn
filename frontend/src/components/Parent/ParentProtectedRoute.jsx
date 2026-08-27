import React from 'react';
import { Navigate } from 'react-router-dom';
import { useParent } from '../../context/ParentContext';

const ParentProtectedRoute = ({ children }) => {
    const { parent, loading } = useParent();

    if (loading) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <div className="w-12 h-12 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    if (!parent) {
        return <Navigate to="/parent/login" replace />;
    }

    return children;
};

export default ParentProtectedRoute;
