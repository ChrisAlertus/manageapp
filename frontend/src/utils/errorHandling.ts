/**
 * Error Handling Utilities
 *
 * Provides type-safe error handling functions for extracting error messages
 * from various error types, including Axios errors and standard JavaScript errors.
 *
 * Based on TypeScript best practices for error handling in catch blocks.
 */

/**
 * Type guard to check if an error has a message property
 */
type ErrorWithMessage = {
  message: string;
};

function isErrorWithMessage(error: unknown): error is ErrorWithMessage {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    typeof (error as Record<string, unknown>).message === 'string'
  );
}

/**
 * Converts an unknown error to an ErrorWithMessage
 * Handles cases where the error might not be a standard Error object
 */
function toErrorWithMessage(maybeError: unknown): ErrorWithMessage {
  if (isErrorWithMessage(maybeError)) {
    return maybeError;
  }

  try {
    return new Error(JSON.stringify(maybeError));
  } catch {
    // Fallback in case there's an error stringifying the maybeError
    // (e.g., circular references)
    return new Error(String(maybeError));
  }
}

/**
 * FastAPI validation error detail structure
 */
type FastAPIValidationError = {
  type?: string;
  loc?: Array<string | number>;
  msg?: string;
};

/**
 * Axios error response structure from our backend
 */
type AxiosErrorResponse = {
  response?: {
    data?: {
      detail?: string | Array<FastAPIValidationError>;
    };
  };
  message?: string;
};

/**
 * Checks if an error is an AxiosError-like object with our backend's response structure
 */
function isAxiosErrorLike(error: unknown): error is AxiosErrorResponse {
  return (
    typeof error === 'object' &&
    error !== null &&
    'response' in error
  );
}

/**
 * Extracts a user-friendly error message from an unknown error.
 *
 * Handles:
 * - Axios errors with FastAPI response structure (string or validation array)
 * - Standard Error objects
 * - Any other thrown value
 *
 * @param error - The error to extract a message from
 * @param defaultMessage - Optional default message if no error message can be extracted
 * @returns A user-friendly error message string
 *
 * @example
 * ```ts
 * try {
 *   await someApiCall();
 * } catch (error) {
 *   const message = getErrorMessage(error, 'Something went wrong');
 *   setError(message);
 * }
 * ```
 */
export function getErrorMessage(
  error: unknown,
  defaultMessage: string = 'An unexpected error occurred. Please try again.'
): string {
  // First, check if it's an AxiosError-like object with our backend's response structure
  if (isAxiosErrorLike(error)) {
    const detail = error.response?.data?.detail;

    if (detail) {
      if (typeof detail === 'string') {
        // Handle string errors (e.g., 401, 403, 500)
        return detail;
      } else if (Array.isArray(detail) && detail.length > 0) {
        // Handle validation errors (422) - extract first error message
        const firstError = detail[0];
        return firstError.msg || defaultMessage;
      }
    }

    // Fall back to Axios error message if available
    if (error.message) {
      return error.message;
    }
  }

  // For standard Error objects or other error types
  return toErrorWithMessage(error).message || defaultMessage;
}

/**
 * Extracts error information including status code and full error details.
 * Useful when you need more context than just the message.
 *
 * @param error - The error to extract information from
 * @returns An object containing the error message, status code (if available), and raw error
 *
 * @example
 * ```ts
 * try {
 *   await someApiCall();
 * } catch (error) {
 *   const errorInfo = getErrorInfo(error);
 *   console.error('Status:', errorInfo.statusCode);
 *   setError(errorInfo.message);
 * }
 * ```
 */
export function getErrorInfo(error: unknown): {
  message: string;
  statusCode?: number;
  rawError: unknown;
} {
  const message = getErrorMessage(error);
  let statusCode: number | undefined;

  if (isAxiosErrorLike(error) && error.response) {
    // TypeScript doesn't know about status, but AxiosError has it
    statusCode = (error.response as { status?: number }).status;
  }

  return {
    message,
    statusCode,
    rawError: error,
  };
}

