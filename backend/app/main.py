"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, households, invitations
from app.core.config import settings


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Household Management API for expense splitting, "
    "chore scheduling, and shared to-do lists",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["auth"])
app.include_router(
    households.router,
    prefix=f"{settings.API_V1_STR}/households",
    tags=["households"])
app.include_router(
    invitations.router,
    prefix=f"{settings.API_V1_STR}",
    tags=["invitations"])


@app.get("/")
def root():
  """
  Root endpoint.

  Returns:
    API information.
  """
  return {
      "message": "Household Management API",
      "version": settings.VERSION,
      "docs": "/docs",
  }


@app.get("/health")
def health_check():
  """
  Health check endpoint.

  Returns:
    Health status.
  """
  return {"status": "healthy"}
