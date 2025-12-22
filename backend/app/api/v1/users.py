"""User preferences endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.schemas.user_preferences import (
    UserPreferencesRead,
    UserPreferencesUpdate,
)


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
  # Get or create preferences
  preferences = db.query(UserPreferences).filter(
      UserPreferences.user_id == current_user.id).first()

  if not preferences:
    # Create default preferences if they don't exist
    preferences = UserPreferences(
        user_id=current_user.id,
        preferred_currency="CAD",
        timezone="UTC",
        language="en",
    )
    db.add(preferences)
    db.commit()
    db.refresh(preferences)

  return preferences


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
    HTTPException: If preferences don't exist (should not happen).
    ValidationError: If timezone is not a valid IANA timezone.
  """
  # Get or create preferences
  preferences = db.query(UserPreferences).filter(
      UserPreferences.user_id == current_user.id).first()

  if not preferences:
    # Create default preferences if they don't exist
    preferences = UserPreferences(
        user_id=current_user.id,
        preferred_currency="CAD",
        timezone="UTC",
        language="en",
    )
    db.add(preferences)

  # Update only provided fields
  update_data = preferences_update.model_dump(exclude_unset=True)
  for field, value in update_data.items():
    setattr(preferences, field, value)

  db.commit()
  db.refresh(preferences)

  return preferences
