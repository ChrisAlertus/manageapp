"""Integration tests for todo models database schema and relationships."""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.core.database import Base
from app.models.todo import Todo
from app.models.todo_claim import TodoClaim
from app.models.todo_completion import TodoCompletion
from app.models.household import Household
from app.models.user import User


@pytest.fixture
def test_db():
  """Create an in-memory SQLite database for testing."""
  from sqlalchemy import event
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
def test_todo(test_db, test_user, test_household):
  """Create a test todo."""
  todo = Todo(
      title="Test Todo",
      household_id=test_household.id,
      created_by=test_user.id,
  )
  test_db.add(todo)
  test_db.commit()
  test_db.refresh(todo)
  return todo


class TestTodoModelsSchema:
  """Test database schema creation for todo models."""

  def test_todos_table_exists(self, test_db):
    """Test that todos table is created."""
    inspector = inspect(test_db.bind)
    tables = inspector.get_table_names()
    assert "todos" in tables

  def test_todo_claims_table_exists(self, test_db):
    """Test that todo_claims table is created."""
    inspector = inspect(test_db.bind)
    tables = inspector.get_table_names()
    assert "todo_claims" in tables

  def test_todo_completions_table_exists(self, test_db):
    """Test that todo_completions table is created."""
    inspector = inspect(test_db.bind)
    tables = inspector.get_table_names()
    assert "todo_completions" in tables

  def test_todos_table_columns(self, test_db):
    """Test that todos table has all required columns."""
    inspector = inspect(test_db.bind)
    columns = [col["name"] for col in inspector.get_columns("todos")]
    expected_columns = [
        "id",
        "title",
        "description",
        "household_id",
        "created_by",
        "priority",
        "due_date",
        "category",
        "created_at",
        "updated_at",
    ]
    for col in expected_columns:
      assert col in columns

  def test_todo_claims_table_columns(self, test_db):
    """Test that todo_claims table has all required columns."""
    inspector = inspect(test_db.bind)
    columns = [col["name"] for col in inspector.get_columns("todo_claims")]
    expected_columns = ["id", "todo_id", "claimed_by", "claimed_at"]
    for col in expected_columns:
      assert col in columns

  def test_todo_completions_table_columns(self, test_db):
    """Test that todo_completions table has all required columns."""
    inspector = inspect(test_db.bind)
    columns = [col["name"] for col in inspector.get_columns("todo_completions")]
    expected_columns = ["id", "todo_id", "completed_by", "completed_at"]
    for col in expected_columns:
      assert col in columns

  def test_todos_indexes_created(self, test_db):
    """Test that todos table has required indexes."""
    inspector = inspect(test_db.bind)
    indexes = [idx["name"] for idx in inspector.get_indexes("todos")]
    expected_indexes = [
        "ix_todos_id",
        "ix_todos_household_id",
        "ix_todos_created_by",
        "ix_todos_priority",
        "ix_todos_due_date",
        "ix_todos_category",
        "ix_todos_household_priority",
    ]
    for idx in expected_indexes:
      assert idx in indexes

  def test_todo_claims_indexes_created(self, test_db):
    """Test that todo_claims table has required indexes."""
    inspector = inspect(test_db.bind)
    indexes = [idx["name"] for idx in inspector.get_indexes("todo_claims")]
    expected_indexes = [
        "ix_todo_claims_id",
        "ix_todo_claims_todo_id",
        "ix_todo_claims_claimed_by"
    ]
    for idx in expected_indexes:
      assert idx in indexes

  def test_todo_completions_indexes_created(self, test_db):
    """Test that todo_completions table has required indexes."""
    inspector = inspect(test_db.bind)
    indexes = [idx["name"] for idx in inspector.get_indexes("todo_completions")]
    expected_indexes = [
        "ix_todo_completions_id",
        "ix_todo_completions_todo_id",
        "ix_todo_completions_completed_by",
    ]
    for idx in expected_indexes:
      assert idx in indexes


class TestTodoModelsForeignKeys:
  """Test foreign key constraints for todo models."""

  def test_todo_foreign_key_to_household(
      self,
      test_db,
      test_user,
      test_household):
    """Test that todo has foreign key to household."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    test_db.add(todo)
    test_db.commit()
    test_db.refresh(todo)

    assert todo.household_id == test_household.id
    assert todo.household is not None
    assert todo.household.id == test_household.id

  def test_todo_foreign_key_to_user(self, test_db, test_user, test_household):
    """Test that todo has foreign key to user."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    test_db.add(todo)
    test_db.commit()
    test_db.refresh(todo)

    assert todo.created_by == test_user.id
    assert todo.creator is not None
    assert todo.creator.id == test_user.id

  def test_todo_cascade_delete_from_household(
      self,
      test_db,
      test_user,
      test_household):
    """Test that todos are deleted when household is deleted (CASCADE)."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    test_db.add(todo)
    test_db.commit()
    todo_id = todo.id

    # Delete household
    test_db.delete(test_household)
    test_db.commit()
    test_db.expire_all()  # Expire all objects to force refresh

    # Todo should be deleted
    deleted_todo = test_db.query(Todo).filter(Todo.id == todo_id).first()
    assert deleted_todo is None

  def test_todo_set_null_on_user_delete(
      self,
      test_db,
      test_user,
      test_household):
    """Test that created_by is set to NULL when user is deleted (SET NULL)."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    test_db.add(todo)
    test_db.commit()
    todo_id = todo.id

    # Delete user
    test_db.delete(test_user)
    test_db.commit()
    test_db.expire_all()  # Expire all objects to force refresh

    # Todo should still exist but created_by should be NULL
    remaining_todo = test_db.query(Todo).filter(Todo.id == todo_id).first()
    assert remaining_todo is not None
    assert remaining_todo.created_by is None

  def test_todo_claim_foreign_key_to_todo(self, test_db, test_user, test_todo):
    """Test that todo_claim has foreign key to todo."""
    claim = TodoClaim(
        todo_id=test_todo.id,
        claimed_by=test_user.id,
    )
    test_db.add(claim)
    test_db.commit()
    test_db.refresh(claim)

    assert claim.todo_id == test_todo.id
    assert claim.todo is not None
    assert claim.todo.id == test_todo.id

  def test_todo_claim_cascade_delete_from_todo(
      self,
      test_db,
      test_user,
      test_todo):
    """Test that claim is deleted when todo is deleted (CASCADE)."""
    claim = TodoClaim(
        todo_id=test_todo.id,
        claimed_by=test_user.id,
    )
    test_db.add(claim)
    test_db.commit()
    claim_id = claim.id

    # Delete todo
    test_db.delete(test_todo)
    test_db.commit()
    test_db.expire_all()  # Expire all objects to force refresh

    # Claim should be deleted
    deleted_claim = test_db.query(TodoClaim).filter(
        TodoClaim.id == claim_id).first()
    assert deleted_claim is None

  def test_todo_completion_foreign_key_to_todo(
      self,
      test_db,
      test_user,
      test_todo):
    """Test that todo_completion has foreign key to todo."""
    completion = TodoCompletion(
        todo_id=test_todo.id,
        completed_by=test_user.id,
    )
    test_db.add(completion)
    test_db.commit()
    test_db.refresh(completion)

    assert completion.todo_id == test_todo.id
    assert completion.todo is not None
    assert completion.todo.id == test_todo.id

  def test_todo_completion_cascade_delete_from_todo(
      self,
      test_db,
      test_user,
      test_todo):
    """Test that completion is deleted when todo is deleted (CASCADE)."""
    completion = TodoCompletion(
        todo_id=test_todo.id,
        completed_by=test_user.id,
    )
    test_db.add(completion)
    test_db.commit()
    completion_id = completion.id

    # Delete todo
    test_db.delete(test_todo)
    test_db.commit()
    test_db.expire_all()  # Expire all objects to force refresh

    # Completion should be deleted
    deleted_completion = test_db.query(TodoCompletion).filter(
        TodoCompletion.id == completion_id).first()
    assert deleted_completion is None


class TestTodoModelsUniqueConstraints:
  """Test unique constraints for todo models."""

  def test_todo_claim_unique_todo_id(self, test_db, test_user, test_todo):
    """Test that only one claim can exist per todo."""
    claim1 = TodoClaim(
        todo_id=test_todo.id,
        claimed_by=test_user.id,
    )
    test_db.add(claim1)
    test_db.commit()

    # Try to create another claim for the same todo
    claim2 = TodoClaim(
        todo_id=test_todo.id,
        claimed_by=test_user.id,
    )
    test_db.add(claim2)
    with pytest.raises(IntegrityError):
      test_db.commit()

  def test_todo_completion_unique_todo_id(self, test_db, test_user, test_todo):
    """Test that only one completion can exist per todo."""
    completion1 = TodoCompletion(
        todo_id=test_todo.id,
        completed_by=test_user.id,
    )
    test_db.add(completion1)
    test_db.commit()

    # Try to create another completion for the same todo
    completion2 = TodoCompletion(
        todo_id=test_todo.id,
        completed_by=test_user.id,
    )
    test_db.add(completion2)
    with pytest.raises(IntegrityError):
      test_db.commit()


class TestTodoModelsRelationships:
  """Test relationships between todo models."""

  def test_todo_claim_relationship(self, test_db, test_user, test_todo):
    """Test that todo can access its claim."""
    claim = TodoClaim(
        todo_id=test_todo.id,
        claimed_by=test_user.id,
    )
    test_db.add(claim)
    test_db.commit()
    test_db.refresh(test_todo)

    assert test_todo.claim is not None
    assert test_todo.claim.id == claim.id
    assert test_todo.claim.todo_id == test_todo.id

  def test_todo_completion_relationship(self, test_db, test_user, test_todo):
    """Test that todo can access its completion."""
    completion = TodoCompletion(
        todo_id=test_todo.id,
        completed_by=test_user.id,
    )
    test_db.add(completion)
    test_db.commit()
    test_db.refresh(test_todo)

    assert test_todo.completion is not None
    assert test_todo.completion.id == completion.id
    assert test_todo.completion.todo_id == test_todo.id

  def test_todo_claim_user_relationship(self, test_db, test_user, test_todo):
    """Test that claim can access its user."""
    claim = TodoClaim(
        todo_id=test_todo.id,
        claimed_by=test_user.id,
    )
    test_db.add(claim)
    test_db.commit()
    test_db.refresh(claim)

    assert claim.user is not None
    assert claim.user.id == test_user.id
    assert claim.user.email == "test@example.com"

  def test_todo_completion_user_relationship(
      self,
      test_db,
      test_user,
      test_todo):
    """Test that completion can access its user."""
    completion = TodoCompletion(
        todo_id=test_todo.id,
        completed_by=test_user.id,
    )
    test_db.add(completion)
    test_db.commit()
    test_db.refresh(completion)

    assert completion.user is not None
    assert completion.user.id == test_user.id
    assert completion.user.email == "test@example.com"

  def test_multiple_todos_same_household(
      self,
      test_db,
      test_user,
      test_household):
    """Test that multiple todos can exist for the same household."""
    todo1 = Todo(
        title="Todo 1",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    todo2 = Todo(
        title="Todo 2",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    test_db.add(todo1)
    test_db.add(todo2)
    test_db.commit()

    todos = test_db.query(Todo).filter(
        Todo.household_id == test_household.id).all()
    assert len(todos) == 2
    assert {t.title for t in todos} == {"Todo 1", "Todo 2"}
