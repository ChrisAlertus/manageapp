/**
 * Send Invitation Dialog
 *
 * Modal dialog for sending a new household invitation.
 */

import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { sendInvitation, type InvitationCreate } from '../api/invitations';
import { getErrorMessage } from '../utils/errorHandling';

interface SendInvitationDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  householdId: number;
}

/**
 * SendInvitationDialog - Form to send a new invitation
 */
export const SendInvitationDialog: React.FC<SendInvitationDialogProps> = ({
  open,
  onClose,
  onSuccess,
  householdId,
}) => {
  const [formData, setFormData] = useState<InvitationCreate>({
    email: '',
    role: 'member',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [emailError, setEmailError] = useState<string | null>(null);

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    setEmailError(null);
    setError(null);

    if (!formData.email.trim()) {
      setEmailError('Email is required');
      return;
    }

    if (!validateEmail(formData.email.trim())) {
      setEmailError('Please enter a valid email address');
      return;
    }

    try {
      setLoading(true);
      await sendInvitation(householdId, {
        email: formData.email.trim(),
        role: formData.role,
      });
      handleClose();
      onSuccess();
    } catch (err) {
      const errorMessage = getErrorMessage(err, 'Failed to send invitation');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({ email: '', role: 'member' });
    setError(null);
    setEmailError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Send Invitation</DialogTitle>
      <DialogContent>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
          <TextField
            fullWidth
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) =>
              setFormData({ ...formData, email: e.target.value })
            }
            error={!!emailError}
            helperText={emailError}
            required
            disabled={loading}
            sx={{ mb: 2 }}
            autoFocus
          />

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Role</InputLabel>
            <Select
              value={formData.role}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  role: e.target.value as 'member' | 'owner',
                })
              }
              label="Role"
              disabled={loading}
            >
              <MenuItem value="member">Member</MenuItem>
              <MenuItem value="owner">Owner</MenuItem>
            </Select>
          </FormControl>

          {error && (
            <Typography color="error" sx={{ mb: 2 }}>
              {error}
            </Typography>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
        >
          {loading ? 'Sending...' : 'Send Invitation'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

