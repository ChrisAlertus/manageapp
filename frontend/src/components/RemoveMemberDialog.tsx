/**
 * Remove Member Dialog
 *
 * Confirmation dialog for removing a member from a household.
 */

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { type HouseholdMember } from '../api/households';

interface RemoveMemberDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  member: HouseholdMember | null;
}

/**
 * RemoveMemberDialog - Confirmation dialog for removing a member
 */
export const RemoveMemberDialog: React.FC<RemoveMemberDialogProps> = ({
  open,
  onClose,
  onConfirm,
  member,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    try {
      setLoading(true);
      setError(null);
      await onConfirm();
      handleClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove member');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setError(null);
    onClose();
  };

  if (!member) {
    return null;
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Remove Member</DialogTitle>
      <DialogContent>
        <Typography variant="body1" paragraph>
          Are you sure you want to remove{' '}
          <strong>{member.full_name || member.email}</strong> from this
          household?
        </Typography>
        <Typography variant="body2" color="text.secondary">
          This action cannot be undone. The member will lose access to all
          household data.
        </Typography>
        {error && (
          <Typography color="error" sx={{ mt: 2 }}>
            {error}
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleConfirm}
          variant="contained"
          color="error"
          disabled={loading}
        >
          {loading ? 'Removing...' : 'Remove'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

