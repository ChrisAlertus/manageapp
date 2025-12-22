"""User preferences-related Pydantic schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CurrencyCode(str, Enum):
  """Supported currency codes."""

  CAD = "CAD"  # Canadian Dollar (default)
  USD = "USD"  # US Dollar
  EUR = "EUR"  # Euro
  BBD = "BBD"  # Barbadian Dollar
  BRL = "BRL"  # Brazilian Real


class UserPreferencesBase(BaseModel):
  """Base user preferences schema with common fields."""

  preferred_currency: Optional[CurrencyCode] = CurrencyCode.CAD
  timezone: Optional[str] = Field(default="UTC", max_length=50)
  language: Optional[str] = Field(default="en", max_length=10)

  @field_validator("preferred_currency", mode="before")
  @classmethod
  def validate_currency(cls, v):
    """Validate currency code."""
    if v is None:
      return CurrencyCode.CAD
    if isinstance(v, str):
      try:
        return CurrencyCode(v.upper())
      except ValueError:
        raise ValueError(
            f"Invalid currency code: {v}. Must be one of: "
            f"{', '.join([c.value for c in CurrencyCode])}")
    return v


class UserPreferencesUpdate(BaseModel):
  """Schema for updating user preferences (all fields optional)."""

  preferred_currency: Optional[CurrencyCode] = None
  timezone: Optional[str] = Field(None, max_length=50)
  language: Optional[str] = Field(None, max_length=10)

  @field_validator("timezone", mode="before")
  @classmethod
  def validate_timezone(cls, v):
    """Validate timezone string using security.validate_timezone."""
    if v is None:
      return None

    from app.core.security import validate_timezone
    validate_timezone(v)  # Raises ValueError if invalid
    return v  # Return the validated value

  @field_validator("preferred_currency", mode="before")
  @classmethod
  def validate_currency(cls, v):
    """Validate currency code."""
    if v is None:
      return None
    if isinstance(v, str):
      try:
        return CurrencyCode(v.upper())
      except ValueError:
        raise ValueError(
            f"Invalid currency code: {v}. Must be one of: "
            f"{', '.join([c.value for c in CurrencyCode])}")
    return v


class UserPreferencesRead(UserPreferencesBase):
  """Schema for user preferences response."""

  id: int
  user_id: int
  created_at: datetime
  updated_at: datetime

  class Config:
    from_attributes = True
