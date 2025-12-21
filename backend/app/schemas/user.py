"""User-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from app.core.security import validate_password_strength


class UserBase(BaseModel):
  """Base user schema with common fields."""

  email: EmailStr
  full_name: Optional[str] = None


class UserCreate(UserBase):
  """Schema for user registration."""

  password: str

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
