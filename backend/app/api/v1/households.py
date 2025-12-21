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
from app.models.household import Household
from app.models.household_member import HouseholdMember
from app.models.user import User
from app.schemas.household import HouseholdCreate, HouseholdRead, TransferOwnership


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

  # Create household
  db_household = Household(
      name=household_in.name,
      description=household_in.description,
      created_by=current_user.id,
  )
  db.add(db_household)
  db.flush()  # Flush to get the household ID

  # Add creator as owner
  db_member = HouseholdMember(
      household_id=db_household.id,
      user_id=current_user.id,
      role="owner",
  )
  db.add(db_member)
  db.commit()
  db.refresh(db_household)

  return db_household


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
  households = (
      db.query(Household).join(HouseholdMember).filter(
          HouseholdMember.user_id == current_user.id).all())
  return households


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
  household, membership = get_household_member_or_404(household_id, current_user, db)

  # Check if user is an owner
  if membership.role == "owner":
    # Count total owners for this household
    owner_count = (
        db.query(HouseholdMember).filter(
            HouseholdMember.household_id == household_id,
            HouseholdMember.role == "owner",
        ).count())

    if owner_count == 1:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="Cannot leave household: you are the last owner. "
          "Please transfer ownership or invite another owner first.",
      )

  # Remove membership
  db.delete(membership)
  db.commit()

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
  _household, _ = get_household_owner_or_403(household_id, current_user, db)

  membership = (
      db.query(HouseholdMember).filter(
          HouseholdMember.household_id == household_id,
          HouseholdMember.user_id == user_id,
      ).first())
  if membership is None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Member not found",
    )

  # Block removing the last owner
  if membership.role == "owner":
    owner_count = (
        db.query(HouseholdMember).filter(
            HouseholdMember.household_id == household_id,
            HouseholdMember.role == "owner",
        ).count())
    if owner_count == 1:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="Cannot remove member: they are the last owner. "
          "Please transfer ownership first.",
      )

  db.delete(membership)
  db.commit()
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
  household, membership = get_household_owner_or_403(household_id, current_user, db)

  # Check if new owner is the current user
  if transfer_data.new_owner_id == current_user.id:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Cannot transfer ownership to yourself",
    )

  # Check if new owner is a member of the household
  new_owner_membership = (
      db.query(HouseholdMember).filter(
          HouseholdMember.household_id == household_id,
          HouseholdMember.user_id == transfer_data.new_owner_id,
      ).first())

  if new_owner_membership is None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="New owner must be a member of the household",
    )

  # Check if new owner is already an owner
  if new_owner_membership.role == "owner":
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="User is already an owner of this household",
    )

  # Transfer ownership: promote new owner, optionally demote current owner
  new_owner_membership.role = "owner"
  # Note: We keep the current user as owner too (shared ownership)
  # If you want to demote the current user, uncomment the next line:
  # membership.role = "member"

  db.commit()

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
  household, _ = get_household_owner_or_403(household_id, current_user, db)

  # Delete household (cascade will handle memberships)
  db.delete(household)
  db.commit()

  return None
