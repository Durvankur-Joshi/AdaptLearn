import React from 'react';
import { Navigate } from 'react-router-dom';
import { useTeacher } from '../../context/TeacherContext';

const TeacherProtectedRoute = ({ children }) => {
    const { teacher, loading } = useTeacher();

    if (loading) {
        return (
            <div className="min-h-screen bg-theme-bg flex items-center justify-center">
                <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    if (!teacher) {
        return <Navigate to="/teacher/login" replace />;
    }

    return children;
};

export default TeacherProtectedRoute;
