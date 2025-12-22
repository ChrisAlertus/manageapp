"""User preferences model."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.utils import utcnow


class UserPreferences(Base):
  """User preferences model for storing user settings.

  Columns:
    id: The preferences' unique identifier
    user_id: The user this preferences record belongs to (one-to-one)
    preferred_currency: The user's preferred currency (CAD, USD, EUR, BBD, BRL)
    timezone: The user's timezone (default: UTC)
    language: The user's language preference (default: en)
    created_at: The date and time the preferences were created
    updated_at: The date and time the preferences were last updated
  """

  __tablename__ = "user_preferences"

  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(
      Integer,
      ForeignKey("users.id",
                 ondelete="CASCADE"),
      unique=True,
      nullable=False,
      index=True)
  preferred_currency = Column(String(3), default="CAD", nullable=False)
  timezone = Column(String(50), default="UTC", nullable=False)
  language = Column(String(10), default="en", nullable=False)
  created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
  updated_at = Column(
      DateTime(timezone=True),
      default=utcnow,
      onupdate=utcnow,
      nullable=False)

  # Relationships
  user = relationship("User", back_populates="preferences")
