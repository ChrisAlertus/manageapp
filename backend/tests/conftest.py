"""Pytest configuration and shared fixtures."""

import os
from unittest.mock import patch

import pytest


def pytest_configure(config):
  """
  Configure pytest and set up test environment variables.

  This runs before test collection to ensure required environment
  variables are set before any modules are imported.
  """
  # Set required environment variables for tests
  # Always set these to ensure tests can run without .env file
  test_env = {
      "JWT_SECRET_KEY": "test-secret-key-for-pytest-12345",
      "DATABASE_URL": "postgresql://test:test@localhost:5432/test_db",
  }
  for key, value in test_env.items():
    os.environ[key] = value


from app.core.deployment import DeploymentConfig


@pytest.fixture
def local_environment():
  """Fixture for local development environment."""
  env = {
      "DATABASE_URL": "postgresql://localhost:5432/test_db",
      "JWT_SECRET_KEY": "test-secret-key",
      "DEBUG": "true",
  }
  with patch.dict(os.environ, env, clear=True):
    yield env


@pytest.fixture
def railway_environment():
  """Fixture for Railway.app environment."""
  env = {
      "RAILWAY_ENVIRONMENT": "production",
      "RAILWAY_PROJECT_ID": "test-project",
      "RAILWAY_SERVICE_NAME": "api",
      "DATABASE_URL": "postgresql://railway:pass@railway.db:5432/railway",
      "JWT_SECRET_KEY": "railway-secret",
  }
  with patch.dict(os.environ, env, clear=True):
    yield env


@pytest.fixture
def render_environment():
  """Fixture for Render.com environment."""
  env = {
      "RENDER": "true",
      "RENDER_SERVICE_ID": "srv-test",
      "RENDER_SERVICE_NAME": "api",
      "DATABASE_URL": "postgresql://render:pass@render.db:5432/render",
      "JWT_SECRET_KEY": "render-secret",
  }
  with patch.dict(os.environ, env, clear=True):
    yield env


@pytest.fixture
def deployment_config():
  """Fixture that returns a fresh DeploymentConfig instance."""

  def _create_config(env_vars=None):
    if env_vars:
      with patch.dict(os.environ, env_vars, clear=True):
        return DeploymentConfig()
    else:
      with patch.dict(os.environ, {}, clear=True):
        return DeploymentConfig()

  return _create_config


@pytest.fixture
def test_secret_key():
  """Fixture providing a test secret key for JWT tokens."""
  return "test-secret-key-for-jwt-tokens-12345"


@pytest.fixture
def test_user_data():
  """Fixture providing test user data for tokens."""
  return {"sub": 1, "email": "test@example.com"}


@pytest.fixture
def test_password():
  """Fixture providing a test password."""
  return "test_password_123"


@pytest.fixture(autouse=True)
def fast_bcrypt(monkeypatch):
  """
  Automatically use faster bcrypt rounds for all tests.

  This fixture reduces bcrypt cost factor from 12 (default) to 4 for tests,
  making password hashing ~256x faster while still testing the same logic.
  """
  from app.core import security

  # Patch get_password_hash to use rounds=4 by default in tests
  original_hash = security.get_password_hash

  def patched_hash(password: str, rounds: int = 4) -> str:
    """Patched version that defaults to fast rounds for tests."""
    return original_hash(password, rounds=rounds)

  monkeypatch.setattr(security, "get_password_hash", patched_hash)
