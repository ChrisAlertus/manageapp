"""Integration tests for todo API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.household import Household
from app.models.household_member import HouseholdMember
from app.models.user import User
from app.models.todo import Todo
from app.models.todo_claim import TodoClaim
from app.models.todo_completion import TodoCompletion
from app.models.todo_share import TodoShare


@pytest.fixture
def test_db():
  """Create an in-memory SQLite database for testing."""
  from sqlalchemy.pool import StaticPool

  # Use StaticPool to ensure all connections share the same in-memory database
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

  def override_get_db():
    db = TestingSessionLocal()
    try:
      yield db
    finally:
      db.close()

  app.dependency_overrides[get_db] = override_get_db

  # Create a session for test data setup
  session = TestingSessionLocal()
  try:
    yield session
  finally:
    session.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_user(test_db):
  """Create a test user."""
  from app.core.security import get_password_hash

  user = User(
      email="test@example.com",
      hashed_password=get_password_hash("TestPass123!"),
      full_name="Test User",
  )
  test_db.add(user)
  test_db.flush()
  test_db.commit()
  test_db.refresh(user)
  return user


@pytest.fixture
def test_user2(test_db):
  """Create a second test user."""
  from app.core.security import get_password_hash

  user = User(
      email="test2@example.com",
      hashed_password=get_password_hash("TestPass123!"),
      full_name="Test User 2",
  )
  test_db.add(user)
  test_db.flush()
  test_db.commit()
  test_db.refresh(user)
  return user


@pytest.fixture
def test_user3(test_db):
  """Create a third test user."""
  from app.core.security import get_password_hash

  user = User(
      email="test3@example.com",
      hashed_password=get_password_hash("TestPass123!"),
      full_name="Test User 3",
  )
  test_db.add(user)
  test_db.flush()
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
  test_db.flush()

  member = HouseholdMember(
      household_id=household.id,
      user_id=test_user.id,
      role="owner",
  )
  test_db.add(member)
  test_db.commit()
  test_db.refresh(household)
  return household


@pytest.fixture
def test_household_with_members(test_db, test_user, test_user2, test_user3):
  """Create a test household with multiple members."""
  household = Household(
      name="Test Household",
      description="A test household",
      created_by=test_user.id,
  )
  test_db.add(household)
  test_db.flush()

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
  test_db.add(member1)
  test_db.add(member2)
  test_db.add(member3)
  test_db.commit()
  test_db.refresh(household)
  return household


@pytest.fixture
def auth_token(test_user):
  """Create an auth token for test user."""
  return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def auth_token2(test_user2):
  """Create an auth token for test user 2."""
  return create_access_token(data={"sub": str(test_user2.id)})


@pytest.fixture
def auth_token3(test_user3):
  """Create an auth token for test user 3."""
  return create_access_token(data={"sub": str(test_user3.id)})


@pytest.fixture
def client():
  """Create a test client."""
  return TestClient(app)


class TestCreateTodo:
  """Test todo creation endpoint."""

  def test_create_todo_success(
      self,
      client,
      test_db,
      test_user,
      test_household,
      auth_token):
    """Test successful todo creation."""
    response = client.post(
        f"/api/v1/households/{test_household.id}/todos",
        json={
            "title": "Test Todo",
            "description": "Test description",
            "priority": "medium",
            "visibility": "household",
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["description"] == "Test description"
    assert data["priority"] == "medium"
    assert data["visibility"] == "household"
    assert data["household_id"] == test_household.id
    assert data["created_by"] == test_user.id

  def test_create_todo_shared_visibility_with_shares(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      test_household,
      auth_token):
    """Test creating a todo with shared visibility and shared users."""
    response = client.post(
        f"/api/v1/households/{test_household.id}/todos",
        json={
            "title": "Shared Todo",
            "visibility": "shared",
            "shared_user_ids": [test_user2.id],
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["visibility"] == "shared"
    assert len(data["shares"]) == 1
    assert data["shares"][0]["user_id"] == test_user2.id

  def test_create_todo_shared_visibility_no_shares_returns_400(
      self,
      client,
      test_db,
      test_user,
      test_household,
      auth_token):
    """Test that creating shared todo without shared_user_ids returns 400."""
    response = client.post(
        f"/api/v1/households/{test_household.id}/todos",
        json={
            "title": "Shared Todo",
            "visibility": "shared",
            "shared_user_ids": [],
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 400

  def test_create_todo_requires_auth(self, client, test_household):
    """Test that todo creation requires authentication."""
    response = client.post(
        f"/api/v1/households/{test_household.id}/todos",
        json={"title": "Test Todo"},
    )

    assert response.status_code == 401


class TestListTodos:
  """Test todo listing endpoint."""

  def test_list_todos_returns_visible_todos(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      test_household_with_members,
      auth_token,
      auth_token2):
    """Test that list endpoint returns only visible todos."""
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
    test_db.add_all([todo1, todo2, todo3])
    test_db.flush()

    share = TodoShare(todo_id=todo3.id, user_id=test_user2.id)
    test_db.add(share)
    test_db.commit()

    # test_user2 should see household and shared todos, but not private
    response = client.get(
        f"/api/v1/households/{test_household_with_members.id}/todos",
        headers={"Authorization": f"Bearer {auth_token2}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    titles = [t["title"] for t in data]
    assert "Household Todo" in titles
    assert "Shared Todo" in titles
    assert "Private Todo" not in titles

  def test_list_todos_with_filters(
      self,
      client,
      test_db,
      test_user,
      test_household,
      auth_token):
    """Test listing todos with filters."""

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
    test_db.add_all([todo1, todo2])
    test_db.commit()

    response = client.get(
        f"/api/v1/households/{test_household.id}/todos",
        params={"priority": "urgent"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Urgent Todo"


class TestGetTodo:
  """Test get todo endpoint."""

  def test_get_todo_success(
      self,
      client,
      test_db,
      test_user,
      test_household,
      auth_token):
    """Test successful todo retrieval."""

    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    test_db.add(todo)
    test_db.commit()

    response = client.get(
        f"/api/v1/households/{test_household.id}/todos/{todo.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Todo"

  def test_get_todo_not_found_returns_404(
      self,
      client,
      test_user,
      test_household,
      auth_token):
    """Test that getting non-existent todo returns 404."""
    response = client.get(
        f"/api/v1/households/{test_household.id}/todos/999",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 404

  def test_get_todo_private_not_visible_returns_403(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      test_household_with_members,
      auth_token2):
    """Test that getting private todo as non-creator returns 403."""

    todo = Todo(
        title="Private Todo",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
        visibility="private",
    )
    test_db.add(todo)
    test_db.commit()

    response = client.get(
        f"/api/v1/households/{test_household_with_members.id}/todos/{todo.id}",
        headers={"Authorization": f"Bearer {auth_token2}"},
    )

    assert response.status_code == 403


class TestUpdateTodo:
  """Test update todo endpoint."""

  def test_update_todo_success(
      self,
      client,
      test_db,
      test_user,
      test_household,
      auth_token):
    """Test successful todo update."""

    todo = Todo(
        title="Original Title",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    test_db.add(todo)
    test_db.commit()

    response = client.patch(
        f"/api/v1/households/{test_household.id}/todos/{todo.id}",
        json={"title": "Updated Title"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"

  def test_update_todo_not_creator_returns_403(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      test_household_with_members,
      auth_token2):
    """Test that updating todo as non-creator returns 403."""

    todo = Todo(
        title="Original Title",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
    )
    test_db.add(todo)
    test_db.commit()

    response = client.patch(
        f"/api/v1/households/{test_household_with_members.id}/todos/{todo.id}",
        json={"title": "Updated Title"},
        headers={"Authorization": f"Bearer {auth_token2}"},
    )

    assert response.status_code == 403


class TestDeleteTodo:
  """Test delete todo endpoint."""

  def test_delete_todo_success(
      self,
      client,
      test_db,
      test_user,
      test_household,
      auth_token):
    """Test successful todo deletion."""

    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    test_db.add(todo)
    test_db.commit()

    response = client.delete(
        f"/api/v1/households/{test_household.id}/todos/{todo.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 204

    # Verify todo was deleted
    todo_check = test_db.query(Todo).filter(Todo.id == todo.id).first()
    assert todo_check is None

  def test_delete_todo_not_creator_returns_403(
      self,
      client,
      test_db,
      test_user,
      test_household_with_members,
      auth_token2):
    """Test that deleting todo as non-creator returns 403."""

    todo = Todo(
        title="Test Todo",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
    )
    test_db.add(todo)
    test_db.commit()

    response = client.delete(
        f"/api/v1/households/{test_household_with_members.id}/todos/{todo.id}",
        headers={"Authorization": f"Bearer {auth_token2}"},
    )

    assert response.status_code == 403


class TestClaimTodo:
  """Test claim management endpoints."""

  def test_claim_todo_self_claim(
      self,
      client,
      test_db,
      test_user,
      test_household,
      auth_token):
    """Test self-claiming a todo."""

    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    test_db.add(todo)
    test_db.commit()

    response = client.post(
        f"/api/v1/households/{test_household.id}/todos/{todo.id}/claim",
        json={},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["claim"] is not None
    assert data["claim"]["claimed_by"] == test_user.id

  def test_claim_todo_for_others(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      test_household_with_members,
      auth_token):
    """Test claiming a todo for another user."""

    todo = Todo(
        title="Test Todo",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
        visibility="household",
    )
    test_db.add(todo)
    test_db.commit()

    response = client.post(
        f"/api/v1/households/{test_household_with_members.id}/todos/{todo.id}/claim",
        json={"user_id": test_user2.id},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["claim"] is not None
    assert data["claim"]["claimed_by"] == test_user2.id

  def test_unclaim_todo_success(
      self,
      client,
      test_db,
      test_user,
      test_household,
      auth_token):
    """Test successful todo unclaim."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    test_db.add(todo)
    test_db.flush()

    claim = TodoClaim(todo_id=todo.id, claimed_by=test_user.id)
    test_db.add(claim)
    test_db.commit()

    response = client.delete(
        f"/api/v1/households/{test_household.id}/todos/{todo.id}/claim",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 204

    # Verify claim was removed
    claim_check = (
        test_db.query(TodoClaim).filter(TodoClaim.todo_id == todo.id).first())
    assert claim_check is None

  def test_unclaim_todo_not_claimer_returns_403(
      self,
      client,
      test_db,
      test_user,
      test_household_with_members,
      auth_token2):
    """Test that unclaiming a todo as non-claimer returns 403."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
    )
    test_db.add(todo)
    test_db.flush()

    claim = TodoClaim(todo_id=todo.id, claimed_by=test_user.id)
    test_db.add(claim)
    test_db.commit()

    response = client.delete(
        f"/api/v1/households/{test_household_with_members.id}/todos/{todo.id}/claim",
        headers={"Authorization": f"Bearer {auth_token2}"},
    )

    assert response.status_code == 403

    # Verify claim was not removed
    claim_check = (
        test_db.query(TodoClaim).filter(TodoClaim.todo_id == todo.id).first())
    assert claim_check is not None


class TestCompleteTodo:
  """Test completion management endpoints."""

  def test_complete_todo_success(
      self,
      client,
      test_db,
      test_user,
      test_household,
      auth_token):
    """Test successful todo completion."""
    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    test_db.add(todo)
    test_db.commit()

    response = client.post(
        f"/api/v1/households/{test_household.id}/todos/{todo.id}/complete",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["completion"] is not None
    assert data["completion"]["completed_by"] == test_user.id

  def test_uncomplete_todo_success(
      self,
      client,
      test_db,
      test_user,
      test_household,
      auth_token):
    """Test successful todo uncompletion."""

    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
    )
    test_db.add(todo)
    test_db.flush()

    completion = TodoCompletion(todo_id=todo.id, completed_by=test_user.id)
    test_db.add(completion)
    test_db.commit()

    response = client.delete(
        f"/api/v1/households/{test_household.id}/todos/{todo.id}/complete",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 204

    # Verify completion was removed
    completion_check = (
        test_db.query(TodoCompletion)
        .filter(TodoCompletion.todo_id == todo.id)
        .first())#yapf:disable
    assert completion_check is None


class TestVisibilityManagement:
  """Test visibility management endpoints."""

  def test_update_todo_visibility_success(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      test_household,
      auth_token):
    """Test successful visibility update."""

    todo = Todo(
        title="Test Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="household",
    )
    test_db.add(todo)
    test_db.commit()

    response = client.patch(
        f"/api/v1/households/{test_household.id}/todos/{todo.id}/visibility",
        json={
            "visibility": "shared",
            "shared_user_ids": [test_user2.id],
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["visibility"] == "shared"

  def test_add_shared_user_success(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      test_household,
      auth_token):
    """Test successful shared user addition."""

    todo = Todo(
        title="Shared Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="shared",
    )
    test_db.add(todo)
    test_db.commit()

    response = client.post(
        f"/api/v1/households/{test_household.id}/todos/{todo.id}/shares",
        json={"user_id": test_user2.id},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == test_user2.id

  def test_add_shared_user_not_creator_returns_403(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      test_household_with_members,
      auth_token2):
    """Test that adding a shared user as non-creator returns 403."""

    todo = Todo(
        title="Shared Todo",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
        visibility="shared",
    )
    test_db.add(todo)
    test_db.flush()

    response = client.post(
        f"/api/v1/households/{test_household_with_members.id}/todos/{todo.id}/shares",
        json={"user_id": test_user2.id},
        headers={"Authorization": f"Bearer {auth_token2}"},
    )

    assert response.status_code == 403

    # Verify share was not created
    share_check = (
        test_db.query(TodoShare).filter(
            TodoShare.todo_id == todo.id,
            TodoShare.user_id == test_user2.id,
        ).first())
    assert share_check is None

  def test_list_shared_users_success(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      test_household,
      auth_token):
    """Test successful shared users listing."""

    todo = Todo(
        title="Shared Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="shared",
    )
    test_db.add(todo)
    test_db.flush()

    share = TodoShare(todo_id=todo.id, user_id=test_user2.id)
    test_db.add(share)
    test_db.commit()

    response = client.get(
        f"/api/v1/households/{test_household.id}/todos/{todo.id}/shares",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == test_user2.id

  def test_remove_shared_user_success(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      test_household,
      auth_token):
    """Test successful shared user removal."""

    todo = Todo(
        title="Shared Todo",
        household_id=test_household.id,
        created_by=test_user.id,
        visibility="shared",
    )
    test_db.add(todo)
    test_db.flush()

    share = TodoShare(todo_id=todo.id, user_id=test_user2.id)
    test_db.add(share)
    test_db.commit()

    response = client.delete(
        f"/api/v1/households/{test_household.id}/todos/{todo.id}/shares/{test_user2.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 204

    # Verify share was removed
    share_check = (
        test_db.query(TodoShare).filter(
            TodoShare.todo_id == todo.id,
            TodoShare.user_id == test_user2.id,
        ).first())
    assert share_check is None

  def test_remove_shared_user_not_creator_returns_403(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      test_household_with_members,
      auth_token2):
    """Test that removing a shared user as non-creator returns 403."""
    todo = Todo(
        title="Shared Todo",
        household_id=test_household_with_members.id,
        created_by=test_user.id,
        visibility="shared",
    )
    test_db.add(todo)
    test_db.flush()

    share = TodoShare(todo_id=todo.id, user_id=test_user2.id)
    test_db.add(share)
    test_db.commit()

    response = client.delete(
        f"/api/v1/households/{test_household_with_members.id}/todos/{todo.id}/shares/{test_user2.id}",
        headers={"Authorization": f"Bearer {auth_token2}"},
    )

    assert response.status_code == 403

    # Verify share was not removed
    share_check = (
        test_db.query(TodoShare).filter(
            TodoShare.todo_id == todo.id,
            TodoShare.user_id == test_user2.id,
        ).first())
    assert share_check is not None
