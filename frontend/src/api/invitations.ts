/**
 * Invitation API Functions
 *
 * These functions handle all invitation-related API operations.
 * They use the apiClient to make requests to the backend.
 */

import apiClient from './client';

// Types for invitation API requests and responses
export interface InvitationCreate {
  email: string;
  role: 'member' | 'owner';
  expires_in_hours?: number;
}

export interface Invitation {
  id: number;
  email: string;
  household_id: number;
  inviter_user_id?: number;
  accepted_by_user_id?: number;
  role: string;
  status: string;
  expires_at: string;
  last_sent_at?: string;
  resend_count: number;
  created_at: string;
  updated_at: string;
  accepted_at?: string;
  cancelled_at?: string;
}

export interface InvitationAcceptRequest {
  token: string;
}

export interface InvitationAcceptResponse {
  household_id: number;
  role: string;
}

/**
 * Send an invitation to join a household (owners only)
 */
export const sendInvitation = async (
  householdId: number,
  data: InvitationCreate
): Promise<Invitation> => {
  const response = await apiClient.post<Invitation>(
    `/households/${householdId}/invitations`,
    data
  );
  return response.data;
};

/**
 * List pending invitations for a household (owners only)
 */
export const listInvitations = async (
  householdId: number
): Promise<Invitation[]> => {
  const response = await apiClient.get<Invitation[]>(
    `/households/${householdId}/invitations`
  );
  return response.data;
};

/**
 * Resend an invitation (owners only)
 */
export const resendInvitation = async (
  householdId: number,
  invitationId: number
): Promise<Invitation> => {
  const response = await apiClient.post<Invitation>(
    `/households/${householdId}/invitations/${invitationId}/resend`
  );
  return response.data;
};

/**
 * Cancel an invitation (owners only)
 */
export const cancelInvitation = async (
  householdId: number,
  invitationId: number
): Promise<void> => {
  await apiClient.post(
    `/households/${householdId}/invitations/${invitationId}/cancel`
  );
};

/**
 * Accept an invitation by token
 */
export const acceptInvitation = async (
  token: string
): Promise<InvitationAcceptResponse> => {
  const response = await apiClient.post<InvitationAcceptResponse>(
    '/invitations/accept',
    { token }
  );
  return response.data;
};

