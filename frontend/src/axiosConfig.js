import axios from 'axios';

const axiosInstance = axios.create({
    baseURL: 'https://adaptlearn-bj1g.onrender.com', // Use the correct backend API root
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add token to requests if it exists
axiosInstance.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Handle 401 errors and token refresh
axiosInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        
        // If error is 401 and we haven't tried to refresh token yet
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            
            try {
                const refreshToken = localStorage.getItem('refresh_token');
                if (refreshToken) {
                    const response = await axios.post('https://adaptlearn-bj1g.onrender.com/api/token/refresh/', {
                        refresh: refreshToken
                    });
                    
                    if (response.data.access) {
                        localStorage.setItem('access_token', response.data.access);
                        originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
                        return axiosInstance(originalRequest);
                    }
                }
            } catch (refreshError) {
                // Refresh failed - clear tokens and redirect to login
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
            }
        }
        
        return Promise.reject(error);
    }
);

export default axiosInstance;