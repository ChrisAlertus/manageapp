"""Todo management endpoints."""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_active_user,
    get_db,
    get_household_member_or_404,
)
from app.models.user import User
from app.schemas.todo import (
    Priority,
    TodoClaimCreate,
    TodoCreate,
    TodoRead,
    TodoShareCreate,
    TodoShareRead,
    TodoUpdate,
    TodoVisibilityUpdate,
    Visibility,
)
from app.services.todo_service import TodoService


router = APIRouter()


@router.post(
    "/{household_id}/todos",
    response_model=TodoRead,
    status_code=status.HTTP_201_CREATED,
)
def create_todo(
    household_id: int,
    todo_in: TodoCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Create a new todo.

  Args:
    household_id: The household ID.
    todo_in: Todo creation data.
    current_user: Current authenticated user.
    db: Database session.

  Returns:
    Created todo object.
  """
  # Verify user is a household member
  get_household_member_or_404(household_id, current_user, db)

  try:
    return TodoService.create_todo(
        db=db,
        todo_in=todo_in,
        household_id=household_id,
        user_id=current_user.id,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e),
    )


@router.get(
    "/{household_id}/todos",
    response_model=List[TodoRead],
)
def list_todos(
    household_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    visibility: Optional[str] = Query(None,
                                      description="Filter by visibility"),
    claimed_by: Optional[int] = Query(
        None,
        description="Filter by claimer user_id"),
    created_by: Optional[int] = Query(
        None,
        description="Filter by creator user_id"),
    priority: Optional[str] = Query(None,
                                    description="Filter by priority"),
    category: Optional[str] = Query(None,
                                    description="Filter by category"),
    due_date_before: Optional[datetime] = Query(
        None,
        description="Filter by due date (before)"),
    due_date_after: Optional[datetime] = Query(
        None,
        description="Filter by due date (after)"),
    status: Optional[str] = Query(
        None,
        description="Filter by completion status (completed, incomplete)"),
    sort: Optional[str] = Query(
        None,
        description="Sort field (priority, due_date, created_at, updated_at)"),
    order: Optional[str] = Query("asc",
                                 description="Sort order (asc, desc)"),
):
  """
  List all todos visible to the current user.

  Args:
    household_id: The household ID.
    current_user: Current authenticated user.
    db: Database session.
    visibility: Filter by visibility.
    claimed_by: Filter by claimer user_id.
    created_by: Filter by creator user_id.
    priority: Filter by priority.
    category: Filter by category.
    due_date_before: Filter by due date (before).
    due_date_after: Filter by due date (after).
    status: Filter by completion status.
    sort: Sort field.
    order: Sort order.

  Returns:
    List of visible todos.
  """
  # Verify user is a household member
  get_household_member_or_404(household_id, current_user, db)

  # Build filters dict
  filters: Dict = {}
  if visibility:
    filters["visibility"] = visibility
  if claimed_by is not None:
    filters["claimed_by"] = claimed_by
  if created_by is not None:
    filters["created_by"] = created_by
  if priority:
    filters["priority"] = priority
  if category:
    filters["category"] = category
  if due_date_before:
    filters["due_date_before"] = due_date_before
  if due_date_after:
    filters["due_date_after"] = due_date_after
  if status:
    filters["status"] = status

  # Validate sort order
  if order not in ["asc", "desc"]:
    order = "asc"

  return TodoService.get_visible_todos(
      db=db,
      household_id=household_id,
      user_id=current_user.id,
      filters=filters if filters else None,
      sort_field=sort,
      sort_order=order,
  )


@router.get(
    "/{household_id}/todos/{todo_id}",
    response_model=TodoRead,
)
def get_todo(
    household_id: int,
    todo_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Get a single todo by ID.

  Args:
    household_id: The household ID.
    todo_id: The todo ID.
    current_user: Current authenticated user.
    db: Database session.

  Returns:
    Todo object.
  """
  # Verify user is a household member
  get_household_member_or_404(household_id, current_user, db)

  try:
    return TodoService.get_todo(
        db=db,
        todo_id=todo_id,
        user_id=current_user.id,
        household_id=household_id,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(e),
    )
  except PermissionError as e:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=str(e),
    )


@router.patch(
    "/{household_id}/todos/{todo_id}",
    response_model=TodoRead,
)
def update_todo(
    household_id: int,
    todo_id: int,
    todo_update: TodoUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Update a todo.

  Args:
    household_id: The household ID.
    todo_id: The todo ID.
    todo_update: Todo update data.
    current_user: Current authenticated user.
    db: Database session.

  Returns:
    Updated todo object.
  """
  # Verify user is a household member
  get_household_member_or_404(household_id, current_user, db)

  try:
    return TodoService.update_todo(
        db=db,
        todo_id=todo_id,
        todo_update=todo_update,
        user_id=current_user.id,
        household_id=household_id,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e),
    )
  except PermissionError as e:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=str(e),
    )


@router.delete(
    "/{household_id}/todos/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_todo(
    household_id: int,
    todo_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Delete a todo.

  Args:
    household_id: The household ID.
    todo_id: The todo ID.
    current_user: Current authenticated user.
    db: Database session.
  """
  # Verify user is a household member
  get_household_member_or_404(household_id, current_user, db)

  try:
    TodoService.delete_todo(
        db=db,
        todo_id=todo_id,
        user_id=current_user.id,
        household_id=household_id,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(e),
    )
  except PermissionError as e:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=str(e),
    )

  return None


@router.patch(
    "/{household_id}/todos/{todo_id}/visibility",
    response_model=TodoRead,
)
def update_todo_visibility(
    household_id: int,
    todo_id: int,
    visibility_update: TodoVisibilityUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Update todo visibility.

  Args:
    household_id: The household ID.
    todo_id: The todo ID.
    visibility_update: Visibility update data.
    current_user: Current authenticated user.
    db: Database session.

  Returns:
    Updated todo object.
  """
  # Verify user is a household member
  get_household_member_or_404(household_id, current_user, db)

  try:
    return TodoService.update_todo_visibility(
        db=db,
        todo_id=todo_id,
        visibility=visibility_update.visibility,
        user_id=current_user.id,
        household_id=household_id,
        shared_user_ids=visibility_update.shared_user_ids,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e),
    )
  except PermissionError as e:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=str(e),
    )


@router.post(
    "/{household_id}/todos/{todo_id}/shares",
    response_model=TodoShareRead,
    status_code=status.HTTP_201_CREATED,
)
def add_shared_user(
    household_id: int,
    todo_id: int,
    share_in: TodoShareCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Add a shared user to a todo.

  Args:
    household_id: The household ID.
    todo_id: The todo ID.
    share_in: Share creation data.
    current_user: Current authenticated user.
    db: Database session.

  Returns:
    Created TodoShare object.
  """
  # Verify user is a household member
  get_household_member_or_404(household_id, current_user, db)

  try:
    return TodoService.add_shared_user(
        db=db,
        todo_id=todo_id,
        shared_user_id=share_in.user_id,
        user_id=current_user.id,
        household_id=household_id,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e),
    )
  except PermissionError as e:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=str(e),
    )


@router.delete(
    "/{household_id}/todos/{todo_id}/shares/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_shared_user(
    household_id: int,
    todo_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Remove a shared user from a todo.

  Args:
    household_id: The household ID.
    todo_id: The todo ID.
    user_id: ID of the user to remove from shares.
    current_user: Current authenticated user.
    db: Database session.
  """
  # Verify user is a household member
  get_household_member_or_404(household_id, current_user, db)

  try:
    TodoService.remove_shared_user(
        db=db,
        todo_id=todo_id,
        shared_user_id=user_id,
        user_id=current_user.id,
        household_id=household_id,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(e),
    )
  except PermissionError as e:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=str(e),
    )

  return None


@router.get(
    "/{household_id}/todos/{todo_id}/shares",
    response_model=List[TodoShareRead],
)
def list_shared_users(
    household_id: int,
    todo_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  List shared users for a todo.

  Args:
    household_id: The household ID.
    todo_id: The todo ID.
    current_user: Current authenticated user.
    db: Database session.

  Returns:
    List of TodoShare objects.
  """
  # Verify user is a household member
  get_household_member_or_404(household_id, current_user, db)

  try:
    return TodoService.list_shared_users(
        db=db,
        todo_id=todo_id,
        user_id=current_user.id,
        household_id=household_id,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(e),
    )
  except PermissionError as e:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=str(e),
    )


@router.post(
    "/{household_id}/todos/{todo_id}/claim",
    response_model=TodoRead,
)
def claim_todo(
    household_id: int,
    todo_id: int,
    claim_in: Optional[TodoClaimCreate] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Claim a todo.

  Args:
    household_id: The household ID.
    todo_id: The todo ID.
    claim_in: Claim creation data (optional, defaults to self-claim).
    current_user: Current authenticated user.
    db: Database session.

  Returns:
    Updated todo object with claim.
  """
  # Verify user is a household member
  get_household_member_or_404(household_id, current_user, db)

  claim_for_user_id = None
  if claim_in and claim_in.user_id is not None:
    claim_for_user_id = claim_in.user_id

  try:
    TodoService.claim_todo(
        db=db,
        todo_id=todo_id,
        user_id=current_user.id,
        household_id=household_id,
        claim_for_user_id=claim_for_user_id,
    )
    # Return the updated todo
    return TodoService.get_todo(
        db=db,
        todo_id=todo_id,
        user_id=current_user.id,
        household_id=household_id,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e),
    )
  except PermissionError as e:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=str(e),
    )


@router.delete(
    "/{household_id}/todos/{todo_id}/claim",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unclaim_todo(
    household_id: int,
    todo_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Unclaim a todo.

  Args:
    household_id: The household ID.
    todo_id: The todo ID.
    current_user: Current authenticated user.
    db: Database session.
  """
  # Verify user is a household member
  get_household_member_or_404(household_id, current_user, db)

  try:
    TodoService.unclaim_todo(
        db=db,
        todo_id=todo_id,
        user_id=current_user.id,
        household_id=household_id,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e),
    )
  except PermissionError as e:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=str(e),
    )

  return None


@router.post(
    "/{household_id}/todos/{todo_id}/complete",
    response_model=TodoRead,
)
def complete_todo(
    household_id: int,
    todo_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Mark a todo as complete.

  Args:
    household_id: The household ID.
    todo_id: The todo ID.
    current_user: Current authenticated user.
    db: Database session.

  Returns:
    Updated todo object with completion.
  """
  # Verify user is a household member
  get_household_member_or_404(household_id, current_user, db)

  try:
    TodoService.complete_todo(
        db=db,
        todo_id=todo_id,
        user_id=current_user.id,
        household_id=household_id,
    )
    # Return the updated todo
    return TodoService.get_todo(
        db=db,
        todo_id=todo_id,
        user_id=current_user.id,
        household_id=household_id,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e),
    )
  except PermissionError as e:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=str(e),
    )


@router.delete(
    "/{household_id}/todos/{todo_id}/complete",
    status_code=status.HTTP_204_NO_CONTENT,
)
def uncomplete_todo(
    household_id: int,
    todo_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
  """
  Mark a todo as incomplete.

  Args:
    household_id: The household ID.
    todo_id: The todo ID.
    current_user: Current authenticated user.
    db: Database session.
  """
  # Verify user is a household member
  get_household_member_or_404(household_id, current_user, db)

  try:
    TodoService.uncomplete_todo(
        db=db,
        todo_id=todo_id,
        user_id=current_user.id,
        household_id=household_id,
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(e),
    )
  except PermissionError as e:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=str(e),
    )

  return None
