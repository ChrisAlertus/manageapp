/**
 * Delete Household Dialog
 *
 * Confirmation dialog for deleting a household.
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

interface DeleteHouseholdDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  householdName: string;
}

/**
 * DeleteHouseholdDialog - Confirmation dialog for deleting a household
 */
export const DeleteHouseholdDialog: React.FC<DeleteHouseholdDialogProps> = ({
  open,
  onClose,
  onConfirm,
  householdName,
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
      setError(err instanceof Error ? err.message : 'Failed to delete household');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Delete Household</DialogTitle>
      <DialogContent>
        <Typography variant="body1" paragraph>
          Are you sure you want to delete <strong>{householdName}</strong>?
        </Typography>
        <Typography variant="body2" color="error" paragraph>
          This action cannot be undone. All household data, including expenses,
          chores, and todos, will be permanently deleted.
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
          {loading ? 'Deleting...' : 'Delete Household'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

