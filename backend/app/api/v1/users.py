"""User preferences endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.user_preferences import (
    UserPreferencesRead,
    UserPreferencesUpdate,
)
from app.services.user_preferences_service import UserPreferencesService


router = APIRouter()


@router.get(
    "/me/preferences",
    response_model=UserPreferencesRead,
    status_code=status.HTTP_200_OK)
def get_user_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Get current user's preferences.

  Returns user preferences including:
  - preferred_currency: User's preferred currency for displaying amounts
  - timezone: User's preferred timezone (IANA format, e.g., "America/New_York")
  - language: User's preferred language code

  If preferences don't exist, creates default preferences (CAD, UTC, en).

  Args:
    current_user: Current authenticated user from dependency.
    db: Database session.

  Returns:
    User preferences object with currency, timezone, and language settings.
  """
  return UserPreferencesService.get_or_create_preferences(
      db=db,
      user_id=current_user.id,
  )


@router.patch(
    "/me/preferences",
    response_model=UserPreferencesRead,
    status_code=status.HTTP_200_OK)
def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Update current user's preferences.

  Supports partial updates of:
  - preferred_currency: Currency code (CAD, USD, EUR, BBD, BRL)
  - timezone: IANA timezone string (e.g., "America/New_York", "Europe/London")
  - language: Language code (e.g., "en", "fr")

  Args:
    preferences_update: Preferences update data (partial update).
    current_user: Current authenticated user from dependency.
    db: Database session.

  Returns:
    Updated user preferences object.

  Raises:
    ValidationError: If timezone is not a valid IANA timezone.
  """
  return UserPreferencesService.update_preferences(
      db=db,
      user_id=current_user.id,
      preferences_update=preferences_update,
  )
