"""FastAPI dependencies for authentication and database access."""

from typing import Optional, Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.household import Household
from app.models.household_member import HouseholdMember
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
  """
  Get the current authenticated user from JWT token.

  Args:
    db: Database session.
    token: JWT access token from request.

  Returns:
    Current authenticated user.

  Raises:
    HTTPException: If token is invalid or user not found.
  """
  credentials_exception = HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Could not validate credentials",
      headers={"WWW-Authenticate": "Bearer"},
  )
  payload = decode_access_token(token)
  if payload is None:
    raise credentials_exception
  user_id: Optional[int] = payload.get("sub")
  if user_id is None:
    raise credentials_exception
  # Convert to int if it's a string (JWT tokens may store as string)
  if isinstance(user_id, str):
    try:
      user_id = int(user_id)
    except (ValueError, TypeError):
      raise credentials_exception
  user = db.query(User).filter(User.id == user_id).first()
  if user is None:
    raise credentials_exception

  return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
  """
  Get the current active user.

  Args:
    current_user: Current authenticated user.

  Returns:
    Current active user.

  Raises:
    HTTPException: If user is not active.
  """
  if not current_user.is_active:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Inactive user",
    )
  return current_user


def get_household_member_or_404(
    household_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Tuple[Household,
           HouseholdMember]:
  """
  Get household and membership, or raise 404 if user is not a member.

  This performs a single query with a join to check membership efficiently.

  Args:
    household_id: The household ID to check.
    current_user: Current authenticated user.
    db: Database session.

  Returns:
    Tuple of (household, membership).

  Raises:
    HTTPException: 404 if household doesn't exist or user is not a member.
  """
  membership = (
      db.query(HouseholdMember).join(Household).filter(
          HouseholdMember.household_id == household_id,
          HouseholdMember.user_id == current_user.id,
      ).first())

  if membership is None:
    # Return 404 to prevent household ID enumeration
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Household not found",
    )

  return membership.household, membership


def get_household_owner_or_403(
    household_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Tuple[Household,
           HouseholdMember]:
  """
  Get household and membership, or raise 403 if user is not an owner.

  Args:
    household_id: The household ID to check.
    current_user: Current authenticated user.
    db: Database session.

  Returns:
    Tuple of (household, membership).

  Raises:
    HTTPException: 404 if household doesn't exist or user is not a member.
    HTTPException: 403 if user is a member but not an owner.
  """
  household, membership = get_household_member_or_404(household_id, current_user, db)

  if membership.role != "owner":
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only owners can perform this action",
    )

  return household, membership
