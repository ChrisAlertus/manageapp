"""Unit tests for household authorization logic."""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_household_member_or_404
from app.models.household import Household
from app.models.household_member import HouseholdMember
from app.models.user import User


class TestHouseholdAuthorization:
  """Test household authorization dependency."""

  def test_get_household_member_or_404_member_allowed(
      self,
      db_session,
      test_user,
      test_household):
    """Test that members can access household."""
    # Create membership
    membership = HouseholdMember(
        household_id=test_household.id,
        user_id=test_user.id,
        role="member",
    )
    db_session.add(membership)
    db_session.commit()

    # Should not raise
    household, membership_result = get_household_member_or_404(
        test_household.id,
        test_user,
        db_session,
    )

    assert household.id == test_household.id
    assert membership_result.user_id == test_user.id
    assert membership_result.role == "member"

  def test_get_household_member_or_404_owner_allowed(
      self,
      db_session,
      test_user,
      test_household):
    """Test that owners can access household."""
    # Create membership
    membership = HouseholdMember(
        household_id=test_household.id,
        user_id=test_user.id,
        role="owner",
    )
    db_session.add(membership)
    db_session.commit()

    # Should not raise
    household, membership_result = get_household_member_or_404(
        test_household.id,
        test_user,
        db_session,
    )

    assert household.id == test_household.id
    assert membership_result.user_id == test_user.id
    assert membership_result.role == "owner"

  def test_get_household_member_or_404_non_member_raises_404(
      self,
      db_session,
      test_user,
      test_household,
  ):
    """Test that non-members get 404."""
    # Create another user
    other_user = User(
        email="other@example.com",
        hashed_password="hashed",
        full_name="Other User",
    )
    db_session.add(other_user)
    db_session.commit()

    # Should raise 404
    with pytest.raises(HTTPException) as exc_info:
      get_household_member_or_404(test_household.id, other_user, db_session)

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()

  def test_get_household_member_or_404_nonexistent_household_raises_404(
      self,
      db_session,
      test_user,
  ):
    """Test that accessing non-existent household raises 404."""
    # Should raise 404
    with pytest.raises(HTTPException) as exc_info:
      get_household_member_or_404(99999, test_user, db_session)

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


# Fixtures for testing
@pytest.fixture
def db_session():
  """Create an in-memory SQLite database session for testing."""
  from sqlalchemy import create_engine
  from sqlalchemy.orm import sessionmaker

  from app.core.database import Base

  engine = create_engine(
      "sqlite:///:memory:",
      connect_args={"check_same_thread": False})
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
