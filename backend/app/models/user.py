"""User model."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
  """User model for authentication and user data.

  Columns:
    id: The user's unique identifier
    email: The user's email address
    hashed_password: The user's hashed password
    full_name: The user's full name
    phone_number: The user's phone number (optional, for SMS/WhatsApp)
    is_active: Whether the user is active
    is_verified: Whether the user has been verified
    created_at: The date and time the user was created
    updated_at: The date and time the user was last updated
  """

  __tablename__ = "users"

  id = Column(Integer, primary_key=True, index=True)
  email = Column(String, unique=True, index=True, nullable=False)
  hashed_password = Column(String, nullable=False)
  full_name = Column(String, nullable=True)
  phone_number = Column(String, nullable=True, index=True)
  is_active = Column(Boolean, default=True)
  is_verified = Column(Boolean, default=False)
  created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
  updated_at = Column(
      DateTime,
      default=datetime.utcnow,
      onupdate=datetime.utcnow,
      nullable=False)
