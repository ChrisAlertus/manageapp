"""User preferences business logic service."""

from sqlalchemy.orm import Session

from app.models.user_preferences import UserPreferences
from app.schemas.user_preferences import UserPreferencesUpdate


class UserPreferencesService:
  """Service for user preferences business logic."""

  @staticmethod
  def get_or_create_preferences(
      db: Session,
      user_id: int,
  ) -> UserPreferences:
    """Get user preferences, creating default preferences if they don't exist.

    Args:
      db: Database session.
      user_id: ID of the user.

    Returns:
      User preferences object.
    """
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id).first()

    if not preferences:
      # Create default preferences if they don't exist
      preferences = UserPreferences(
          user_id=user_id,
          preferred_currency="CAD",
          timezone="UTC",
          language="en",
      )
      db.add(preferences)
      db.commit()
      db.refresh(preferences)

    return preferences

  @staticmethod
  def update_preferences(
      db: Session,
      user_id: int,
      preferences_update: UserPreferencesUpdate,
  ) -> UserPreferences:
    """Update user preferences.

    Supports partial updates of:
      - preferred_currency: Currency code (CAD, USD, EUR, BBD, BRL)
      - timezone: IANA timezone string (e.g., "America/New_York", "Europe/London")
      - language: Language code (e.g., "en", "fr")

    Args:
      db: Database session.
      user_id: ID of the user.
      preferences_update: Preferences update data (partial update).

    Returns:
      Updated user preferences object.
    """
    # Get or create preferences
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id).first()

    if not preferences:
      # Create default preferences if they don't exist
      preferences = UserPreferences(
          user_id=user_id,
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
