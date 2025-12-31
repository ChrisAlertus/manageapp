"""Unit tests for TodoClaim model."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.models.todo import Todo
from app.models.todo_claim import TodoClaim
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


class TestTodoClaimModel:
  """Test TodoClaim model validation and relationships."""

  def test_create_todo_claim(self, db_session, test_user, test_todo):
    """Test that todo claim can be created."""
    claim = TodoClaim(
        todo_id=test_todo.id,
        claimed_by=test_user.id,
    )
    db_session.add(claim)
    db_session.commit()
    db_session.refresh(claim)

    assert claim.id is not None
    assert claim.todo_id == test_todo.id
    assert claim.claimed_by == test_user.id
    assert claim.claimed_at is not None

  def test_todo_claim_unique_constraint(self, db_session, test_user, test_todo):
    """Test that only one claim can exist per todo."""
    claim1 = TodoClaim(
        todo_id=test_todo.id,
        claimed_by=test_user.id,
    )
    db_session.add(claim1)
    db_session.commit()

    # Try to create another claim for the same todo
    claim2 = TodoClaim(
        todo_id=test_todo.id,
        claimed_by=test_user.id,
    )
    db_session.add(claim2)
    with pytest.raises(IntegrityError):
      db_session.commit()

  def test_todo_claim_relationship_todo(self, db_session, test_user, test_todo):
    """Test that claim has relationship to todo."""
    claim = TodoClaim(
        todo_id=test_todo.id,
        claimed_by=test_user.id,
    )
    db_session.add(claim)
    db_session.commit()
    db_session.refresh(claim)

    assert claim.todo is not None
    assert claim.todo.id == test_todo.id
    assert claim.todo.title == "Test Todo"

  def test_todo_claim_relationship_user(self, db_session, test_user, test_todo):
    """Test that claim has relationship to user."""
    claim = TodoClaim(
        todo_id=test_todo.id,
        claimed_by=test_user.id,
    )
    db_session.add(claim)
    db_session.commit()
    db_session.refresh(claim)

    assert claim.user is not None
    assert claim.user.id == test_user.id
    assert claim.user.email == "test@example.com"

  def test_todo_claim_timestamp_auto_set(
      self,
      db_session,
      test_user,
      test_todo):
    """Test that claimed_at is automatically set."""
    before = datetime.now(timezone.utc)
    claim = TodoClaim(
        todo_id=test_todo.id,
        claimed_by=test_user.id,
    )
    db_session.add(claim)
    db_session.commit()
    db_session.refresh(claim)
    after = datetime.now(timezone.utc)

    assert claim.claimed_at is not None
    # SQLite may return naive datetime, so normalize for comparison
    claimed_at = claim.claimed_at if claim.claimed_at.tzinfo else claim.claimed_at.replace(
        tzinfo=timezone.utc)
    assert before <= claimed_at <= after

  def test_todo_claim_cascade_delete_from_todo(
      self,
      db_session,
      test_user,
      test_todo):
    """Test that claim is deleted when todo is deleted."""
    claim = TodoClaim(
        todo_id=test_todo.id,
        claimed_by=test_user.id,
    )
    db_session.add(claim)
    db_session.commit()
    claim_id = claim.id

    # Delete todo
    db_session.delete(test_todo)
    db_session.commit()

    # Claim should be deleted
    deleted_claim = db_session.query(TodoClaim).filter(
        TodoClaim.id == claim_id).first()
    assert deleted_claim is None

  def test_todo_claim_set_null_on_user_delete(
      self,
      db_session,
      test_user,
      test_todo):
    """Test that claimed_by is set to NULL when user is deleted."""
    claim = TodoClaim(
        todo_id=test_todo.id,
        claimed_by=test_user.id,
    )
    db_session.add(claim)
    db_session.commit()
    claim_id = claim.id

    # Delete user
    db_session.delete(test_user)
    db_session.commit()
    db_session.expire_all()  # Expire all objects to force refresh

    # Claim should still exist but claimed_by should be NULL
    remaining_claim = db_session.query(TodoClaim).filter(
        TodoClaim.id == claim_id).first()
    assert remaining_claim is not None
    assert remaining_claim.claimed_by is None

  def test_todo_claim_requires_todo_id(self, db_session, test_user):
    """Test that claim requires todo_id."""
    claim = TodoClaim(claimed_by=test_user.id, )
    db_session.add(claim)
    with pytest.raises(IntegrityError):
      db_session.commit()
