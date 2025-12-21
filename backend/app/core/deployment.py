"""Deployment platform abstraction layer.

This module provides platform-agnostic deployment configuration, allowing
the application to run on Railway.app, Render.com, GCP, AWS, or locally
without platform-specific code in the application logic.

Supported Platforms:
- Railway.app (primary)
- Render.com (secondary)
- Local development (default)
- GCP (future)
- AWS (future)
"""

import os
from enum import Enum
from typing import Optional


class DeploymentPlatform(str, Enum):
  """Supported deployment platforms."""

  LOCAL = "local"
  RAILWAY = "railway"
  RENDER = "render"
  GCP = "gcp"
  AWS = "aws"
  UNKNOWN = "unknown"


class DeploymentConfig:
  """Platform-agnostic deployment configuration.

  This class detects the deployment platform and provides normalized
  configuration values that work across all platforms.
  """

  def __init__(self):
    """Initialize deployment configuration."""
    self.platform = self._detect_platform()
    self._config = self._load_platform_config()

  def _detect_platform(self) -> DeploymentPlatform:
    """Detect the current deployment platform.

    Detection order:
    1. Explicit DEPLOYMENT_PLATFORM environment variable
    2. Railway-specific environment variables
    3. Render-specific environment variables
    4. GCP-specific environment variables
    5. AWS-specific environment variables
    6. Default to LOCAL

    Returns:
      DeploymentPlatform: The detected platform.
    """
    # Explicit platform override
    explicit_platform = os.getenv("DEPLOYMENT_PLATFORM", "").lower()
    if explicit_platform:
      try:
        return DeploymentPlatform(explicit_platform)
      except ValueError:
        pass

    # Railway.app detection
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"):
      return DeploymentPlatform.RAILWAY

    # Render.com detection
    if os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID"):
      return DeploymentPlatform.RENDER

    # GCP detection
    if os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT"):
      return DeploymentPlatform.GCP

    # AWS detection
    if os.getenv("AWS_REGION") or os.getenv("AWS_EXECUTION_ENV"):
      return DeploymentPlatform.AWS

    # Default to local development
    return DeploymentPlatform.LOCAL

  def _load_platform_config(self) -> dict:
    """Load platform-specific configuration.

    Returns:
      dict: Platform-specific configuration values.
    """
    config = {
        "platform": self.platform.value,
        "is_production": self._is_production(),
        "database_url": self._get_database_url(),
        "environment": self._get_environment(),
    }

    # Platform-specific configurations
    if self.platform == DeploymentPlatform.RAILWAY:
      config.update(self._get_railway_config())
    elif self.platform == DeploymentPlatform.RENDER:
      config.update(self._get_render_config())
    elif self.platform == DeploymentPlatform.GCP:
      config.update(self._get_gcp_config())
    elif self.platform == DeploymentPlatform.AWS:
      config.update(self._get_aws_config())
    else:
      config.update(self._get_local_config())

    return config

  def _is_production(self) -> bool:
    """Check if running in production environment.

    Returns:
      bool: True if production, False otherwise.
    """
    env = os.getenv("ENVIRONMENT", "").lower()
    railway_env = os.getenv("RAILWAY_ENVIRONMENT", "").lower()

    # Production indicators
    production_indicators = ["production", "prod", "live"]

    return (
        env in production_indicators or railway_env in production_indicators
        or self.platform
        not in [DeploymentPlatform.LOCAL,
                DeploymentPlatform.UNKNOWN])

  def _get_database_url(self) -> Optional[str]:
    """Get normalized database URL.

    Different platforms use different environment variable names:
    - Railway: DATABASE_URL (automatically provided)
    - Render: DATABASE_URL (automatically provided)
    - Local: DATABASE_URL (from .env file)
    - GCP: DATABASE_URL or constructed from Cloud SQL
    - AWS: DATABASE_URL or constructed from RDS

    Returns:
      Optional[str]: Database connection URL, or None if not configured.
    """
    # Standard DATABASE_URL (works for Railway, Render, local)
    database_url = os.getenv("DATABASE_URL")

    if database_url:
      return database_url

    # Platform-specific fallbacks
    if self.platform == DeploymentPlatform.GCP:
      # GCP Cloud SQL connection string construction
      return self._construct_gcp_database_url()

    if self.platform == DeploymentPlatform.AWS:
      # AWS RDS connection string construction
      return self._construct_aws_database_url()

    return None

  def _construct_gcp_database_url(self) -> Optional[str]:
    """Construct GCP Cloud SQL database URL.

    Returns:
      Optional[str]: Constructed database URL, or None if insufficient info.
    """
    # This would be implemented when GCP support is added
    # For now, return None to use standard DATABASE_URL
    return os.getenv("DATABASE_URL")

  def _construct_aws_database_url(self) -> Optional[str]:
    """Construct AWS RDS database URL.

    Returns:
      Optional[str]: Constructed database URL, or None if insufficient info.
    """
    # This would be implemented when AWS support is added
    # For now, return None to use standard DATABASE_URL
    return os.getenv("DATABASE_URL")

  def _get_environment(self) -> str:
    """Get normalized environment name.

    Returns:
      str: Environment name (development, staging, production).
    """
    # Read environment variables directly (not from cached config)
    # Use get() method to avoid issues with None values
    env_raw = os.getenv("ENVIRONMENT")
    railway_env_raw = os.getenv("RAILWAY_ENVIRONMENT")

    # Process environment variables
    env = env_raw.strip().lower() if env_raw else ""
    railway_env = railway_env_raw.strip().lower() if railway_env_raw else ""

    if env:
      return env
    if railway_env:
      return railway_env
    if self._is_production():
      return "production"
    return "development"

  def _get_railway_config(self) -> dict:
    """Get Railway.app-specific configuration.

    Returns:
      dict: Railway-specific configuration values.
    """
    return {
        "service_name": os.getenv("RAILWAY_SERVICE_NAME"),
        "project_id": os.getenv("RAILWAY_PROJECT_ID"),
        # Note: "environment" is already set by _get_environment()
        # RAILWAY_ENVIRONMENT is used by _get_environment() for detection
        "railway_environment": os.getenv("RAILWAY_ENVIRONMENT",
                                         "production"),
        "region": os.getenv("RAILWAY_REGION"),
        "replica_id": os.getenv("RAILWAY_REPLICA_ID"),
    }

  def _get_render_config(self) -> dict:
    """Get Render.com-specific configuration.

    Returns:
      dict: Render-specific configuration values.
    """
    return {
        "service_id": os.getenv("RENDER_SERVICE_ID"),
        "service_name": os.getenv("RENDER_SERVICE_NAME"),
        "service_type": os.getenv("RENDER_SERVICE_TYPE"),
        "region": os.getenv("RENDER_REGION"),
        "instance_id": os.getenv("RENDER_INSTANCE_ID"),
    }

  def _get_gcp_config(self) -> dict:
    """Get GCP-specific configuration.

    Returns:
      dict: GCP-specific configuration values.
    """
    return {
        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT"),
        "region": os.getenv("GCP_REGION") or os.getenv("GOOGLE_CLOUD_REGION"),
        "service_name": os.getenv("GAE_SERVICE")
        or os.getenv("CLOUD_RUN_SERVICE"),
        "instance_id": os.getenv("GAE_INSTANCE")
        or os.getenv("CLOUD_RUN_REVISION"),
    }

  def _get_aws_config(self) -> dict:
    """Get AWS-specific configuration.

    Returns:
      dict: AWS-specific configuration values.
    """
    return {
        "region": os.getenv("AWS_REGION"),
        "execution_env": os.getenv("AWS_EXECUTION_ENV"),
        "lambda_function_name": os.getenv("AWS_LAMBDA_FUNCTION_NAME"),
        "ecs_cluster": os.getenv("ECS_CLUSTER"),
        "ecs_service": os.getenv("ECS_SERVICE"),
    }

  def _get_local_config(self) -> dict:
    """Get local development configuration.

    Returns:
      dict: Local development configuration values.
    """
    return {
        # Note: "environment" is already set by _get_environment()
        # Don't overwrite it here
        "debug": os.getenv("DEBUG",
                           "False").lower() == "true",
    }

  def get(self, key: str, default=None):
    """Get a configuration value.

    Args:
      key: Configuration key.
      default: Default value if key not found.

    Returns:
      Configuration value or default.
    """
    return self._config.get(key, default)

  def get_database_url(self) -> Optional[str]:
    """Get the database URL for the current platform.

    Returns:
      Optional[str]: Database connection URL.
    """
    return self._config.get("database_url")

  def is_production(self) -> bool:
    """Check if running in production.

    Returns:
      bool: True if production environment.
    """
    return self._config.get("is_production", False)

  def get_platform(self) -> DeploymentPlatform:
    """Get the detected deployment platform.

    Returns:
      DeploymentPlatform: The current platform.
    """
    return self.platform

  def get_environment(self) -> str:
    """Get the normalized environment name.

    Returns:
      str: Environment name.
    """
    return self._config.get("environment", "development")

  def to_dict(self) -> dict:
    """Get all configuration as a dictionary.

    Returns:
      dict: Complete configuration dictionary.
    """
    return self._config.copy()


# Global deployment configuration instance
deployment = DeploymentConfig()
