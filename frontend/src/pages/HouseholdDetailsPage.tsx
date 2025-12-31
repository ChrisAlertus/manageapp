/**
 * Household Details Page
 *
 * Displays household information, members, and invitation management.
 */

import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  Typography,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import PersonRemoveIcon from '@mui/icons-material/PersonRemove';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  deleteHousehold,
  getHousehold,
  getHouseholdMembers,
  leaveHousehold,
  removeMember,
  transferOwnership,
  type Household,
  type HouseholdMember,
} from '../api/households';
import {
  cancelInvitation,
  listInvitations,
  resendInvitation,
  type Invitation,
} from '../api/invitations';
import { useAuthStore } from '../stores/authStore';
import { getErrorMessage } from '../utils/errorHandling';
import { DeleteHouseholdDialog } from '../components/DeleteHouseholdDialog';
import { InvitationList } from '../components/InvitationList';
import { MemberList } from '../components/MemberList';
import { RemoveMemberDialog } from '../components/RemoveMemberDialog';
import { SendInvitationDialog } from '../components/SendInvitationDialog';
import { TransferOwnershipDialog } from '../components/TransferOwnershipDialog';

/**
 * HouseholdDetailsPage - Comprehensive household management page
 */
export const HouseholdDetailsPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { user } = useAuthStore();
  const householdId = id ? parseInt(id, 10) : null;

  const [household, setHousehold] = useState<Household | null>(null);
  const [members, setMembers] = useState<HouseholdMember[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOwner, setIsOwner] = useState(false);

  // Dialog states
  const [transferDialogOpen, setTransferDialogOpen] = useState(false);
  const [removeMemberDialogOpen, setRemoveMemberDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [sendInvitationDialogOpen, setSendInvitationDialogOpen] =
    useState(false);
  const [selectedMember, setSelectedMember] = useState<HouseholdMember | null>(
    null
  );

  useEffect(() => {
    if (householdId) {
      loadHouseholdData();
    }
  }, [householdId]);

  const loadHouseholdData = async () => {
    if (!householdId) return;

    try {
      setLoading(true);
      setError(null);

      const [householdData, membersData, invitationsData] = await Promise.all([
        getHousehold(householdId),
        getHouseholdMembers(householdId),
        listInvitations(householdId).catch(() => []), // Invitations may fail if not owner
      ]);

      setHousehold(householdData);
      setMembers(membersData);
      setInvitations(invitationsData);

      // Check if current user is owner
      const currentUserMember = membersData.find(
        (m) => m.user_id === user?.id
      );
      setIsOwner(currentUserMember?.role === 'owner');
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load household data'));
    } finally {
      setLoading(false);
    }
  };

  const handleTransferOwnership = async (newOwnerId: number) => {
    if (!householdId) return;
    await transferOwnership(householdId, newOwnerId);
    await loadHouseholdData();
  };

  const handleRemoveMember = async () => {
    if (!householdId || !selectedMember) return;
    await removeMember(householdId, selectedMember.user_id);
    setSelectedMember(null);
    await loadHouseholdData();
  };

  const handleDeleteHousehold = async () => {
    if (!householdId) return;
    await deleteHousehold(householdId);
    navigate('/households');
  };

  const handleLeaveHousehold = async () => {
    if (!householdId) return;
    if (
      !window.confirm(
        'Are you sure you want to leave this household? You will lose access to all household data.'
      )
    ) {
      return;
    }

    try {
      await leaveHousehold(householdId);
      navigate('/households');
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to leave household'));
    }
  };

  const handleResendInvitation = async (invitationId: number) => {
    if (!householdId) return;
    try {
      await resendInvitation(householdId, invitationId);
      await loadHouseholdData();
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to resend invitation'));
    }
  };

  const handleCancelInvitation = async (invitationId: number) => {
    if (!householdId) return;
    try {
      await cancelInvitation(householdId, invitationId);
      await loadHouseholdData();
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to cancel invitation'));
    }
  };

  if (!householdId) {
    return (
      <Typography color="error">Invalid household ID</Typography>
    );
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error && !household) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Household Details
        </Typography>
        <Typography color="error" paragraph>
          {error}
        </Typography>
        <Button variant="contained" onClick={loadHouseholdData}>
          Retry
        </Button>
      </Box>
    );
  }

  if (!household) {
    return <Typography>Household not found</Typography>;
  }

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 3,
        }}
      >
        <Box>
          <Typography variant="h4" component="h1">
            {household.name}
          </Typography>
          {household.description && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {household.description}
            </Typography>
          )}
        </Box>
        <Button variant="outlined" onClick={() => navigate('/households')}>
          Back to Households
        </Button>
      </Box>

      {error && (
        <Typography color="error" paragraph>
          {error}
        </Typography>
      )}

      {/* Members Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              mb: 2,
            }}
          >
            <Typography variant="h6">Members</Typography>
            {isOwner && (
              <Button
                variant="outlined"
                startIcon={<SwapHorizIcon />}
                onClick={() => setTransferDialogOpen(true)}
                size="small"
              >
                Transfer Ownership
              </Button>
            )}
          </Box>
          <MemberList members={members} currentUserId={user?.id} />
          {isOwner && members.length > 1 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Owner Actions:
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {members
                  .filter((m) => m.user_id !== user?.id && m.role !== 'owner')
                  .map((member) => (
                    <Button
                      key={member.user_id}
                      variant="outlined"
                      color="error"
                      size="small"
                      startIcon={<PersonRemoveIcon />}
                      onClick={() => {
                        setSelectedMember(member);
                        setRemoveMemberDialogOpen(true);
                      }}
                    >
                      Remove {member.full_name || member.email}
                    </Button>
                  ))}
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Invitations Section (Owners only) */}
      {isOwner && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                mb: 2,
              }}
            >
              <Typography variant="h6">Pending Invitations</Typography>
              <Button
                variant="contained"
                onClick={() => setSendInvitationDialogOpen(true)}
                size="small"
              >
                Send Invitation
              </Button>
            </Box>
            <InvitationList
              invitations={invitations}
              onResend={handleResendInvitation}
              onCancel={handleCancelInvitation}
            />
          </CardContent>
        </Card>
      )}

      <Divider sx={{ my: 3 }} />

      {/* Actions Section */}
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'space-between' }}>
        <Button
          variant="outlined"
          color="error"
          onClick={handleLeaveHousehold}
        >
          Leave Household
        </Button>
        {isOwner && (
          <Button
            variant="contained"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={() => setDeleteDialogOpen(true)}
          >
            Delete Household
          </Button>
        )}
      </Box>

      {/* Dialogs */}
      <TransferOwnershipDialog
        open={transferDialogOpen}
        onClose={() => setTransferDialogOpen(false)}
        onConfirm={handleTransferOwnership}
        members={members}
        currentUserId={user?.id}
      />

      <RemoveMemberDialog
        open={removeMemberDialogOpen}
        onClose={() => {
          setRemoveMemberDialogOpen(false);
          setSelectedMember(null);
        }}
        onConfirm={handleRemoveMember}
        member={selectedMember}
      />

      <DeleteHouseholdDialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={handleDeleteHousehold}
        householdName={household.name}
      />

      <SendInvitationDialog
        open={sendInvitationDialogOpen}
        onClose={() => setSendInvitationDialogOpen(false)}
        onSuccess={loadHouseholdData}
        householdId={householdId}
      />
    </Box>
  );
};

