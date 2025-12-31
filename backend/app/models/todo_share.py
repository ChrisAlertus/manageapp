"""Todo share model."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.utils import utcnow


class TodoShare(Base):
  """Todo share model for managing shared visibility of todos.

  This model links todos to specific users who can see them when
  the todo's visibility is set to "shared".

  Columns:
    id: The share's unique identifier
    todo_id: Foreign key to todos table
    user_id: Foreign key to users table
    created_at: The date and time the share was created
  """

  __tablename__ = "todo_shares"

  id = Column(Integer, primary_key=True, index=True)
  todo_id = Column(
      Integer,
      ForeignKey("todos.id",
                 ondelete="CASCADE"),
      nullable=False,
      index=True)
  user_id = Column(
      Integer,
      ForeignKey("users.id",
                 ondelete="CASCADE"),
      nullable=False,
      index=True)
  created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

  # Relationships
  todo = relationship("Todo", back_populates="shares")
  user = relationship("User")

  __table_args__ = (
      UniqueConstraint("todo_id",
                       "user_id",
                       name="uq_todo_share"),
      Index("ix_todo_shares_todo_user",
            "todo_id",
            "user_id"),
  )
