"""Todo model."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.utils import utcnow


class Todo(Base):
  """Todo model for shared household to-do items.

  Columns:
    id: The todo's unique identifier
    title: The todo's title (required)
    description: Optional description of the todo
    household_id: Foreign key to households table
    created_by: Foreign key to users table (who created the todo)
    priority: Priority level (low, medium, high, urgent, default: medium)
    due_date: Optional due date for the todo (deadline for completion)
    category: Optional category/tag for the todo
    visibility: Visibility level (private, household, shared, default: household)
    created_at: The date and time the todo was created
    updated_at: The date and time the todo was last updated
  """

  __tablename__ = "todos"

  id = Column(Integer, primary_key=True, index=True)
  title = Column(String, nullable=False)
  description = Column(Text, nullable=True)
  household_id = Column(
      Integer,
      ForeignKey("households.id",
                 ondelete="CASCADE"),
      nullable=False,
      index=True)
  created_by = Column(
      Integer,
      ForeignKey("users.id",
                 ondelete="SET NULL"),
      nullable=True,
      index=True)
  priority = Column(String, nullable=False, default="medium", index=True)
  due_date = Column(DateTime(timezone=True), nullable=True, index=True)
  category = Column(String, nullable=True, index=True)
  visibility = Column(String, nullable=False, default="household", index=True)
  created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
  updated_at = Column(
      DateTime(timezone=True),
      default=utcnow,
      onupdate=utcnow,
      nullable=False)

  # Relationships
  household = relationship("Household")
  creator = relationship("User", foreign_keys=[created_by])
  claim = relationship(
      "TodoClaim",
      back_populates="todo",
      uselist=False,
      cascade="all, delete-orphan")
  completion = relationship(
      "TodoCompletion",
      back_populates="todo",
      uselist=False,
      cascade="all, delete-orphan")
  shares = relationship(
      "TodoShare",
      back_populates="todo",
      cascade="all, delete-orphan")

  __table_args__ = (
      Index("ix_todos_household_priority",
            "household_id",
            "priority"),
  )
