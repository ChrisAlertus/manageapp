"""Utility functions for the application."""

from datetime import datetime, timezone


def utcnow():
  """Return current UTC datetime with timezone awareness."""
  return datetime.now(timezone.utc)
