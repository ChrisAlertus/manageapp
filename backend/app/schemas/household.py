"""Household-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HouseholdBase(BaseModel):
  """Base household schema with common fields."""

  name: str = Field(..., min_length=1, max_length=255)
  description: Optional[str] = None


class HouseholdCreate(HouseholdBase):
  """Schema for household creation."""

  pass


class HouseholdRead(HouseholdBase):
  """Schema for household response."""

  id: int
  created_by: Optional[int] = None
  created_at: datetime
  updated_at: datetime

  class Config:
    from_attributes = True


class HouseholdMemberRead(BaseModel):
  """Schema for household member response."""

  user_id: int
  role: str
  joined_at: datetime

  class Config:
    from_attributes = True


class TransferOwnership(BaseModel):
  """Schema for transferring household ownership."""

  new_owner_id: int = Field(..., description="User ID of the new owner")
