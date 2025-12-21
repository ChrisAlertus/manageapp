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
  SECRET_KEY: str
  ALGORITHM: str = "HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

  # Database
  DATABASE_URL: str

  # CORS
  BACKEND_CORS_ORIGINS: List[str] = [
      "http://localhost:3000",
      "http://localhost:8080",
  ]

  model_config = SettingsConfigDict(
      env_file=".env",
      case_sensitive=True,
  )


settings = Settings()
