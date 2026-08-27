import React, { createContext, useState, useContext, useEffect, useMemo, useCallback } from 'react';
import axios from '../axiosConfig';
import { useNavigate } from 'react-router-dom';

const ParentContext = createContext(null);

const PARENT_ACCESS_KEY = 'parent_access_token';
const PARENT_REFRESH_KEY = 'parent_refresh_token';

export const ParentProvider = ({ children }) => {
    const [parent, setParent] = useState(null);
    const [parentChildren, setParentChildren] = useState({ children: [], pending_invites: [] });
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const token = localStorage.getItem(PARENT_ACCESS_KEY);
        if (token) {
            fetchParent();
        } else {
            setLoading(false);
        }
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const parentAxiosStatic = useMemo(() => {
        const instance = axios.create({
            baseURL: 'http://localhost:8000',
            headers: { 'Content-Type': 'application/json' },
        });
        instance.interceptors.request.use((config) => {
            const token = localStorage.getItem(PARENT_ACCESS_KEY);
            if (token) config.headers.Authorization = `Bearer ${token}`;
            return config;
        });
        instance.interceptors.response.use(
            (response) => response,
            async (error) => {
                const originalRequest = error.config;
                if (error.response?.status === 401 && !originalRequest._retry) {
                    originalRequest._retry = true;
                    try {
                        const refreshToken = localStorage.getItem(PARENT_REFRESH_KEY);
                        if (refreshToken) {
                            const res = await axios.post('http://localhost:8000/api/token/refresh/', { refresh: refreshToken });
                            if (res.data.access) {
                                localStorage.setItem(PARENT_ACCESS_KEY, res.data.access);
                                originalRequest.headers.Authorization = `Bearer ${res.data.access}`;
                                return instance(originalRequest);
                            }
                        }
                    } catch {
                        localStorage.removeItem(PARENT_ACCESS_KEY);
                        localStorage.removeItem(PARENT_REFRESH_KEY);
                        window.location.href = '/parent/login';
                    }
                }
                return Promise.reject(error);
            }
        );
        return instance;
    }, []);

    const fetchChildren = useCallback(async () => {
        try {
            const response = await parentAxiosStatic.get('/auth/api/parent/children/');
            setParentChildren(response.data);
        } catch (error) {
            console.error('Failed to fetch children:', error);
            setParentChildren({ children: [], pending_invites: [] });
        }
    }, [parentAxiosStatic]);

    const fetchParent = useCallback(async () => {
        try {
            const response = await parentAxiosStatic.get('/auth/api/parent/check/');
            if (response.data.is_parent && response.data.parent_profile) {
                setParent(response.data.parent_profile);
                await fetchChildren();
            } else {
                setParent(null);
            }
        } catch (error) {
            console.error('Failed to fetch parent:', error);
            localStorage.removeItem(PARENT_ACCESS_KEY);
            localStorage.removeItem(PARENT_REFRESH_KEY);
            setParent(null);
        } finally {
            setLoading(false);
        }
    }, [parentAxiosStatic, fetchChildren]);

    const parentLogin = async (username, password) => {
        try {
            const response = await axios.post('/auth/api/parent/login/', { username, password });
            const { access, refresh, user, parent_profile } = response.data;
            localStorage.setItem(PARENT_ACCESS_KEY, access);
            localStorage.setItem(PARENT_REFRESH_KEY, refresh);
            setParent(parent_profile);
            await fetchChildren();
            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.error || 'Login failed',
            };
        }
    };

    const parentRegister = async (userData) => {
        try {
            await axios.post('/auth/api/parent/register/', userData);
            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data || 'Registration failed',
            };
        }
    };

    const parentLogout = () => {
        localStorage.removeItem(PARENT_ACCESS_KEY);
        localStorage.removeItem(PARENT_REFRESH_KEY);
        setParent(null);
        setParentChildren({ children: [], pending_invites: [] });
        navigate('/parent/login');
    };

    const parentAxios = parentAxiosStatic;

    const value = {
        parent,
        parentChildren,
        parentLogin,
        parentRegister,
        parentLogout,
        parentAxios,
        loading,
        fetchChildren,
        fetchParent,
    };

    return (
        <ParentContext.Provider value={value}>
            {children}
        </ParentContext.Provider>
    );
};

export const useParent = () => {
    const context = useContext(ParentContext);
    if (!context) {
        throw new Error('useParent must be used within a ParentProvider');
    }
    return context;
};
