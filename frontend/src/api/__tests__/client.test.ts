/**
 * API Client Tests
 *
 * Tests for the API client configuration and interceptors.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import apiClient from '../client';

describe('API Client', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  it('should have the correct base URL', () => {
    expect(apiClient.defaults.baseURL).toBe('http://localhost:8000/api/v1');
  });

  it('should have JSON content type header', () => {
    expect(apiClient.defaults.headers['Content-Type']).toBe('application/json');
  });
});
