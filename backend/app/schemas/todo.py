"""Todo-related Pydantic schemas."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Priority(str, Enum):
  """Priority levels for todos."""

  LOW = "low"
  MEDIUM = "medium"
  HIGH = "high"
  URGENT = "urgent"


class Visibility(str, Enum):
  """Visibility levels for todos."""

  PRIVATE = "private"
  HOUSEHOLD = "household"
  SHARED = "shared"


class TodoBase(BaseModel):
  """Base todo schema with common fields."""

  title: str = Field(..., min_length=1, max_length=255)
  description: Optional[str] = None
  priority: Priority = Field(default=Priority.MEDIUM)
  due_date: Optional[datetime] = None
  category: Optional[str] = Field(None, max_length=100)
  visibility: Visibility = Field(default=Visibility.HOUSEHOLD)


class TodoCreate(TodoBase):
  """Schema for creating a todo."""

  shared_user_ids: Optional[List[int]] = Field(
      default=None,
      description=
      "List of user IDs to share with (required if visibility='shared')")


class TodoUpdate(BaseModel):
  """Schema for updating a todo (all fields optional)."""

  title: Optional[str] = Field(None, min_length=1, max_length=255)
  description: Optional[str] = None
  priority: Optional[Priority] = None
  due_date: Optional[datetime] = None
  category: Optional[str] = Field(None, max_length=100)
  visibility: Optional[Visibility] = None
  shared_user_ids: Optional[List[int]] = Field(
      default=None,
      description=
      "List of user IDs to share with (required if visibility='shared')")


class TodoClaimRead(BaseModel):
  """Schema for reading a todo claim."""

  id: int
  todo_id: int
  claimed_by: Optional[int] = None
  claimed_at: datetime

  class Config:
    from_attributes = True


class TodoCompletionRead(BaseModel):
  """Schema for reading a todo completion."""

  id: int
  todo_id: int
  completed_by: Optional[int] = None
  completed_at: datetime

  class Config:
    from_attributes = True


class TodoShareRead(BaseModel):
  """Schema for reading a todo share."""

  id: int
  todo_id: int
  user_id: int
  created_at: datetime

  class Config:
    from_attributes = True


class TodoRead(TodoBase):
  """Schema for reading a todo."""

  id: int
  household_id: int
  created_by: Optional[int] = None
  created_at: datetime
  updated_at: datetime
  claim: Optional[TodoClaimRead] = None
  completion: Optional[TodoCompletionRead] = None
  shares: List[TodoShareRead] = Field(default_factory=list)

  class Config:
    from_attributes = True


class TodoClaimCreate(BaseModel):
  """Schema for claiming a todo."""

  user_id: Optional[int] = Field(
      None,
      description=
      "User ID to claim for (None for self-claim, required for claiming on behalf of others)"
  )


class TodoShareCreate(BaseModel):
  """Schema for adding a shared user to a todo."""

  user_id: int = Field(..., description="User ID to share with")


class TodoVisibilityUpdate(BaseModel):
  """Schema for updating todo visibility."""

  visibility: Visibility
  shared_user_ids: Optional[List[int]] = Field(
      default=None,
      description=
      "List of user IDs to share with (required if visibility='shared')")
