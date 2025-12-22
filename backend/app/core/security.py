"""Security utilities for authentication and password hashing."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


logger = logging.getLogger(__name__)

# Bcrypt has a 72-byte limit for passwords
# We validate this but don't reveal the specific limit in error messages
MAX_PASSWORD_BYTES = 72


def validate_timezone(timezone_str: str) -> None:
  """
  Validate that a timezone string is a valid IANA timezone.

  Args:
    timezone_str: Timezone string to validate (e.g., "America/New_York").

  Raises:
    ValueError: If timezone is invalid.
  """
  try:
    from zoneinfo import ZoneInfo
    ZoneInfo(timezone_str)
  except Exception as e:
    if isinstance(e, ValueError):
      raise
    raise ValueError(f"Invalid timezone: {timezone_str}")


def validate_password_strength(password: str) -> None:
  """
  Validate password strength requirements.

  Requirements:
    - At least 8 characters
    - At most 72 bytes
    - Contains both letters and numbers
    - Contains at least one special character

  Args:
    password: The password to validate.

  Raises:
    ValueError: If password doesn't meet strength requirements.
  """
  if len(password) < 8:
    raise ValueError("Password must be at least 8 characters long.")

  password_bytes = len(password.encode('utf-8'))
  if password_bytes > MAX_PASSWORD_BYTES:
    raise ValueError("Password is too long. Please choose a shorter password.")

  has_letter = any(c.isalpha() for c in password)
  has_digit = any(c.isdigit() for c in password)
  has_special = any(not c.isalnum() for c in password)

  if not has_letter:
    raise ValueError("Password must contain at least one letter.")
  if not has_digit:
    raise ValueError("Password must contain at least one number.")
  if not has_special:
    raise ValueError("Password must contain at least one special character.")


def get_password_hash(password: str, rounds: int = 12) -> str:
  """
  Hash a password using bcrypt.

  Args:
    password: The plain text password to hash.
    rounds: Bcrypt cost factor (4-31). Default 12 for production.
        Lower values are faster but less secure. Use 4 for tests.

  Returns:
    The hashed password as a string.
  """
  return bcrypt.hashpw(password.encode("utf-8"),
                       bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
  """
  Verify a plain password against a hashed password.

  Args:
    plain_password: The plain text password to verify.
    hashed_password: The hashed password to compare against.

  Returns:
    True if passwords match, False otherwise.
  """
  return bcrypt.checkpw(
      plain_password.encode("utf-8"),
      hashed_password.encode("utf-8"),
  )


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None) -> str:
  """
  Create a JWT access token.

  Args:
    data: Dictionary containing data to encode in the token.
    expires_delta: Optional timedelta for token expiration. If not
        provided, uses default from settings.

  Returns:
    Encoded JWT token string.
  """
  logger.debug(f"create_access_token: Creating token with data: {data}")
  logger.debug(
      f"create_access_token: Using SECRET_KEY length: "
      f"{len(settings.SECRET_KEY)}, algorithm: {settings.ALGORITHM}")
  to_encode = data.copy()
  if expires_delta:
    expire = datetime.now(timezone.utc) + expires_delta
  else:
    expire = datetime.now(
        timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
  # JWT exp claim must be a Unix timestamp (int)
  to_encode.update({"exp": int(expire.timestamp())})
  encoded_jwt = jwt.encode(
      to_encode,
      settings.SECRET_KEY,
      algorithm=settings.ALGORITHM)
  logger.debug(
      f"create_access_token: Token created successfully, length:"
      f" {len(encoded_jwt)}")
  return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
  """
  Decode and verify a JWT access token.

  Args:
    token: The JWT token string to decode.

  Returns:
    Decoded token payload if valid, None otherwise.
  """
  try:
    logger.debug(
        f"decode_access_token: Attempting to decode token with SECRET_KEY "
        f"length: {len(settings.SECRET_KEY)}")
    logger.debug(f"decode_access_token: Using algorithm: {settings.ALGORITHM}")
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM])
    logger.debug(
        f"decode_access_token: Token decoded successfully, payload keys:"
        f" {list(payload.keys())}")
    return payload
  except JWTError as e:
    logger.warning(
        f"decode_access_token: JWT decode failed with error:"
        f" {type(e).__name__}: {str(e)}")
    return None
  except Exception as e:
    logger.error(
        f"decode_access_token: Unexpected error during decode:"
        f" {type(e).__name__}: {str(e)}")
    return None
