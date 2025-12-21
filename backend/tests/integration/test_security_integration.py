"""Integration tests for security module with real dependencies."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password)


@pytest.mark.integration
class TestSecurityWithRealDependencies:
  """Integration tests using real bcrypt and JWT libraries."""

  def test_password_hashing_with_real_bcrypt(self):
    """Test password hashing with actual bcrypt implementation."""
    password = "complex_P@ssw0rd_123!@#"
    hashed = get_password_hash(password)
    # Verify it's a valid bcrypt hash
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(password, hashed) is True
    assert isinstance(hashed, str)
    assert len(hashed) > 0
    assert hashed != password

  def test_jwt_token_with_real_jose(self):
    """Test JWT token creation and decoding with real jose library."""
    data = {"sub": "1", "email": "test@example.com"}
    token = create_access_token(data)
    # Verify token structure (JWT has 3 parts separated by dots)
    parts = token.split(".")
    assert len(parts) == 3
    # Decode and verify
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "1"

  def test_token_verification_with_different_secrets(self):
    """Test that tokens are properly validated against secret key."""
    data = {"sub": "1"}
    token = create_access_token(data)
    # Should decode successfully with correct secret
    payload = decode_access_token(token)
    assert payload is not None
    # Should fail with wrong secret (tested via decode_access_token)
    wrong_secret_token = jwt.encode(
        data,
        "wrong_secret",
        algorithm=settings.ALGORITHM)
    wrong_payload = decode_access_token(wrong_secret_token)
    assert wrong_payload is None

  def test_password_verification_edge_cases(self):
    """Test password verification with edge case passwords."""
    # Note: These passwords bypass strength validation for testing hashing
    # In production, passwords must meet strength requirements
    edge_cases = [
        "LongPass123!@#456789012345",  # Valid password meeting requirements
        "Unicode测试1!",  # Unicode with requirements
    ]
    for password in edge_cases:
      # Bcrypt has 72 byte limit, skip if too long
      if len(password.encode('utf-8')) <= 72:
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        assert verify_password(password + "x", hashed) is False

  def test_token_with_various_data_types(self):
    """Test token creation with various data types."""
    test_cases = [
        {"sub": "1"},  # String ID
        {"sub": "string_id"},  # String
        {"sub": "1", "active": True},  # Boolean
        {"sub": "1", "score": 95.5},  # Float
        {"sub": "1", "tags": ["admin", "user"]},  # List
        {"sub": "1", "meta": {"key": "value"}},  # Dict
    ]
    for data in test_cases:
      token = create_access_token(data)
      payload = decode_access_token(token)
      assert payload is not None
      for key, value in data.items():
        assert payload[key] == value

  def test_token_expiration_timing(self):
    """Test that token expiration timing works correctly."""
    data = {"sub": "1"}
    # Create token that expires in the past (already expired)
    expires_delta = timedelta(seconds=-1)
    token = create_access_token(data, expires_delta=expires_delta)
    # Should be expired immediately
    payload = decode_access_token(token)
    assert payload is None

  def test_multiple_concurrent_tokens(self):
    """Test creating and verifying multiple tokens concurrently."""
    tokens = []
    for i in range(10):
      data = {"sub": str(i), "email": f"user{i}@example.com"}
      token = create_access_token(data)
      tokens.append((str(i), token))
    # Verify all tokens
    for user_id, token in tokens:
      payload = decode_access_token(token)
      assert payload is not None
      assert payload["sub"] == user_id

  def test_password_hash_performance(self):
    """Test that password hashing is reasonably fast."""
    import time
    password = "Test123!@#"
    start = time.time()
    hashed = get_password_hash(password, rounds=12)
    elapsed = time.time() - start
    # Should complete in reasonable time (< 0.3 second)
    assert elapsed < 0.3
    # Verify it works
    assert verify_password(password, hashed) is True

  def test_token_creation_performance(self):
    """Test that token creation is fast."""
    import time
    data = {"sub": "1"}
    start = time.time()
    token = create_access_token(data)
    elapsed = time.time() - start
    # Should be very fast (< 0.1 seconds)
    assert elapsed < 0.1
    # Verify it works
    payload = decode_access_token(token)
    assert payload is not None

  @patch("app.core.security.settings.SECRET_KEY", "test-secret-key")
  @patch("app.core.security.settings.ALGORITHM", "HS256")
  def test_security_with_custom_settings(self):
    """Test security functions with custom settings."""
    data = {"sub": "1"}
    token = create_access_token(data)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "1"

  def test_password_hash_uniqueness(self):
    """Test that password hashes are unique even for same password."""
    password = "SamePass123!@#"
    hashes = [get_password_hash(password) for _ in range(3)]
    # All hashes should be different (due to salt)
    assert len(set(hashes)) == 3
    # But all should verify correctly
    for hashed in hashes:
      assert verify_password(password, hashed) is True

  def test_token_with_large_payload(self):
    """Test token creation with large payload."""
    large_data = {
        "sub": "1",
        "permissions": [f"perm_{i}" for i in range(100)],
        "metadata": {
            f"key_{i}": f"value_{i}"
            for i in range(50)
        },
    }
    token = create_access_token(large_data)
    payload = decode_access_token(token)
    assert payload is not None
    assert len(payload["permissions"]) == 100
    assert len(payload["metadata"]) == 50
