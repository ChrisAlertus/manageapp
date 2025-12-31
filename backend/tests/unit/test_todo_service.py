"""Unit tests for TodoService business logic."""

import pytest
from datetime import datetime, timezone

from app.models.household import Household
from app.models.household_member import HouseholdMember
from app.models.todo import Todo
from app.models.todo_claim import TodoClaim
from app.models.todo_completion import TodoCompletion
from app.models.todo_share import TodoShare
from app.models.user import User
from app.schemas.todo import Priority, TodoCreate, TodoUpdate, Visibility
from app.services.todo_service import TodoService


@pytest.fixture
def db_session():
  """Create an in-memory SQLite database session for testing."""
  from sqlalchemy import create_engine, event
  from sqlalchemy.orm import sessionmaker

  from app.core.database import Base

  engine = create_engine(
      "sqlite:///:memory:",
      connect_args={"check_same_thread": False})

  # Enable foreign key constraints for SQLite
  @event.listens_for(engine, "connect")
  def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

  Base.metadata.create_all(engine)
  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  session = SessionLocal()
  try:
    yield session
  finally:
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_user(db_session):
  """Create a test user."""
  user = User(
      email="test@example.com",
      hashed_password="hashed_password",
      full_name="Test User",
  )
  db_session.add(user)
  db_session.commit()
  db_session.refresh(user)
  return user


@pytest.fixture
def test_user2(db_session):
  """Create a second test user."""
  user = User(
      email="test2@example.com",
      hashed_password="hashed_password",
      full_name="Test User 2",
  )
  db_session.add(user)
  db_session.commit()
  db_session.refresh(user)
  return user


@pytest.fixture
def test_user3(db_session):
  """Create a third test user."""
  user = User(
      email="test3@example.com",
      hashed_password="hashed_password",
      full_name="Test User 3",
  )
  db_session.add(user)
  db_session.commit()
  db_session.refresh(user)
  return user


@pytest.fixture
def test_household(db_session, test_user):
  """Create a test household."""
  household = Household(
      name="Test Household",
      description="A test household",
      created_by=test_user.id,
  )
  db_session.add(household)
  db_session.flush()

  # Add user as household member
  member = HouseholdMember(
      household_id=household.id,
      user_id=test_user.id,
      role="owner",
  )
  db_session.add(member)
  db_session.commit()
  db_session.refresh(household)
  return household


@pytest.fixture
def test_household_with_members(db_session, test_user, test_user2, test_user3):
  """Create a test household with multiple members."""
  household = Household(
      name="Test Household",
      description="A test household",
      created_by=test_user.id,
  )
  db_session.add(household)
  db_session.flush()

  # Add members
  member1 = HouseholdMember(
      household_id=household.id,
      user_id=test_user.id,
      role="owner",
  )
  member2 = HouseholdMember(
      household_id=household.id,
      user_id=test_user2.id,
      role="member",
  )
  member3 = HouseholdMember(
      household_id=household.id,
      user_id=test_user3.id,
      role="member",
  )
  db_session.add(member1)
  db_session.add(member2)
  db_session.add(member3)
  db_session.commit()
  db_session.refresh(household)
  return household


class TestTodoServiceCreate:
  """Test TodoService.create_todo."""

  def test_create_todo_household_visibility(
      self,
      db_session,
      test_user,
      test_household):
    """Test creating a todo with household visibility."""
    todo_in = TodoCreate(
        title="Test Todo",
        description="Test description",
        priority=Priority.MEDIUM,
        visibility=Visibility.HOUSEHOLD,
    )

    todo = TodoService.create_todo(
        db=db_session,
        todo_in=todo_in,
        household_id=test_household.id,
        user_id=test_user.id,
    )

    assert todo.id is not None
    assert todo.title == "Test Todo"
    assert todo.description == "Test description"
    assert todo.priority == "medium"
    assert todo.visibility == "household"
    assert todo.household_id == test_household.id
    assert todo.created_by == test_user.id

  def test_create_todo_private_visibility(
      self,
      db_session,
      test_user,
      test_household):
    """Test creating a todo with private visibility."""
    todo_in = TodoCreate(
        title="Private Todo",
        visibility=Visibility.PRIVATE,
    )

    todo = TodoService.create_todo(
        db=db_session,
        todo_in=todo_in,
        household_id=test_household.id,
        user_id=test_user.id,
    )

    assert todo.visibility == "private"

  def test_create_todo_shared_visibility_with_shares(
      self,
      db_session,
      test_user,
      test_user2,
      test_household):
    """Test creating a todo with shared visibility and shared users."""
    todo_in = TodoCreate(
        title="Shared Todo",
        visibility=Visibility.SHARED,
        shared_user_ids=[test_user2.id],
    )

    todo = TodoService.create_todo(
        db=db_session,
        todo_in=todo_in,
        household_id=test_household.id,
        user_id=test_user.id,
    )

    assert todo.visibility == "shared"
    # Check that share was created
    shares = (
        db_session.query(TodoShare).filter(TodoShare.todo_id == todo.id).all())
    assert len(shares) == 1
    assert shares[0].user_id == test_user2.id

  def test_create_todo_shared_visibility_no_shares_raises_error(
      self,
      db_session,
      test_user,
      test_household):
    """Test that creating shared todo without shared_user_ids raises error."""
    todo_in = TodoCreate(
        title="Shared Todo",
        visibility=Visibility.SHARED,
        shared_user_ids=[],
    )

    with pytest.raises(ValueError, match="shared_user_ids is required"):
      TodoService.create_todo(
          db=db_session,
          todo_in=todo_in,
          household_id=test_household.id,
          user_id=test_user.id,
      )


class TestTodoServiceVisibility:
  """Test TodoService visibility and authorization logic."""

  def test_can_user_see_todo_creator_always_sees(
      self,
      db_session,
      test_user,
      test_household):
    """Test that creator can always see their todos."""
    todo = Todo(
        title="Private Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="private",
    )
    db_session.add(todo)
    db_session.commit()

    assert TodoService.can_user_see_todo(test_user.id, todo, db_session) is True

  def test_can_user_see_todo_private_not_creator(
      self,
      db_session,
      test_user,
      test_user2,
      test_household):
    """Test that non-creator cannot see private todos."""
    todo = Todo(
        title="Private Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="private",
    )
    db_session.add(todo)
    db_session.commit()

    assert TodoService.can_user_see_todo(
        test_user2.id,
        todo,
        db_session) is False

  def test_can_user_see_todo_household_member_sees(
      self,
      db_session,
      test_user,
      test_user2,
      test_household_with_members):
    """Test that household members can see household visibility todos."""
    todo = Todo(
        title="Household Todo",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
        visibility="household",
    )
    db_session.add(todo)
    db_session.commit()

    assert TodoService.can_user_see_todo(
        test_user2.id,
        todo,
        db_session) is True

  def test_can_user_see_todo_household_non_member_cannot_see(
      self,
      db_session,
      test_user,
      test_user2,
      test_household):
    """Test that non-household members cannot see household todos."""
    todo = Todo(
        title="Household Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="household",
    )
    db_session.add(todo)
    db_session.commit()

    assert TodoService.can_user_see_todo(
        test_user2.id,
        todo,
        db_session) is False

  def test_can_user_see_todo_shared_user_sees(
      self,
      db_session,
      test_user,
      test_user2,
      test_household):
    """Test that shared users can see shared visibility todos."""
    todo = Todo(
        title="Shared Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="shared",
    )
    db_session.add(todo)
    db_session.flush()

    share = TodoShare(todo_id=todo.id, user_id=test_user2.id)
    db_session.add(share)
    db_session.commit()

    assert TodoService.can_user_see_todo(
        test_user2.id,
        todo,
        db_session) is True

  def test_can_user_see_todo_shared_non_shared_user_cannot_see(
      self,
      db_session,
      test_user,
      test_user2,
      test_user3,
      test_household):
    """Test that non-shared users cannot see shared todos."""
    todo = Todo(
        title="Shared Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="shared",
    )
    db_session.add(todo)
    db_session.flush()

    share = TodoShare(todo_id=todo.id, user_id=test_user2.id)
    db_session.add(share)
    db_session.commit()

    assert TodoService.can_user_see_todo(
        test_user3.id,
        todo,
        db_session) is False


class TestTodoServiceGetVisibleTodos:
  """Test TodoService.get_visible_todos filtering and sorting."""

  def test_get_visible_todos_returns_only_visible(
      self,
      db_session,
      test_user,
      test_user2,
      test_household_with_members):
    """Test that get_visible_todos only returns todos visible to user."""
    # Create todos with different visibility
    todo1 = Todo(
        title="Private Todo",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
        visibility="private",
    )
    todo2 = Todo(
        title="Household Todo",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
        visibility="household",
    )
    todo3 = Todo(
        title="Shared Todo",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
        visibility="shared",
    )
    db_session.add_all([todo1, todo2, todo3])
    db_session.flush()

    # Share todo3 with test_user2
    share = TodoShare(todo_id=todo3.id, user_id=test_user2.id)
    db_session.add(share)
    db_session.commit()

    # test_user2 should see household and shared todos, but not private
    todos = TodoService.get_visible_todos(
        db=db_session,
        household_id=test_household_with_members.id,
        user_id=test_user2.id,
    )

    assert len(todos) == 2
    todo_titles = [t.title for t in todos]
    assert "Household Todo" in todo_titles
    assert "Shared Todo" in todo_titles
    assert "Private Todo" not in todo_titles

  def test_get_visible_todos_filters_by_priority(
      self,
      db_session,
      test_user,
      test_household):
    """Test filtering todos by priority."""
    todo1 = Todo(
        title="Urgent Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        priority="urgent",
    )
    todo2 = Todo(
        title="Low Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        priority="low",
    )
    db_session.add_all([todo1, todo2])
    db_session.commit()

    todos = TodoService.get_visible_todos(
        db=db_session,
        household_id=test_household.id,
        user_id=test_user.id,
        filters={"priority": "urgent"},
    )

    assert len(todos) == 1
    assert todos[0].title == "Urgent Todo"

  def test_get_visible_todos_filters_by_status(
      self,
      db_session,
      test_user,
      test_household):
    """Test filtering todos by completion status."""
    todo1 = Todo(
        title="Completed Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    todo2 = Todo(
        title="Incomplete Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add_all([todo1, todo2])
    db_session.flush()

    completion = TodoCompletion(todo_id=todo1.id, completed_by=test_user.id)
    db_session.add(completion)
    db_session.commit()

    # Filter by completed
    completed_todos = TodoService.get_visible_todos(
        db=db_session,
        household_id=test_household.id,
        user_id=test_user.id,
        filters={"status": "completed"},
    )
    assert len(completed_todos) == 1
    assert completed_todos[0].title == "Completed Todo"

    # Filter by incomplete
    incomplete_todos = TodoService.get_visible_todos(
        db=db_session,
        household_id=test_household.id,
        user_id=test_user.id,
        filters={"status": "incomplete"},
    )
    assert len(incomplete_todos) == 1
    assert incomplete_todos[0].title == "Incomplete Todo"

  def test_get_visible_todos_default_sorting(
      self,
      db_session,
      test_user,
      test_user2,
      test_household_with_members):
    """Test default sorting (claimed first, then user-created, then priority)."""
    # Create todos with different priorities
    todo1 = Todo(
        title="Low Priority",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
        priority="low",
    )
    todo2 = Todo(
        title="High Priority",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
        priority="high",
    )
    todo3 = Todo(
        title="Claimed Todo",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
        priority="low",
    )
    db_session.add_all([todo1, todo2, todo3])
    db_session.flush()

    # Claim todo3 by test_user2
    claim = TodoClaim(todo_id=todo3.id, claimed_by=test_user2.id)
    db_session.add(claim)
    db_session.commit()

    # Get todos for test_user2 - claimed should be first
    todos = TodoService.get_visible_todos(
        db=db_session,
        household_id=test_household_with_members.id,
        user_id=test_user2.id,
    )

    # Claimed todo should be first
    assert todos[0].title == "Claimed Todo"


class TestTodoServiceClaims:
  """Test TodoService claim methods."""

  def test_claim_todo_self_claim(self, db_session, test_user, test_household):
    """Test self-claiming a todo."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.commit()

    claim = TodoService.claim_todo(
        db=db_session,
        todo_id=todo.id,
        user_id=test_user.id,
        household_id=test_household.id,
    )

    assert claim.todo_id == todo.id
    assert claim.claimed_by == test_user.id

  def test_claim_todo_for_others(
      self,
      db_session,
      test_user,
      test_user2,
      test_household_with_members):
    """Test claiming a todo on behalf of another user."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
        visibility="household",
    )
    db_session.add(todo)
    db_session.commit()

    claim = TodoService.claim_todo(
        db=db_session,
        todo_id=todo.id,
        user_id=test_user.id,
        household_id=test_household_with_members.id,
        claim_for_user_id=test_user2.id,
    )

    assert claim.claimed_by == test_user2.id

  def test_claim_todo_already_claimed_raises_error(
      self,
      db_session,
      test_user,
      test_household):
    """Test that claiming an already claimed todo raises error."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.flush()

    claim = TodoClaim(todo_id=todo.id, claimed_by=test_user.id)
    db_session.add(claim)
    db_session.commit()

    with pytest.raises(ValueError, match="already claimed"):
      TodoService.claim_todo(
          db=db_session,
          todo_id=todo.id,
          user_id=test_user.id,
          household_id=test_household.id,
      )

  def test_claim_todo_already_completed_raises_error(
      self,
      db_session,
      test_user,
      test_household):
    """Test that claiming a completed todo raises error."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.flush()

    completion = TodoCompletion(todo_id=todo.id, completed_by=test_user.id)
    db_session.add(completion)
    db_session.commit()

    with pytest.raises(ValueError, match="completed"):
      TodoService.claim_todo(
          db=db_session,
          todo_id=todo.id,
          user_id=test_user.id,
          household_id=test_household.id,
      )

  def test_unclaim_todo(self, db_session, test_user, test_household):
    """Test unclaiming a todo."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.flush()

    claim = TodoClaim(todo_id=todo.id, claimed_by=test_user.id)
    db_session.add(claim)
    db_session.commit()

    TodoService.unclaim_todo(
        db=db_session,
        todo_id=todo.id,
        user_id=test_user.id,
        household_id=test_household.id,
    )

    # Verify claim was removed
    claim_check = (
        db_session.query(TodoClaim).filter(
            TodoClaim.todo_id == todo.id).first())
    assert claim_check is None

  def test_unclaim_todo_creator_can_unclaim(
      self,
      db_session,
      test_user,
      test_user2,
      test_household_with_members):
    """Test that todo creator can unclaim even if not the claimer."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.flush()

    claim = TodoClaim(todo_id=todo.id, claimed_by=test_user2.id)
    db_session.add(claim)
    db_session.commit()

    # Creator can unclaim
    TodoService.unclaim_todo(
        db=db_session,
        todo_id=todo.id,
        user_id=test_user.id,
        household_id=test_household_with_members.id,
    )

    claim_check = (
        db_session.query(TodoClaim).filter(
            TodoClaim.todo_id == todo.id).first())
    assert claim_check is None


class TestTodoServiceCompletion:
  """Test TodoService completion methods."""

  def test_complete_todo(self, db_session, test_user, test_household):
    """Test completing a todo."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.commit()

    completion = TodoService.complete_todo(
        db=db_session,
        todo_id=todo.id,
        user_id=test_user.id,
        household_id=test_household.id,
    )

    assert completion.todo_id == todo.id
    assert completion.completed_by == test_user.id

  def test_complete_todo_already_completed_raises_error(
      self,
      db_session,
      test_user,
      test_household):
    """Test that completing an already completed todo raises error."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.flush()

    completion = TodoCompletion(todo_id=todo.id, completed_by=test_user.id)
    db_session.add(completion)
    db_session.commit()

    with pytest.raises(ValueError, match="already completed"):
      TodoService.complete_todo(
          db=db_session,
          todo_id=todo.id,
          user_id=test_user.id,
          household_id=test_household.id,
      )

  def test_uncomplete_todo(self, db_session, test_user, test_household):
    """Test uncompleting a todo."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.flush()

    completion = TodoCompletion(todo_id=todo.id, completed_by=test_user.id)
    db_session.add(completion)
    db_session.commit()

    TodoService.uncomplete_todo(
        db=db_session,
        todo_id=todo.id,
        user_id=test_user.id,
        household_id=test_household.id,
    )

    # Verify completion was removed
    completion_check = (
        db_session.query(TodoCompletion).filter(
            TodoCompletion.todo_id == todo.id).first())
    assert completion_check is None
