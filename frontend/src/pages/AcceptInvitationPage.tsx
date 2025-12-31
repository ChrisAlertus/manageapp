/**
 * Accept Invitation Page
 *
 * Handles token-based invitation acceptance from URL query parameter.
 */

import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { acceptInvitation } from '../api/invitations';
import { getErrorMessage } from '../utils/errorHandling';

/**
 * AcceptInvitationPage - Accepts invitation by token from URL
 */
export const AcceptInvitationPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!token) {
      setError('No invitation token provided');
    }
  }, [token]);

  const handleAccept = async () => {
    if (!token) return;

    try {
      setLoading(true);
      setError(null);
      const response = await acceptInvitation(token);
      setSuccess(true);
      // Redirect to household details after a short delay
      setTimeout(() => {
        navigate(`/households/${response.household_id}`);
      }, 2000);
    } catch (err) {
      setError(
        getErrorMessage(
          err,
          'Failed to accept invitation. The invitation may have expired or already been used.'
        )
      );
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <Box sx={{ maxWidth: 600, mx: 'auto', mt: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h5" component="h1" gutterBottom>
              Invalid Invitation
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              No invitation token was provided. Please check your invitation
              link.
            </Typography>
            <Button variant="contained" onClick={() => navigate('/households')}>
              Go to Households
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  if (success) {
    return (
      <Box sx={{ maxWidth: 600, mx: 'auto', mt: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h5" component="h1" gutterBottom sx={{ color: 'success.main' }}>
              Invitation Accepted!
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              You have successfully accepted the invitation. Redirecting to the
              household...
            </Typography>
            <CircularProgress size={24} sx={{ mt: 2 }} />
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', mt: 4 }}>
      <Card>
        <CardContent>
          <Typography variant="h5" component="h1" gutterBottom>
            Accept Invitation
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            You have been invited to join a household. Click the button below
            to accept the invitation.
          </Typography>

          {error && (
            <Typography color="error" paragraph>
              {error}
            </Typography>
          )}

          <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
            <Button
              variant="outlined"
              onClick={() => navigate('/households')}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              onClick={handleAccept}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : null}
            >
              {loading ? 'Accepting...' : 'Accept Invitation'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

