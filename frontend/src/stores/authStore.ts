/**
 * Authentication Store (State Management)
 *
 * This file uses Zustand to manage authentication state.
 * Zustand is simpler than Redux - it's just a store that holds data and functions.
 *
 * What this store does:
 * - Keeps track of whether the user is logged in
 * - Stores the user's information
 * - Provides functions to login, logout, and check authentication status
 * - Saves/loads data from localStorage so it persists across page refreshes
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '../api/auth';
import { getCurrentUser, login as apiLogin, register as apiRegister } from '../api/auth';
import type { LoginRequest, RegisterRequest } from '../api/auth';

interface AuthState {
  // State: the data we're storing
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions: functions that change the state
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

/**
 * Create the auth store
 * The 'persist' middleware saves the state to localStorage automatically
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state: no user, not authenticated
      user: null,
      isAuthenticated: false,
      isLoading: false,

      /**
       * Login function
       * 1. Call the API to login
       * 2. Save the token to localStorage
       * 3. Update the store with user info
       */
      login: async (credentials: LoginRequest) => {
        set({ isLoading: true });
        try {
          // Call the backend API - this will throw if credentials are invalid
          const tokenResponse = await apiLogin(credentials);

          // Validate we got a token (defensive check)
          if (!tokenResponse?.access_token) {
            throw new Error('No access token received from server');
          }

          // Save the token to localStorage (the apiClient will use this automatically)
          localStorage.setItem('access_token', tokenResponse.access_token);

          // Get the user's information
          const user = await getCurrentUser();

          // Update the store - only if everything succeeded
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          // Ensure we clear any partial state on error
          set({
            isLoading: false,
            isAuthenticated: false,
            user: null,
          });
          // Re-throw the error so the component can handle it
          throw error;
        }
      },

      /**
       * Register function
       * 1. Call the API to register
       * 2. Automatically log the user in after registration
       */
      register: async (userData: RegisterRequest) => {
        set({ isLoading: true });
        try {
          // Register the user
          await apiRegister(userData);

          // Automatically log them in
          await get().login({
            email: userData.email,
            password: userData.password,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      /**
       * Logout function
       * Clear everything and redirect to login
       */
      logout: () => {
        localStorage.removeItem('access_token');
        set({
          user: null,
          isAuthenticated: false,
        });
      },

      /**
       * Check if user is still authenticated
       * Useful when the app loads - check if we have a valid token
       * Sets isLoading = true immediately to prevent flash of authenticated content
       */
      checkAuth: async () => {
        // Set loading immediately to prevent protected routes from rendering during validation
        set({ isLoading: true });

        const token = localStorage.getItem('access_token');
        if (!token) {
          set({ isAuthenticated: false, user: null, isLoading: false });
          return;
        }

        try {
          // Try to get the current user - if this fails, token is invalid
          const user = await getCurrentUser();
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          // Token is invalid, clear everything
          localStorage.removeItem('access_token');
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      },
    }),
    {
      // Zustand persist configuration
      name: 'auth-storage', // Key in localStorage
      partialize: (state) => ({
        // Only persist the user, not loading states
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);




