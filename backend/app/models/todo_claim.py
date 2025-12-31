"""Todo claim model."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.utils import utcnow


class TodoClaim(Base):
  """Todo claim model for tracking who claimed a todo.

  Columns:
    id: The claim's unique identifier
    todo_id: Foreign key to todos table (unique, one claim per todo)
    claimed_by: Foreign key to users table (who claimed the todo)
    claimed_at: The date and time the todo was claimed
  """

  __tablename__ = "todo_claims"

  id = Column(Integer, primary_key=True, index=True)
  todo_id = Column(
      Integer,
      ForeignKey("todos.id", ondelete="CASCADE"),
      nullable=False,
      unique=True,
      index=True)
  claimed_by = Column(
      Integer,
      ForeignKey("users.id", ondelete="SET NULL"),
      nullable=True,
      index=True)
  claimed_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

  # Relationships
  todo = relationship("Todo", back_populates="claim")
  user = relationship("User", foreign_keys=[claimed_by])

  __table_args__ = (
      UniqueConstraint("todo_id", name="uq_todo_claim_todo_id"),
  )

