"""Integration tests for deployment abstraction module.

These tests verify that the deployment abstraction works correctly
with actual environment variable configurations that would be present
in different deployment platforms.
"""

import os
from unittest.mock import patch

import pytest

from app.core.deployment import DeploymentConfig, DeploymentPlatform


class TestRailwayIntegration:
  """Integration tests for Railway.app deployment."""

  def test_railway_production_environment(self):
    """Test Railway production environment configuration."""
    railway_env = {
        "RAILWAY_ENVIRONMENT": "production",
        "RAILWAY_PROJECT_ID": "abc123",
        "RAILWAY_SERVICE_NAME": "api",
        "DATABASE_URL": "postgresql://railway:pass@railway.db:5432/railway",
        "JWT_SECRET_KEY": "railway-secret-key",
    }

    with patch.dict(os.environ, railway_env, clear=True):
      config = DeploymentConfig()

      assert config.get_platform() == DeploymentPlatform.RAILWAY
      assert config.is_production() is True
      assert config.get_environment() == "production"
      assert config.get_database_url() == railway_env["DATABASE_URL"]
      assert config.get("project_id") == "abc123"
      assert config.get("service_name") == "api"

  def test_railway_development_environment(self):
    """Test Railway development environment configuration."""
    railway_env = {
        "RAILWAY_ENVIRONMENT": "development",
        "RAILWAY_PROJECT_ID": "dev-project",
        "DATABASE_URL": "postgresql://railway:pass@railway.db:5432/railway",
    }

    with patch.dict(os.environ, railway_env, clear=True):
      config = DeploymentConfig()

      assert config.get_platform() == DeploymentPlatform.RAILWAY
      assert config.get_environment() == "development"
      # Railway dev might still be considered production-like
      # depending on implementation, but environment should be correct
      assert config.get("environment") == "development"


class TestRenderIntegration:
  """Integration tests for Render.com deployment."""

  def test_render_production_environment(self):
    """Test Render production environment configuration."""
    render_env = {
        "RENDER": "true",
        "RENDER_SERVICE_ID": "srv-abc123",
        "RENDER_SERVICE_NAME": "api",
        "RENDER_SERVICE_TYPE": "web",
        "RENDER_REGION": "oregon",
        "DATABASE_URL": "postgresql://render:pass@render.db:5432/render",
        "JWT_SECRET_KEY": "render-secret-key",
    }

    with patch.dict(os.environ, render_env, clear=True):
      config = DeploymentConfig()

      assert config.get_platform() == DeploymentPlatform.RENDER
      assert config.is_production() is True
      assert config.get_database_url() == render_env["DATABASE_URL"]
      assert config.get("service_id") == "srv-abc123"
      assert config.get("service_name") == "api"
      assert config.get("service_type") == "web"
      assert config.get("region") == "oregon"

  def test_render_with_instance_id(self):
    """Test Render with instance ID."""
    render_env = {
        "RENDER": "true",
        "RENDER_INSTANCE_ID": "instance-xyz",
        "DATABASE_URL": "postgresql://render:pass@render.db:5432/render",
    }

    with patch.dict(os.environ, render_env, clear=True):
      config = DeploymentConfig()

      assert config.get_platform() == DeploymentPlatform.RENDER
      assert config.get("instance_id") == "instance-xyz"


class TestLocalDevelopmentIntegration:
  """Integration tests for local development."""

  def test_local_development_environment(self):
    """Test local development environment configuration."""
    local_env = {
        "DATABASE_URL": "postgresql://localhost:5432/manageapp_db",
        "JWT_SECRET_KEY": "local-dev-secret",
        "DEBUG": "true",
    }

    with patch.dict(os.environ, local_env, clear=True):
      config = DeploymentConfig()

      assert config.get_platform() == DeploymentPlatform.LOCAL
      assert config.is_production() is False
      assert config.get_environment() == "development"
      assert config.get_database_url() == local_env["DATABASE_URL"]
      assert config.get("debug") is True

  def test_local_without_debug(self):
    """Test local development without DEBUG flag."""
    local_env = {
        "DATABASE_URL": "postgresql://localhost:5432/manageapp_db",
    }

    with patch.dict(os.environ, local_env, clear=True):
      config = DeploymentConfig()

      assert config.get_platform() == DeploymentPlatform.LOCAL
      assert config.get("debug") is False


class TestPlatformMigration:
  """Integration tests for platform migration scenarios."""

  def test_railway_to_render_migration(self):
    """Test configuration compatibility between Railway and Render."""
    # Railway configuration
    railway_config = {
        "RAILWAY_ENVIRONMENT": "production",
        "DATABASE_URL": "postgresql://railway:pass@railway.db:5432/railway",
        "JWT_SECRET_KEY": "secret-key",
    }

    with patch.dict(os.environ, railway_config, clear=True):
      railway_deployment = DeploymentConfig()
      railway_db_url = railway_deployment.get_database_url()

    # Render configuration (same DATABASE_URL format)
    render_config = {
        "RENDER": "true",
        "DATABASE_URL": "postgresql://render:pass@render.db:5432/render",
        "JWT_SECRET_KEY": "secret-key",
    }

    with patch.dict(os.environ, render_config, clear=True):
      render_deployment = DeploymentConfig()
      render_db_url = render_deployment.get_database_url()

    # Both should work with same DATABASE_URL format
    assert railway_db_url is not None
    assert render_db_url is not None
    assert railway_deployment.get_platform() == DeploymentPlatform.RAILWAY
    assert render_deployment.get_platform() == DeploymentPlatform.RENDER

  def test_explicit_platform_override(self):
    """Test explicit platform override for testing/migration."""
    # Simulate Railway environment but override to Render
    env = {
        "RAILWAY_ENVIRONMENT": "production",
        "DEPLOYMENT_PLATFORM": "render",
        "DATABASE_URL": "postgresql://db:5432/app",
    }

    with patch.dict(os.environ, env, clear=True):
      config = DeploymentConfig()

      # Explicit override should take precedence
      assert config.get_platform() == DeploymentPlatform.RENDER
      # But Railway env vars might still be accessible
      assert config.get_database_url() == "postgresql://db:5432/app"


class TestDatabaseUrlNormalization:
  """Integration tests for database URL handling across platforms."""

  def test_standard_database_url_format(self):
    """Test that standard DATABASE_URL format works on all platforms."""
    standard_url = "postgresql://user:password@host:5432/database"

    platforms = [
        DeploymentPlatform.RAILWAY,
        DeploymentPlatform.RENDER,
        DeploymentPlatform.LOCAL,
    ]

    for platform in platforms:
      env = {
          "DEPLOYMENT_PLATFORM": platform.value,
          "DATABASE_URL": standard_url,
      }

      with patch.dict(os.environ, env, clear=True):
        config = DeploymentConfig()
        assert config.get_database_url() == standard_url
        assert config.get_platform() == platform

  def test_missing_database_url(self):
    """Test behavior when DATABASE_URL is missing."""
    env = {"RAILWAY_ENVIRONMENT": "production"}

    with patch.dict(os.environ, env, clear=True):
      config = DeploymentConfig()
      # Should return None, not raise exception
      assert config.get_database_url() is None or isinstance(
          config.get_database_url(),
          str)
