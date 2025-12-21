"""Pytest configuration and shared fixtures."""

import os
from unittest.mock import patch

import pytest

from app.core.deployment import DeploymentConfig


@pytest.fixture
def local_environment():
  """Fixture for local development environment."""
  env = {
      "DATABASE_URL": "postgresql://localhost:5432/test_db",
      "SECRET_KEY": "test-secret-key",
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
      "SECRET_KEY": "railway-secret",
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
      "SECRET_KEY": "render-secret",
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
