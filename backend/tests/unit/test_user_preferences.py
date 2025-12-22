"""Unit tests for user preferences schemas and validation."""

import pytest
from pydantic import ValidationError

from app.schemas.user_preferences import (
    CurrencyCode,
    UserPreferencesBase,
    UserPreferencesUpdate,
)


class TestCurrencyCode:
  """Test CurrencyCode enum."""

  def test_valid_currency_codes(self):
    """Test that all valid currency codes are accepted."""
    valid_codes = ["CAD", "USD", "EUR", "BBD", "BRL"]
    for code in valid_codes:
      currency = CurrencyCode(code)
      assert currency.value == code

  def test_currency_code_case_insensitive(self):
    """Test that currency codes are case-insensitive in validation."""
    # This will be handled by the validator in the schema
    pass


class TestUserPreferencesBase:
  """Test UserPreferencesBase schema validation."""

  def test_default_values(self):
    """Test that default values are set correctly."""
    prefs = UserPreferencesBase()
    assert prefs.preferred_currency == CurrencyCode.CAD
    assert prefs.timezone == "UTC"
    assert prefs.language == "en"

  def test_valid_currency_codes(self):
    """Test that valid currency codes are accepted."""
    for currency in CurrencyCode:
      prefs = UserPreferencesBase(preferred_currency=currency)
      assert prefs.preferred_currency == currency

  def test_invalid_currency_code(self):
    """Test that invalid currency codes are rejected."""
    with pytest.raises(ValidationError) as exc_info:
      UserPreferencesBase(preferred_currency="INVALID")
    errors = exc_info.value.errors()
    assert any(
        error["loc"] == ("preferred_currency",
                         ) and "Invalid currency code" in str(error["msg"])
        for error in errors)

  def test_currency_code_case_insensitive_string(self):
    """Test that currency codes are converted to uppercase."""
    prefs = UserPreferencesBase(preferred_currency="usd")
    assert prefs.preferred_currency == CurrencyCode.USD

    prefs = UserPreferencesBase(preferred_currency="cad")
    assert prefs.preferred_currency == CurrencyCode.CAD

  def test_custom_timezone(self):
    """Test that custom timezone values are accepted."""
    prefs = UserPreferencesBase(timezone="America/New_York")
    assert prefs.timezone == "America/New_York"

  def test_custom_language(self):
    """Test that custom language values are accepted."""
    prefs = UserPreferencesBase(language="fr")
    assert prefs.language == "fr"

  def test_timezone_max_length(self):
    """Test that timezone respects max length."""
    long_timezone = "A" * 51  # Exceeds max_length=50
    with pytest.raises(ValidationError) as exc_info:
      UserPreferencesBase(timezone=long_timezone)
    errors = exc_info.value.errors()
    assert any(
        error["loc"] == ("timezone",
                         ) and "at most 50" in str(error["msg"]).lower()
        for error in errors)

  def test_language_max_length(self):
    """Test that language respects max length."""
    long_language = "A" * 11  # Exceeds max_length=10
    with pytest.raises(ValidationError) as exc_info:
      UserPreferencesBase(language=long_language)
    errors = exc_info.value.errors()
    assert any(
        error["loc"] == ("language",
                         ) and "at most 10" in str(error["msg"]).lower()
        for error in errors)


class TestUserPreferencesUpdate:
  """Test UserPreferencesUpdate schema validation."""

  def test_all_fields_optional(self):
    """Test that all fields are optional in update schema."""
    prefs = UserPreferencesUpdate()
    assert prefs.preferred_currency is None
    assert prefs.timezone is None
    assert prefs.language is None

  def test_partial_update_currency(self):
    """Test updating only currency."""
    prefs = UserPreferencesUpdate(preferred_currency=CurrencyCode.USD)
    assert prefs.preferred_currency == CurrencyCode.USD
    assert prefs.timezone is None
    assert prefs.language is None

  def test_partial_update_timezone(self):
    """Test updating only timezone."""
    prefs = UserPreferencesUpdate(timezone="America/New_York")
    assert prefs.preferred_currency is None
    assert prefs.timezone == "America/New_York"
    assert prefs.language is None

  def test_partial_update_language(self):
    """Test updating only language."""
    prefs = UserPreferencesUpdate(language="fr")
    assert prefs.preferred_currency is None
    assert prefs.timezone is None
    assert prefs.language == "fr"

  def test_update_all_fields(self):
    """Test updating all fields at once."""
    prefs = UserPreferencesUpdate(
        preferred_currency=CurrencyCode.EUR,
        timezone="Europe/Paris",
        language="fr")
    assert prefs.preferred_currency == CurrencyCode.EUR
    assert prefs.timezone == "Europe/Paris"
    assert prefs.language == "fr"

  def test_invalid_currency_code_in_update(self):
    """Test that invalid currency codes are rejected in update."""
    with pytest.raises(ValidationError) as exc_info:
      UserPreferencesUpdate(preferred_currency="INVALID")
    errors = exc_info.value.errors()
    assert any(
        error["loc"] == ("preferred_currency",
                         ) and "Invalid currency code" in str(error["msg"])
        for error in errors)

  def test_currency_code_case_insensitive_in_update(self):
    """Test that currency codes are converted to uppercase in update."""
    prefs = UserPreferencesUpdate(preferred_currency="brl")
    assert prefs.preferred_currency == CurrencyCode.BRL
