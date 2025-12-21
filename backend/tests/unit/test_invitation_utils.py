"""Unit tests for invitation helper utilities."""

from app.services import invitation_utils


def test_normalize_email_lowercases_and_strips():
  assert invitation_utils.normalize_email(
      "  Test@Example.com ") == "test@example.com"


def test_generate_token_and_hash_are_stable():
  token = invitation_utils.generate_invitation_token()
  assert isinstance(token, str)
  assert len(token) >= 40

  h1 = invitation_utils.hash_invitation_token(token)
  h2 = invitation_utils.hash_invitation_token(token)
  assert h1 == h2
  assert len(h1) == 64
  assert h1 != token


def test_build_invitation_accept_url_uses_configured_base(monkeypatch):
  monkeypatch.setattr(
      invitation_utils.settings,
      "INVITATION_ACCEPT_URL_BASE",
      "http://localhost:3000/accept",
  )
  url = invitation_utils.build_invitation_accept_url("abc123")
  assert url == "http://localhost:3000/accept?token=abc123"
