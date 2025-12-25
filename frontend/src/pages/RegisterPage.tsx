/**
 * Register Page
 *
 * User registration form with automatic timezone detection.
 * Collects email, password, name, and optional phone number.
 */

import {
  Alert,
  Box,
  Button,
  Container,
  Paper,
  TextField,
  Typography,
} from '@mui/material';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { getUserTimezone } from '../utils/timezone';
import { getErrorMessage } from '../utils/errorHandling';

/**
 * RegisterPage - User registration form
 */
export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { register, isLoading } = useAuthStore();

  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [detectedTimezone, setDetectedTimezone] = useState<string>('');

  // Automatically detect timezone when component loads
  useEffect(() => {
    const timezone = getUserTimezone();
    setDetectedTimezone(timezone);
  }, []);

  // Validate passwords match whenever either password field changes
  useEffect(() => {
    // Only validate if both fields have values
    if (password && confirmPassword) {
      if (password !== confirmPassword) {
        setPasswordError('Passwords do not match');
      } else {
        setPasswordError(null);
      }
    } else {
      // Clear error if either field is empty
      setPasswordError(null);
    }
  }, [password, confirmPassword]);

  // Validate passwords match (for form submission)
  const validatePasswords = (): boolean => {
    if (password !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return false;
    }
    setPasswordError(null);
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setPasswordError(null);

    // Validate passwords match before submitting
    if (!validatePasswords()) {
      return;
    }

    try {
      // Register with all the form data, including detected timezone
      await register({
        email,
        password,
        full_name: fullName || undefined,
        phone_number: phoneNumber || undefined,
        timezone: detectedTimezone,
      });

      // If successful, user is automatically logged in, redirect to dashboard
      navigate('/');
    } catch (err) {
      // Extract user-friendly error message using our reusable utility
      const errorMessage = getErrorMessage(
        err,
        'Registration failed. Please try again.'
      );
      setError(errorMessage);
      // Log error for debugging
      console.error('Registration error:', err);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ padding: 4, width: '100%' }}>
          <Typography component="h1" variant="h4" align="center" gutterBottom>
            Sign Up
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="email"
              label="Email Address"
              name="email"
              autoComplete="email"
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type="password"
              id="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              helperText="Password must be at least 8 characters"
              error={!!passwordError}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="confirmPassword"
              label="Confirm Password"
              type="password"
              id="confirmPassword"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isLoading}
              error={!!passwordError}
              helperText={passwordError || 'Re-enter your password to confirm'}
            />
            <TextField
              margin="normal"
              fullWidth
              id="fullName"
              label="Full Name (Optional)"
              name="fullName"
              autoComplete="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              disabled={isLoading}
            />
            <TextField
              margin="normal"
              fullWidth
              id="phoneNumber"
              label="Phone Number (Optional)"
              name="phoneNumber"
              autoComplete="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              disabled={isLoading}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={isLoading || !!passwordError || !password || !confirmPassword}
            >
              {isLoading ? 'Creating account...' : 'Sign Up'}
            </Button>
            <Button
              fullWidth
              variant="text"
              onClick={() => navigate('/login')}
              disabled={isLoading}
            >
              Already have an account? Sign In
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};




