"""Unit tests for user Pydantic schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate


class TestUserCreateSchema:
  """Test UserCreate schema validation."""

  def test_valid_user_create(self):
    """Test that valid user data passes validation."""
    user_data = {
        "email": "test@example.com",
        "password": "ValidPass123!",
        "full_name": "Test User",
    }
    user = UserCreate(**user_data)
    assert user.email == "test@example.com"
    assert user.password == "ValidPass123!"
    assert user.full_name == "Test User"

  def test_user_create_empty_password(self):
    """Test that empty password is rejected."""
    user_data = {
        "email": "test@example.com",
        "password": "",
    }
    with pytest.raises(ValidationError) as exc_info:
      UserCreate(**user_data)
    errors = exc_info.value.errors()
    assert any(
        error["loc"] == ("password",
                         ) and "empty" in str(error["msg"]).lower()
        for error in errors)

  def test_user_create_weak_password_short(self):
    """Test that passwords shorter than 8 characters are rejected."""
    user_data = {
        "email": "test@example.com",
        "password": "Test1!",
    }
    with pytest.raises(ValidationError) as exc_info:
      UserCreate(**user_data)
    errors = exc_info.value.errors()
    password_errors = [
        error for error in errors if error["loc"] == ("password", )
    ]
    assert len(password_errors) > 0
    assert "8 characters" in str(password_errors[0]["msg"]).lower()

  def test_user_create_weak_password_no_letters(self):
    """Test that passwords without letters are rejected."""
    user_data = {
        "email": "test@example.com",
        "password": "12345678!",
    }
    with pytest.raises(ValidationError) as exc_info:
      UserCreate(**user_data)
    errors = exc_info.value.errors()
    password_errors = [
        error for error in errors if error["loc"] == ("password", )
    ]
    assert len(password_errors) > 0
    assert "letter" in str(password_errors[0]["msg"]).lower()

  def test_user_create_weak_password_no_digits(self):
    """Test that passwords without digits are rejected."""
    user_data = {
        "email": "test@example.com",
        "password": "TestPass!",
    }
    with pytest.raises(ValidationError) as exc_info:
      UserCreate(**user_data)
    errors = exc_info.value.errors()
    password_errors = [
        error for error in errors if error["loc"] == ("password", )
    ]
    assert len(password_errors) > 0
    assert "number" in str(password_errors[0]["msg"]).lower()

  def test_user_create_weak_password_no_special(self):
    """Test that passwords without special characters are rejected."""
    user_data = {
        "email": "test@example.com",
        "password": "TestPass123",
    }
    with pytest.raises(ValidationError) as exc_info:
      UserCreate(**user_data)
    errors = exc_info.value.errors()
    password_errors = [
        error for error in errors if error["loc"] == ("password", )
    ]
    assert len(password_errors) > 0
    assert "special character" in str(password_errors[0]["msg"]).lower()

  def test_user_create_valid_strong_password(self):
    """Test that passwords meeting all requirements are accepted."""
    user_data = {
        "email": "test@example.com",
        "password": "Test123!@#",
    }
    user = UserCreate(**user_data)
    assert user.password == "Test123!@#"

  def test_user_create_too_long_password(self):
    """Test that password exceeding 72 bytes is rejected."""
    # Create a password that's 73 bytes but meets strength requirements
    # "Test1!" is 6 bytes, so we need 67 more bytes to reach 73
    # Use pattern that includes letters, numbers, and special chars
    base = "Test1!"
    remaining = 67  # Need 67 more bytes to reach 73 total
    # Add characters that include all requirements
    too_long_password = base + "A" * (remaining - 2) + "1!"
    assert len(too_long_password.encode('utf-8')) > 72
    user_data = {
        "email": "test@example.com",
        "password": too_long_password,
    }
    with pytest.raises(ValidationError) as exc_info:
      UserCreate(**user_data)
    errors = exc_info.value.errors()
    # Should have a validation error for password
    password_errors = [
        error for error in errors if error["loc"] == ("password", )
    ]
    assert len(password_errors) > 0
    # Error message should not reveal the specific limit
    error_msg = str(password_errors[0]["msg"]).lower()
    assert "72" not in error_msg
    assert "byte" not in error_msg
    assert "too long" in error_msg or "long" in error_msg

  def test_user_create_password_at_limit(self):
    """Test that password at exactly 72 bytes is accepted."""
    # Create a password that's exactly 72 bytes and meets all requirements
    # "Test1!" is 6 bytes, so we need 66 more bytes to reach 72 total
    base = "Test1!"
    remaining = 66  # Need 66 more bytes to reach 72 total
    # Add characters that include all requirements
    password_at_limit = base + "A" * (remaining - 2) + "1!"
    assert len(password_at_limit.encode('utf-8')) == 72
    user_data = {
        "email": "test@example.com",
        "password": password_at_limit,
    }
    user = UserCreate(**user_data)
    assert user.password == password_at_limit

  def test_user_create_unicode_password_validation(self):
    """Test that Unicode passwords are validated correctly."""
    # Each Chinese character is 3 bytes in UTF-8
    # Create password with Unicode that meets requirements and exceeds limit
    # "测试1!" = 3+3+1+1 = 8 bytes, need 65 more to exceed 72
    # Use pattern: 测试1! + more chars
    base = "测试1!"
    # Add more Unicode chars to exceed 72 bytes but still meet requirements
    # 22 more Chinese chars = 66 bytes, total = 74 bytes (over limit)
    unicode_password = base + "测试" * 11 + "1!"
    assert len(unicode_password.encode('utf-8')) > 72
    user_data = {
        "email": "test@example.com",
        "password": unicode_password,
    }
    with pytest.raises(ValidationError):
      UserCreate(**user_data)

    # Create password at exactly 72 bytes with Unicode
    # "测试1!" = 8 bytes, need 64 more bytes
    # 21 Chinese chars = 63 bytes, plus "1" = 1 byte, total = 64 bytes
    unicode_password_at_limit = base + "测试" * 10 + "测1"
    assert len(unicode_password_at_limit.encode('utf-8')) == 72
    user_data = {
        "email": "test@example.com",
        "password": unicode_password_at_limit,
    }
    user = UserCreate(**user_data)
    assert user.password == unicode_password_at_limit

  def test_user_create_optional_full_name(self):
    """Test that full_name is optional."""
    user_data = {
        "email": "test@example.com",
        "password": "ValidPass123!",
    }
    user = UserCreate(**user_data)
    assert user.full_name is None

  def test_user_create_with_valid_timezone(self):
    """Test that valid timezone is accepted."""
    user_data = {
        "email": "test@example.com",
        "password": "ValidPass123!",
        "timezone": "America/Toronto",
    }
    user = UserCreate(**user_data)
    assert user.timezone == "America/Toronto"

  def test_user_create_with_utc_timezone(self):
    """Test that UTC timezone is accepted."""
    user_data = {
        "email": "test@example.com",
        "password": "ValidPass123!",
        "timezone": "UTC",
    }
    user = UserCreate(**user_data)
    assert user.timezone == "UTC"

  def test_user_create_without_timezone(self):
    """Test that timezone is optional and defaults to None."""
    user_data = {
        "email": "test@example.com",
        "password": "ValidPass123!",
    }
    user = UserCreate(**user_data)
    assert user.timezone is None

  def test_user_create_with_invalid_timezone(self):
    """Test that invalid timezone is rejected."""
    user_data = {
        "email": "test@example.com",
        "password": "ValidPass123!",
        "timezone": "Invalid/Timezone",
    }
    with pytest.raises(ValidationError) as exc_info:
      UserCreate(**user_data)
    errors = exc_info.value.errors()
    assert any(
        error["loc"] == ("timezone",
                         ) and "Invalid timezone" in str(error["msg"])
        for error in errors)

  def test_user_create_with_malformed_timezone(self):
    """Test that malformed timezone format is rejected."""
    user_data = {
        "email": "test@example.com",
        "password": "ValidPass123!",
        "timezone": "NotAValidFormat",
    }
    with pytest.raises(ValidationError) as exc_info:
      UserCreate(**user_data)
    errors = exc_info.value.errors()
    assert any(
        error["loc"] == ("timezone",
                         ) and (
                             "Invalid timezone" in str(error["msg"])
                             or "Invalid timezone format" in str(error["msg"]))
        for error in errors)

  def test_user_create_with_common_timezones(self):
    """Test that common timezones are accepted."""
    common_timezones = [
        "America/New_York",
        "America/Toronto",
        "Europe/London",
        "Europe/Paris",
        "Asia/Tokyo",
        "Australia/Sydney",
    ]
    for tz in common_timezones:
      user_data = {
          "email": f"test_{tz.replace('/', '_')}@example.com",
          "password": "ValidPass123!",
          "timezone": tz,
      }
      user = UserCreate(**user_data)
      assert user.timezone == tz
