"""Household business logic service."""

from typing import List

from sqlalchemy.orm import Session, joinedload

from app.models.household import Household
from app.models.household_member import HouseholdMember
from app.schemas.household import HouseholdCreate, TransferOwnership


class HouseholdService:
  """Service for household business logic."""

  @staticmethod
  def create_household(
      db: Session,
      household_in: HouseholdCreate,
      user_id: int,
  ) -> Household:
    """Create a new household and add the creator as owner.

    Args:
      db: Database session.
      household_in: Household creation data.
      user_id: ID of the user creating the household.

    Returns:
      Created household object.
    """
    # Create household
    db_household = Household(
        name=household_in.name,
        description=household_in.description,
        created_by=user_id,
    )
    db.add(db_household)
    db.flush()  # Flush to get the household ID

    # Add creator as owner
    db_member = HouseholdMember(
        household_id=db_household.id,
        user_id=user_id,
        role="owner",
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_household)

    return db_household

  @staticmethod
  def list_user_households(
      db: Session,
      user_id: int,
  ) -> List[Household]:
    """List all households where the user is a member.

    Args:
      db: Database session.
      user_id: ID of the user.

    Returns:
      List of households the user belongs to.
    """
    households = (
        db.query(Household).join(HouseholdMember).filter(
            HouseholdMember.user_id == user_id).all())
    return households

  @staticmethod
  def leave_household(
      db: Session,
      household_id: int,
      user_id: int,
  ) -> None:
    """Leave a household by removing membership.

    Args:
      db: Database session.
      household_id: The household ID.
      user_id: ID of the user leaving.

    Raises:
      ValueError: If user is the last owner.
    """
    membership = (
        db.query(HouseholdMember).filter(
            HouseholdMember.household_id == household_id,
            HouseholdMember.user_id == user_id,
        ).first())

    if membership is None:
      raise ValueError("User is not a member of this household")

    # Check if user is an owner
    if membership.role == "owner":
      # Count total owners for this household
      owner_count = (
          db.query(HouseholdMember).filter(
              HouseholdMember.household_id == household_id,
              HouseholdMember.role == "owner",
          ).count())

      if owner_count == 1:
        raise ValueError(
            "Cannot leave household: you are the last owner. "
            "Please transfer ownership or invite another owner first.")

    # Remove membership
    db.delete(membership)
    db.commit()

  @staticmethod
  def remove_household_member(
      db: Session,
      household_id: int,
      user_id_to_remove: int,
  ) -> None:
    """Remove a member from a household (kick out).

    Args:
      db: Database session.
      household_id: The household ID.
      user_id_to_remove: ID of the user to remove.

    Raises:
      ValueError: If member not found or is the last owner.
    """
    membership = (
        db.query(HouseholdMember).filter(
            HouseholdMember.household_id == household_id,
            HouseholdMember.user_id == user_id_to_remove,
        ).first())

    if membership is None:
      raise ValueError("Member not found")

    # Block removing the last owner
    if membership.role == "owner":
      owner_count = (
          db.query(HouseholdMember).filter(
              HouseholdMember.household_id == household_id,
              HouseholdMember.role == "owner",
          ).count())
      if owner_count == 1:
        raise ValueError(
            "Cannot remove member: they are the last owner. "
            "Please transfer ownership first.")

    db.delete(membership)
    db.commit()

  @staticmethod
  def transfer_ownership(
      db: Session,
      household_id: int,
      current_user_id: int,
      transfer_data: TransferOwnership,
  ) -> None:
    """Transfer ownership of a household to another member.

    Args:
      db: Database session.
      household_id: The household ID.
      current_user_id: ID of the current user (must be owner).
      transfer_data: Transfer ownership data containing new_owner_id.

    Raises:
      ValueError: If new owner is not a member, already an owner, or is the current user.
    """
    # Check if new owner is the current user
    if transfer_data.new_owner_id == current_user_id:
      raise ValueError("Cannot transfer ownership to yourself")

    # Check if new owner is a member of the household
    new_owner_membership = (
        db.query(HouseholdMember).filter(
            HouseholdMember.household_id == household_id,
            HouseholdMember.user_id == transfer_data.new_owner_id,
        ).first())

    if new_owner_membership is None:
      raise ValueError("New owner must be a member of the household")

    # Check if new owner is already an owner
    if new_owner_membership.role == "owner":
      raise ValueError("User is already an owner of this household")

    # Transfer ownership: promote new owner, optionally demote current owner
    new_owner_membership.role = "owner"
    # Note: We keep the current user as owner too (shared ownership)
    # If you want to demote the current user, uncomment the next line:
    # current_membership.role = "member"

    db.commit()

  @staticmethod
  def delete_household(
      db: Session,
      household_id: int,
  ) -> None:
    """Delete a household.

    This will cascade delete all memberships and related data.

    Args:
      db: Database session.
      household_id: The household ID.
    """
    household = db.query(Household).filter(Household.id == household_id).first()
    if household is None:
      raise ValueError("Household not found")

    # Delete household (cascade will handle memberships)
    db.delete(household)
    db.commit()

  @staticmethod
  def get_household_members_with_users(
      db: Session,
      household_id: int,
  ) -> List[HouseholdMember]:
    """Get all household members with their user information loaded.

    Args:
      db: Database session.
      household_id: The household ID.

    Returns:
      List of HouseholdMember objects with user relationships loaded.

    Raises:
      ValueError: If household doesn't exist.
    """
    # Verify household exists
    household = db.query(Household).filter(Household.id == household_id).first()
    if household is None:
      raise ValueError("Household not found")

    # Query members with user relationship eagerly loaded
    members = (
        db.query(HouseholdMember).filter(
            HouseholdMember.household_id == household_id).options(
                joinedload(HouseholdMember.user)).all())

    return members
