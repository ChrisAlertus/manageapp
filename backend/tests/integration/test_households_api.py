"""Integration tests for household API endpoints."""

import logging
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.household import Household
from app.models.household_member import HouseholdMember
from app.models.user import User

# Enable debug logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
  test_db.flush()  # Flush to get the ID
  logger.debug(
      f"test_user fixture: User created with id: {user.id} (before commit)")
  test_db.commit()  # Commit to make it visible to other sessions
  test_db.refresh(user)
  logger.debug(
      f"test_user fixture: User committed and refreshed, id: {user.id}, email: {user.email}"
  )

  # Verify user exists in database
  all_users = test_db.query(User).all()
  logger.debug(
      f"test_user fixture: All users in test_db session: {[(u.id, u.email) for u in all_users]}"
  )

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
  test_db.flush()  # Flush to get the ID
  test_db.commit()  # Commit to make it visible to other sessions
  test_db.refresh(user)
  return user


@pytest.fixture
def auth_token(test_user):
  """Create an auth token for test user."""
  from app.core.config import settings
  logger.debug(
      f"auth_token fixture: Creating token for user_id: {test_user.id} (type: {type(test_user.id)})"
  )
  logger.debug(
      f"auth_token fixture: SECRET_KEY length: {len(settings.SECRET_KEY)}, algorithm: {settings.ALGORITHM}"
  )
  token = create_access_token(
      data={"sub": str(test_user.id)})  # JWT requires sub to be a string
  logger.debug(
      f"auth_token fixture: Token created, length: {len(token)}, first 50 chars: {token[:50]}"
  )

  # Verify token can be decoded immediately
  from app.core.security import decode_access_token
  test_payload = decode_access_token(token)
  logger.debug(
      f"auth_token fixture: Token verification - can decode: {test_payload is not None}"
  )
  if test_payload:
    logger.debug(f"auth_token fixture: Decoded payload: {test_payload}")

  return token


@pytest.fixture
def auth_token2(test_user2):
  """Create an auth token for test user 2."""
  return create_access_token(
      data={"sub": str(test_user2.id)})  # JWT requires sub to be a string


@pytest.fixture
def client():
  """Create a test client."""
  return TestClient(app)


class TestCreateHousehold:
  """Test household creation endpoint."""

  def test_create_household_success(
      self,
      client,
      test_db,
      test_user,
      auth_token):
    """Test successful household creation."""
    logger.debug(
        f"test_create_household_success: test_user.id = {test_user.id}")
    logger.debug(
        f"test_create_household_success: auth_token = {auth_token[:50]}...")

    # Verify user exists in database before making request
    users_before = test_db.query(User).all()
    logger.debug(
        f"test_create_household_success: Users in test_db before request: {[(u.id, u.email) for u in users_before]}"
    )

    response = client.post(
        "/api/v1/households/",
        json={
            "name": "My Household",
            "description": "A test household"
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    logger.debug(
        f"test_create_household_success: Response status: {response.status_code}"
    )
    if response.status_code != 201:
      logger.error(
          f"test_create_household_success: Response body: {response.text}")

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Household"
    assert data["description"] == "A test household"
    assert "id" in data
    assert data["created_by"] == test_user.id
    assert "created_at" in data
    assert "updated_at" in data

    # Verify membership was created
    membership = (
        test_db.query(HouseholdMember).filter(
            HouseholdMember.household_id == data["id"],
            HouseholdMember.user_id == test_user.id,
        ).first())
    assert membership is not None
    assert membership.role == "owner"

  def test_create_household_requires_auth(self, client):
    """Test that household creation requires authentication."""
    response = client.post(
        "/api/v1/households/",
        json={"name": "My Household"},
    )

    assert response.status_code == 401

  def test_create_household_empty_name(self, client, auth_token):
    """Test that household creation with empty name is rejected."""
    response = client.post(
        "/api/v1/households/",
        json={"name": ""},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 422

  def test_create_household_optional_description(self, client, auth_token):
    """Test that description is optional in household creation."""
    response = client.post(
        "/api/v1/households/",
        json={"name": "My Household"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Household"
    assert data["description"] is None


class TestListHouseholds:
  """Test household listing endpoint."""

  def test_list_households_empty(self, client, auth_token):
    """Test listing households when user has none."""
    response = client.get(
        "/api/v1/households/",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    assert response.json() == []

  def test_list_households_with_memberships(
      self,
      client,
      test_db,
      test_user,
      auth_token,
  ):
    """Test listing households when user is a member."""
    # Create households
    household1 = Household(name="Household 1")
    household2 = Household(name="Household 2")
    test_db.add_all([household1, household2])
    test_db.flush()

    # Add memberships
    membership1 = HouseholdMember(
        household_id=household1.id,
        user_id=test_user.id,
        role="owner",
    )
    membership2 = HouseholdMember(
        household_id=household2.id,
        user_id=test_user.id,
        role="member",
    )
    test_db.add_all([membership1, membership2])
    test_db.commit()

    response = client.get(
        "/api/v1/households/",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    household_ids = {h["id"] for h in data}
    assert household1.id in household_ids
    assert household2.id in household_ids

  def test_list_households_only_user_households(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      auth_token,
  ):
    """Test that listing only returns user's households."""
    # Create household for user 1
    household1 = Household(name="User 1 Household")
    test_db.add(household1)
    test_db.flush()

    membership1 = HouseholdMember(
        household_id=household1.id,
        user_id=test_user.id,
        role="owner",
    )
    test_db.add(membership1)

    # Create household for user 2
    household2 = Household(name="User 2 Household")
    test_db.add(household2)
    test_db.flush()

    membership2 = HouseholdMember(
        household_id=household2.id,
        user_id=test_user2.id,
        role="owner",
    )
    test_db.add(membership2)
    test_db.commit()

    # User 1 should only see their household
    response = client.get(
        "/api/v1/households/",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == household1.id


class TestGetHousehold:
  """Test household detail endpoint."""

  def test_get_household_success(
      self,
      client,
      test_db,
      test_user,
      auth_token,
  ):
    """Test successful household retrieval."""
    # Create household and membership
    household = Household(name="My Household", description="Test")
    test_db.add(household)
    test_db.flush()

    membership = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="member",
    )
    test_db.add(membership)
    test_db.commit()

    response = client.get(
        f"/api/v1/households/{household.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == household.id
    assert data["name"] == "My Household"
    assert data["description"] == "Test"

  def test_get_household_non_member_404(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      auth_token2,
  ):
    """Test that non-members get 404."""
    # Create household for user 1
    household = Household(name="User 1 Household")
    test_db.add(household)
    test_db.flush()

    membership = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="owner",
    )
    test_db.add(membership)
    test_db.commit()

    # User 2 should get 404
    response = client.get(
        f"/api/v1/households/{household.id}",
        headers={"Authorization": f"Bearer {auth_token2}"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

  def test_get_household_nonexistent_404(self, client, auth_token):
    """Test that accessing non-existent household returns 404."""
    response = client.get(
        "/api/v1/households/99999",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 404


class TestLeaveHousehold:
  """Test leave household endpoint."""

  def test_leave_household_member_success(
      self,
      client,
      test_db,
      test_user,
      auth_token,
  ):
    """Test that members can leave household."""
    # Create household and membership
    household = Household(name="My Household")
    test_db.add(household)
    test_db.flush()

    membership = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="member",
    )
    test_db.add(membership)
    test_db.commit()

    response = client.post(
        f"/api/v1/households/{household.id}/leave",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 204

    # Verify membership was removed
    membership_check = (
        test_db.query(HouseholdMember).filter(
            HouseholdMember.household_id == household.id,
            HouseholdMember.user_id == test_user.id,
        ).first())
    assert membership_check is None

  def test_leave_household_owner_with_other_owners(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      auth_token,
  ):
    """Test that owners can leave if there are other owners."""
    # Create household
    household = Household(name="My Household")
    test_db.add(household)
    test_db.flush()

    # Add two owners
    membership1 = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="owner",
    )
    membership2 = HouseholdMember(
        household_id=household.id,
        user_id=test_user2.id,
        role="owner",
    )
    test_db.add_all([membership1, membership2])
    test_db.commit()

    response = client.post(
        f"/api/v1/households/{household.id}/leave",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 204

    # Verify membership was removed
    membership_check = (
        test_db.query(HouseholdMember).filter(
            HouseholdMember.household_id == household.id,
            HouseholdMember.user_id == test_user.id,
        ).first())
    assert membership_check is None

  def test_leave_household_last_owner_blocked(
      self,
      client,
      test_db,
      test_user,
      auth_token,
  ):
    """Test that last owner cannot leave household."""
    # Create household
    household = Household(name="My Household")
    test_db.add(household)
    test_db.flush()

    # Add single owner
    membership = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="owner",
    )
    test_db.add(membership)
    test_db.commit()

    response = client.post(
        f"/api/v1/households/{household.id}/leave",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 400
    assert "last owner" in response.json()["detail"].lower()

    # Verify membership was NOT removed
    membership_check = (
        test_db.query(HouseholdMember).filter(
            HouseholdMember.household_id == household.id,
            HouseholdMember.user_id == test_user.id,
        ).first())
    assert membership_check is not None

  def test_leave_household_non_member_404(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      auth_token2,
  ):
    """Test that non-members get 404 when trying to leave."""
    # Create household for user 1
    household = Household(name="User 1 Household")
    test_db.add(household)
    test_db.flush()

    membership = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="owner",
    )
    test_db.add(membership)
    test_db.commit()

    # User 2 should get 404
    response = client.post(
        f"/api/v1/households/{household.id}/leave",
        headers={"Authorization": f"Bearer {auth_token2}"},
    )

    assert response.status_code == 404


class TestTransferOwnership:
  """Test transfer ownership endpoint."""

  def test_transfer_ownership_success(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      auth_token,
  ):
    """Test successful ownership transfer."""
    # Create household with user1 as owner
    household = Household(name="My Household")
    test_db.add(household)
    test_db.flush()

    membership1 = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="owner",
    )
    membership2 = HouseholdMember(
        household_id=household.id,
        user_id=test_user2.id,
        role="member",
    )
    test_db.add_all([membership1, membership2])
    test_db.commit()

    # Transfer ownership to user2
    response = client.post(
        f"/api/v1/households/{household.id}/transfer-ownership",
        json={"new_owner_id": test_user2.id},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 204

    # Verify user2 is now an owner
    test_db.refresh(membership2)
    assert membership2.role == "owner"
    # Verify user1 is still an owner (shared ownership)
    test_db.refresh(membership1)
    assert membership1.role == "owner"

  def test_transfer_ownership_requires_owner(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      auth_token2,
  ):
    """Test that only owners can transfer ownership."""
    # Create household with user1 as owner, user2 as member
    household = Household(name="My Household")
    test_db.add(household)
    test_db.flush()

    membership1 = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="owner",
    )
    membership2 = HouseholdMember(
        household_id=household.id,
        user_id=test_user2.id,
        role="member",
    )
    test_db.add_all([membership1, membership2])
    test_db.commit()

    # User2 (member) tries to transfer ownership - should fail
    response = client.post(
        f"/api/v1/households/{household.id}/transfer-ownership",
        json={"new_owner_id": test_user2.id},
        headers={"Authorization": f"Bearer {auth_token2}"},
    )

    assert response.status_code == 403
    assert "owner" in response.json()["detail"].lower()

  def test_transfer_ownership_to_non_member(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      auth_token,
  ):
    """Test that transferring to non-member fails."""
    # Create household with user1 as owner
    household = Household(name="My Household")
    test_db.add(household)
    test_db.flush()

    membership = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="owner",
    )
    test_db.add(membership)
    test_db.commit()

    # Try to transfer to user2 who is not a member
    response = client.post(
        f"/api/v1/households/{household.id}/transfer-ownership",
        json={"new_owner_id": test_user2.id},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 400
    assert "member" in response.json()["detail"].lower()

  def test_transfer_ownership_to_self(
      self,
      client,
      test_db,
      test_user,
      auth_token,
  ):
    """Test that transferring ownership to self fails."""
    # Create household with user1 as owner
    household = Household(name="My Household")
    test_db.add(household)
    test_db.flush()

    membership = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="owner",
    )
    test_db.add(membership)
    test_db.commit()

    # Try to transfer to self
    response = client.post(
        f"/api/v1/households/{household.id}/transfer-ownership",
        json={"new_owner_id": test_user.id},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 400
    assert "yourself" in response.json()["detail"].lower()

  def test_transfer_ownership_to_existing_owner(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      auth_token,
  ):
    """Test that transferring to existing owner fails."""
    # Create household with both users as owners
    household = Household(name="My Household")
    test_db.add(household)
    test_db.flush()

    membership1 = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="owner",
    )
    membership2 = HouseholdMember(
        household_id=household.id,
        user_id=test_user2.id,
        role="owner",
    )
    test_db.add_all([membership1, membership2])
    test_db.commit()

    # Try to transfer to user2 who is already an owner
    response = client.post(
        f"/api/v1/households/{household.id}/transfer-ownership",
        json={"new_owner_id": test_user2.id},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower()


class TestDeleteHousehold:
  """Test delete household endpoint."""

  def test_delete_household_success(
      self,
      client,
      test_db,
      test_user,
      auth_token,
  ):
    """Test successful household deletion by owner."""
    # Create household
    household = Household(name="My Household")
    test_db.add(household)
    test_db.flush()

    membership = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="owner",
    )
    test_db.add(membership)
    test_db.commit()

    # Delete household
    response = client.delete(
        f"/api/v1/households/{household.id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response.status_code == 204

    # Verify household is deleted
    household_check = test_db.query(Household).filter(
        Household.id == household.id).first()
    assert household_check is None

    # Verify memberships are cascade deleted
    membership_check = (
        test_db.query(HouseholdMember).filter(
            HouseholdMember.household_id == household.id).first())
    assert membership_check is None

  def test_delete_household_requires_owner(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      auth_token2,
  ):
    """Test that only owners can delete household."""
    # Create household with user1 as owner, user2 as member
    household = Household(name="My Household")
    test_db.add(household)
    test_db.flush()

    membership1 = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="owner",
    )
    membership2 = HouseholdMember(
        household_id=household.id,
        user_id=test_user2.id,
        role="member",
    )
    test_db.add_all([membership1, membership2])
    test_db.commit()

    # User2 (member) tries to delete - should fail
    response = client.delete(
        f"/api/v1/households/{household.id}",
        headers={"Authorization": f"Bearer {auth_token2}"},
    )

    assert response.status_code == 403
    assert "owner" in response.json()["detail"].lower()

    # Verify household still exists
    household_check = test_db.query(Household).filter(
        Household.id == household.id).first()
    assert household_check is not None

  def test_delete_household_non_member_404(
      self,
      client,
      test_db,
      test_user,
      test_user2,
      auth_token2,
  ):
    """Test that non-members get 404 when trying to delete."""
    # Create household for user1
    household = Household(name="User 1 Household")
    test_db.add(household)
    test_db.flush()

    membership = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="owner",
    )
    test_db.add(membership)
    test_db.commit()

    # User2 should get 404
    response = client.delete(
        f"/api/v1/households/{household.id}",
        headers={"Authorization": f"Bearer {auth_token2}"},
    )

    assert response.status_code == 404
