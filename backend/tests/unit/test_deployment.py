"""Unit tests for deployment abstraction module."""

import os
from unittest.mock import patch

import pytest

from app.core.deployment import (
    DeploymentConfig,
    DeploymentPlatform,
    deployment)


class TestDeploymentPlatform:
  """Test DeploymentPlatform enum."""

  def test_enum_values(self):
    """Test that all expected platform values exist."""
    assert DeploymentPlatform.LOCAL.value == "local"
    assert DeploymentPlatform.RAILWAY.value == "railway"
    assert DeploymentPlatform.RENDER.value == "render"
    assert DeploymentPlatform.GCP.value == "gcp"
    assert DeploymentPlatform.AWS.value == "aws"
    assert DeploymentPlatform.UNKNOWN.value == "unknown"


class TestDeploymentConfig:
  """Test DeploymentConfig class."""

  def test_local_detection_default(self):
    """Test that local is detected when no platform indicators exist."""
    with patch.dict(os.environ, {}, clear=True):
      config = DeploymentConfig()
      assert config.get_platform() == DeploymentPlatform.LOCAL

  def test_explicit_platform_override(self):
    """Test explicit platform override via DEPLOYMENT_PLATFORM."""
    with patch.dict(os.environ, {"DEPLOYMENT_PLATFORM": "railway"}):
      config = DeploymentConfig()
      assert config.get_platform() == DeploymentPlatform.RAILWAY

    with patch.dict(os.environ, {"DEPLOYMENT_PLATFORM": "render"}):
      config = DeploymentConfig()
      assert config.get_platform() == DeploymentPlatform.RENDER

  def test_railway_detection(self):
    """Test Railway.app platform detection."""
    # Test with RAILWAY_ENVIRONMENT
    with patch.dict(os.environ, {"RAILWAY_ENVIRONMENT": "production"}):
      config = DeploymentConfig()
      assert config.get_platform() == DeploymentPlatform.RAILWAY

    # Test with RAILWAY_PROJECT_ID
    with patch.dict(os.environ, {"RAILWAY_PROJECT_ID": "test-project"}):
      config = DeploymentConfig()
      assert config.get_platform() == DeploymentPlatform.RAILWAY

  def test_render_detection(self):
    """Test Render.com platform detection."""
    # Test with RENDER
    with patch.dict(os.environ, {"RENDER": "true"}):
      config = DeploymentConfig()
      assert config.get_platform() == DeploymentPlatform.RENDER

    # Test with RENDER_SERVICE_ID
    with patch.dict(os.environ, {"RENDER_SERVICE_ID": "test-service"}):
      config = DeploymentConfig()
      assert config.get_platform() == DeploymentPlatform.RENDER

  def test_gcp_detection(self):
    """Test GCP platform detection."""
    with patch.dict(os.environ, {"GOOGLE_CLOUD_PROJECT": "test-project"}):
      config = DeploymentConfig()
      assert config.get_platform() == DeploymentPlatform.GCP

    with patch.dict(os.environ, {"GCP_PROJECT": "test-project"}):
      config = DeploymentConfig()
      assert config.get_platform() == DeploymentPlatform.GCP

  def test_aws_detection(self):
    """Test AWS platform detection."""
    with patch.dict(os.environ, {"AWS_REGION": "ca-central-1"}):
      config = DeploymentConfig()
      assert config.get_platform() == DeploymentPlatform.AWS

    with patch.dict(os.environ, {"AWS_EXECUTION_ENV": "AWS_LAMBDA"}):
      config = DeploymentConfig()
      assert config.get_platform() == DeploymentPlatform.AWS

  def test_platform_priority(self):
    """Test that explicit DEPLOYMENT_PLATFORM takes priority."""
    with patch.dict(os.environ,
                    {
                        "DEPLOYMENT_PLATFORM": "local",
                        "RAILWAY_ENVIRONMENT": "production",
                        "RENDER": "true",
                    }):
      config = DeploymentConfig()
      assert config.get_platform() == DeploymentPlatform.LOCAL

  def test_is_production(self):
    """Test production environment detection."""
    # Production via ENVIRONMENT
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
      config = DeploymentConfig()
      assert config.is_production() is True

    # Production via RAILWAY_ENVIRONMENT
    with patch.dict(os.environ, {"RAILWAY_ENVIRONMENT": "production"}):
      config = DeploymentConfig()
      assert config.is_production() is True

    # Not production (local)
    with patch.dict(os.environ, {}, clear=True):
      config = DeploymentConfig()
      assert config.is_production() is False

    # Not production (explicit development)
    with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
      config = DeploymentConfig()
      assert config.is_production() is False

  def test_get_database_url(self):
    """Test database URL retrieval."""
    # Standard DATABASE_URL
    with patch.dict(os.environ,
                    {"DATABASE_URL": "postgresql://user:pass@localhost/db"}):
      config = DeploymentConfig()
      assert config.get_database_url() == "postgresql://user:pass@localhost/db"

    # Missing DATABASE_URL
    with patch.dict(os.environ, {}, clear=True):
      config = DeploymentConfig()
      assert config.get_database_url() is None

  def test_get_environment(self):
    """Test environment name retrieval."""
    # Explicit ENVIRONMENT - test that it's read correctly
    with patch.dict(os.environ, {"ENVIRONMENT": "staging"}, clear=True):
      # Verify environment is set before creating config
      env_value = os.getenv("ENVIRONMENT")
      assert env_value == "staging", (
          f"ENVIRONMENT should be 'staging', got '{env_value}'")

      # Create config - this should read ENVIRONMENT during init
      config = DeploymentConfig()

      # Check what _get_environment would return if called now
      # (it reads from os.getenv directly, not from stored config)
      current_env = config._get_environment()

      # Check stored value
      stored_env = config._config.get("environment")
      method_env = config.get_environment()

      # Debug output if assertion fails
      if stored_env != "staging":
        print(f"DEBUG: ENVIRONMENT var = {os.getenv('ENVIRONMENT')}")
        print(f"DEBUG: _get_environment() returns = {current_env}")
        print(f"DEBUG: stored in config = {stored_env}")
        print(f"DEBUG: get_environment() returns = {method_env}")

      # All should be "staging"
      assert current_env == "staging", (
          f"_get_environment() returned '{current_env}', expected 'staging'")
      assert stored_env == "staging", (
          f"Stored config has '{stored_env}', expected 'staging'")
      assert method_env == "staging", (
          f"get_environment() returned '{method_env}', expected 'staging'")

    # Railway ENVIRONMENT
    with patch.dict(os.environ,
                    {"RAILWAY_ENVIRONMENT": "production"},
                    clear=True):
      config = DeploymentConfig()
      assert config.get_environment() == "production"

    # Default to development (no environment variables)
    with patch.dict(os.environ, {}, clear=True):
      config = DeploymentConfig()
      assert config.get_environment() == "development"

  def test_railway_config(self):
    """Test Railway-specific configuration."""
    with patch.dict(os.environ,
                    {
                        "RAILWAY_ENVIRONMENT": "production",
                        "RAILWAY_SERVICE_NAME": "api",
                        "RAILWAY_PROJECT_ID": "test-project",
                        "RAILWAY_REGION": "us-west",
                        "RAILWAY_REPLICA_ID": "replica-1",
                    }):
      config = DeploymentConfig()
      assert config.get("service_name") == "api"
      assert config.get("project_id") == "test-project"
      assert config.get("region") == "us-west"
      assert config.get("replica_id") == "replica-1"

  def test_render_config(self):
    """Test Render-specific configuration."""
    with patch.dict(os.environ,
                    {
                        "RENDER": "true",
                        "RENDER_SERVICE_ID": "service-123",
                        "RENDER_SERVICE_NAME": "api",
                        "RENDER_SERVICE_TYPE": "web",
                        "RENDER_REGION": "oregon",
                        "RENDER_INSTANCE_ID": "instance-1",
                    }):
      config = DeploymentConfig()
      assert config.get("service_id") == "service-123"
      assert config.get("service_name") == "api"
      assert config.get("service_type") == "web"
      assert config.get("region") == "oregon"
      assert config.get("instance_id") == "instance-1"

  def test_local_config(self):
    """Test local development configuration."""
    with patch.dict(os.environ, {"DEBUG": "true"}, clear=True):
      config = DeploymentConfig()
      assert config.get("environment") == "development"
      assert config.get("debug") is True

    with patch.dict(os.environ, {"DEBUG": "false"}, clear=True):
      config = DeploymentConfig()
      assert config.get("debug") is False

  def test_get_method(self):
    """Test generic get method."""
    with patch.dict(os.environ, {"RAILWAY_ENVIRONMENT": "production"}):
      config = DeploymentConfig()
      assert config.get("platform") == "railway"
      assert config.get("nonexistent", "default") == "default"
      assert config.get("nonexistent") is None

  def test_to_dict(self):
    """Test configuration dictionary export."""
    with patch.dict(os.environ,
                    {"RAILWAY_ENVIRONMENT": "production",
                     "DATABASE_URL": "postgresql://localhost/db"}):
      config = DeploymentConfig()
      config_dict = config.to_dict()

      assert isinstance(config_dict, dict)
      assert config_dict["platform"] == "railway"
      assert config_dict["database_url"] == "postgresql://localhost/db"
      assert "is_production" in config_dict
      assert "environment" in config_dict

  def test_gcp_config(self):
    """Test GCP-specific configuration."""
    with patch.dict(os.environ,
                    {
                        "GOOGLE_CLOUD_PROJECT": "test-project",
                        "GCP_REGION": "us-central1",
                        "CLOUD_RUN_SERVICE": "api-service",
                        "CLOUD_RUN_REVISION": "rev-1",
                    }):
      config = DeploymentConfig()
      assert config.get("project_id") == "test-project"
      assert config.get("region") == "us-central1"
      assert config.get("service_name") == "api-service"
      assert config.get("instance_id") == "rev-1"

  def test_aws_config(self):
    """Test AWS-specific configuration."""
    with patch.dict(os.environ,
                    {
                        "AWS_REGION": "us-east-1",
                        "AWS_EXECUTION_ENV": "AWS_LAMBDA",
                        "AWS_LAMBDA_FUNCTION_NAME": "api-function",
                        "ECS_CLUSTER": "api-cluster",
                        "ECS_SERVICE": "api-service",
                    }):
      config = DeploymentConfig()
      assert config.get("region") == "us-east-1"
      assert config.get("execution_env") == "AWS_LAMBDA"
      assert config.get("lambda_function_name") == "api-function"
      assert config.get("ecs_cluster") == "api-cluster"
      assert config.get("ecs_service") == "api-service"


class TestGlobalDeploymentInstance:
  """Test the global deployment instance."""

  def test_global_instance_exists(self):
    """Test that global deployment instance exists."""
    assert deployment is not None
    assert isinstance(deployment, DeploymentConfig)

  def test_global_instance_platform(self):
    """Test global instance platform detection."""
    # Should default to LOCAL in test environment
    assert deployment.get_platform() in [
        DeploymentPlatform.LOCAL,
        DeploymentPlatform.UNKNOWN
    ]
