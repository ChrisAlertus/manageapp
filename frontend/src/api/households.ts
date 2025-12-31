/**
 * Household API Functions
 *
 * These functions handle all household-related API operations.
 * They use the apiClient to make requests to the backend.
 */

import apiClient from './client';

// Types for household API requests and responses
export interface HouseholdCreate {
  name: string;
  description?: string;
}

export interface Household {
  id: number;
  name: string;
  description?: string;
  created_by?: number;
  created_at: string;
  updated_at: string;
}

export interface HouseholdMember {
  user_id: number;
  email: string;
  full_name?: string;
  role: string;
  joined_at: string;
}

export interface TransferOwnershipRequest {
  new_owner_id: number;
}

/**
 * List all households where the current user is a member
 */
export const listHouseholds = async (): Promise<Household[]> => {
  const response = await apiClient.get<Household[]>('/households');
  return response.data;
};

/**
 * Get household details by ID
 */
export const getHousehold = async (id: number): Promise<Household> => {
  const response = await apiClient.get<Household>(`/households/${id}`);
  return response.data;
};

/**
 * Create a new household
 */
export const createHousehold = async (
  data: HouseholdCreate
): Promise<Household> => {
  const response = await apiClient.post<Household>('/households', data);
  return response.data;
};

/**
 * Delete a household (owners only)
 */
export const deleteHousehold = async (id: number): Promise<void> => {
  await apiClient.delete(`/households/${id}`);
};

/**
 * Leave a household
 */
export const leaveHousehold = async (id: number): Promise<void> => {
  await apiClient.post(`/households/${id}/leave`);
};

/**
 * Get list of household members with user details
 */
export const getHouseholdMembers = async (
  id: number
): Promise<HouseholdMember[]> => {
  const response = await apiClient.get<HouseholdMember[]>(
    `/households/${id}/members`
  );
  return response.data;
};

/**
 * Remove a member from a household (owners only)
 */
export const removeMember = async (
  householdId: number,
  userId: number
): Promise<void> => {
  await apiClient.delete(`/households/${householdId}/members/${userId}`);
};

/**
 * Transfer ownership of a household to another member (owners only)
 */
export const transferOwnership = async (
  householdId: number,
  newOwnerId: number
): Promise<void> => {
  await apiClient.post(`/households/${householdId}/transfer-ownership`, {
    new_owner_id: newOwnerId,
  });
};

