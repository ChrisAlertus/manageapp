"""Invitation-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


ALLOWED_INVITE_ROLES = {"member", "owner"}


class InvitationCreate(BaseModel):
  """Schema for creating/sending an invitation."""

  email: EmailStr
  role: str = Field(default="member", description="member or owner")
  expires_in_hours: Optional[int] = Field(
      default=None,
      ge=1,
      le=24 * 30,
      description="Optional expiration override (1..720 hours)",
  )

  @field_validator("role")
  @classmethod
  def validate_role(cls, v: str) -> str:
    role = (v or "").strip().lower()
    if role not in ALLOWED_INVITE_ROLES:
      raise ValueError("Invalid role. Must be 'member' or 'owner'.")
    return role


class InvitationRead(BaseModel):
  """Schema for invitation response."""

  id: int
  email: EmailStr
  household_id: int
  inviter_user_id: Optional[int] = None
  accepted_by_user_id: Optional[int] = None

  role: str
  status: str
  expires_at: datetime
  last_sent_at: Optional[datetime] = None
  resend_count: int

  created_at: datetime
  updated_at: datetime
  accepted_at: Optional[datetime] = None
  cancelled_at: Optional[datetime] = None

  class Config:
    from_attributes = True


class InvitationAcceptRequest(BaseModel):
  """Schema for accepting an invitation by token."""

  token: str = Field(..., min_length=10, max_length=2048)


class InvitationAcceptResponse(BaseModel):
  """Schema returned after a successful accept."""

  household_id: int
  role: str


