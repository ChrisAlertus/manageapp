"""Household model."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Household(Base):
  """Household model for grouping users and managing shared resources.

  Columns:
    id: The household's unique identifier
    name: The household's name
    description: Optional description of the household
    created_by: The user ID of the original creator (immutable)
    created_at: The date and time the household was created
    updated_at: The date and time the household was last updated
  """

  __tablename__ = "households"

  id = Column(Integer, primary_key=True, index=True)
  name = Column(String, nullable=False, index=True)
  description = Column(Text, nullable=True)
  created_by = Column(
      Integer,
      ForeignKey("users.id",
                 ondelete="SET NULL"),
      nullable=True,
      index=True)
  created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
  updated_at = Column(
      DateTime,
      default=datetime.utcnow,
      onupdate=datetime.utcnow,
      nullable=False)

  # Relationships
  members = relationship(
      "HouseholdMember",
      back_populates="household",
      cascade="all, delete-orphan")
  creator = relationship("User", foreign_keys=[created_by])
