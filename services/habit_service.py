"""
Business logic service for habit management and streak tracking.

This module contains the HabitService class that handles all business logic
for habit operations including streak calculations and validation.
"""

from datetime import date
from typing import List, Optional, Literal
from models.habit import Habit, CreateHabitRequest, UpdateHabitRequest, StatsResponse
from repositories.habit_repository import HabitRepository


class HabitServiceError(Exception):
    """Base exception for habit service errors."""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class HabitNotFoundError(HabitServiceError):
    """Raised when a habit is not found."""
    def __init__(self, habit_id: int):
        message = f"Habit with ID {habit_id} not found. Please verify the habit ID exists."
        super().__init__(message, "HABIT_NOT_FOUND")
        self.habit_id = habit_id


class DuplicateCompletionError(HabitServiceError):
    """Raised when trying to complete a habit twice on the same day."""
    def __init__(self, habit_name: str, completion_date: str):
        message = f"Habit '{habit_name}' is already completed for {completion_date}. Each habit can only be completed once per day."
        super().__init__(message, "DUPLICATE_COMPLETION")
        self.habit_name = habit_name
        self.completion_date = completion_date


class InvalidHabitDataError(HabitServiceError):
    """Raised when habit data validation fails."""
    def __init__(self, field: str, value: str, constraint: str):
        message = f"Invalid value for {field}: '{value}'. {constraint}"
        super().__init__(message, "INVALID_HABIT_DATA")
        self.field = field
        self.value = value
        self.constraint = constraint


class HabitOperationError(HabitServiceError):
    """Raised when a habit operation fails due to business rules."""
    def __init__(self, operation: str, reason: str):
        message = f"Cannot {operation}: {reason}"
        super().__init__(message, "HABIT_OPERATION_ERROR")
        self.operation = operation
        self.reason = reason


class HabitService:
    """Service class for habit business logic and operations."""
    
    def __init__(self, repository: HabitRepository):
        """
        Initialize the service with a habit repository.
        
        Args:
            repository: The HabitRepository instance for data storage
        """
        self.repository = repository
    
    def create_habit(self, request: CreateHabitRequest) -> Habit:
        """
        Create a new habit with default values.
        
        Args:
            request: CreateHabitRequest with habit name and optional description
            
        Returns:
            The created Habit instance
        """
        habit_data = {
            "name": request.name,
            "description": request.description,
            "status": "pending",
            "streak_days": 0,
            "last_completed_at": None
        }
        return self.repository.create(habit_data)
    
    def get_habits(self, status: Optional[Literal["pending", "completed"]] = None) -> List[Habit]:
        """
        Retrieve all habits with optional status filtering.
        
        Args:
            status: Optional status filter ("pending" or "completed")
            
        Returns:
            List of habits matching the filter criteria
        """
        habits = self.repository.get_all()
        
        if status is not None:
            habits = [habit for habit in habits if habit.status == status]
        
        return habits
    
    def get_habit_by_id(self, habit_id: int) -> Habit:
        """
        Retrieve a habit by its ID.
        
        Args:
            habit_id: The ID of the habit to retrieve
            
        Returns:
            The Habit instance
            
        Raises:
            HabitNotFoundError: If the habit is not found
        """
        if not isinstance(habit_id, int) or habit_id <= 0:
            raise InvalidHabitDataError("habit_id", str(habit_id), "Habit ID must be a positive integer")
        
        habit = self.repository.get_by_id(habit_id)
        if habit is None:
            raise HabitNotFoundError(habit_id)
        return habit
    
    def update_habit(self, habit_id: int, request: UpdateHabitRequest) -> Habit:
        """
        Update habit details without affecting streak calculations.
        
        Args:
            habit_id: The ID of the habit to update
            request: UpdateHabitRequest with fields to update
            
        Returns:
            The updated Habit instance
            
        Raises:
            HabitNotFoundError: If the habit is not found
            InvalidHabitDataError: If the update data is invalid
        """
        # Validate habit_id
        if not isinstance(habit_id, int) or habit_id <= 0:
            raise InvalidHabitDataError("habit_id", str(habit_id), "Habit ID must be a positive integer")
        
        # Check if habit exists
        existing_habit = self.get_habit_by_id(habit_id)
        
        # Validate that at least one field is being updated
        if all(field is None for field in [request.name, request.description, request.status]):
            raise InvalidHabitDataError("update_request", "empty", "At least one field must be provided for update")
        
        # Prepare update data (only include non-None fields)
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.status is not None:
            updates["status"] = request.status
        
        # Update the habit
        updated_habit = self.repository.update(habit_id, updates)
        if updated_habit is None:
            raise HabitNotFoundError(habit_id)
        
        return updated_habit
    
    def delete_habit(self, habit_id: int) -> None:
        """
        Delete a habit by its ID.
        
        Args:
            habit_id: The ID of the habit to delete
            
        Raises:
            HabitNotFoundError: If the habit is not found
            InvalidHabitDataError: If the habit_id is invalid
        """
        # Validate habit_id
        if not isinstance(habit_id, int) or habit_id <= 0:
            raise InvalidHabitDataError("habit_id", str(habit_id), "Habit ID must be a positive integer")
        
        if not self.repository.delete(habit_id):
            raise HabitNotFoundError(habit_id)    

    def complete_habit_today(self, habit_id: int, completion_date: Optional[date] = None) -> Habit:
        """
        Mark a habit as completed for today with streak calculation.
        
        Args:
            habit_id: The ID of the habit to complete
            completion_date: Optional date for completion (defaults to today)
            
        Returns:
            The updated Habit instance with new streak information
            
        Raises:
            HabitNotFoundError: If the habit is not found
            DuplicateCompletionError: If the habit is already completed for the given date
            InvalidHabitDataError: If the habit_id or completion_date is invalid
        """
        # Validate habit_id
        if not isinstance(habit_id, int) or habit_id <= 0:
            raise InvalidHabitDataError("habit_id", str(habit_id), "Habit ID must be a positive integer")
        
        if completion_date is None:
            completion_date = date.today()
        
        # Validate completion_date
        if not isinstance(completion_date, date):
            raise InvalidHabitDataError("completion_date", str(completion_date), "Completion date must be a valid date object")
        
        # Don't allow future dates
        if completion_date > date.today():
            raise InvalidHabitDataError("completion_date", completion_date.isoformat(), "Cannot complete habits for future dates")
        
        # Get the existing habit
        habit = self.get_habit_by_id(habit_id)
        
        # Check for duplicate completion on the same day
        if habit.last_completed_at == completion_date:
            raise DuplicateCompletionError(habit.name, completion_date.isoformat())
        
        # Calculate new streak based on completion pattern
        new_streak_days = self._calculate_new_streak(habit, completion_date)
        
        # Update habit with completion data
        updates = {
            "status": "completed",
            "streak_days": new_streak_days,
            "last_completed_at": completion_date
        }
        
        updated_habit = self.repository.update(habit_id, updates)
        if updated_habit is None:
            raise HabitNotFoundError(habit_id)
        
        return updated_habit
    
    def _calculate_new_streak(self, habit: Habit, completion_date: date) -> int:
        """
        Calculate the new streak count based on completion pattern.
        
        Args:
            habit: The current habit instance
            completion_date: The date of the new completion
            
        Returns:
            The new streak count
        """
        # If this is the first completion
        if habit.last_completed_at is None:
            return 1
        
        # Calculate days between last completion and new completion
        days_diff = (completion_date - habit.last_completed_at).days
        
        if days_diff == 1:
            # Consecutive day completion - increment streak
            return habit.streak_days + 1
        else:
            # Gap in completion - reset streak to 1
            return 1
    
    def get_stats(self) -> StatsResponse:
        """
        Calculate and return habit statistics.
        
        Returns:
            StatsResponse with current habit statistics
        """
        habits = self.repository.get_all()
        today = date.today()
        
        total_habits = len(habits)
        completed_today = sum(
            1 for habit in habits 
            if habit.last_completed_at == today
        )
        active_streaks_ge_3 = sum(
            1 for habit in habits 
            if habit.streak_days >= 3
        )
        
        return StatsResponse(
            total_habits=total_habits,
            completed_today=completed_today,
            active_streaks_ge_3=active_streaks_ge_3
        )