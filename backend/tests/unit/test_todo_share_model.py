"""Unit tests for TodoShare model."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.models.todo import Todo
from app.models.todo_share import TodoShare
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


@pytest.fixture
def test_todo(db_session, test_user, test_household):
  """Create a test todo."""
  todo = Todo(
      title="Test Todo",
      household_id=test_household.id,
      created_by=test_user.id,
      visibility="shared",
  )
  db_session.add(todo)
  db_session.commit()
  db_session.refresh(todo)
  return todo


class TestTodoShareModel:
  """Test TodoShare model validation and relationships."""

  def test_create_todo_share(self, db_session, test_user2, test_todo):
    """Test that todo share can be created."""
    share = TodoShare(
        todo_id=test_todo.id,
        user_id=test_user2.id,
    )
    db_session.add(share)
    db_session.commit()
    db_session.refresh(share)

    assert share.id is not None
    assert share.todo_id == test_todo.id
    assert share.user_id == test_user2.id
    assert share.created_at is not None

  def test_todo_share_unique_constraint(
      self,
      db_session,
      test_user2,
      test_todo):
    """Test that only one share can exist per user per todo."""
    share1 = TodoShare(
        todo_id=test_todo.id,
        user_id=test_user2.id,
    )
    db_session.add(share1)
    db_session.commit()

    # Try to create another share for the same user and todo
    share2 = TodoShare(
        todo_id=test_todo.id,
        user_id=test_user2.id,
    )
    db_session.add(share2)
    with pytest.raises(IntegrityError):
      db_session.commit()

  def test_todo_share_allows_multiple_users(
      self,
      db_session,
      test_user,
      test_user2,
      test_todo):
    """Test that multiple users can share the same todo."""
    # Create a third user
    user3 = User(
        email="test3@example.com",
        hashed_password="hashed_password",
        full_name="Test User 3",
    )
    db_session.add(user3)
    db_session.commit()
    db_session.refresh(user3)

    share1 = TodoShare(
        todo_id=test_todo.id,
        user_id=test_user2.id,
    )
    share2 = TodoShare(
        todo_id=test_todo.id,
        user_id=user3.id,
    )
    db_session.add_all([share1, share2])
    db_session.commit()

    # Both shares should exist
    shares = db_session.query(TodoShare).filter(
        TodoShare.todo_id == test_todo.id).all()
    assert len(shares) == 2
    assert {s.user_id for s in shares} == {test_user2.id, user3.id}

  def test_todo_share_relationship_todo(
      self,
      db_session,
      test_user2,
      test_todo):
    """Test that share has relationship to todo."""
    share = TodoShare(
        todo_id=test_todo.id,
        user_id=test_user2.id,
    )
    db_session.add(share)
    db_session.commit()
    db_session.refresh(share)

    assert share.todo is not None
    assert share.todo.id == test_todo.id
    assert share.todo.title == "Test Todo"

  def test_todo_share_relationship_user(
      self,
      db_session,
      test_user2,
      test_todo):
    """Test that share has relationship to user."""
    share = TodoShare(
        todo_id=test_todo.id,
        user_id=test_user2.id,
    )
    db_session.add(share)
    db_session.commit()
    db_session.refresh(share)

    assert share.user is not None
    assert share.user.id == test_user2.id
    assert share.user.email == "test2@example.com"

  def test_todo_share_timestamp_auto_set(
      self,
      db_session,
      test_user2,
      test_todo):
    """Test that created_at is automatically set."""
    before = datetime.now(timezone.utc)
    share = TodoShare(
        todo_id=test_todo.id,
        user_id=test_user2.id,
    )
    db_session.add(share)
    db_session.commit()
    db_session.refresh(share)
    after = datetime.now(timezone.utc)

    assert share.created_at is not None
    # SQLite may return naive datetime, so normalize for comparison
    created_at = share.created_at if share.created_at.tzinfo else share.created_at.replace(
        tzinfo=timezone.utc)
    assert before <= created_at <= after

  def test_todo_share_cascade_delete_from_todo(
      self,
      db_session,
      test_user2,
      test_todo):
    """Test that share is deleted when todo is deleted."""
    share = TodoShare(
        todo_id=test_todo.id,
        user_id=test_user2.id,
    )
    db_session.add(share)
    db_session.commit()
    share_id = share.id

    # Delete todo
    db_session.delete(test_todo)
    db_session.commit()
    db_session.expire_all()  # Expire all objects to force refresh

    # Share should be deleted
    deleted_share = db_session.query(TodoShare).filter(
        TodoShare.id == share_id).first()
    assert deleted_share is None

  def test_todo_share_cascade_delete_from_user(
      self,
      db_session,
      test_user2,
      test_todo):
    """Test that share is deleted when user is deleted."""
    share = TodoShare(
        todo_id=test_todo.id,
        user_id=test_user2.id,
    )
    db_session.add(share)
    db_session.commit()
    share_id = share.id

    # Delete user
    db_session.delete(test_user2)
    db_session.commit()
    db_session.expire_all()  # Expire all objects to force refresh

    # Share should be deleted
    deleted_share = db_session.query(TodoShare).filter(
        TodoShare.id == share_id).first()
    assert deleted_share is None

  def test_todo_share_requires_todo_id(self, db_session, test_user2):
    """Test that share requires todo_id."""
    share = TodoShare(user_id=test_user2.id, )
    db_session.add(share)
    with pytest.raises(IntegrityError):
      db_session.commit()

  def test_todo_share_requires_user_id(self, db_session, test_todo):
    """Test that share requires user_id."""
    share = TodoShare(todo_id=test_todo.id, )
    db_session.add(share)
    with pytest.raises(IntegrityError):
      db_session.commit()

  def test_todo_shares_relationship(self, db_session, test_user2, test_todo):
    """Test that todo can access its shares."""
    share = TodoShare(
        todo_id=test_todo.id,
        user_id=test_user2.id,
    )
    db_session.add(share)
    db_session.commit()
    db_session.refresh(test_todo)

    assert test_todo.shares is not None
    assert len(test_todo.shares) == 1
    assert test_todo.shares[0].id == share.id
    assert test_todo.shares[0].user_id == test_user2.id
