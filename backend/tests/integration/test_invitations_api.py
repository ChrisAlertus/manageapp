"""Integration tests for invitation API endpoints."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.household import Household
from app.models.household_member import HouseholdMember
from app.models.invitation import Invitation
from app.models.user import User
from app.services.email import (
    EmailSendError,  # Backward compatibility
    MessageSendError,
    get_email_client,  # Backward compatibility
    get_message_client,
)


class FakeMessageClient:
  """Fake message client for testing."""

  def __init__(self, should_fail: bool = False):
    self.should_fail = should_fail
    self.sent = []

  def send_invitation(
      self,
      *,
      to_email: str | None = None,
      to_phone: str | None = None,
      inviter_email: str,
      household_name: str,
      accept_url: str,
  ) -> None:
    if self.should_fail:
      raise MessageSendError("boom")
    self.sent.append({
        "to_email": to_email,
        "to_phone": to_phone,
        "inviter_email": inviter_email,
        "household_name": household_name,
        "accept_url": accept_url,
    })


# Backward compatibility alias
FakeEmailClient = FakeMessageClient


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
  Base.metadata.create_all(engine)
  TestingSessionLocal = sessionmaker(
      autocommit=False,
      autoflush=False,
      bind=engine,
  )

  def override_get_db():
    db = TestingSessionLocal()
    try:
      yield db
    finally:
      db.close()

  app.dependency_overrides[get_db] = override_get_db

  session = TestingSessionLocal()
  try:
    yield session
  finally:
    session.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(test_db):
  return TestClient(app)


@pytest.fixture
def fake_message_client():
  return FakeMessageClient()


@pytest.fixture
def fake_email_client(fake_message_client):
  """Backward compatibility alias."""
  return fake_message_client


@pytest.fixture
def override_email_client(fake_message_client):
  """Override message client dependency for testing."""
  app.dependency_overrides[get_message_client] = lambda: fake_message_client
  # Also override get_email_client for backward compatibility
  app.dependency_overrides[get_email_client] = lambda: fake_message_client
  try:
    yield fake_message_client
  finally:
    app.dependency_overrides.pop(get_message_client, None)
    app.dependency_overrides.pop(get_email_client, None)


def _extract_token(accept_url: str) -> str:
  assert "?token=" in accept_url
  return accept_url.split("?token=", 1)[1]


@pytest.fixture
def owner_user(test_db):
  user = User(
      email="owner@example.com",
      hashed_password=get_password_hash("TestPass123!"),
      full_name="Owner",
  )
  test_db.add(user)
  test_db.commit()
  test_db.refresh(user)
  return user


@pytest.fixture
def invitee_user(test_db):
  user = User(
      email="invitee@example.com",
      hashed_password=get_password_hash("TestPass123!"),
      full_name="Invitee",
  )
  test_db.add(user)
  test_db.commit()
  test_db.refresh(user)
  return user


@pytest.fixture
def owner_token(owner_user):
  return create_access_token(data={"sub": str(owner_user.id)})


@pytest.fixture
def invitee_token(invitee_user):
  return create_access_token(data={"sub": str(invitee_user.id)})


@pytest.fixture
def household_with_owner(test_db, owner_user):
  household = Household(
      name="Test Household",
      description="desc",
      created_by=owner_user.id)
  test_db.add(household)
  test_db.flush()
  membership = HouseholdMember(
      household_id=household.id,
      user_id=owner_user.id,
      role="owner",
  )
  test_db.add(membership)
  test_db.commit()
  test_db.refresh(household)
  return household


def test_send_and_accept_invitation_flow(
    client,
    test_db,
    household_with_owner,
    owner_token,
    invitee_user,
    invitee_token,
    override_email_client,
):
  # Send invitation
  resp = client.post(
      f"/api/v1/households/{household_with_owner.id}/invitations",
      headers={"Authorization": f"Bearer {owner_token}"},
      json={
          "email": invitee_user.email,
          "role": "member"
      },
  )
  assert resp.status_code == 201, resp.text
  body = resp.json()
  assert body["status"] == "pending"
  assert body["email"] == invitee_user.email
  assert body["last_sent_at"] is not None

  # Email was "sent" and includes accept URL with token
  assert len(override_email_client.sent) == 1
  token = _extract_token(override_email_client.sent[0]["accept_url"])

  # Accept invitation as invitee
  resp2 = client.post(
      "/api/v1/invitations/accept",
      headers={"Authorization": f"Bearer {invitee_token}"},
      json={"token": token},
  )
  assert resp2.status_code == 200, resp2.text
  assert resp2.json()["household_id"] == household_with_owner.id

  # Membership exists
  membership = (
      test_db.query(HouseholdMember).filter(
          HouseholdMember.household_id == household_with_owner.id,
          HouseholdMember.user_id == invitee_user.id,
      ).first())
  assert membership is not None
  assert membership.role == "member"

  # Invitation marked accepted
  inv = test_db.query(Invitation).filter(Invitation.id == body["id"]).first()
  assert inv.status == "accepted"
  assert inv.accepted_by_user_id == invitee_user.id


def test_duplicate_invitation_prevention(
    client,
    household_with_owner,
    owner_token,
    invitee_user,
    override_email_client,
):
  r1 = client.post(
      f"/api/v1/households/{household_with_owner.id}/invitations",
      headers={"Authorization": f"Bearer {owner_token}"},
      json={
          "email": invitee_user.email,
          "role": "member"
      },
  )
  assert r1.status_code == 201

  r2 = client.post(
      f"/api/v1/households/{household_with_owner.id}/invitations",
      headers={"Authorization": f"Bearer {owner_token}"},
      json={
          "email": invitee_user.email,
          "role": "member"
      },
  )
  assert r2.status_code == 409


def test_expired_invitation_rejected(
    client,
    test_db,
    household_with_owner,
    owner_token,
    invitee_user,
    invitee_token,
    override_email_client,
):
  r1 = client.post(
      f"/api/v1/households/{household_with_owner.id}/invitations",
      headers={"Authorization": f"Bearer {owner_token}"},
      json={
          "email": invitee_user.email,
          "role": "member"
      },
  )
  assert r1.status_code == 201
  inv_id = r1.json()["id"]
  token = _extract_token(override_email_client.sent[-1]["accept_url"])

  # Force expire
  inv = test_db.query(Invitation).filter(Invitation.id == inv_id).first()
  inv.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
  test_db.commit()

  r2 = client.post(
      "/api/v1/invitations/accept",
      headers={"Authorization": f"Bearer {invitee_token}"},
      json={"token": token},
  )
  assert r2.status_code == 400
  assert "expired" in r2.json()["detail"].lower()
