"""Unit tests for Todo visibility and assignment features."""

import pytest
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


class TestTodoVisibility:
  """Test Todo visibility field."""

  def test_visibility_defaults_to_household(
      self,
      db_session,
      test_user,
      test_household):
    """Test that visibility defaults to 'household'."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)

    assert todo.visibility == "household"

  def test_visibility_accepts_private(
      self,
      db_session,
      test_user,
      test_household):
    """Test that visibility can be set to 'private'."""
    todo = Todo(
        title="Private Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="private",
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)

    assert todo.visibility == "private"

  def test_visibility_accepts_household(
      self,
      db_session,
      test_user,
      test_household):
    """Test that visibility can be set to 'household'."""
    todo = Todo(
        title="Household Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="household",
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)

    assert todo.visibility == "household"

  def test_visibility_accepts_shared(
      self,
      db_session,
      test_user,
      test_household):
    """Test that visibility can be set to 'shared'."""
    todo = Todo(
        title="Shared Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="shared",
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)

    assert todo.visibility == "shared"


class TestTodoAssignmentViaClaim:
  """Test Todo assignment via TodoClaim (claim on behalf of others)."""

  def test_assignment_via_claim(
      self,
      db_session,
      test_user,
      test_user2,
      test_household):
    """Test that assignment is done by creating a claim on behalf of another user."""
    from app.models.todo_claim import TodoClaim

    todo = Todo(
        title="Assigned Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)

    # Create claim on behalf of user2 (assignment)
    claim = TodoClaim(
        todo_id=todo.id,
        claimed_by=test_user2.id,
    )
    db_session.add(claim)
    db_session.commit()
    db_session.refresh(todo)

    # Todo should have a claim
    assert todo.claim is not None
    assert todo.claim.claimed_by == test_user2.id
    assert todo.claim.user.id == test_user2.id

  def test_assignment_via_claim_queries(
      self,
      db_session,
      test_user,
      test_user2,
      test_household):
    """Test that assignment queries work via TodoClaim."""
    from app.models.todo_claim import TodoClaim

    todo1 = Todo(
        title="Unclaimed Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    todo2 = Todo(
        title="Assigned Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    db_session.add_all([todo1, todo2])
    db_session.commit()

    # Create claim for todo2 on behalf of user2
    claim = TodoClaim(
        todo_id=todo2.id,
        claimed_by=test_user2.id,
    )
    db_session.add(claim)
    db_session.commit()

    # Query todos claimed by user2 (assignment)
    claimed_todos = db_session.query(Todo).join(TodoClaim).filter(
        TodoClaim.claimed_by == test_user2.id).all()
    assert len(claimed_todos) == 1
    assert claimed_todos[0].title == "Assigned Todo"
