"""Household invitation model."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


def utcnow():
  """Return current UTC datetime with timezone awareness."""
  return datetime.now(timezone.utc)


class Invitation(Base):
  """Invitation model for email-based household invites.

  Notes:
    - We store a hash of the token (not the raw token) for security.
    - Status is stored as a string for SQLite/Postgres compatibility.

  Columns:
    id: Primary key
    token_hash: SHA-256 hash (hex) of the invitation token
    email: Invitee email address (normalized to lowercase)
    household_id: Target household ID
    inviter_user_id: User ID of inviter
    accepted_by_user_id: User ID of accepter (if accepted)
    role: Role to grant on acceptance ("member" or "owner")
    status: Invitation state ("pending", "accepted", "cancelled", "expired")
    expires_at: Expiration timestamp
    last_sent_at: When we last successfully sent an email for this invitation
    resend_count: Number of resends
    created_at/updated_at: Timestamps
    accepted_at/cancelled_at: Terminal timestamps
  """

  __tablename__ = "invitations"

  id = Column(Integer, primary_key=True, index=True)

  token_hash = Column(String(64), nullable=False, unique=True, index=True)
  email = Column(String, nullable=False, index=True)

  household_id = Column(
      Integer,
      ForeignKey("households.id",
                 ondelete="CASCADE"),
      nullable=False,
      index=True,
  )
  inviter_user_id = Column(
      Integer,
      ForeignKey("users.id",
                 ondelete="SET NULL"),
      nullable=True,
      index=True,
  )
  accepted_by_user_id = Column(
      Integer,
      ForeignKey("users.id",
                 ondelete="SET NULL"),
      nullable=True,
      index=True,
  )

  role = Column(String, nullable=False, default="member")
  status = Column(String, nullable=False, default="pending", index=True)

  expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
  last_sent_at = Column(DateTime(timezone=True), nullable=True)
  resend_count = Column(Integer, nullable=False, default=0)

  created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
  updated_at = Column(
      DateTime(timezone=True),
      default=utcnow,
      onupdate=utcnow,
      nullable=False,
  )
  accepted_at = Column(DateTime(timezone=True), nullable=True)
  cancelled_at = Column(DateTime(timezone=True), nullable=True)

  # Relationships
  household = relationship("Household")
  inviter = relationship("User", foreign_keys=[inviter_user_id])
  accepted_by = relationship("User", foreign_keys=[accepted_by_user_id])

  __table_args__ = (
      UniqueConstraint("token_hash",
                       name="uq_invitations_token_hash"),
      Index("ix_invitations_household_status",
            "household_id",
            "status"),
      Index("ix_invitations_household_email",
            "household_id",
            "email"),
  )
