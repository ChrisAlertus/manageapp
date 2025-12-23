/**
 * Timezone Utility Functions
 *
 * Simple helper to detect the user's timezone automatically.
 * This is used during registration to set the user's preferred timezone.
 */

/**
 * Get the user's IANA timezone (e.g., "America/New_York", "Europe/London")
 * Uses the browser's built-in Intl API
 *
 * @returns The IANA timezone string
 */
export const getUserTimezone = (): string => {
  try {
    // This is a standard browser API that works in all modern browsers
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch (error) {
    // Fallback to UTC if detection fails (shouldn't happen in modern browsers)
    console.warn('Timezone detection failed, defaulting to UTC', error);
    return 'UTC';
  }
};




