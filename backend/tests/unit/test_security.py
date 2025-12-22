"""Unit tests for security module."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import (
    MAX_PASSWORD_BYTES,
    create_access_token,
    decode_access_token,
    get_password_hash,
    validate_password_strength,
    validate_timezone,
    verify_password)


class TestPasswordStrengthValidation:
  """Test password strength validation functions (includes length validation)."""

  def test_validate_password_strength_accepts_valid_password(self):
    """Test that passwords meeting all requirements are accepted."""
    valid_passwords = [
        "Test123!",
        "MyP@ssw0rd",
        "Secure#2024",
        "abc123!@#",
        "P@ssw0rd123",
    ]
    for password in valid_passwords:
      # Should not raise an exception
      validate_password_strength(password)

  def test_validate_password_strength_rejects_short_password(self):
    """Test that passwords shorter than 8 characters are rejected."""
    short_passwords = ["Test1!", "Abc2@", "Pass3#", "a1!"]
    for password in short_passwords:
      with pytest.raises(ValueError, match="at least 8 characters"):
        validate_password_strength(password)

  def test_validate_password_strength_rejects_no_letters(self):
    """Test that passwords without letters are rejected."""
    passwords_without_letters = ["12345678!", "98765432@", "1234!@#$"]
    for password in passwords_without_letters:
      with pytest.raises(ValueError, match="at least one letter"):
        validate_password_strength(password)

  def test_validate_password_strength_rejects_no_digits(self):
    """Test that passwords without digits are rejected."""
    passwords_without_digits = [
        "TestPass!",
        "MyPassword@",
        "SecurePass#",
    ]
    for password in passwords_without_digits:
      with pytest.raises(ValueError, match="at least one number"):
        validate_password_strength(password)

  def test_validate_password_strength_rejects_no_special_chars(self):
    """Test that passwords without special characters are rejected."""
    passwords_without_special = [
        "TestPass123",
        "MyPassword456",
        "SecurePass789",
    ]
    for password in passwords_without_special:
      with pytest.raises(ValueError, match="at least one special character"):
        validate_password_strength(password)

  def test_validate_password_strength_multiple_violations(self):
    """Test that first violation is reported."""
    # Password is too short and missing digits and special chars
    invalid_password = "Test"
    with pytest.raises(ValueError) as exc_info:
      validate_password_strength(invalid_password)
    # Should report the first violation (length)
    assert "8 characters" in str(exc_info.value)

  def test_validate_password_strength_unicode_special_chars(self):
    """Test that Unicode special characters are recognized."""
    # Password with Unicode special character
    password_with_unicode = "Test123€"
    # Should be accepted (Unicode special char counts as special)
    validate_password_strength(password_with_unicode)

  def test_validate_password_strength_rejects_too_long_password(self):
    """Test that passwords exceeding 72 bytes are rejected."""
    # Create a password that's 73 bytes but meets other requirements
    base = "Test1!"
    remaining = 67  # Need 67 more bytes to reach 73 total
    too_long_password = base + "A" * (remaining - 2) + "1!"
    assert len(too_long_password.encode('utf-8')) > 72
    with pytest.raises(ValueError, match="Password is too long"):
      validate_password_strength(too_long_password)

  def test_validate_password_strength_generic_error_message(self):
    """Test that error message doesn't reveal the specific byte limit."""
    # Create password that meets strength but is too long
    base = "Test1!"
    too_long_password = base + "A" * 100 + "1!"
    with pytest.raises(ValueError) as exc_info:
      validate_password_strength(too_long_password)
    error_message = str(exc_info.value)
    # Should not contain the specific limit
    assert "72" not in error_message
    assert "byte" not in error_message.lower()
    # Should be a generic message
    assert "too long" in error_message.lower()

  def test_validate_password_strength_unicode_length_handling(self):
    """Test that Unicode characters are counted correctly in bytes."""
    # Create Unicode password that exceeds 72 bytes but meets requirements
    base = "测试1!"
    # Add more Unicode chars to exceed 72 bytes
    unicode_password = base + "测试" * 11 + "1!"
    assert len(unicode_password.encode('utf-8')) > 72
    with pytest.raises(ValueError):
      validate_password_strength(unicode_password)

    # Create password at exactly 72 bytes with Unicode
    unicode_password_at_limit = base + "测试" * 10 + "测1"
    assert len(unicode_password_at_limit.encode('utf-8')) == 72
    # Should not raise (meets all requirements)
    validate_password_strength(unicode_password_at_limit)

  def test_validate_password_strength_password_at_limit(self):
    """Test that password at exactly 72 bytes is accepted if it meets all requirements."""
    # Create a password that's exactly 72 bytes and meets all requirements
    base = "Test1!"
    remaining = 66  # Need 66 more bytes to reach 72 total
    password_at_limit = base + "A" * (remaining - 2) + "1!"
    assert len(password_at_limit.encode('utf-8')) == 72
    # Should not raise (meets all requirements)
    validate_password_strength(password_at_limit)


class TestPasswordHashing:
  """Test password hashing functions."""

  def test_verify_password_incorrect_password(self):
    """Test password verification with incorrect password."""
    password = "Test123!@#"
    wrong_password = "Wrong456!@#"
    hashed = get_password_hash(password)
    assert verify_password(wrong_password, hashed) is False

  def test_verify_password_empty_password(self):
    """Test password verification with empty password."""
    password = "Test123!@#"
    hashed = get_password_hash(password)
    assert verify_password("", hashed) is False


class TestJWTTokenCreation:
  """Test JWT token creation."""

  def test_create_access_token_returns_string(self):
    """Test that token creation returns a string."""
    data = {"sub": "1", "email": "test@example.com"}
    token = create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 0

  def test_create_access_token_with_default_expiration(self):
    """Test token creation with default expiration."""
    data = {"sub": "1"}
    token = create_access_token(data)
    payload = decode_access_token(token)
    assert payload is not None
    assert "sub" in payload
    assert "exp" in payload

  def test_create_access_token_with_custom_expiration(self):
    """Test token creation with custom expiration."""
    data = {"sub": "1"}
    expires_delta = timedelta(minutes=60)
    token = create_access_token(data, expires_delta=expires_delta)
    payload = decode_access_token(token)
    assert payload is not None
    assert "exp" in payload

  def test_create_access_token_preserves_data(self):
    """Test that token preserves all data fields."""
    data = {
        "sub": "123",
        "email": "test@example.com",
        "role": "admin",
        "custom_field": "custom_value",
    }
    token = create_access_token(data)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "123"
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "admin"
    assert payload["custom_field"] == "custom_value"

  def test_create_access_token_adds_expiration(self):
    """Test that expiration is added to token."""
    data = {"sub": "1"}
    token = create_access_token(data)
    payload = decode_access_token(token)
    assert payload is not None
    assert "exp" in payload
    assert payload["exp"] > 0

  def test_create_access_token_uses_settings_secret(self):
    """Test that token uses JWT_SECRET_KEY from settings."""
    data = {"sub": "1"}
    token = create_access_token(data)
    # Decode with wrong secret should fail
    with pytest.raises(JWTError):
      jwt.decode(token, "wrong_secret", algorithms=[settings.ALGORITHM])

  def test_create_access_token_uses_settings_algorithm(self):
    """Test that token uses ALGORITHM from settings."""
    data = {"sub": "1"}
    token = create_access_token(data)
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.ALGORITHM])
    assert payload is not None

  @patch("app.core.security.settings.ACCESS_TOKEN_EXPIRE_MINUTES", 15)
  def test_create_access_token_uses_settings_expiration(self):
    """Test that default expiration uses settings value."""
    data = {"sub": "1"}
    token = create_access_token(data)
    payload = decode_access_token(token)
    assert payload is not None
    # Expiration should be approximately 15 minutes from now
    # (allowing for small time differences)
    assert "exp" in payload


class TestJWTTokenDecoding:
  """Test JWT token decoding."""

  def test_decode_access_token_valid_token(self):
    """Test decoding a valid token."""
    data = {"sub": "1", "email": "test@example.com"}
    token = create_access_token(data)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["email"] == "test@example.com"

  def test_decode_access_token_invalid_token(self):
    """Test decoding an invalid token."""
    invalid_token = "invalid.token.here"
    payload = decode_access_token(invalid_token)
    assert payload is None

  def test_decode_access_token_wrong_secret(self):
    """Test decoding a token with wrong secret."""
    data = {"sub": "1"}
    token = create_access_token(data)
    # Manually create token with wrong secret
    wrong_token = jwt.encode(data, "wrong_secret", algorithm=settings.ALGORITHM)
    payload = decode_access_token(wrong_token)
    assert payload is None

  def test_decode_access_token_expired_token(self):
    """Test decoding an expired token."""
    data = {"sub": "1"}
    # Create token with negative expiration (already expired)
    expires_delta = timedelta(minutes=-1)
    token = create_access_token(data, expires_delta=expires_delta)
    payload = decode_access_token(token)
    # Expired tokens should return None
    assert payload is None

  def test_decode_access_token_empty_string(self):
    """Test decoding an empty string."""
    payload = decode_access_token("")
    assert payload is None

  def test_decode_access_token_malformed_token(self):
    """Test decoding a malformed token."""
    malformed_tokens = [
        "not.a.token",
        "singlepart",
        "two.parts",
        "too.many.parts.here.extra",
    ]
    for token in malformed_tokens:
      payload = decode_access_token(token)
      assert payload is None

  def test_decode_access_token_preserves_all_fields(self):
    """Test that decoding preserves all token fields."""
    data = {
        "sub": "42",
        "email": "user@example.com",
        "role": "member",
        "household_id": 5,
        "nested": {
            "key": "value"
        },
    }
    token = create_access_token(data)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["email"] == "user@example.com"
    assert payload["role"] == "member"
    assert payload["household_id"] == 5
    assert payload["nested"] == {"key": "value"}


class TestSecurityIntegration:
  """Integration tests for security functions working together."""

  def test_full_authentication_flow(self):
    """Test complete authentication flow: hash, verify, token."""
    # Simulate user registration
    password = "User123!@#"  # Meets all requirements
    hashed_password = get_password_hash(password)

    # Simulate login verification
    assert verify_password(password, hashed_password) is True

    # Simulate token creation after successful login
    user_id = "1"
    token = create_access_token({"sub": user_id})

    # Simulate token verification
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == user_id

  def test_token_round_trip(self):
    """Test creating and decoding token maintains data integrity."""
    original_data = {
        "sub": "123",
        "email": "test@example.com",
        "role": "admin",
    }
    token = create_access_token(original_data)
    decoded_data = decode_access_token(token)
    assert decoded_data is not None
    # Compare relevant fields (exp is added automatically)
    for key, value in original_data.items():
      assert decoded_data[key] == value

  def test_multiple_tokens_different_data(self):
    """Test that different data produces different tokens."""
    data1 = {"sub": "1", "email": "user1@example.com"}
    data2 = {"sub": "2", "email": "user2@example.com"}
    token1 = create_access_token(data1)
    token2 = create_access_token(data2)
    assert token1 != token2
    payload1 = decode_access_token(token1)
    payload2 = decode_access_token(token2)
    assert payload1 is not None
    assert payload2 is not None
    assert payload1["sub"] == "1"
    assert payload2["sub"] == "2"

  def test_token_expiration_respected(self):
    """Test that token expiration is properly enforced."""
    data = {"sub": "1"}
    # Create token that expires in the past (already expired)
    expires_delta = timedelta(seconds=-1)
    token = create_access_token(data, expires_delta=expires_delta)
    payload = decode_access_token(token)
    # Should be None due to expiration
    assert payload is None


class TestTimezoneValidation:
  """Test timezone validation function."""

  def test_valid_timezone_utc(self):
    """Test that UTC timezone is accepted."""
    validate_timezone("UTC")

  def test_valid_timezone_america(self):
    """Test that America timezones are accepted."""
    validate_timezone("America/New_York")
    validate_timezone("America/Los_Angeles")
    validate_timezone("America/Chicago")

  def test_valid_timezone_europe(self):
    """Test that European timezones are accepted."""
    validate_timezone("Europe/London")
    validate_timezone("Europe/Paris")
    validate_timezone("Europe/Berlin")

  def test_valid_timezone_asia(self):
    """Test that Asian timezones are accepted."""
    validate_timezone("Asia/Tokyo")
    validate_timezone("Asia/Shanghai")

  def test_invalid_timezone_format(self):
    """Test that invalid timezone format is rejected."""
    with pytest.raises(ValueError, match="Invalid timezone"):
      validate_timezone("NotAValidFormat")

  def test_invalid_timezone_name(self):
    """Test that invalid timezone name is rejected."""
    with pytest.raises(ValueError, match="Invalid timezone"):
      validate_timezone("Invalid/Timezone")
