"""Unit tests for Todo model."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.models.todo import Todo
from app.models.household import Household
from app.models.user import User


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
def test_household(db_session, test_user):
  """Create a test household."""
  household = Household(
      name="Test Household",
      description="A test household",
      created_by=test_user.id,
  )
  db_session.add(household)
  db_session.commit()
  db_session.refresh(household)
  return household


class TestTodoModel:
  """Test Todo model validation and relationships."""

  def test_create_todo_with_required_fields(
      self,
      db_session,
      test_user,
      test_household):
    """Test that todo can be created with required fields."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)

    assert todo.id is not None
    assert todo.title == "Test Todo"
    assert todo.household_id == test_household.id
    assert todo.created_by == test_user.id
    assert todo.priority == "medium"  # Default value
    assert todo.description is None
    assert todo.due_date is None
    assert todo.category is None
    assert todo.created_at is not None
    assert todo.updated_at is not None

  def test_create_todo_with_all_fields(
      self,
      db_session,
      test_user,
      test_household):
    """Test that todo can be created with all fields."""
    due_date = datetime.now(timezone.utc)
    todo = Todo(
        title="Complete Task",
        description="This is a detailed description",
        household_id=test_household.id,
        created_by=test_user.id,
        priority="high",
        due_date=due_date,
        category="shopping",
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)

    assert todo.title == "Complete Task"
    assert todo.description == "This is a detailed description"
    assert todo.priority == "high"
    # SQLite may return naive datetime, so compare timestamps
    if todo.due_date.tzinfo is None:
      # Convert to UTC for comparison
      assert todo.due_date.replace(tzinfo=timezone.utc) == due_date
    else:
      assert todo.due_date == due_date
    assert todo.category == "shopping"

  def test_todo_priority_default(self, db_session, test_user, test_household):
    """Test that priority defaults to 'medium'."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)

    assert todo.priority == "medium"

  def test_todo_priority_custom_values(
      self,
      db_session,
      test_user,
      test_household):
    """Test that todo accepts different priority values."""
    priorities = ["low", "medium", "high", "urgent"]
    for priority in priorities:
      todo = Todo(
          title=f"Todo {priority}",
          household_id=test_household.id,
          created_by=test_user.id,
          priority=priority,
      )
      db_session.add(todo)
      db_session.commit()
      db_session.refresh(todo)
      assert todo.priority == priority

  def test_todo_optional_fields(self, db_session, test_user, test_household):
    """Test that optional fields can be None."""
    todo = Todo(
        title="Minimal Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)

    assert todo.description is None
    assert todo.due_date is None
    assert todo.category is None

  def test_todo_relationship_household(
      self,
      db_session,
      test_user,
      test_household):
    """Test that todo has relationship to household."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)

    assert todo.household is not None
    assert todo.household.id == test_household.id
    assert todo.household.name == "Test Household"

  def test_todo_relationship_creator(
      self,
      db_session,
      test_user,
      test_household):
    """Test that todo has relationship to creator user."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)

    assert todo.creator is not None
    assert todo.creator.id == test_user.id
    assert todo.creator.email == "test@example.com"

  def test_todo_timestamps_auto_set(
      self,
      db_session,
      test_user,
      test_household):
    """Test that created_at and updated_at are automatically set."""
    before = datetime.now(timezone.utc)
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)
    after = datetime.now(timezone.utc)

    assert todo.created_at is not None
    assert todo.updated_at is not None
    # SQLite may return naive datetime, so normalize for comparison
    created_at = todo.created_at if todo.created_at.tzinfo else todo.created_at.replace(
        tzinfo=timezone.utc)
    updated_at = todo.updated_at if todo.updated_at.tzinfo else todo.updated_at.replace(
        tzinfo=timezone.utc)
    assert before <= created_at <= after
    assert before <= updated_at <= after
    assert created_at.replace(microsecond=0) == updated_at.replace(
        microsecond=0)  # Initially same

  def test_todo_updated_at_changes_on_update(
      self,
      db_session,
      test_user,
      test_household):
    """Test that updated_at changes when todo is updated."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)

    original_updated_at = todo.updated_at
    original_created_at = todo.created_at

    # Update the todo
    import time
    time.sleep(0.01)  # Small delay to ensure timestamp difference
    todo.title = "Updated Todo"
    db_session.commit()
    db_session.refresh(todo)

    assert todo.created_at == original_created_at  # Should not change
    assert todo.updated_at > original_updated_at  # Should be updated

  def test_todo_requires_title(self, db_session, test_user, test_household):
    """Test that todo requires title."""
    todo = Todo(
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    with pytest.raises(IntegrityError):
      db_session.commit()

  def test_todo_requires_household_id(self, db_session, test_user):
    """Test that todo requires household_id."""
    todo = Todo(
        title="Test Todo",
        created_by=test_user.id,
    )
    db_session.add(todo)
    with pytest.raises(IntegrityError):
      db_session.commit()

  def test_todo_cascade_delete_from_household(
      self,
      db_session,
      test_user,
      test_household):
    """Test that todos are deleted when household is deleted."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.commit()
    todo_id = todo.id

    # Delete household
    db_session.delete(test_household)
    db_session.commit()
    db_session.expire_all()  # Expire all objects to force refresh

    # Todo should be deleted
    deleted_todo = db_session.query(Todo).filter(Todo.id == todo_id).first()
    assert deleted_todo is None

  def test_todo_set_null_on_user_delete(
      self,
      db_session,
      test_user,
      test_household):
    """Test that created_by is set to NULL when user is deleted."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.commit()
    todo_id = todo.id

    # Delete user
    db_session.delete(test_user)
    db_session.commit()
    db_session.expire_all()  # Expire all objects to force refresh

    # Todo should still exist but created_by should be NULL
    remaining_todo = db_session.query(Todo).filter(Todo.id == todo_id).first()
    assert remaining_todo is not None
    assert remaining_todo.created_by is None
