"""Integration tests for user preferences API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.user import User
from app.models.user_preferences import UserPreferences

# Create test client
client = TestClient(app)


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
  test_db.commit()  # Commit to make it visible to other sessions
  test_db.refresh(user)

  return user


@pytest.fixture
def auth_token(test_user):
  """Create an authentication token for test user."""
  return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def auth_headers(auth_token):
  """Create authorization headers for authenticated requests."""
  return {"Authorization": f"Bearer {auth_token}"}


@pytest.mark.integration
class TestUserPreferencesAPI:
  """Integration tests for user preferences endpoints."""

  def test_get_preferences_returns_defaults_for_new_user(
      self,
      test_db,
      test_user,
      auth_headers):
    """Test that getting preferences for a new user returns defaults."""
    # User should not have preferences yet
    prefs = test_db.query(UserPreferences).filter(
        UserPreferences.user_id == test_user.id).first()
    assert prefs is None

    # Get preferences (should create defaults)
    response = client.get("/api/v1/me/preferences", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["preferred_currency"] == "CAD"
    assert data["timezone"] == "UTC"
    assert data["language"] == "en"
    assert data["user_id"] == test_user.id

    # Verify preferences were created in database
    prefs = test_db.query(UserPreferences).filter(
        UserPreferences.user_id == test_user.id).first()
    assert prefs is not None
    assert prefs.preferred_currency == "CAD"

  def test_get_preferences_returns_existing_preferences(
      self,
      test_db,
      test_user,
      auth_headers):
    """Test that getting preferences returns existing preferences."""
    # Create preferences manually
    prefs = UserPreferences(
        user_id=test_user.id,
        preferred_currency="USD",
        timezone="America/New_York",
        language="en",
    )
    test_db.add(prefs)
    test_db.commit()

    # Get preferences
    response = client.get("/api/v1/me/preferences", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["preferred_currency"] == "USD"
    assert data["timezone"] == "America/New_York"
    assert data["language"] == "en"

  def test_update_preferences_with_valid_currency(
      self,
      test_db,
      test_user,
      auth_headers):
    """Test updating preferences with valid currency."""
    # Create default preferences
    prefs = UserPreferences(
        user_id=test_user.id,
        preferred_currency="CAD",
        timezone="UTC",
        language="en",
    )
    test_db.add(prefs)
    test_db.commit()

    # Update currency
    response = client.patch(
        "/api/v1/me/preferences",
        headers=auth_headers,
        json={"preferred_currency": "USD"})
    assert response.status_code == 200
    data = response.json()
    assert data["preferred_currency"] == "USD"
    assert data["timezone"] == "UTC"  # Should remain unchanged
    assert data["language"] == "en"  # Should remain unchanged

    # Verify in database
    test_db.refresh(prefs)
    assert prefs.preferred_currency == "USD"

  def test_update_preferences_with_invalid_currency(
      self,
      test_db,
      test_user,
      auth_headers):
    """Test updating preferences with invalid currency returns 400."""
    # Create default preferences
    prefs = UserPreferences(
        user_id=test_user.id,
        preferred_currency="CAD",
        timezone="UTC",
        language="en",
    )
    test_db.add(prefs)
    test_db.commit()

    # Try to update with invalid currency
    response = client.patch(
        "/api/v1/me/preferences",
        headers=auth_headers,
        json={"preferred_currency": "INVALID"})
    assert response.status_code == 422  # Validation error
    assert "Invalid currency code" in response.json()["detail"][0]["msg"]

  def test_update_preferences_partial_update(
      self,
      test_db,
      test_user,
      auth_headers):
    """Test that partial updates work correctly."""
    # Create preferences
    prefs = UserPreferences(
        user_id=test_user.id,
        preferred_currency="CAD",
        timezone="UTC",
        language="en",
    )
    test_db.add(prefs)
    test_db.commit()

    # Update only timezone
    response = client.patch(
        "/api/v1/me/preferences",
        headers=auth_headers,
        json={"timezone": "America/New_York"})
    assert response.status_code == 200
    data = response.json()
    assert data["preferred_currency"] == "CAD"  # Unchanged
    assert data["timezone"] == "America/New_York"  # Updated
    assert data["language"] == "en"  # Unchanged

  def test_update_preferences_all_fields(
      self,
      test_db,
      test_user,
      auth_headers):
    """Test updating all preference fields at once."""
    # Create default preferences
    prefs = UserPreferences(
        user_id=test_user.id,
        preferred_currency="CAD",
        timezone="UTC",
        language="en",
    )
    test_db.add(prefs)
    test_db.commit()

    # Update all fields
    response = client.patch(
        "/api/v1/me/preferences",
        headers=auth_headers,
        json={
            "preferred_currency": "EUR",
            "timezone": "Europe/Paris",
            "language": "fr"
        })
    assert response.status_code == 200
    data = response.json()
    assert data["preferred_currency"] == "EUR"
    assert data["timezone"] == "Europe/Paris"
    assert data["language"] == "fr"

  def test_update_preferences_creates_if_not_exists(
      self,
      test_db,
      test_user,
      auth_headers):
    """Test that updating preferences creates them if they don't exist."""
    # User should not have preferences
    prefs = test_db.query(UserPreferences).filter(
        UserPreferences.user_id == test_user.id).first()
    assert prefs is None

    # Update preferences (should create)
    response = client.patch(
        "/api/v1/me/preferences",
        headers=auth_headers,
        json={"preferred_currency": "USD"})
    assert response.status_code == 200
    data = response.json()
    assert data["preferred_currency"] == "USD"
    assert data["timezone"] == "UTC"  # Default
    assert data["language"] == "en"  # Default

    # Verify created in database
    prefs = test_db.query(UserPreferences).filter(
        UserPreferences.user_id == test_user.id).first()
    assert prefs is not None
    assert prefs.preferred_currency == "USD"

  def test_get_preferences_unauthenticated(self, test_db):
    """Test that unauthenticated access returns 401."""
    response = client.get("/api/v1/me/preferences")
    assert response.status_code == 401

  def test_update_preferences_unauthenticated(self, test_db):
    """Test that unauthenticated update returns 401."""
    response = client.patch(
        "/api/v1/me/preferences",
        json={"preferred_currency": "USD"})
    assert response.status_code == 401

  def test_preferences_created_on_user_registration(self, test_db):
    """Test that preferences are created automatically on user registration."""
    # Register a new user
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "TestPass123!",
            "full_name": "New User"
        })
    assert response.status_code == 201
    user_data = response.json()
    user_id = user_data["id"]

    # Verify preferences were created with defaults
    prefs = test_db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id).first()
    assert prefs is not None
    assert prefs.preferred_currency == "CAD"
    assert prefs.timezone == "UTC"  # Default when not provided
    assert prefs.language == "en"

  def test_preferences_created_with_timezone_on_registration(self, test_db):
    """Test that preferences use provided timezone on user registration."""
    # Register a new user with timezone
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "timezoneuser@example.com",
            "password": "TestPass123!",
            "full_name": "Timezone User",
            "timezone": "America/New_York"
        })
    assert response.status_code == 201
    user_data = response.json()
    user_id = user_data["id"]

    # Verify preferences were created with provided timezone
    prefs = test_db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id).first()
    assert prefs is not None
    assert prefs.preferred_currency == "CAD"
    assert prefs.timezone == "America/New_York"  # Uses provided timezone
    assert prefs.language == "en"

  def test_registration_with_invalid_timezone(self, test_db):
    """Test that registration with invalid timezone returns validation error."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "invalidtz@example.com",
            "password": "TestPass123!",
            "timezone": "Invalid/Timezone"
        })
    assert response.status_code == 422  # Validation error
    assert "timezone" in str(response.json()).lower()

  def test_update_preferences_with_all_supported_currencies(
      self,
      test_db,
      test_user,
      auth_headers):
    """Test updating preferences with all supported currencies."""
    # Create default preferences
    prefs = UserPreferences(
        user_id=test_user.id,
        preferred_currency="CAD",
        timezone="UTC",
        language="en",
    )
    test_db.add(prefs)
    test_db.commit()

    # Test all supported currencies
    supported_currencies = ["CAD", "USD", "EUR", "BBD", "BRL"]
    for currency in supported_currencies:
      response = client.patch(
          "/api/v1/me/preferences",
          headers=auth_headers,
          json={"preferred_currency": currency})
      assert response.status_code == 200
      data = response.json()
      assert data["preferred_currency"] == currency

  def test_update_preferences_case_insensitive_currency(
      self,
      test_db,
      test_user,
      auth_headers):
    """Test that currency codes are case-insensitive."""
    # Create default preferences
    prefs = UserPreferences(
        user_id=test_user.id,
        preferred_currency="CAD",
        timezone="UTC",
        language="en",
    )
    test_db.add(prefs)
    test_db.commit()

    # Update with lowercase currency
    response = client.patch(
        "/api/v1/me/preferences",
        headers=auth_headers,
        json={"preferred_currency": "usd"})
    assert response.status_code == 200
    data = response.json()
    assert data["preferred_currency"] == "USD"
