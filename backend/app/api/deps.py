"""FastAPI dependencies for authentication and database access."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
  """
  Get the current authenticated user from JWT token.

  Args:
    db: Database session.
    token: JWT access token from request.

  Returns:
    Current authenticated user.

  Raises:
    HTTPException: If token is invalid or user not found.
  """
  credentials_exception = HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Could not validate credentials",
      headers={"WWW-Authenticate": "Bearer"},
  )
  payload = decode_access_token(token)
  if payload is None:
    raise credentials_exception
  user_id: Optional[int] = payload.get("sub")
  if user_id is None:
    raise credentials_exception
  user = db.query(User).get(user_id)
  if user is None:
    raise credentials_exception

  return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
  """
  Get the current active user.

  Args:
    current_user: Current authenticated user.

  Returns:
    Current active user.

  Raises:
    HTTPException: If user is not active.
  """
  if not current_user.is_active:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Inactive user",
    )
  return current_user
