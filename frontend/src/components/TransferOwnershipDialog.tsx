/**
 * Transfer Ownership Dialog
 *
 * Modal dialog for transferring household ownership to another member.
 */

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { type HouseholdMember } from '../api/households';

interface TransferOwnershipDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (newOwnerId: number) => Promise<void>;
  members: HouseholdMember[];
  currentUserId?: number;
}

/**
 * TransferOwnershipDialog - Dialog for selecting new owner
 */
export const TransferOwnershipDialog: React.FC<
  TransferOwnershipDialogProps
> = ({ open, onClose, onConfirm, members, currentUserId }) => {
  const [selectedUserId, setSelectedUserId] = useState<number | ''>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter out current user and only show members (not owners)
  const eligibleMembers = members.filter(
    (m) => m.user_id !== currentUserId && m.role === 'member'
  );

  const handleConfirm = async () => {
    if (!selectedUserId) {
      setError('Please select a member');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await onConfirm(selectedUserId as number);
      handleClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to transfer ownership');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setSelectedUserId('');
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Transfer Ownership</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" paragraph>
          Select a member to transfer ownership to. The new owner will have
          full control of the household.
        </Typography>

        {eligibleMembers.length === 0 ? (
          <Typography variant="body2" color="error">
            No eligible members found. All members are already owners.
          </Typography>
        ) : (
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>New Owner</InputLabel>
            <Select
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value as number)}
              label="New Owner"
              disabled={loading}
            >
              {eligibleMembers.map((member) => (
                <MenuItem key={member.user_id} value={member.user_id}>
                  {member.full_name || member.email}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}

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
          disabled={loading || eligibleMembers.length === 0}
        >
          Transfer
        </Button>
      </DialogActions>
    </Dialog>
  );
};

