/**
 * API Client Configuration
 *
 * This file sets up Axios to communicate with our backend API.
 * It automatically adds authentication tokens to requests and handles errors.
 */

import axios, { AxiosError } from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

// Get the API URL from environment variables
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Create an Axios instance with default configuration
 * This is our main way to talk to the backend
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request Interceptor
 * This runs before every API request.
 * It automatically adds the JWT token to the Authorization header if we have one.
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get the token from localStorage (where we store it after login)
    const token = localStorage.getItem('access_token');

    // If we have a token, add it to the request headers
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    // If something goes wrong before the request, reject it
    return Promise.reject(error);
  }
);

/**
 * Response Interceptor
 * This runs after every API response.
 * It handles common errors like 401 (unauthorized) which means we need to log in again.
 */
apiClient.interceptors.response.use(
  (response) => {
    // If the request was successful, just return the response
    return response;
  },
  (error: AxiosError) => {
    // If we get a 401 error, it means our token is invalid or expired
    if (error.response?.status === 401) {
      const requestUrl = error.config?.url || '';

      // Don't redirect on login/register failures - let the component handle the error
      const isAuthRequest = requestUrl.includes('/auth/login') || requestUrl.includes('/auth/register');

      if (!isAuthRequest) {
        // Only clear token and redirect for authenticated requests (not login attempts)
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');

        // Redirect to login page (if we're not already there)
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    }

    // Pass the error along so components can handle it
    return Promise.reject(error);
  }
);

export default apiClient;

