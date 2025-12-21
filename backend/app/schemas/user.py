"""User-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
  """Base user schema with common fields."""

  email: EmailStr
  full_name: Optional[str] = None


class UserCreate(UserBase):
  """Schema for user registration."""

  password: str


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

