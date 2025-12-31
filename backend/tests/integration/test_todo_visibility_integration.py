"""Integration tests for todo visibility and assignment features."""

import pytest
from sqlalchemy import create_engine, inspect, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.core.database import Base
from app.models.todo import Todo
from app.models.todo_claim import TodoClaim
from app.models.todo_share import TodoShare
from app.models.household import Household
from app.models.household_member import HouseholdMember
from app.models.user import User


@pytest.fixture
def test_db():
  """Create an in-memory SQLite database for testing."""
  from sqlalchemy.pool import StaticPool

  engine = create_engine(
      "sqlite:///:memory:",
      connect_args={"check_same_thread": False},
      poolclass=StaticPool,
      echo=False,
  )

  # Enable foreign key constraints for SQLite
  @event.listens_for(engine, "connect")
  def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

  Base.metadata.create_all(engine)
  TestingSessionLocal = sessionmaker(
      autocommit=False,
      autoflush=False,
      bind=engine)

  session = TestingSessionLocal()
  try:
    yield session
  finally:
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_user(test_db):
  """Create a test user."""
  user = User(
      email="test@example.com",
      hashed_password="hashed_password",
      full_name="Test User",
  )
  test_db.add(user)
  test_db.commit()
  test_db.refresh(user)
  return user


@pytest.fixture
def test_user2(test_db):
  """Create a second test user."""
  user = User(
      email="test2@example.com",
      hashed_password="hashed_password",
      full_name="Test User 2",
  )
  test_db.add(user)
  test_db.commit()
  test_db.refresh(user)
  return user


@pytest.fixture
def test_user3(test_db):
  """Create a third test user."""
  user = User(
      email="test3@example.com",
      hashed_password="hashed_password",
      full_name="Test User 3",
  )
  test_db.add(user)
  test_db.commit()
  test_db.refresh(user)
  return user


@pytest.fixture
def test_household(test_db, test_user):
  """Create a test household."""
  household = Household(
      name="Test Household",
      description="A test household",
      created_by=test_user.id,
  )
  test_db.add(household)
  test_db.commit()
  test_db.refresh(household)
  return household


@pytest.fixture
def test_household_members(
    test_db,
    test_user,
    test_user2,
    test_user3,
    test_household):
  """Create household members."""
  member1 = HouseholdMember(
      household_id=test_household.id,
      user_id=test_user.id,
      role="owner",
  )
  member2 = HouseholdMember(
      household_id=test_household.id,
      user_id=test_user2.id,
      role="member",
  )
  member3 = HouseholdMember(
      household_id=test_household.id,
      user_id=test_user3.id,
      role="member",
  )
  test_db.add_all([member1, member2, member3])
  test_db.commit()
  return [member1, member2, member3]


class TestTodoVisibilitySchema:
  """Test database schema for visibility and assignment."""

  def test_visibility_column_exists(self, test_db):
    """Test that visibility column exists in todos table."""
    inspector = inspect(test_db.bind)
    columns = [col["name"] for col in inspector.get_columns("todos")]
    assert "visibility" in columns

  def test_todo_shares_table_exists(self, test_db):
    """Test that todo_shares table exists."""
    inspector = inspect(test_db.bind)
    tables = inspector.get_table_names()
    assert "todo_shares" in tables

  def test_todo_shares_table_columns(self, test_db):
    """Test that todo_shares table has all required columns."""
    inspector = inspect(test_db.bind)
    columns = [col["name"] for col in inspector.get_columns("todo_shares")]
    expected_columns = ["id", "todo_id", "user_id", "created_at"]
    for col in expected_columns:
      assert col in columns

  def test_visibility_index_exists(self, test_db):
    """Test that visibility index exists."""
    inspector = inspect(test_db.bind)
    indexes = [idx["name"] for idx in inspector.get_indexes("todos")]
    assert "ix_todos_visibility" in indexes

  def test_todo_shares_indexes_exist(self, test_db):
    """Test that todo_shares table has required indexes."""
    inspector = inspect(test_db.bind)
    indexes = [idx["name"] for idx in inspector.get_indexes("todo_shares")]
    expected_indexes = [
        "ix_todo_shares_id",
        "ix_todo_shares_todo_id",
        "ix_todo_shares_user_id",
        "ix_todo_shares_todo_user",
    ]
    for idx in expected_indexes:
      assert idx in indexes


class TestTodoVisibilityForeignKeys:
  """Test foreign key constraints for visibility."""

  def test_todo_share_foreign_key_to_todo(
      self,
      test_db,
      test_user,
      test_user2,
      test_household):
    """Test that todo_share has foreign key to todo."""
    todo = Todo(
        title="Shared Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="shared",
    )
    test_db.add(todo)
    test_db.commit()
    test_db.refresh(todo)

    share = TodoShare(
        todo_id=todo.id,
        user_id=test_user2.id,
    )
    test_db.add(share)
    test_db.commit()
    test_db.refresh(share)

    assert share.todo_id == todo.id
    assert share.todo is not None
    assert share.todo.id == todo.id

  def test_todo_share_foreign_key_to_user(
      self,
      test_db,
      test_user,
      test_user2,
      test_household):
    """Test that todo_share has foreign key to user."""
    todo = Todo(
        title="Shared Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="shared",
    )
    test_db.add(todo)
    test_db.commit()

    share = TodoShare(
        todo_id=todo.id,
        user_id=test_user2.id,
    )
    test_db.add(share)
    test_db.commit()
    test_db.refresh(share)

    assert share.user_id == test_user2.id
    assert share.user is not None
    assert share.user.id == test_user2.id

  def test_todo_share_cascade_delete_from_todo(
      self,
      test_db,
      test_user,
      test_user2,
      test_household):
    """Test that share is deleted when todo is deleted."""
    todo = Todo(
        title="Shared Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="shared",
    )
    test_db.add(todo)
    test_db.commit()

    share = TodoShare(
        todo_id=todo.id,
        user_id=test_user2.id,
    )
    test_db.add(share)
    test_db.commit()
    share_id = share.id

    # Delete todo
    test_db.delete(todo)
    test_db.commit()
    test_db.expire_all()  # Expire all objects to force refresh

    # Share should be deleted
    deleted_share = test_db.query(TodoShare).filter(
        TodoShare.id == share_id).first()
    assert deleted_share is None

  def test_todo_share_cascade_delete_from_user(
      self,
      test_db,
      test_user,
      test_user2,
      test_household):
    """Test that share is deleted when user is deleted."""
    todo = Todo(
        title="Shared Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="shared",
    )
    test_db.add(todo)
    test_db.commit()

    share = TodoShare(
        todo_id=todo.id,
        user_id=test_user2.id,
    )
    test_db.add(share)
    test_db.commit()
    share_id = share.id

    # Delete user
    test_db.delete(test_user2)
    test_db.commit()
    test_db.expire_all()  # Expire all objects to force refresh

    # Share should be deleted
    deleted_share = test_db.query(TodoShare).filter(
        TodoShare.id == share_id).first()
    assert deleted_share is None


class TestTodoVisibilityUniqueConstraints:
  """Test unique constraints for visibility features."""

  def test_todo_share_unique_constraint(
      self,
      test_db,
      test_user,
      test_user2,
      test_household):
    """Test that only one share can exist per user per todo."""
    todo = Todo(
        title="Shared Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="shared",
    )
    test_db.add(todo)
    test_db.commit()

    share1 = TodoShare(
        todo_id=todo.id,
        user_id=test_user2.id,
    )
    test_db.add(share1)
    test_db.commit()

    # Try to create another share for the same user and todo
    share2 = TodoShare(
        todo_id=todo.id,
        user_id=test_user2.id,
    )
    test_db.add(share2)
    with pytest.raises(IntegrityError):
      test_db.commit()


class TestTodoVisibilityFiltering:
  """Test visibility filtering logic."""

  def test_private_todo_only_visible_to_creator(
      self,
      test_db,
      test_user,
      test_user2,
      test_household,
      test_household_members):
    """Test that private todos are only visible to creator."""
    todo = Todo(
        title="Private Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="private",
    )
    test_db.add(todo)
    test_db.commit()

    # Creator should be able to see it
    creator_todos = test_db.query(Todo).filter(
        Todo.created_by == test_user.id,
        Todo.visibility == "private").all()
    assert len(creator_todos) == 1
    assert creator_todos[0].title == "Private Todo"

    # Other household members should not see it in household queries
    # (This will be enforced in API layer, but we test the data model here)
    household_todos = test_db.query(Todo).filter(
        Todo.household_id == test_household.id,
        Todo.visibility == "household").all()
    assert len(household_todos) == 0

  def test_household_todo_visible_to_all_members(
      self,
      test_db,
      test_user,
      test_user2,
      test_household,
      test_household_members):
    """Test that household todos are visible to all household members."""
    todo = Todo(
        title="Household Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="household",
    )
    test_db.add(todo)
    test_db.commit()

    # All household members should be able to see it
    household_todos = test_db.query(Todo).filter(
        Todo.household_id == test_household.id,
        Todo.visibility == "household").all()
    assert len(household_todos) == 1
    assert household_todos[0].title == "Household Todo"

  def test_shared_todo_visible_only_to_shared_users(
      self,
      test_db,
      test_user,
      test_user2,
      test_user3,
      test_household,
      test_household_members):
    """Test that shared todos are visible only to users in TodoShare."""
    todo = Todo(
        title="Shared Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="shared",
    )
    test_db.add(todo)
    test_db.commit()

    # Share with user2 only
    share = TodoShare(
        todo_id=todo.id,
        user_id=test_user2.id,
    )
    test_db.add(share)
    test_db.commit()

    # Query todos shared with user2
    shared_todos = test_db.query(Todo).join(TodoShare).filter(
        TodoShare.user_id == test_user2.id).all()
    assert len(shared_todos) == 1
    assert shared_todos[0].title == "Shared Todo"

    # Query todos shared with user3 (should be empty)
    shared_todos_user3 = test_db.query(Todo).join(TodoShare).filter(
        TodoShare.user_id == test_user3.id).all()
    assert len(shared_todos_user3) == 0

  def test_assignment_queries_via_claim(
      self,
      test_db,
      test_user,
      test_user2,
      test_household):
    """Test that assignment queries work via TodoClaim."""
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
    test_db.add_all([todo1, todo2])
    test_db.commit()

    # Create claim for todo2 on behalf of user2 (assignment)
    claim = TodoClaim(
        todo_id=todo2.id,
        claimed_by=test_user2.id,
    )
    test_db.add(claim)
    test_db.commit()

    # Query todos claimed by user2 (assignment)
    claimed_todos = test_db.query(Todo).join(TodoClaim).filter(
        TodoClaim.claimed_by == test_user2.id).all()
    assert len(claimed_todos) == 1
    assert claimed_todos[0].title == "Assigned Todo"

    # Query unclaimed todos
    unclaimed_todos = test_db.query(Todo).outerjoin(TodoClaim).filter(
        TodoClaim.id.is_(None)).all()
    assert len(unclaimed_todos) == 1
    assert unclaimed_todos[0].title == "Unclaimed Todo"
