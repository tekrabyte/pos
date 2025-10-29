import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Create axios instance with default config
const axiosInstance = axios.create({
  baseURL: BACKEND_URL, // Already includes /api from env
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
axiosInstance.interceptors.request.use(
  (config) => {
    // Add token if exists
    const token = localStorage.getItem('token') || localStorage.getItem('customer_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Show loading indicator for non-GET requests
    if (config.method !== 'get' && !config.hideLoading) {
      config.metadata = { startTime: new Date() };
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
axiosInstance.interceptors.response.use(
  (response) => {
    // Calculate request duration
    const config = response.config;
    if (config.metadata && config.metadata.startTime) {
      const duration = new Date() - config.metadata.startTime;
      console.log(`API Request completed in ${duration}ms: ${config.method.toUpperCase()} ${config.url}`);
    }
    
    return response;
  },
  (error) => {
    // Handle different error types
    if (error.code === 'ECONNABORTED') {
      toast.error('Request timeout - Server tidak merespons');
      console.error('Request timeout:', error.config.url);
    } else if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const message = error.response.data?.message || error.response.data?.detail || 'Terjadi kesalahan';
      
      // Check if request should be silent (no toast)
      const isSilent = error.config?.silent === true;
      
      switch (status) {
        case 400:
          if (!isSilent) toast.error(`Bad Request: ${message}`);
          break;
        case 401:
          // Only show toast and redirect if user was previously authenticated
          const hadToken = localStorage.getItem('token') || localStorage.getItem('customer_token');
          if (hadToken && !isSilent) {
            toast.error('Session expired - Silakan login kembali');
          }
          // Clear auth data
          localStorage.removeItem('token');
          localStorage.removeItem('customer_token');
          localStorage.removeItem('user');
          localStorage.removeItem('customer');
          // Only redirect if not already on login page
          const currentPath = window.location.pathname;
          if (!currentPath.includes('/login') && hadToken) {
            setTimeout(() => {
              const isCustomer = currentPath.includes('customer');
              window.location.href = isCustomer ? '/customer/login' : '/staff/login';
            }, 1500);
          }
          break;
        case 403:
          if (!isSilent) toast.error('Akses ditolak - Anda tidak memiliki izin');
          break;
        case 404:
          if (!isSilent) toast.error('Data tidak ditemukan');
          break;
        case 422:
          if (!isSilent) toast.error(`Validasi gagal: ${message}`);
          break;
        case 500:
          if (!isSilent) toast.error('Server error - Silakan coba lagi');
          console.error('Server error:', error.response.data);
          break;
        default:
          if (!isSilent) toast.error(`Error: ${message}`);
      }
    } else if (error.request) {
      // Request made but no response
      const isSilent = error.config?.silent === true;
      if (!isSilent) {
        toast.error('Tidak dapat terhubung ke server - Periksa koneksi internet');
      }
      console.error('Network error:', error.request);
    } else {
      // Something else happened
      const isSilent = error.config?.silent === true;
      if (!isSilent) {
        toast.error('Terjadi kesalahan yang tidak terduga');
      }
      console.error('Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Helper functions for common CRUD operations
export const api = {
  // GET request with optional params
  get: async (url, params = {}, config = {}) => {
    try {
      const response = await axiosInstance.get(url, { params, ...config });
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // POST request
  post: async (url, data, config = {}) => {
    try {
      const response = await axiosInstance.post(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // PUT request
  put: async (url, data, config = {}) => {
    try {
      const response = await axiosInstance.put(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // PATCH request
  patch: async (url, data, config = {}) => {
    try {
      const response = await axiosInstance.patch(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // DELETE request
  delete: async (url, config = {}) => {
    try {
      const response = await axiosInstance.delete(url, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },
};

// Retry logic for failed requests
export const retryRequest = async (fn, retries = 3, delay = 1000) => {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === retries - 1) throw error;
      console.log(`Retry attempt ${i + 1}/${retries}...`);
      await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
    }
  }
};

export default axiosInstance;
