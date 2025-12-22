"""User-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.security import validate_password_strength, validate_timezone


class UserBase(BaseModel):
  """Base user schema with common fields."""

  email: EmailStr
  full_name: Optional[str] = None
  phone_number: Optional[str] = None


class UserCreate(UserBase):
  """Schema for user registration."""

  password: str
  timezone: Optional[str] = Field(
      None,
      max_length=50,
      description="IANA timezone (e.g., 'America/New_York'). "
      "If not provided, defaults to UTC.")

  @field_validator("password")
  @classmethod
  def validate_password(cls, v: str) -> str:
    """
    Validate password meets requirements.

    Args:
      v: The password value to validate.

    Returns:
      The validated password.

    Raises:
      ValueError: If password is invalid.
    """
    if not v:
      raise ValueError("Password cannot be empty")
    validate_password_strength(v)
    return v

  @field_validator("timezone")
  @classmethod
  def validate_timezone(cls, v: Optional[str]) -> Optional[str]:
    """
    Validate timezone is a valid IANA timezone.

    Args:
      v: The timezone value to validate.

    Returns:
      The validated timezone, or None if not provided.

    Raises:
      ValueError: If timezone is invalid.
    """
    if v is None:
      return None
    validate_timezone(v)
    return v


class UserLogin(BaseModel):
  """Schema for user login."""

  email: EmailStr
  password: str


class User(UserBase):
  """Schema for user response."""

  id: int
  is_active: bool
  is_verified: bool
  created_at: datetime
  updated_at: datetime

  class Config:
    from_attributes = True


class UserInDB(User):
  """Schema for user in database (includes hashed password)."""

  hashed_password: str


class Token(BaseModel):
  """Schema for JWT token response."""

  access_token: str
  token_type: str = "bearer"
