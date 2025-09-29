"""
Pydantic models for the Habit Tracker API.

This module contains all data models including the core Habit entity,
request models, and response models with proper validation constraints.
"""

from datetime import date
from typing import Optional, Literal
from pydantic import BaseModel, Field


class Habit(BaseModel):
    """Core Habit entity model with validation constraints."""
    
    id: int
    name: str = Field(..., min_length=1, max_length=80, description="Habit name (1-80 characters)")
    description: Optional[str] = Field(None, max_length=280, description="Optional habit description (max 280 characters)")
    status: Literal["pending", "completed"] = Field(default="pending", description="Current habit status")
    streak_days: int = Field(default=0, ge=0, description="Number of consecutive completion days")
    last_completed_at: Optional[date] = Field(None, description="Date of last completion")

    class Config:
        """Pydantic configuration for the Habit model."""
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }


class CreateHabitRequest(BaseModel):
    """Request model for creating a new habit."""
    
    name: str = Field(..., min_length=1, max_length=80, description="Habit name (1-80 characters)")
    description: Optional[str] = Field(None, max_length=280, description="Optional habit description (max 280 characters)")


class UpdateHabitRequest(BaseModel):
    """Request model for updating an existing habit."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=80, description="Updated habit name (1-80 characters)")
    description: Optional[str] = Field(None, max_length=280, description="Updated habit description (max 280 characters)")
    status: Optional[Literal["pending", "completed"]] = Field(None, description="Updated habit status")


class StatsResponse(BaseModel):
    """Response model for habit statistics."""
    
    total_habits: int = Field(..., ge=0, description="Total number of habits")
    completed_today: int = Field(..., ge=0, description="Number of habits completed today")
    active_streaks_ge_3: int = Field(..., ge=0, description="Number of habits with streaks >= 3 days")


class ErrorResponse(BaseModel):
    """Response model for API errors."""
    
    error: str = Field(..., description="Error message describing what went wrong")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")


class HabitNotFoundErrorResponse(ErrorResponse):
    """Response model for habit not found errors."""
    
    error_code: str = Field("HABIT_NOT_FOUND", description="Error code for habit not found")
    habit_id: int = Field(..., description="The ID of the habit that was not found")


class DuplicateCompletionErrorResponse(ErrorResponse):
    """Response model for duplicate completion errors."""
    
    error_code: str = Field("DUPLICATE_COMPLETION", description="Error code for duplicate completion")
    habit_name: str = Field(..., description="Name of the habit that was already completed")
    completion_date: str = Field(..., description="Date for which the habit was already completed")


class InvalidHabitDataErrorResponse(ErrorResponse):
    """Response model for invalid habit data errors."""
    
    error_code: str = Field("INVALID_HABIT_DATA", description="Error code for invalid data")
    field: str = Field(..., description="The field that contains invalid data")
    value: str = Field(..., description="The invalid value that was provided")
    constraint: str = Field(..., description="Description of the constraint that was violated")