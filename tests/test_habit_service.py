"""
Unit tests for the HabitService class.

This module contains comprehensive tests for all business logic including
streak calculations, validation, and error handling.
"""

import pytest
from datetime import date, timedelta
from models.habit import CreateHabitRequest, UpdateHabitRequest
from repositories.habit_repository import HabitRepository
from services.habit_service import (
    HabitService, 
    HabitNotFoundError, 
    DuplicateCompletionError,
    InvalidHabitDataError,
    HabitOperationError
)


@pytest.fixture
def repository():
    """Create a fresh repository for each test."""
    return HabitRepository()


@pytest.fixture
def service(repository):
    """Create a habit service with a fresh repository."""
    return HabitService(repository)


@pytest.fixture
def sample_habit_request():
    """Create a sample habit creation request."""
    return CreateHabitRequest(
        name="Exercise",
        description="Daily workout routine"
    )


class TestHabitCreation:
    """Tests for habit creation functionality."""
    
    def test_create_habit_with_name_and_description(self, service, sample_habit_request):
        """Test creating a habit with name and description."""
        habit = service.create_habit(sample_habit_request)
        
        assert habit.id == 1
        assert habit.name == "Exercise"
        assert habit.description == "Daily workout routine"
        assert habit.status == "pending"
        assert habit.streak_days == 0
        assert habit.last_completed_at is None
    
    def test_create_habit_with_name_only(self, service):
        """Test creating a habit with only a name."""
        request = CreateHabitRequest(name="Read")
        habit = service.create_habit(request)
        
        assert habit.name == "Read"
        assert habit.description is None
        assert habit.status == "pending"
        assert habit.streak_days == 0
        assert habit.last_completed_at is None
    
    def test_create_multiple_habits_auto_increment_ids(self, service):
        """Test that multiple habits get auto-incrementing IDs."""
        habit1 = service.create_habit(CreateHabitRequest(name="Habit 1"))
        habit2 = service.create_habit(CreateHabitRequest(name="Habit 2"))
        
        assert habit1.id == 1
        assert habit2.id == 2


class TestHabitRetrieval:
    """Tests for habit retrieval functionality."""
    
    def test_get_habits_empty_list(self, service):
        """Test getting habits when none exist."""
        habits = service.get_habits()
        assert habits == []
    
    def test_get_all_habits(self, service):
        """Test getting all habits without filtering."""
        service.create_habit(CreateHabitRequest(name="Habit 1"))
        service.create_habit(CreateHabitRequest(name="Habit 2"))
        
        habits = service.get_habits()
        assert len(habits) == 2
        assert habits[0].name == "Habit 1"
        assert habits[1].name == "Habit 2"
    
    def test_get_habits_filtered_by_status(self, service):
        """Test getting habits filtered by status."""
        habit1 = service.create_habit(CreateHabitRequest(name="Pending Habit"))
        habit2 = service.create_habit(CreateHabitRequest(name="Completed Habit"))
        
        # Complete one habit
        service.complete_habit_today(habit2.id)
        
        pending_habits = service.get_habits(status="pending")
        completed_habits = service.get_habits(status="completed")
        
        assert len(pending_habits) == 1
        assert pending_habits[0].name == "Pending Habit"
        assert len(completed_habits) == 1
        assert completed_habits[0].name == "Completed Habit"
    
    def test_get_habit_by_id_success(self, service, sample_habit_request):
        """Test successfully getting a habit by ID."""
        created_habit = service.create_habit(sample_habit_request)
        retrieved_habit = service.get_habit_by_id(created_habit.id)
        
        assert retrieved_habit.id == created_habit.id
        assert retrieved_habit.name == created_habit.name
    
    def test_get_habit_by_id_not_found(self, service):
        """Test getting a habit by non-existent ID."""
        with pytest.raises(HabitNotFoundError, match="Habit with ID 999 not found"):
            service.get_habit_by_id(999)


class TestHabitUpdate:
    """Tests for habit update functionality."""
    
    def test_update_habit_name(self, service, sample_habit_request):
        """Test updating a habit's name."""
        habit = service.create_habit(sample_habit_request)
        update_request = UpdateHabitRequest(name="Updated Exercise")
        
        updated_habit = service.update_habit(habit.id, update_request)
        
        assert updated_habit.name == "Updated Exercise"
        assert updated_habit.description == habit.description  # Unchanged
        assert updated_habit.status == habit.status  # Unchanged
    
    def test_update_habit_description(self, service, sample_habit_request):
        """Test updating a habit's description."""
        habit = service.create_habit(sample_habit_request)
        update_request = UpdateHabitRequest(description="Updated description")
        
        updated_habit = service.update_habit(habit.id, update_request)
        
        assert updated_habit.description == "Updated description"
        assert updated_habit.name == habit.name  # Unchanged
    
    def test_update_habit_status(self, service, sample_habit_request):
        """Test updating a habit's status."""
        habit = service.create_habit(sample_habit_request)
        update_request = UpdateHabitRequest(status="completed")
        
        updated_habit = service.update_habit(habit.id, update_request)
        
        assert updated_habit.status == "completed"
        assert updated_habit.streak_days == 0  # Status change doesn't affect streak
    
    def test_update_habit_multiple_fields(self, service, sample_habit_request):
        """Test updating multiple fields at once."""
        habit = service.create_habit(sample_habit_request)
        update_request = UpdateHabitRequest(
            name="New Name",
            description="New Description",
            status="completed"
        )
        
        updated_habit = service.update_habit(habit.id, update_request)
        
        assert updated_habit.name == "New Name"
        assert updated_habit.description == "New Description"
        assert updated_habit.status == "completed"
    
    def test_update_habit_not_found(self, service):
        """Test updating a non-existent habit."""
        update_request = UpdateHabitRequest(name="New Name")
        
        with pytest.raises(HabitNotFoundError, match="Habit with ID 999 not found"):
            service.update_habit(999, update_request)


class TestHabitDeletion:
    """Tests for habit deletion functionality."""
    
    def test_delete_habit_success(self, service, sample_habit_request):
        """Test successfully deleting a habit."""
        habit = service.create_habit(sample_habit_request)
        
        service.delete_habit(habit.id)
        
        with pytest.raises(HabitNotFoundError):
            service.get_habit_by_id(habit.id)
    
    def test_delete_habit_not_found(self, service):
        """Test deleting a non-existent habit."""
        with pytest.raises(HabitNotFoundError, match="Habit with ID 999 not found"):
            service.delete_habit(999)


class TestHabitCompletion:
    """Tests for habit completion and streak calculation functionality."""
    
    def test_complete_habit_first_time(self, service, sample_habit_request):
        """Test completing a habit for the first time."""
        habit = service.create_habit(sample_habit_request)
        today = date.today()
        
        completed_habit = service.complete_habit_today(habit.id)
        
        assert completed_habit.status == "completed"
        assert completed_habit.streak_days == 1
        assert completed_habit.last_completed_at == today
    
    def test_complete_habit_consecutive_days(self, service, sample_habit_request):
        """Test completing a habit on consecutive days."""
        habit = service.create_habit(sample_habit_request)
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Complete yesterday
        service.complete_habit_today(habit.id, yesterday)
        # Complete today
        completed_habit = service.complete_habit_today(habit.id, today)
        
        assert completed_habit.streak_days == 2
        assert completed_habit.last_completed_at == today
    
    def test_complete_habit_streak_increment(self, service, sample_habit_request):
        """Test streak incrementing over multiple consecutive days."""
        habit = service.create_habit(sample_habit_request)
        base_date = date.today() - timedelta(days=2)
        
        # Complete for 3 consecutive days
        for i in range(3):
            completion_date = base_date + timedelta(days=i)
            completed_habit = service.complete_habit_today(habit.id, completion_date)
        
        assert completed_habit.streak_days == 3
    
    def test_complete_habit_after_gap_resets_streak(self, service, sample_habit_request):
        """Test that completing a habit after a gap resets the streak."""
        habit = service.create_habit(sample_habit_request)
        today = date.today()
        three_days_ago = today - timedelta(days=3)
        
        # Complete three days ago (streak = 1)
        service.complete_habit_today(habit.id, three_days_ago)
        # Complete today (should reset streak to 1 due to gap)
        completed_habit = service.complete_habit_today(habit.id, today)
        
        assert completed_habit.streak_days == 1
        assert completed_habit.last_completed_at == today
    
    def test_complete_habit_duplicate_same_day(self, service, sample_habit_request):
        """Test that completing a habit twice on the same day raises an error."""
        habit = service.create_habit(sample_habit_request)
        today = date.today()
        
        # Complete once
        service.complete_habit_today(habit.id, today)
        
        # Try to complete again on the same day
        with pytest.raises(DuplicateCompletionError, match="already completed for"):
            service.complete_habit_today(habit.id, today)
    
    def test_complete_habit_not_found(self, service):
        """Test completing a non-existent habit."""
        with pytest.raises(HabitNotFoundError, match="Habit with ID 999 not found"):
            service.complete_habit_today(999)
    
    def test_complete_habit_with_custom_date(self, service, sample_habit_request):
        """Test completing a habit with a custom date."""
        habit = service.create_habit(sample_habit_request)
        custom_date = date(2024, 1, 15)
        
        completed_habit = service.complete_habit_today(habit.id, custom_date)
        
        assert completed_habit.last_completed_at == custom_date
        assert completed_habit.streak_days == 1


class TestStreakCalculation:
    """Tests specifically for streak calculation logic."""
    
    def test_streak_calculation_first_completion(self, service, sample_habit_request):
        """Test streak calculation for first completion."""
        habit = service.create_habit(sample_habit_request)
        today = date.today()
        
        # Test the private method directly
        new_streak = service._calculate_new_streak(habit, today)
        
        assert new_streak == 1
    
    def test_streak_calculation_consecutive_day(self, service, sample_habit_request):
        """Test streak calculation for consecutive day completion."""
        habit = service.create_habit(sample_habit_request)
        yesterday = date.today() - timedelta(days=1)
        today = date.today()
        
        # Simulate habit completed yesterday with streak of 2
        habit.last_completed_at = yesterday
        habit.streak_days = 2
        
        new_streak = service._calculate_new_streak(habit, today)
        
        assert new_streak == 3
    
    def test_streak_calculation_gap_resets(self, service, sample_habit_request):
        """Test streak calculation when there's a gap."""
        habit = service.create_habit(sample_habit_request)
        three_days_ago = date.today() - timedelta(days=3)
        today = date.today()
        
        # Simulate habit completed three days ago with streak of 5
        habit.last_completed_at = three_days_ago
        habit.streak_days = 5
        
        new_streak = service._calculate_new_streak(habit, today)
        
        assert new_streak == 1


class TestStatistics:
    """Tests for habit statistics functionality."""
    
    def test_get_stats_empty(self, service):
        """Test getting statistics when no habits exist."""
        stats = service.get_stats()
        
        assert stats.total_habits == 0
        assert stats.completed_today == 0
        assert stats.active_streaks_ge_3 == 0
    
    def test_get_stats_with_habits(self, service):
        """Test getting statistics with various habits."""
        today = date.today()
        
        # Create habits
        habit1 = service.create_habit(CreateHabitRequest(name="Habit 1"))
        habit2 = service.create_habit(CreateHabitRequest(name="Habit 2"))
        habit3 = service.create_habit(CreateHabitRequest(name="Habit 3"))
        
        # Complete habit1 today (streak will be 1)
        service.complete_habit_today(habit1.id, today)
        
        # Complete habit2 for multiple days to get streak >= 3
        for i in range(3):
            completion_date = today - timedelta(days=2-i)
            service.complete_habit_today(habit2.id, completion_date)
        
        # habit3 remains uncompleted
        
        stats = service.get_stats()
        
        assert stats.total_habits == 3
        assert stats.completed_today == 2  # habit1 and habit2 completed today
        assert stats.active_streaks_ge_3 == 1  # only habit2 has streak >= 3
    
    def test_get_stats_completed_today_count(self, service):
        """Test that completed_today only counts habits completed on current date."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        habit1 = service.create_habit(CreateHabitRequest(name="Today Habit"))
        habit2 = service.create_habit(CreateHabitRequest(name="Yesterday Habit"))
        
        service.complete_habit_today(habit1.id, today)
        service.complete_habit_today(habit2.id, yesterday)
        
        stats = service.get_stats()
        
        assert stats.total_habits == 2
        assert stats.completed_today == 1  # Only habit1 completed today
        assert stats.active_streaks_ge_3 == 0
    
    def test_get_stats_active_streaks_ge_3(self, service):
        """Test counting habits with streaks >= 3."""
        today = date.today()
        
        # Create habits with different streak lengths
        habit1 = service.create_habit(CreateHabitRequest(name="Streak 1"))
        habit2 = service.create_habit(CreateHabitRequest(name="Streak 3"))
        habit3 = service.create_habit(CreateHabitRequest(name="Streak 5"))
        
        # habit1: streak = 1
        service.complete_habit_today(habit1.id, today)
        
        # habit2: streak = 3
        for i in range(3):
            completion_date = today - timedelta(days=2-i)
            service.complete_habit_today(habit2.id, completion_date)
        
        # habit3: streak = 5
        for i in range(5):
            completion_date = today - timedelta(days=4-i)
            service.complete_habit_today(habit3.id, completion_date)
        
        stats = service.get_stats()
        
        assert stats.total_habits == 3
        assert stats.active_streaks_ge_3 == 2  # habit2 and habit3 have streaks >= 3


class TestBusinessRuleValidation:
    """Tests for business rule validation and edge cases."""
    
    def test_habit_status_update_does_not_affect_streak(self, service, sample_habit_request):
        """Test that updating status manually doesn't affect streak calculations."""
        habit = service.create_habit(sample_habit_request)
        today = date.today()
        
        # Complete the habit to establish a streak
        service.complete_habit_today(habit.id, today)
        
        # Manually update status to pending (shouldn't affect streak)
        update_request = UpdateHabitRequest(status="pending")
        updated_habit = service.update_habit(habit.id, update_request)
        
        assert updated_habit.status == "pending"
        assert updated_habit.streak_days == 1  # Streak unchanged
        assert updated_habit.last_completed_at == today  # Date unchanged
    
    def test_multiple_habits_independent_streaks(self, service):
        """Test that multiple habits maintain independent streaks."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        habit1 = service.create_habit(CreateHabitRequest(name="Habit 1"))
        habit2 = service.create_habit(CreateHabitRequest(name="Habit 2"))
        
        # Complete habit1 for 2 consecutive days
        service.complete_habit_today(habit1.id, yesterday)
        service.complete_habit_today(habit1.id, today)
        
        # Complete habit2 only today
        service.complete_habit_today(habit2.id, today)
        
        # Check that streaks are independent
        updated_habit1 = service.get_habit_by_id(habit1.id)
        updated_habit2 = service.get_habit_by_id(habit2.id)
        
        assert updated_habit1.streak_days == 2
        assert updated_habit2.streak_days == 1

clas
s TestErrorHandling:
    """Tests for enhanced error handling and validation."""
    
    def test_get_habit_by_id_invalid_id_type(self, service):
        """Test getting a habit with invalid ID type."""
        with pytest.raises(InvalidHabitDataError) as exc_info:
            service.get_habit_by_id("invalid")
        
        assert exc_info.value.error_code == "INVALID_HABIT_DATA"
        assert "positive integer" in exc_info.value.message
        assert exc_info.value.field == "habit_id"
    
    def test_get_habit_by_id_zero_id(self, service):
        """Test getting a habit with ID 0."""
        with pytest.raises(InvalidHabitDataError) as exc_info:
            service.get_habit_by_id(0)
        
        assert exc_info.value.error_code == "INVALID_HABIT_DATA"
        assert "positive integer" in exc_info.value.message
        assert exc_info.value.field == "habit_id"
    
    def test_get_habit_by_id_negative_id(self, service):
        """Test getting a habit with negative ID."""
        with pytest.raises(InvalidHabitDataError) as exc_info:
            service.get_habit_by_id(-1)
        
        assert exc_info.value.error_code == "INVALID_HABIT_DATA"
        assert "positive integer" in exc_info.value.message
        assert exc_info.value.field == "habit_id"
    
    def test_update_habit_invalid_id(self, service):
        """Test updating a habit with invalid ID."""
        update_request = UpdateHabitRequest(name="New Name")
        
        with pytest.raises(InvalidHabitDataError) as exc_info:
            service.update_habit(0, update_request)
        
        assert exc_info.value.error_code == "INVALID_HABIT_DATA"
        assert "positive integer" in exc_info.value.message
    
    def test_update_habit_empty_request(self, service, sample_habit_request):
        """Test updating a habit with empty request."""
        habit = service.create_habit(sample_habit_request)
        empty_request = UpdateHabitRequest()
        
        with pytest.raises(InvalidHabitDataError) as exc_info:
            service.update_habit(habit.id, empty_request)
        
        assert exc_info.value.error_code == "INVALID_HABIT_DATA"
        assert "at least one field" in exc_info.value.message.lower()
    
    def test_delete_habit_invalid_id(self, service):
        """Test deleting a habit with invalid ID."""
        with pytest.raises(InvalidHabitDataError) as exc_info:
            service.delete_habit(0)
        
        assert exc_info.value.error_code == "INVALID_HABIT_DATA"
        assert "positive integer" in exc_info.value.message
    
    def test_complete_habit_invalid_id(self, service):
        """Test completing a habit with invalid ID."""
        with pytest.raises(InvalidHabitDataError) as exc_info:
            service.complete_habit_today(0)
        
        assert exc_info.value.error_code == "INVALID_HABIT_DATA"
        assert "positive integer" in exc_info.value.message
    
    def test_complete_habit_future_date(self, service, sample_habit_request):
        """Test completing a habit with future date."""
        habit = service.create_habit(sample_habit_request)
        future_date = date.today() + timedelta(days=1)
        
        with pytest.raises(InvalidHabitDataError) as exc_info:
            service.complete_habit_today(habit.id, future_date)
        
        assert exc_info.value.error_code == "INVALID_HABIT_DATA"
        assert "future dates" in exc_info.value.message
    
    def test_complete_habit_invalid_date_type(self, service, sample_habit_request):
        """Test completing a habit with invalid date type."""
        habit = service.create_habit(sample_habit_request)
        
        with pytest.raises(InvalidHabitDataError) as exc_info:
            service.complete_habit_today(habit.id, "2024-01-01")
        
        assert exc_info.value.error_code == "INVALID_HABIT_DATA"
        assert "valid date object" in exc_info.value.message
    
    def test_habit_not_found_error_details(self, service):
        """Test that HabitNotFoundError contains proper details."""
        with pytest.raises(HabitNotFoundError) as exc_info:
            service.get_habit_by_id(999)
        
        assert exc_info.value.error_code == "HABIT_NOT_FOUND"
        assert exc_info.value.habit_id == 999
        assert "999" in exc_info.value.message
        assert "verify the habit ID exists" in exc_info.value.message
    
    def test_duplicate_completion_error_details(self, service, sample_habit_request):
        """Test that DuplicateCompletionError contains proper details."""
        habit = service.create_habit(sample_habit_request)
        today = date.today()
        
        # Complete once
        service.complete_habit_today(habit.id, today)
        
        # Try to complete again
        with pytest.raises(DuplicateCompletionError) as exc_info:
            service.complete_habit_today(habit.id, today)
        
        assert exc_info.value.error_code == "DUPLICATE_COMPLETION"
        assert exc_info.value.habit_name == habit.name
        assert exc_info.value.completion_date == today.isoformat()
        assert "already completed" in exc_info.value.message
        assert "once per day" in exc_info.value.message


class TestErrorMessageQuality:
    """Tests for error message quality and descriptiveness."""
    
    def test_habit_not_found_message_descriptive(self, service):
        """Test that habit not found messages are descriptive."""
        with pytest.raises(HabitNotFoundError) as exc_info:
            service.get_habit_by_id(123)
        
        message = exc_info.value.message
        assert "Habit with ID 123 not found" in message
        assert "verify the habit ID exists" in message
    
    def test_duplicate_completion_message_descriptive(self, service, sample_habit_request):
        """Test that duplicate completion messages are descriptive."""
        habit = service.create_habit(sample_habit_request)
        today = date.today()
        
        service.complete_habit_today(habit.id, today)
        
        with pytest.raises(DuplicateCompletionError) as exc_info:
            service.complete_habit_today(habit.id, today)
        
        message = exc_info.value.message
        assert habit.name in message
        assert today.isoformat() in message
        assert "already completed" in message
        assert "once per day" in message
    
    def test_invalid_data_message_descriptive(self, service):
        """Test that invalid data messages are descriptive."""
        with pytest.raises(InvalidHabitDataError) as exc_info:
            service.get_habit_by_id(-5)
        
        message = exc_info.value.message
        assert "habit_id" in message
        assert "-5" in message
        assert "positive integer" in message
    
    def test_future_date_message_descriptive(self, service, sample_habit_request):
        """Test that future date error messages are descriptive."""
        habit = service.create_habit(sample_habit_request)
        future_date = date.today() + timedelta(days=5)
        
        with pytest.raises(InvalidHabitDataError) as exc_info:
            service.complete_habit_today(habit.id, future_date)
        
        message = exc_info.value.message
        assert "future dates" in message
        assert future_date.isoformat() in message