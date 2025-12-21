"""Household member association model."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class HouseholdMember(Base):
  """Household member association model for user-household relationships.

  Columns:
    id: The membership's unique identifier
    household_id: Foreign key to households table
    user_id: Foreign key to users table
    role: The member's role (owner or member)
    joined_at: The date and time the user joined the household
  """

  __tablename__ = "household_members"

  id = Column(Integer, primary_key=True, index=True)
  household_id = Column(Integer, ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True)
  user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
  role = Column(String, nullable=False, default="member")
  joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

  # Constraints
  __table_args__ = (
      UniqueConstraint("household_id", "user_id", name="uq_household_member"),
      Index("ix_household_members_household_role", "household_id", "role"),
  )

  # Relationships
  household = relationship("Household", back_populates="members")
  user = relationship("User")

