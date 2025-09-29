"""
Unit tests for Pydantic models in the Habit Tracker API.

Tests cover validation rules, constraints, and edge cases for all models.
"""

import pytest
from datetime import date, datetime
from pydantic import ValidationError
from models import (
    Habit,
    CreateHabitRequest,
    UpdateHabitRequest,
    StatsResponse,
    ErrorResponse
)


class TestHabitModel:
    """Test cases for the Habit model."""

    def test_habit_creation_with_valid_data(self):
        """Test creating a habit with all valid fields."""
        habit = Habit(
            id=1,
            name="Exercise",
            description="Daily workout routine",
            status="pending",
            streak_days=5,
            last_completed_at=date(2024, 1, 15)
        )
        
        assert habit.id == 1
        assert habit.name == "Exercise"
        assert habit.description == "Daily workout routine"
        assert habit.status == "pending"
        assert habit.streak_days == 5
        assert habit.last_completed_at == date(2024, 1, 15)

    def test_habit_creation_with_minimal_data(self):
        """Test creating a habit with only required fields."""
        habit = Habit(id=1, name="Read")
        
        assert habit.id == 1
        assert habit.name == "Read"
        assert habit.description is None
        assert habit.status == "pending"  # default value
        assert habit.streak_days == 0  # default value
        assert habit.last_completed_at is None

    def test_habit_name_validation_empty_string(self):
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Habit(id=1, name="")
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error.any_str.min_length" for error in errors)

    def test_habit_name_validation_too_long(self):
        """Test that name longer than 80 characters raises validation error."""
        long_name = "a" * 81
        with pytest.raises(ValidationError) as exc_info:
            Habit(id=1, name=long_name)
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error.any_str.max_length" for error in errors)

    def test_habit_name_validation_max_length(self):
        """Test that name with exactly 80 characters is valid."""
        max_name = "a" * 80
        habit = Habit(id=1, name=max_name)
        assert habit.name == max_name

    def test_habit_description_validation_too_long(self):
        """Test that description longer than 280 characters raises validation error."""
        long_description = "a" * 281
        with pytest.raises(ValidationError) as exc_info:
            Habit(id=1, name="Test", description=long_description)
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error.any_str.max_length" for error in errors)

    def test_habit_description_validation_max_length(self):
        """Test that description with exactly 280 characters is valid."""
        max_description = "a" * 280
        habit = Habit(id=1, name="Test", description=max_description)
        assert habit.description == max_description

    def test_habit_status_validation_invalid_value(self):
        """Test that invalid status raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Habit(id=1, name="Test", status="invalid")
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error.const" for error in errors)

    def test_habit_status_validation_valid_values(self):
        """Test that valid status values are accepted."""
        habit_pending = Habit(id=1, name="Test", status="pending")
        habit_completed = Habit(id=2, name="Test", status="completed")
        
        assert habit_pending.status == "pending"
        assert habit_completed.status == "completed"

    def test_habit_streak_days_validation_negative(self):
        """Test that negative streak_days raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Habit(id=1, name="Test", streak_days=-1)
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error.number.not_ge" for error in errors)

    def test_habit_streak_days_validation_zero(self):
        """Test that zero streak_days is valid."""
        habit = Habit(id=1, name="Test", streak_days=0)
        assert habit.streak_days == 0

    def test_habit_json_serialization(self):
        """Test that habit can be serialized to JSON with proper date formatting."""
        habit = Habit(
            id=1,
            name="Test",
            last_completed_at=date(2024, 1, 15)
        )
        
        json_data = habit.dict()
        assert json_data["last_completed_at"] == date(2024, 1, 15)


class TestCreateHabitRequest:
    """Test cases for the CreateHabitRequest model."""

    def test_create_habit_request_valid_data(self):
        """Test creating request with valid data."""
        request = CreateHabitRequest(
            name="Exercise",
            description="Daily workout"
        )
        
        assert request.name == "Exercise"
        assert request.description == "Daily workout"

    def test_create_habit_request_minimal_data(self):
        """Test creating request with only required fields."""
        request = CreateHabitRequest(name="Read")
        
        assert request.name == "Read"
        assert request.description is None

    def test_create_habit_request_name_validation_empty(self):
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            CreateHabitRequest(name="")
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error.any_str.min_length" for error in errors)

    def test_create_habit_request_name_validation_too_long(self):
        """Test that name longer than 80 characters raises validation error."""
        long_name = "a" * 81
        with pytest.raises(ValidationError) as exc_info:
            CreateHabitRequest(name=long_name)
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error.any_str.max_length" for error in errors)

    def test_create_habit_request_description_validation_too_long(self):
        """Test that description longer than 280 characters raises validation error."""
        long_description = "a" * 281
        with pytest.raises(ValidationError) as exc_info:
            CreateHabitRequest(name="Test", description=long_description)
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error.any_str.max_length" for error in errors)


class TestUpdateHabitRequest:
    """Test cases for the UpdateHabitRequest model."""

    def test_update_habit_request_all_fields(self):
        """Test updating request with all fields."""
        request = UpdateHabitRequest(
            name="Updated Exercise",
            description="Updated description",
            status="completed"
        )
        
        assert request.name == "Updated Exercise"
        assert request.description == "Updated description"
        assert request.status == "completed"

    def test_update_habit_request_partial_fields(self):
        """Test updating request with partial fields."""
        request = UpdateHabitRequest(name="Updated Name")
        
        assert request.name == "Updated Name"
        assert request.description is None
        assert request.status is None

    def test_update_habit_request_empty_object(self):
        """Test creating empty update request."""
        request = UpdateHabitRequest()
        
        assert request.name is None
        assert request.description is None
        assert request.status is None

    def test_update_habit_request_name_validation_empty(self):
        """Test that empty name raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateHabitRequest(name="")
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error.any_str.min_length" for error in errors)

    def test_update_habit_request_name_validation_too_long(self):
        """Test that name longer than 80 characters raises validation error."""
        long_name = "a" * 81
        with pytest.raises(ValidationError) as exc_info:
            UpdateHabitRequest(name=long_name)
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error.any_str.max_length" for error in errors)

    def test_update_habit_request_status_validation_invalid(self):
        """Test that invalid status raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateHabitRequest(status="invalid")
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error.const" for error in errors)

    def test_update_habit_request_status_validation_valid(self):
        """Test that valid status values are accepted."""
        request_pending = UpdateHabitRequest(status="pending")
        request_completed = UpdateHabitRequest(status="completed")
        
        assert request_pending.status == "pending"
        assert request_completed.status == "completed"


class TestStatsResponse:
    """Test cases for the StatsResponse model."""

    def test_stats_response_valid_data(self):
        """Test creating stats response with valid data."""
        stats = StatsResponse(
            total_habits=10,
            completed_today=5,
            active_streaks_ge_3=3
        )
        
        assert stats.total_habits == 10
        assert stats.completed_today == 5
        assert stats.active_streaks_ge_3 == 3

    def test_stats_response_zero_values(self):
        """Test creating stats response with zero values."""
        stats = StatsResponse(
            total_habits=0,
            completed_today=0,
            active_streaks_ge_3=0
        )
        
        assert stats.total_habits == 0
        assert stats.completed_today == 0
        assert stats.active_streaks_ge_3 == 0

    def test_stats_response_negative_values_validation(self):
        """Test that negative values raise validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            StatsResponse(
                total_habits=-1,
                completed_today=0,
                active_streaks_ge_3=0
            )
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error.number.not_ge" for error in errors)


class TestErrorResponse:
    """Test cases for the ErrorResponse model."""

    def test_error_response_valid_data(self):
        """Test creating error response with valid data."""
        error = ErrorResponse(error="Something went wrong")
        
        assert error.error == "Something went wrong"

    def test_error_response_empty_string(self):
        """Test creating error response with empty string."""
        error = ErrorResponse(error="")
        
        assert error.error == ""

    def test_error_response_missing_error_field(self):
        """Test that missing error field raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            ErrorResponse()
        
        errors = exc_info.value.errors()
        assert any(error["type"] == "value_error.missing" for error in errors)