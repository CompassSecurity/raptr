import type { AxiosInstance } from 'axios';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
import { handleApiError } from '@/utils/errorHandler';

// Create Axios instance
export const api: AxiosInstance = axios.create({
    baseURL:
        import.meta.env.VITE_API_URL ||
        (import.meta.env.DEV ? 'http://localhost:8000/api/v1' : '/api/v1'),
    headers: {
        'Content-Type': 'application/json',
    },
    // Serialize arrays as repeated params (priority=Low&priority=High) instead of bracket notation (priority[]=Low)
    paramsSerializer: {
        indexes: null, // Remove brackets from array params
    },
});

// Request interceptor: Attach token
api.interceptors.request.use(
    (config) => {
        const authStore = useAuthStore();
        if (authStore.token) {
            config.headers.Authorization = `Bearer ${authStore.token}`;
        }
        return config;
    },
    (error) => Promise.reject(error),
);

// Response interceptor: Global error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        handleApiError(error);
        return Promise.reject(error);
    },
);
