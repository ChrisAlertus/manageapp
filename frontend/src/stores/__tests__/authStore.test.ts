/**
 * Auth Store Tests
 *
 * Tests for the authentication store functionality.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from '../authStore';
import * as authApi from '../../api/auth';

// Mock the API functions
vi.mock('../../api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
  getCurrentUser: vi.fn(),
}));

describe('Auth Store', () => {
  beforeEach(() => {
    // Reset the store state before each test
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    });
    localStorage.clear();
    vi.clearAllMocks();
  });

  it('should have initial state', () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(false);
  });

  it('should login successfully', async () => {
    const mockToken = { access_token: 'test-token', token_type: 'bearer' };
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      full_name: 'Test User',
      is_active: true,
      is_verified: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    vi.mocked(authApi.login).mockResolvedValue(mockToken);
    vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser);

    await useAuthStore.getState().login({
      email: 'test@example.com',
      password: 'password123',
    });

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual(mockUser);
    expect(localStorage.getItem('access_token')).toBe('test-token');
  });

  it('should logout successfully', () => {
    // Set up logged in state
    useAuthStore.setState({
      user: { id: 1, email: 'test@example.com' } as any,
      isAuthenticated: true,
    });
    localStorage.setItem('access_token', 'test-token');

    useAuthStore.getState().logout();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
  });

  it('should check auth and update state if token is valid', async () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      is_active: true,
      is_verified: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    localStorage.setItem('access_token', 'valid-token');
    vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser);

    await useAuthStore.getState().checkAuth();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(true);
    expect(state.user).toEqual(mockUser);
  });

  it('should clear state if token is invalid', async () => {
    localStorage.setItem('access_token', 'invalid-token');
    vi.mocked(authApi.getCurrentUser).mockRejectedValue(new Error('Unauthorized'));

    await useAuthStore.getState().checkAuth();

    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
  });
});




