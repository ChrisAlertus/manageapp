"""Authentication endpoints."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password)
from app.models.user import User
from app.schemas.user import Token, User as UserSchema, UserCreate, UserLogin


router = APIRouter()


@router.post(
    "/register",
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
  """
  Register a new user.

  Args:
    user_in: User registration data.
    db: Database session.

  Returns:
    Created user object.

  Raises:
    HTTPException: If email already exists.
  """
  # Check if user already exists
  existing_user = db.query(User).filter(User.email == user_in.email).first()
  if existing_user:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Email already registered",
    )

  # Create new user
  hashed_password = get_password_hash(user_in.password)
  db_user = User(
      email=user_in.email,
      hashed_password=hashed_password,
      full_name=user_in.full_name,
      phone_number=user_in.phone_number,
  )
  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return db_user


@router.post("/login", response_model=Token)
def login(
    user_in: UserLogin,
    db: Session = Depends(get_db),
):
  """
  Authenticate user and return JWT token.

  Args:
    user_in: User login credentials.
    db: Database session.

  Returns:
    JWT access token.

  Raises:
    HTTPException: If credentials are invalid.
  """
  user = db.query(User).filter(User.email == user_in.email).first()
  if not user or not verify_password(user_in.password, user.hashed_password):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
  if not user.is_active:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Inactive user",
    )

  access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
  access_token = create_access_token(
      data={"sub": str(user.id)},  # JWT requires sub to be a string
      expires_delta=access_token_expires)
  return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_active_user)):
  """
  Get current authenticated user information.

  Args:
    current_user: Current authenticated user from dependency.

  Returns:
    Current user information.
  """
  return current_user
