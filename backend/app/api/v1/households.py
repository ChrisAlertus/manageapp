"""Household management endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_active_user,
    get_db,
    get_household_member_or_404,
    get_household_owner_or_403,
)
from app.models.user import User
from app.schemas.household import HouseholdCreate, HouseholdRead, TransferOwnership
from app.services.household_service import HouseholdService


router = APIRouter()


@router.post(
    "/",
    response_model=HouseholdRead,
    status_code=status.HTTP_201_CREATED,
)
def create_household(
    household_in: HouseholdCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Create a new household and add the creator as owner.

  Args:
    household_in: Household creation data.
    current_user: Current authenticated user.
    db: Database session.

  Returns:
    Created household object.
  """
  try:
    return HouseholdService.create_household(
        db=db,
        household_in=household_in,
        user_id=current_user.id,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e),
    )


@router.get(
    "/",
    response_model=List[HouseholdRead],
)
def list_households(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  List all households where the current user is a member.

  Args:
    current_user: Current authenticated user.
    db: Database session.

  Returns:
    List of households the user belongs to.
  """
  return HouseholdService.list_user_households(
      db=db,
      user_id=current_user.id,
  )


@router.get(
    "/{household_id}",
    response_model=HouseholdRead,
)
def get_household(
    household_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Get household details.

  Args:
    household_id: The household ID.
    current_user: Current authenticated user.
    db: Database session.

  Returns:
    Household details.
  """
  household, _ = get_household_member_or_404(household_id, current_user, db)
  return household


@router.post(
    "/{household_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
)
def leave_household(
    household_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Leave a household by removing membership.

  Args:
    household_id: The household ID.
    current_user: Current authenticated user.
    db: Database session.

  Raises:
    HTTPException: 400 if user is the last owner.
  """
  # Verify user is a member
  get_household_member_or_404(household_id, current_user, db)

  try:
    HouseholdService.leave_household(
        db=db,
        household_id=household_id,
        user_id=current_user.id,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e),
    )

  return None


@router.delete(
    "/{household_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_household_member(
    household_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Remove a member from a household (kick out).

  Only owners can remove members. Removing the last remaining owner is blocked.
  """
  # Verify current user is an owner
  get_household_owner_or_403(household_id, current_user, db)

  try:
    HouseholdService.remove_household_member(
        db=db,
        household_id=household_id,
        user_id_to_remove=user_id,
    )
  except ValueError as e:
    error_detail = str(e)
    if "not found" in error_detail.lower():
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=error_detail,
      )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=error_detail,
    )

  return None


@router.post(
    "/{household_id}/transfer-ownership",
    status_code=status.HTTP_204_NO_CONTENT,
)
def transfer_ownership(
    household_id: int,
    transfer_data: TransferOwnership,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Transfer ownership of a household to another member.

  Only owners can transfer ownership. The new owner must already be a member
  of the household.

  Args:
    household_id: The household ID.
    transfer_data: Transfer ownership data containing new_owner_id.
    current_user: Current authenticated user.
    db: Database session.

  Raises:
    HTTPException: 404 if household doesn't exist or user is not a member.
    HTTPException: 403 if user is not an owner.
    HTTPException: 400 if new owner is not a member or is already an owner.
  """
  # Verify current user is an owner
  get_household_owner_or_403(household_id, current_user, db)

  try:
    HouseholdService.transfer_ownership(
        db=db,
        household_id=household_id,
        current_user_id=current_user.id,
        transfer_data=transfer_data,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e),
    )

  return None


@router.delete(
    "/{household_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_household(
    household_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Delete a household. Only owners can delete a household.

  This will cascade delete all memberships and related data.

  Args:
    household_id: The household ID.
    current_user: Current authenticated user.
    db: Database session.

  Raises:
    HTTPException: 404 if household doesn't exist or user is not a member.
    HTTPException: 403 if user is not an owner.
  """
  # Verify current user is an owner
  get_household_owner_or_403(household_id, current_user, db)

  try:
    HouseholdService.delete_household(
        db=db,
        household_id=household_id,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(e),
    )

  return None
