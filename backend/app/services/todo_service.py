"""Todo business logic service."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import and_, case, or_
from sqlalchemy.orm import Session, joinedload

from app.models.household_member import HouseholdMember
from app.models.todo import Todo
from app.models.todo_claim import TodoClaim
from app.models.todo_completion import TodoCompletion
from app.models.todo_share import TodoShare
from app.schemas.todo import Priority, TodoCreate, TodoUpdate, Visibility


class TodoService:
  """Service for todo business logic."""

  @staticmethod
  def create_todo(
      db: Session,
      todo_in: TodoCreate,
      household_id: int,
      user_id: int,
  ) -> Todo:
    """Create a new todo.

    Args:
      db: Database session.
      todo_in: Todo creation data.
      household_id: The household ID.
      user_id: ID of the user creating the todo.

    Returns:
      Created todo object.

    Raises:
      ValueError: If visibility is 'shared' but no shared_user_ids provided.
    """
    # Validate shared visibility requires shared_user_ids
    if todo_in.visibility == Visibility.SHARED:
      if not todo_in.shared_user_ids or len(todo_in.shared_user_ids) == 0:
        raise ValueError(
            "shared_user_ids is required when visibility is 'shared'")

    # Create todo
    db_todo = Todo(
        title=todo_in.title,
        description=todo_in.description,
        household_id=household_id,
        created_by=user_id,
        priority=todo_in.priority.value,
        due_date=todo_in.due_date,
        category=todo_in.category,
        visibility=todo_in.visibility.value,
    )
    db.add(db_todo)
    db.flush()  # Flush to get the todo ID

    # Create TodoShare records if visibility is 'shared'
    if todo_in.visibility == Visibility.SHARED and todo_in.shared_user_ids:
      for shared_user_id in todo_in.shared_user_ids:
        # Skip if trying to share with self (creator can always see their own
        # todos)
        if shared_user_id == user_id:
          continue
        db_share = TodoShare(todo_id=db_todo.id, user_id=shared_user_id)
        db.add(db_share)

    db.commit()
    db.refresh(db_todo)
    return db_todo

  @staticmethod
  def get_todo(
      db: Session,
      todo_id: int,
      user_id: int,
      household_id: int,
  ) -> Todo:
    """Get a single todo by ID.

    Args:
      db: Database session.
      todo_id: The todo ID.
      user_id: ID of the user requesting the todo.
      household_id: The household ID.

    Returns:
      Todo object.

    Raises:
      ValueError: If todo not found.
      PermissionError: If user cannot see the todo.
    """
    todo = (
        db.query(Todo).options(
            joinedload(Todo.claim),
            joinedload(Todo.completion),
            joinedload(Todo.shares),
        ).filter(Todo.id == todo_id,
                 Todo.household_id == household_id).first())

    if todo is None:
      raise ValueError("Todo not found")

    if not TodoService.can_user_see_todo(user_id, todo, db):
      raise PermissionError("You do not have permission to view this todo")

    return todo

  @staticmethod
  def get_visible_todos(
      db: Session,
      household_id: int,
      user_id: int,
      filters: Optional[Dict] = None,
      sort_field: Optional[str] = None,
      sort_order: str = "asc",
  ) -> List[Todo]:
    """Get all todos visible to the user with filtering and sorting.

    Args:
      db: Database session.
      household_id: The household ID.
      user_id: ID of the user.
      filters: Optional dict of filter criteria.
      sort_field: Optional field to sort by (priority, due_date, created_at,
        updated_at).
      sort_order: Sort order (asc or desc).

    Returns:
      List of visible todos.
    """
    query = db.query(Todo).filter(Todo.household_id == household_id)

    # Apply visibility filter
    query = TodoService._apply_visibility_filter(
        query,
        user_id,
        household_id,
        db)

    # Apply additional filters
    if filters:
      query = TodoService._apply_filters(
          query,
          filters,
          user_id,
          household_id,
          db)

    # Apply sorting
    query = TodoService._apply_sorting(query, user_id, sort_field, sort_order)

    # Eager load relationships
    query = query.options(
        joinedload(Todo.claim),
        joinedload(Todo.completion),
        joinedload(Todo.shares),
    )

    return query.all()

  @staticmethod
  def update_todo(
      db: Session,
      todo_id: int,
      todo_update: TodoUpdate,
      user_id: int,
      household_id: int,
  ) -> Todo:
    """Update a todo.

    Args:
      db: Database session.
      todo_id: The todo ID.
      todo_update: Todo update data.
      user_id: ID of the user updating the todo.
      household_id: The household ID.

    Returns:
      Updated todo object.

    Raises:
      ValueError: If todo not found or validation fails.
      PermissionError: If user cannot edit the todo.
    """
    todo = (
        db.query(Todo).filter(
            Todo.id == todo_id,
            Todo.household_id == household_id).first())

    if todo is None:
      raise ValueError("Todo not found")

    # Only creator can edit
    if todo.created_by != user_id:
      raise PermissionError("Only the creator can edit this todo")

    # Update fields
    if todo_update.title is not None:
      todo.title = todo_update.title
    if todo_update.description is not None:
      todo.description = todo_update.description
    if todo_update.priority is not None:
      todo.priority = todo_update.priority.value
    if todo_update.due_date is not None:
      todo.due_date = todo_update.due_date
    if todo_update.category is not None:
      todo.category = todo_update.category

    # Handle visibility change
    if todo_update.visibility is not None:
      new_visibility = todo_update.visibility.value
      old_visibility = todo.visibility

      if new_visibility != old_visibility:
        # If changing to shared, validate shared_user_ids
        if new_visibility == Visibility.SHARED.value:
          if not todo_update.shared_user_ids or len(
              todo_update.shared_user_ids) == 0:
            raise ValueError(
                "shared_user_ids is required when visibility is 'shared'")
          # Remove old shares
          db.query(TodoShare).filter(TodoShare.todo_id == todo_id).delete()
          # Create new shares
          for shared_user_id in todo_update.shared_user_ids:
            if shared_user_id != user_id:  # Skip self
              db_share = TodoShare(todo_id=todo_id, user_id=shared_user_id)
              db.add(db_share)
        elif (new_visibility == Visibility.PRIVATE.value
              or new_visibility == Visibility.HOUSEHOLD.value):
          # Remove all shares when changing away from shared
          db.query(TodoShare).filter(TodoShare.todo_id == todo_id).delete()

        todo.visibility = new_visibility
    elif todo_update.shared_user_ids is not None:
      # Update shares without changing visibility (only if already shared)
      if todo.visibility == Visibility.SHARED.value:
        # Remove old shares
        db.query(TodoShare).filter(TodoShare.todo_id == todo_id).delete()
        # Create new shares
        for shared_user_id in todo_update.shared_user_ids:
          if shared_user_id != user_id:  # Skip self
            db_share = TodoShare(todo_id=todo_id, user_id=shared_user_id)
            db.add(db_share)

    db.commit()
    db.refresh(todo)
    return todo

  @staticmethod
  def delete_todo(
      db: Session,
      todo_id: int,
      user_id: int,
      household_id: int,
  ) -> None:
    """Delete a todo.

    Args:
      db: Database session.
      todo_id: The todo ID.
      user_id: ID of the user deleting the todo.
      household_id: The household ID.

    Raises:
      ValueError: If todo not found.
      PermissionError: If user cannot delete the todo.
    """
    todo = (
        db.query(Todo).filter(
            Todo.id == todo_id,
            Todo.household_id == household_id).first())

    if todo is None:
      raise ValueError("Todo not found")

    # Only creator can delete
    if todo.created_by != user_id:
      raise PermissionError("Only the creator can delete this todo")

    db.delete(todo)
    db.commit()

  @staticmethod
  def can_user_see_todo(user_id: int, todo: Todo, db: Session) -> bool:
    """Check if a user can see a todo based on visibility rules.

    Args:
      user_id: ID of the user.
      todo: The todo object.
      db: Database session.

    Returns:
      True if user can see the todo, False otherwise.
    """
    # Creator can always see their todos
    if todo.created_by == user_id:
      return True

    # Check visibility rules
    if todo.visibility == Visibility.PRIVATE.value:
      return False
    elif todo.visibility == Visibility.HOUSEHOLD.value:
      # Check if user is a household member
      membership = (
          db.query(HouseholdMember).filter(
              HouseholdMember.household_id == todo.household_id,
              HouseholdMember.user_id == user_id,
          ).first())
      return membership is not None
    elif todo.visibility == Visibility.SHARED.value:
      # Check if user is in TodoShare
      share = (
          db.query(TodoShare).filter(
              TodoShare.todo_id == todo.id,
              TodoShare.user_id == user_id,
          ).first())
      return share is not None

    return False

  @staticmethod
  def update_todo_visibility(
      db: Session,
      todo_id: int,
      visibility: Visibility,
      user_id: int,
      household_id: int,
      shared_user_ids: Optional[List[int]] = None,
  ) -> Todo:
    """Update todo visibility.

    Args:
      db: Database session.
      todo_id: The todo ID.
      visibility: New visibility level.
      user_id: ID of the user updating visibility.
      household_id: The household ID.
      shared_user_ids: List of user IDs to share with (required if visibility='shared').

    Returns:
      Updated todo object.

    Raises:
      ValueError: If todo not found or validation fails.
      PermissionError: If user cannot update visibility.
    """
    todo = (
        db.query(Todo).filter(
            Todo.id == todo_id,
            Todo.household_id == household_id).first())

    if todo is None:
      raise ValueError("Todo not found")

    if todo.created_by != user_id:
      raise PermissionError("Only the creator can update visibility")

    if visibility == Visibility.SHARED:
      if not shared_user_ids or len(shared_user_ids) == 0:
        raise ValueError(
            "shared_user_ids is required when visibility is 'shared'")

    # Remove old shares
    db.query(TodoShare).filter(TodoShare.todo_id == todo_id).delete()

    # Create new shares if shared
    if visibility == Visibility.SHARED and shared_user_ids:
      for shared_user_id in shared_user_ids:
        if shared_user_id != user_id:  # Skip self
          db_share = TodoShare(todo_id=todo_id, user_id=shared_user_id)
          db.add(db_share)

    todo.visibility = visibility.value
    db.commit()
    db.refresh(todo)
    return todo

  @staticmethod
  def add_shared_user(
      db: Session,
      todo_id: int,
      shared_user_id: int,
      user_id: int,
      household_id: int,
  ) -> TodoShare:
    """Add a shared user to a todo.

    Args:
      db: Database session.
      todo_id: The todo ID.
      shared_user_id: ID of the user to share with.
      user_id: ID of the user making the request.
      household_id: The household ID.

    Returns:
      Created TodoShare object.

    Raises:
      ValueError: If todo not found, not shared visibility, or share already
          exists.
      PermissionError: If user cannot add shared users.
    """
    todo = (
        db.query(Todo).filter(
            Todo.id == todo_id,
            Todo.household_id == household_id).first())

    if todo is None:
      raise ValueError("Todo not found")

    if todo.created_by != user_id:
      raise PermissionError("Only the creator can add shared users")

    if todo.visibility != Visibility.SHARED.value:
      raise ValueError("Todo must have 'shared' visibility to add shared users")

    # Check if share already exists
    existing_share = (
        db.query(TodoShare).filter(
            TodoShare.todo_id == todo_id,
            TodoShare.user_id == shared_user_id,
        ).first())
    if existing_share is not None:
      raise ValueError("User is already shared on this todo")

    # Don't allow sharing with self (creator can always see)
    if shared_user_id == user_id:
      raise ValueError("Cannot share todo with yourself")

    db_share = TodoShare(todo_id=todo_id, user_id=shared_user_id)
    db.add(db_share)
    db.commit()
    db.refresh(db_share)
    return db_share

  @staticmethod
  def remove_shared_user(
      db: Session,
      todo_id: int,
      shared_user_id: int,
      user_id: int,
      household_id: int,
  ) -> None:
    """Remove a shared user from a todo.

    Args:
      db: Database session.
      todo_id: The todo ID.
      shared_user_id: ID of the user to remove from shares.
      user_id: ID of the user making the request.
      household_id: The household ID.

    Raises:
      ValueError: If todo not found or share not found.
      PermissionError: If user cannot remove shared users.
    """
    todo = (
        db.query(Todo).filter(
            Todo.id == todo_id,
            Todo.household_id == household_id).first())

    if todo is None:
      raise ValueError("Todo not found")

    if todo.created_by != user_id:
      raise PermissionError("Only the creator can remove shared users")

    share = (
        db.query(TodoShare).filter(
            TodoShare.todo_id == todo_id,
            TodoShare.user_id == shared_user_id,
        ).first())

    if share is None:
      raise ValueError("Share not found")

    db.delete(share)
    db.commit()

  @staticmethod
  def list_shared_users(
      db: Session,
      todo_id: int,
      user_id: int,
      household_id: int,
  ) -> List[TodoShare]:
    """List shared users for a todo.

    Args:
      db: Database session.
      todo_id: The todo ID.
      user_id: ID of the user making the request.
      household_id: The household ID.

    Returns:
      List of TodoShare objects.

    Raises:
      ValueError: If todo not found.
      PermissionError: If user cannot view shared users.
    """
    todo = (
        db.query(Todo).filter(
            Todo.id == todo_id,
            Todo.household_id == household_id).first())

    if todo is None:
      raise ValueError("Todo not found")

    if not TodoService.can_user_see_todo(user_id, todo, db):
      raise PermissionError("You do not have permission to view this todo")

    shares = (db.query(TodoShare).filter(TodoShare.todo_id == todo_id).all())
    return shares

  @staticmethod
  def claim_todo(
      db: Session,
      todo_id: int,
      user_id: int,
      household_id: int,
      claim_for_user_id: Optional[int] = None,
  ) -> TodoClaim:
    """Claim a todo.

    Args:
      db: Database session.
      todo_id: The todo ID.
      user_id: ID of the user making the claim.
      household_id: The household ID.
      claim_for_user_id: Optional user ID to claim for (None for self-claim).

    Returns:
      Created TodoClaim object.

    Raises:
      ValueError: If todo not found, already claimed, or already completed.
      PermissionError: If user cannot see the todo.
    """
    todo = (
        db.query(Todo).filter(
            Todo.id == todo_id,
            Todo.household_id == household_id).first())

    if todo is None:
      raise ValueError("Todo not found")

    if not TodoService.can_user_see_todo(user_id, todo, db):
      raise PermissionError("You do not have permission to view this todo")

    # Check if already completed
    completion = (
        db.query(TodoCompletion).filter(
            TodoCompletion.todo_id == todo_id).first())
    if completion is not None:
      raise ValueError("Cannot claim a completed todo")

    # Check if already claimed
    existing_claim = (
        db.query(TodoClaim).filter(TodoClaim.todo_id == todo_id).first())
    if existing_claim is not None:
      raise ValueError("Todo is already claimed")

    # Determine who the claim is for
    actual_claimer_id = (
        claim_for_user_id if claim_for_user_id is not None else user_id)

    # Validate claimer can see the todo (if claiming for someone else)
    if claim_for_user_id is not None:
      if not TodoService.can_user_see_todo(claim_for_user_id, todo, db):
        raise PermissionError(
            "The user you are claiming for cannot see this todo")

    db_claim = TodoClaim(todo_id=todo_id, claimed_by=actual_claimer_id)
    db.add(db_claim)
    db.commit()
    db.refresh(db_claim)
    return db_claim

  @staticmethod
  def unclaim_todo(
      db: Session,
      todo_id: int,
      user_id: int,
      household_id: int,
  ) -> None:
    """Unclaim a todo.

    Args:
      db: Database session.
      todo_id: The todo ID.
      user_id: ID of the user making the request.
      household_id: The household ID.

    Raises:
      ValueError: If todo not found or claim not found.
      PermissionError: If user cannot unclaim the todo.
    """
    todo = (
        db.query(Todo).filter(
            Todo.id == todo_id,
            Todo.household_id == household_id).first())

    if todo is None:
      raise ValueError("Todo not found")

    claim = (db.query(TodoClaim).filter(TodoClaim.todo_id == todo_id).first())

    if claim is None:
      raise ValueError("Todo is not claimed")

    # User can unclaim if they are the claimer or the todo creator
    if claim.claimed_by != user_id and todo.created_by != user_id:
      raise PermissionError("Only the claimer or creator can unclaim this todo")

    db.delete(claim)
    db.commit()

  @staticmethod
  def complete_todo(
      db: Session,
      todo_id: int,
      user_id: int,
      household_id: int,
  ) -> TodoCompletion:
    """Mark a todo as complete.

    Args:
      db: Database session.
      todo_id: The todo ID.
      user_id: ID of the user completing the todo.
      household_id: The household ID.

    Returns:
      Created TodoCompletion object.

    Raises:
      ValueError: If todo not found or already completed.
      PermissionError: If user cannot see the todo.
    """
    todo = (
        db.query(Todo).filter(
            Todo.id == todo_id,
            Todo.household_id == household_id).first())

    if todo is None:
      raise ValueError("Todo not found")

    if not TodoService.can_user_see_todo(user_id, todo, db):
      raise PermissionError("You do not have permission to view this todo")

    # Check if already completed
    existing_completion = (
        db.query(TodoCompletion).filter(
            TodoCompletion.todo_id == todo_id).first())
    if existing_completion is not None:
      raise ValueError("Todo is already completed")

    db_completion = TodoCompletion(todo_id=todo_id, completed_by=user_id)
    db.add(db_completion)
    db.commit()
    db.refresh(db_completion)
    return db_completion

  @staticmethod
  def uncomplete_todo(
      db: Session,
      todo_id: int,
      user_id: int,
      household_id: int,
  ) -> None:
    """Mark a todo as incomplete.

    Args:
      db: Database session.
      todo_id: The todo ID.
      user_id: ID of the user making the request.
      household_id: The household ID.

    Raises:
      ValueError: If todo not found or completion not found.
      PermissionError: If user cannot uncomplete the todo.
    """
    todo = (
        db.query(Todo).filter(
            Todo.id == todo_id,
            Todo.household_id == household_id).first())

    if todo is None:
      raise ValueError("Todo not found")

    completion = (
        db.query(TodoCompletion).filter(
            TodoCompletion.todo_id == todo_id).first())

    if completion is None:
      raise ValueError("Todo is not completed")

    # User can uncomplete if they are the completer or the todo creator
    if completion.completed_by != user_id and todo.created_by != user_id:
      raise PermissionError(
          "Only the completer or creator can uncomplete this todo")

    db.delete(completion)
    db.commit()

  @staticmethod
  def _apply_visibility_filter(
      query,
      user_id: int,
      household_id: int,
      db: Session):
    """Apply visibility filtering to a query.

    Args:
      query: SQLAlchemy query object.
      user_id: ID of the user.
      household_id: The household ID.
      db: Database session.

    Returns:
      Filtered query.
    """
    # Subquery for household members
    user_household_membership_subq = (
        db.query(HouseholdMember.household_id)
        .filter(HouseholdMember.user_id == user_id)
        .filter(HouseholdMember.household_id == household_id)
        .subquery()) #yapf:disable

    # Subquery for shared todos
    shared_todos_subq = (
        db.query(
            TodoShare.todo_id).filter(TodoShare.user_id == user_id).subquery())

    # Visibility filter:
    # - private: only creator
    # - household: creator OR household member
    # - shared: creator OR user in TodoShare
    query = query.filter(
        or_(
            # Creator can always see
            Todo.created_by == user_id,
            # Household visibility: user is household member
            and_(
                Todo.visibility == Visibility.HOUSEHOLD.value,
                Todo.household_id.in_(user_household_membership_subq),
            ),
            # Shared visibility: user is in TodoShare
            and_(
                Todo.visibility == Visibility.SHARED.value,
                Todo.id.in_(shared_todos_subq),
            ),
        ))

    return query

  @staticmethod
  def _apply_filters(
      query,
      filters: Dict,
      user_id: int,
      household_id: int,
      db: Session):
    """Apply additional filters to a query.

    Args:
      query: SQLAlchemy query object.
      filters: Dict of filter criteria.
      user_id: ID of the user.
      household_id: The household ID.
      db: Database session.

    Returns:
      Filtered query.
    """
    if "visibility" in filters and filters["visibility"]:
      query = query.filter(Todo.visibility == filters["visibility"])

    if "claimed_by" in filters and filters["claimed_by"] is not None:
      query = query.join(TodoClaim).filter(
          TodoClaim.claimed_by == filters["claimed_by"])

    if "created_by" in filters and filters["created_by"] is not None:
      query = query.filter(Todo.created_by == filters["created_by"])

    if "priority" in filters and filters["priority"]:
      query = query.filter(Todo.priority == filters["priority"])

    if "category" in filters and filters["category"]:
      query = query.filter(Todo.category == filters["category"])

    if "due_date_before" in filters and filters["due_date_before"]:
      query = query.filter(Todo.due_date <= filters["due_date_before"])

    if "due_date_after" in filters and filters["due_date_after"]:
      query = query.filter(Todo.due_date >= filters["due_date_after"])

    if "status" in filters and filters["status"]:
      if filters["status"] == "completed":
        query = query.join(TodoCompletion)
      elif filters["status"] == "incomplete":
        query = query.outerjoin(TodoCompletion).filter(
            TodoCompletion.id.is_(None))

    return query

  @staticmethod
  def _apply_sorting(
      query,
      user_id: int,
      sort_field: Optional[str] = None,
      sort_order: str = "asc"):
    """Apply sorting to a query.

    Default sorting: Claimed todos (where user is claimer) first, then
    user-created todos, then by priority/due_date.

    Args:
      query: SQLAlchemy query object.
      user_id: ID of the user.
      sort_field: Optional field to sort by.
      sort_order: Sort order (asc or desc).

    Returns:
      Sorted query.
    """
    # Get session from query
    db = query.session

    if sort_field:
      # Custom sorting
      if sort_field == "priority":
        priority_order = case(
            (Todo.priority == Priority.URGENT.value,
             1),
            (Todo.priority == Priority.HIGH.value,
             2),
            (Todo.priority == Priority.MEDIUM.value,
             3),
            (Todo.priority == Priority.LOW.value,
             4),
            else_=5,
        )
        if sort_order == "desc":
          query = query.order_by(priority_order.desc(), Todo.created_at.desc())
        else:
          query = query.order_by(priority_order.asc(), Todo.created_at.asc())
      elif sort_field == "due_date":
        if sort_order == "desc":
          query = query.order_by(
              Todo.due_date.desc().nulls_last(),
              Todo.created_at.desc())
        else:
          query = query.order_by(
              Todo.due_date.asc().nulls_last(),
              Todo.created_at.asc())
      elif sort_field == "created_at":
        if sort_order == "desc":
          query = query.order_by(Todo.created_at.desc())
        else:
          query = query.order_by(Todo.created_at.asc())
      elif sort_field == "updated_at":
        if sort_order == "desc":
          query = query.order_by(Todo.updated_at.desc())
        else:
          query = query.order_by(Todo.updated_at.asc())
      else:
        # Default fallback
        query = query.order_by(Todo.created_at.desc())
    else:
      # Default sorting: claimed first, then user-created, then
      # priority/due_date
      claimed_subq = (
          db.query(TodoClaim.todo_id)
          .filter(TodoClaim.claimed_by == user_id)
          .subquery()) #yapf:disable

      query = query.order_by(
          # Claimed todos first (where user is claimer)
          case(
              (Todo.id.in_(claimed_subq),
               1),
              else_=2,
          ).asc(),
          # Then user-created todos
          case(
              (Todo.created_by == user_id,
               1),
              else_=2,
          ).asc(),
          # Then by priority
          case(
              (Todo.priority == Priority.URGENT.value,
               1),
              (Todo.priority == Priority.HIGH.value,
               2),
              (Todo.priority == Priority.MEDIUM.value,
               3),
              (Todo.priority == Priority.LOW.value,
               4),
              else_=5,
          ).asc(),
          # Then by due_date (nulls last)
          Todo.due_date.asc().nulls_last(),
          # Finally by created_at
          Todo.created_at.desc(),
      )

    return query
