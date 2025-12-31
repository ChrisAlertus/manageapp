"""Todo completion model."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.utils import utcnow


class TodoCompletion(Base):
  """Todo completion model for tracking when a todo was completed.

  Columns:
    id: The completion's unique identifier
    todo_id: Foreign key to todos table (unique, one completion per todo)
    completed_by: Foreign key to users table (who completed the todo)
    completed_at: The date and time the todo was completed
  """

  __tablename__ = "todo_completions"

  id = Column(Integer, primary_key=True, index=True)
  todo_id = Column(
      Integer,
      ForeignKey("todos.id", ondelete="CASCADE"),
      nullable=False,
      unique=True,
      index=True)
  completed_by = Column(
      Integer,
      ForeignKey("users.id", ondelete="SET NULL"),
      nullable=True,
      index=True)
  completed_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

  # Relationships
  todo = relationship("Todo", back_populates="completion")
  user = relationship("User", foreign_keys=[completed_by])

  __table_args__ = (
      UniqueConstraint("todo_id", name="uq_todo_completion_todo_id"),
  )

