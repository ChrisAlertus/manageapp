/**
 * Timezone Utility Tests
 *
 * Tests for timezone detection functionality.
 */

import { describe, it, expect, vi } from 'vitest';
import { getUserTimezone } from '../timezone';

describe('Timezone Utility', () => {
  it('should return a valid timezone string', () => {
    const timezone = getUserTimezone();
    // Should be a non-empty string
    expect(timezone).toBeTruthy();
    expect(typeof timezone).toBe('string');
    // Should be a valid IANA timezone format (contains a slash or is UTC)
    expect(timezone === 'UTC' || timezone.includes('/')).toBe(true);
  });

  it('should fallback to UTC if detection fails', () => {
    // Mock Intl.DateTimeFormat to throw an error
    const originalIntl = window.Intl;
    // @ts-ignore
    window.Intl = {
      DateTimeFormat: vi.fn(() => {
        throw new Error('Timezone detection failed');
      }),
    } as any;

    const timezone = getUserTimezone();
    expect(timezone).toBe('UTC');

    // Restore original Intl
    window.Intl = originalIntl;
  });
});

