"""Unit tests for household Pydantic schemas."""

import pytest

from datetime import datetime, timezone

from pydantic import ValidationError

from app.schemas.household import HouseholdCreate, HouseholdRead


class TestHouseholdCreateSchema:
  """Test HouseholdCreate schema validation."""

  def test_valid_household_create(self):
    """Test that valid household data passes validation."""
    household_data = {
        "name": "My Household",
        "description": "A test household",
    }
    household = HouseholdCreate(**household_data)
    assert household.name == "My Household"
    assert household.description == "A test household"

  def test_household_create_empty_name(self):
    """Test that empty name is rejected."""
    household_data = {
        "name": "",
        "description": "A test household",
    }
    with pytest.raises(ValidationError) as exc_info:
      HouseholdCreate(**household_data)
    errors = exc_info.value.errors()
    assert any(
        error["loc"] == (
            "name",
        ) and "at least 1 character" in str(error["msg"]).lower()
        for error in errors)

  def test_household_create_no_name(self):
    """Test that missing name is rejected."""
    household_data = {
        "description": "A test household",
    }
    with pytest.raises(ValidationError):
      HouseholdCreate(**household_data)

  def test_household_create_optional_description(self):
    """Test that description is optional."""
    household_data = {
        "name": "My Household",
    }
    household = HouseholdCreate(**household_data)
    assert household.name == "My Household"
    assert household.description is None

  def test_household_create_long_name(self):
    """Test that name exceeding 255 characters is rejected."""
    household_data = {
        "name": "A" * 256,
        "description": "A test household",
    }
    with pytest.raises(ValidationError) as exc_info:
      HouseholdCreate(**household_data)
    errors = exc_info.value.errors()
    assert any(
        error["loc"] == (
            "name",
        ) and "at most 255 characters" in str(error["msg"]).lower()
        for error in errors)

  def test_household_create_name_at_limit(self):
    """Test that name at exactly 255 characters is accepted."""
    household_data = {
        "name": "A" * 255,
        "description": "A test household",
    }
    household = HouseholdCreate(**household_data)
    assert len(household.name) == 255


class TestHouseholdReadSchema:
  """Test HouseholdRead schema validation."""

  def test_valid_household_read(self):
    """Test that valid household read data passes validation."""
    from datetime import datetime

    household_data = {
        "id": 1,
        "name": "My Household",
        "description": "A test household",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    household = HouseholdRead(**household_data)
    assert household.id == 1
    assert household.name == "My Household"
    assert household.description == "A test household"

  def test_household_read_optional_description(self):
    """Test that description can be None in read schema."""
    from datetime import datetime

    household_data = {
        "id": 1,
        "name": "My Household",
        "description": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    household = HouseholdRead(**household_data)
    assert household.description is None
