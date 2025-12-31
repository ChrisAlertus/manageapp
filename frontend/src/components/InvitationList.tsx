/**
 * Invitation List Component
 *
 * Displays a list of pending invitations with actions.
 */

import {
  Box,
  Chip,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Tooltip,
  Typography,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import SendIcon from '@mui/icons-material/Send';
import { type Invitation } from '../api/invitations';

interface InvitationListProps {
  invitations: Invitation[];
  onResend: (invitationId: number) => Promise<void>;
  onCancel: (invitationId: number) => Promise<void>;
  loading?: boolean;
}

/**
 * InvitationList - Displays pending invitations with actions
 */
export const InvitationList: React.FC<InvitationListProps> = ({
  invitations,
  onResend,
  onCancel,
  loading = false,
}) => {
  if (invitations.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No pending invitations.
      </Typography>
    );
  }

  const isExpired = (expiresAt: string): boolean => {
    return new Date(expiresAt) < new Date();
  };

  return (
    <List>
      {invitations.map((invitation) => {
        const expired = isExpired(invitation.expires_at);
        return (
          <ListItem
            key={invitation.id}
            secondaryAction={
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Tooltip title="Resend invitation">
                  <IconButton
                    edge="end"
                    onClick={() => onResend(invitation.id)}
                    disabled={loading || expired}
                    size="small"
                  >
                    <SendIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Cancel invitation">
                  <IconButton
                    edge="end"
                    onClick={() => onCancel(invitation.id)}
                    disabled={loading}
                    color="error"
                    size="small"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            }
          >
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body1">{invitation.email}</Typography>
                  <Chip
                    label={invitation.role}
                    size="small"
                    color={invitation.role === 'owner' ? 'primary' : 'default'}
                  />
                  {expired && (
                    <Chip label="Expired" size="small" color="error" />
                  )}
                </Box>
              }
              secondary={
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Expires {new Date(invitation.expires_at).toLocaleString()}
                  </Typography>
                  {invitation.resend_count > 0 && (
                    <Typography variant="caption" color="text.secondary">
                      Resent {invitation.resend_count} time(s)
                    </Typography>
                  )}
                </Box>
              }
            />
          </ListItem>
        );
      })}
    </List>
  );
};

