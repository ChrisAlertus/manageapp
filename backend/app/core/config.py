"""Application configuration management."""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  """Application settings loaded from environment variables."""

  # Application
  PROJECT_NAME: str = "Household Management API"
  VERSION: str = "1.0.0"
  API_V1_STR: str = "/api/v1"
  DEBUG: bool = False

  # Security
  JWT_SECRET_KEY: str
  ALGORITHM: str = "HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

  # Database
  DATABASE_URL: str

  # CORS - Allow override via environment variable
  BACKEND_CORS_ORIGINS: str = (
      "http://localhost:3000,http://localhost:5173,"
      "http://localhost:5174,http://localhost:8080")

  @property
  def cors_origins_list(self) -> List[str]:
    """Parse CORS origins from comma-separated string."""
    return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(',')]

  # Invitations / Email
  INVITATION_EXPIRE_HOURS: int = 168  # 7 days
  INVITATION_ACCEPT_URL_BASE: str = "http://localhost:3000/invitations/accept"

  EMAIL_PROVIDER: str = "console"  # console | resend
  EMAIL_FROM: str = "no-reply@localhost"
  RESEND_API_KEY: str | None = None

  model_config = SettingsConfigDict(
      env_file=".env",
      case_sensitive=True,
  )


settings = Settings()
