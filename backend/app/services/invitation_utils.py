"""Invitation helper utilities."""

import hashlib
import secrets

from app.core.config import settings


def normalize_email(email: str) -> str:
  """Normalize emails for storage/comparison."""
  return (email or "").strip().lower()


def generate_invitation_token() -> str:
  """Generate a cryptographically secure invitation token."""
  # ~43 chars for 32 bytes, URL-safe
  return secrets.token_urlsafe(32)


def hash_invitation_token(token: str) -> str:
  """Hash an invitation token (SHA-256 hex)."""
  token_bytes = (token or "").encode("utf-8")
  return hashlib.sha256(token_bytes).hexdigest()


def build_invitation_accept_url(token: str) -> str:
  """Build the frontend accept URL."""
  base = settings.INVITATION_ACCEPT_URL_BASE.rstrip("?")
  return f"{base}?token={token}"


