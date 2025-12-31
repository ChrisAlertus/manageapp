"""Unit tests for TodoCompletion model."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.models.todo import Todo
from app.models.todo_completion import TodoCompletion
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


@pytest.fixture
def test_todo(db_session, test_user, test_household):
  """Create a test todo."""
  todo = Todo(
      title="Test Todo",
      household_id=test_household.id,
      created_by=test_user.id,
  )
  db_session.add(todo)
  db_session.commit()
  db_session.refresh(todo)
  return todo


class TestTodoCompletionModel:
  """Test TodoCompletion model validation and relationships."""

  def test_create_todo_completion(self, db_session, test_user, test_todo):
    """Test that todo completion can be created."""
    completion = TodoCompletion(
        todo_id=test_todo.id,
        completed_by=test_user.id,
    )
    db_session.add(completion)
    db_session.commit()
    db_session.refresh(completion)

    assert completion.id is not None
    assert completion.todo_id == test_todo.id
    assert completion.completed_by == test_user.id
    assert completion.completed_at is not None

  def test_todo_completion_unique_constraint(
      self,
      db_session,
      test_user,
      test_todo):
    """Test that only one completion can exist per todo."""
    completion1 = TodoCompletion(
        todo_id=test_todo.id,
        completed_by=test_user.id,
    )
    db_session.add(completion1)
    db_session.commit()

    # Try to create another completion for the same todo
    completion2 = TodoCompletion(
        todo_id=test_todo.id,
        completed_by=test_user.id,
    )
    db_session.add(completion2)
    with pytest.raises(IntegrityError):
      db_session.commit()

  def test_todo_completion_relationship_todo(
      self,
      db_session,
      test_user,
      test_todo):
    """Test that completion has relationship to todo."""
    completion = TodoCompletion(
        todo_id=test_todo.id,
        completed_by=test_user.id,
    )
    db_session.add(completion)
    db_session.commit()
    db_session.refresh(completion)

    assert completion.todo is not None
    assert completion.todo.id == test_todo.id
    assert completion.todo.title == "Test Todo"

  def test_todo_completion_relationship_user(
      self,
      db_session,
      test_user,
      test_todo):
    """Test that completion has relationship to user."""
    completion = TodoCompletion(
        todo_id=test_todo.id,
        completed_by=test_user.id,
    )
    db_session.add(completion)
    db_session.commit()
    db_session.refresh(completion)

    assert completion.user is not None
    assert completion.user.id == test_user.id
    assert completion.user.email == "test@example.com"

  def test_todo_completion_timestamp_auto_set(
      self,
      db_session,
      test_user,
      test_todo):
    """Test that completed_at is automatically set."""
    before = datetime.now(timezone.utc)
    completion = TodoCompletion(
        todo_id=test_todo.id,
        completed_by=test_user.id,
    )
    db_session.add(completion)
    db_session.commit()
    db_session.refresh(completion)
    after = datetime.now(timezone.utc)

    assert completion.completed_at is not None
    # SQLite may return naive datetime, so normalize for comparison
    completed_at = completion.completed_at if completion.completed_at.tzinfo else completion.completed_at.replace(
        tzinfo=timezone.utc)
    assert before <= completed_at <= after

  def test_todo_completion_cascade_delete_from_todo(
      self,
      db_session,
      test_user,
      test_todo):
    """Test that completion is deleted when todo is deleted."""
    completion = TodoCompletion(
        todo_id=test_todo.id,
        completed_by=test_user.id,
    )
    db_session.add(completion)
    db_session.commit()
    completion_id = completion.id

    # Delete todo
    db_session.delete(test_todo)
    db_session.commit()

    # Completion should be deleted
    deleted_completion = db_session.query(TodoCompletion).filter(
        TodoCompletion.id == completion_id).first()
    assert deleted_completion is None

  def test_todo_completion_set_null_on_user_delete(
      self,
      db_session,
      test_user,
      test_todo):
    """Test that completed_by is set to NULL when user is deleted."""
    completion = TodoCompletion(
        todo_id=test_todo.id,
        completed_by=test_user.id,
    )
    db_session.add(completion)
    db_session.commit()
    completion_id = completion.id

    # Delete user
    db_session.delete(test_user)
    db_session.commit()
    db_session.expire_all()  # Expire all objects to force refresh

    # Completion should still exist but completed_by should be NULL
    remaining_completion = db_session.query(TodoCompletion).filter(
        TodoCompletion.id == completion_id).first()
    assert remaining_completion is not None
    assert remaining_completion.completed_by is None

  def test_todo_completion_requires_todo_id(self, db_session, test_user):
    """Test that completion requires todo_id."""
    completion = TodoCompletion(completed_by=test_user.id, )
    db_session.add(completion)
    with pytest.raises(IntegrityError):
      db_session.commit()
