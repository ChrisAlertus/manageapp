/**
 * Login Page
 *
 * Simple login form that allows users to sign in.
 * Uses Material UI components for a clean, professional look.
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
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { getErrorMessage } from '../utils/errorHandling';

/**
 * LoginPage - User login form
 */
export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading } = useAuthStore();

  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    try {
      // Call the login function from the auth store
      await login({ email, password });

      // Verify authentication state before navigating (defensive check)
      // If login succeeded, isAuthenticated should be true
      const store = useAuthStore.getState();
      if (store.isAuthenticated) {
        navigate('/');
      } else {
        // This shouldn't happen if login() succeeds, but just in case
        setError('Login failed. Please check your credentials.');
      }
    } catch (err) {
      // Extract user-friendly error message using our reusable utility
      const errorMessage = getErrorMessage(
        err,
        'Login failed. Please check your credentials and try again.'
      );
      setError(errorMessage);
      // Log error for debugging
      console.error('Login error:', err);
    }
  };

  return (
    <Container
      maxWidth="sm"
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          width: '100%',
        }}
      >
        <Paper elevation={3} sx={{ padding: 4, width: '100%' }}>
          <Typography component="h1" variant="h4" align="center" gutterBottom>
            Sign In
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
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={isLoading}
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </Button>
            <Button
              fullWidth
              variant="text"
              onClick={() => navigate('/register')}
              disabled={isLoading}
            >
              Don't have an account? Sign Up
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};




