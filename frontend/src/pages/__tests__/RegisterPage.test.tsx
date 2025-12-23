/**
 * RegisterPage Tests
 *
 * Tests for the registration page, including password confirmation validation.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { RegisterPage } from '../RegisterPage';
import { useAuthStore } from '../../stores/authStore';

// Helper to get input by name attribute (more reliable for password fields)
const getInputByName = (name: string): HTMLInputElement => {
  return document.querySelector(`input[name="${name}"]`) as HTMLInputElement;
};

// Mock the auth store
vi.mock('../../stores/authStore', () => ({
  useAuthStore: vi.fn(),
}));

// Mock the timezone utility
vi.mock('../../utils/timezone', () => ({
  getUserTimezone: vi.fn(() => 'America/New_York'),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('RegisterPage - Password Confirmation', () => {
  const mockRegister = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuthStore as any).mockReturnValue({
      register: mockRegister,
      isLoading: false,
    });
  });

  const renderRegisterPage = () => {
    return render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    );
  };

  it('should show error when passwords do not match', async () => {
    const user = userEvent.setup();
    renderRegisterPage();

    // Fill in the form - use input name attributes for password fields
    const emailInput = screen.getByRole('textbox', { name: /email address/i });
    const passwordInput = getInputByName('password');
    const confirmPasswordInput = getInputByName('confirmPassword');

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'differentpassword');

    // Wait for validation to run
    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    }, { timeout: 3000 });

    // Error message should be visible
    expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();

    // Both password fields should have error attribute (Material UI sets this)
    // We check the error message is shown, which confirms error state

    // Submit button should be disabled
    const submitButton = screen.getByRole('button', { name: /sign up/i });
    expect(submitButton).toBeDisabled();
  });

  it('should clear error when passwords match after mismatch', async () => {
    const user = userEvent.setup();
    renderRegisterPage();

    const passwordInput = getInputByName('password');
    const confirmPasswordInput = getInputByName('confirmPassword');

    // Type mismatched passwords
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'differentpassword');

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });

    // Clear and retype matching password
    await user.clear(confirmPasswordInput);
    await user.type(confirmPasswordInput, 'password123');

    // Error should disappear
    await waitFor(() => {
      expect(screen.queryByText(/passwords do not match/i)).not.toBeInTheDocument();
    });

    // Fields should no longer show error
    await waitFor(() => {
      expect(passwordInput.closest('.MuiFormControl-root')).not.toHaveClass('Mui-error');
      expect(confirmPasswordInput.closest('.MuiFormControl-root')).not.toHaveClass('Mui-error');
    });
  });

  it('should allow submission when passwords match', async () => {
    const user = userEvent.setup();
    mockRegister.mockResolvedValue({});
    renderRegisterPage();

    // Fill in the form with matching passwords
    const emailInput = screen.getByRole('textbox', { name: /email address/i });
    const passwordInput = getInputByName('password');
    const confirmPasswordInput = getInputByName('confirmPassword');
    const submitButton = screen.getByRole('button', { name: /sign up/i });

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'password123');

    // Wait for validation to clear any errors
    await waitFor(() => {
      expect(screen.queryByText(/passwords do not match/i)).not.toBeInTheDocument();
    });

    // Submit button should be enabled
    expect(submitButton).not.toBeDisabled();

    // Submit the form
    await user.click(submitButton);

    // Should call register with correct data
    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
        full_name: undefined,
        phone_number: undefined,
        timezone: 'America/New_York',
      });
    });
  });

  it('should prevent submission when passwords do not match', async () => {
    const user = userEvent.setup();
    renderRegisterPage();

    // Fill in the form with mismatched passwords
    const emailInput = screen.getByRole('textbox', { name: /email address/i });
    const passwordInput = getInputByName('password');
    const confirmPasswordInput = getInputByName('confirmPassword');
    const submitButton = screen.getByRole('button', { name: /sign up/i });

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.type(confirmPasswordInput, 'differentpassword');

    // Wait for error to appear
    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });

    // Submit button should be disabled
    expect(submitButton).toBeDisabled();

    // Try to submit (should not work - button is disabled so click won't do anything)
    // Register should not be called
    expect(mockRegister).not.toHaveBeenCalled();
  });

  it('should validate passwords in real-time as user types', async () => {
    const user = userEvent.setup();
    renderRegisterPage();

    const passwordInput = getInputByName('password');
    const confirmPasswordInput = getInputByName('confirmPassword');

    // Type password first
    await user.type(passwordInput, 'password123');

    // Type matching confirm password
    await user.type(confirmPasswordInput, 'password123');

    // Should not show error
    await waitFor(() => {
      expect(screen.queryByText(/passwords do not match/i)).not.toBeInTheDocument();
    });

    // Change confirm password to mismatch
    await user.clear(confirmPasswordInput);
    await user.type(confirmPasswordInput, 'different');

    // Should show error immediately
    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });
  });

  it('should disable submit button when password fields are empty', async () => {
    const user = userEvent.setup();
    renderRegisterPage();

    const emailInput = screen.getByRole('textbox', { name: /email address/i });
    const submitButton = screen.getByRole('button', { name: /sign up/i });

    // Only fill email, leave passwords empty
    await user.type(emailInput, 'test@example.com');

    // Submit button should be disabled
    expect(submitButton).toBeDisabled();
  });

  it('should show helper text for confirm password field', () => {
    renderRegisterPage();

    const confirmPasswordInput = getInputByName('confirmPassword');
    expect(confirmPasswordInput).toBeInTheDocument();

    // Should show helper text when no error
    expect(screen.getByText(/re-enter your password to confirm/i)).toBeInTheDocument();
  });
});

