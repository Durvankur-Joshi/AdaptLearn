import React, { createContext, useState, useContext, useEffect, useMemo } from 'react';
import axios from '../axiosConfig';
import { useNavigate } from 'react-router-dom';

const TeacherContext = createContext(null);

export const TeacherProvider = ({ children }) => {
    const [teacher, setTeacher] = useState(null);
    const [teacherProfile, setTeacherProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const token = localStorage.getItem('teacher_access_token');
        if (token) {
            fetchTeacher();
        } else {
            setLoading(false);
        }
    }, []);

    const fetchTeacher = async () => {
        try {
            const response = await axios.get('/auth/api/teacher/dashboard/', {
                headers: {
                    Authorization: `Bearer ${localStorage.getItem('teacher_access_token')}`
                }
            });
            setTeacher(response.data.teacher);
            setTeacherProfile(response.data);
        } catch (error) {
            console.error("Failed to fetch teacher:", error);
            localStorage.removeItem('teacher_access_token');
            localStorage.removeItem('teacher_refresh_token');
        } finally {
            setLoading(false);
        }
    };

    const teacherLogin = async (username, password) => {
        try {
            const response = await axios.post('/auth/api/teacher/login/', { username, password });
            const { access, refresh, user, teacher_profile } = response.data;

            localStorage.setItem('teacher_access_token', access);
            localStorage.setItem('teacher_refresh_token', refresh);
            setTeacher(teacher_profile);

            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Login failed'
            };
        }
    };

    const teacherRegister = async (userData) => {
        try {
            const response = await axios.post('/auth/api/teacher/register/', userData);
            // No tokens — account needs admin approval first
            return { success: true, pendingApproval: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data || 'Registration failed'
            };
        }
    };

    const teacherLogout = () => {
        localStorage.removeItem('teacher_access_token');
        localStorage.removeItem('teacher_refresh_token');
        setTeacher(null);
        setTeacherProfile(null);
        navigate('/teacher/login');
    };

    const teacherAxios = useMemo(() => {
        const instance = axios.create({
            baseURL: 'http://localhost:8000',
            headers: { 'Content-Type': 'application/json' },
        });

        instance.interceptors.request.use((config) => {
            const token = localStorage.getItem('teacher_access_token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        });

        instance.interceptors.response.use(
            (response) => response,
            async (error) => {
                const originalRequest = error.config;
                if (error.response?.status === 401 && !originalRequest._retry) {
                    originalRequest._retry = true;
                    try {
                        const refreshToken = localStorage.getItem('teacher_refresh_token');
                        if (refreshToken) {
                            const response = await axios.post('http://localhost:8000/api/token/refresh/', {
                                refresh: refreshToken
                            });
                            if (response.data.access) {
                                localStorage.setItem('teacher_access_token', response.data.access);
                                originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
                                return instance(originalRequest);
                            }
                        }
                    } catch {
                        localStorage.removeItem('teacher_access_token');
                        localStorage.removeItem('teacher_refresh_token');
                        window.location.href = '/teacher/login';
                    }
                }
                return Promise.reject(error);
            }
        );

        return instance;
    }, []);

    const value = {
        teacher,
        teacherProfile,
        teacherLogin,
        teacherRegister,
        teacherLogout,
        teacherAxios,
        loading,
        refreshDashboard: fetchTeacher,
    };

    return (
        <TeacherContext.Provider value={value}>
            {children}
        </TeacherContext.Provider>
    );
};

export const useTeacher = () => {
    const context = useContext(TeacherContext);
    if (!context) {
        throw new Error('useTeacher must be used within a TeacherProvider');
    }
    return context;
};
