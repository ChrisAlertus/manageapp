/**
 * Authentication API Functions
 *
 * These functions handle login, registration, and getting user info.
 * They use the apiClient to make requests to the backend.
 */

import apiClient from './client';

// Types for the API requests and responses
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
  phone_number?: string;
  timezone?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  email: string;
  full_name?: string;
  phone_number?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Login a user
 * Sends email and password to the backend, gets back a JWT token
 */
export const login = async (credentials: LoginRequest): Promise<TokenResponse> => {
  const response = await apiClient.post<TokenResponse>('/auth/login', credentials);
  return response.data;
};

/**
 * Register a new user
 * Sends user information to the backend, creates a new account
 */
export const register = async (userData: RegisterRequest): Promise<User> => {
  const response = await apiClient.post<User>('/auth/register', userData);
  return response.data;
};

/**
 * Get the current logged-in user's information
 * Requires authentication (token will be added automatically by apiClient)
 */
export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<User>('/auth/me');
  return response.data;
};




