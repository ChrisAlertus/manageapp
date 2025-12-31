/**
 * Member List Component
 *
 * Displays a list of household members with their details and role badges.
 */

import {
  Box,
  Chip,
  List,
  ListItem,
  ListItemText,
  Typography,
} from '@mui/material';
import { type HouseholdMember } from '../api/households';

interface MemberListProps {
  members: HouseholdMember[];
  currentUserId?: number;
}

/**
 * MemberList - Displays household members with role badges
 */
export const MemberList: React.FC<MemberListProps> = ({
  members,
  currentUserId,
}) => {
  if (members.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No members found.
      </Typography>
    );
  }

  return (
    <List>
      {members.map((member) => (
        <ListItem key={member.user_id}>
          <ListItemText
            primary={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body1">
                  {member.full_name || member.email}
                  {member.user_id === currentUserId && (
                    <Typography
                      component="span"
                      variant="caption"
                      color="text.secondary"
                      sx={{ ml: 1 }}
                    >
                      (You)
                    </Typography>
                  )}
                </Typography>
                <Chip
                  label={member.role}
                  size="small"
                  color={member.role === 'owner' ? 'primary' : 'default'}
                />
              </Box>
            }
            secondary={
              <Box>
                <Typography variant="body2" color="text.secondary">
                  {member.email}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Joined {new Date(member.joined_at).toLocaleDateString()}
                </Typography>
              </Box>
            }
          />
        </ListItem>
      ))}
    </List>
  );
};

