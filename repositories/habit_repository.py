"""
In-memory repository for habit data storage.

This module provides the HabitRepository class that manages habit data
using dictionary-based storage with auto-incrementing IDs.
"""

from typing import Dict, List, Optional
from models.habit import Habit


class HabitRepository:
    """In-memory repository for habit data storage."""
    
    def __init__(self):
        """Initialize the repository with empty storage."""
        self._habits: Dict[int, Habit] = {}
        self._next_id: int = 1
    
    def create(self, habit_data: dict) -> Habit:
        """
        Create a new habit with auto-generated ID.
        
        Args:
            habit_data: Dictionary containing habit data (without ID)
            
        Returns:
            The created Habit instance with assigned ID
        """
        habit_data_with_id = {**habit_data, "id": self._next_id}
        habit = Habit(**habit_data_with_id)
        self._habits[self._next_id] = habit
        self._next_id += 1
        return habit
    
    def get_by_id(self, habit_id: int) -> Optional[Habit]:
        """
        Retrieve a habit by its ID.
        
        Args:
            habit_id: The ID of the habit to retrieve
            
        Returns:
            The Habit instance if found, None otherwise
        """
        return self._habits.get(habit_id)
    
    def get_all(self) -> List[Habit]:
        """
        Retrieve all habits.
        
        Returns:
            List of all Habit instances
        """
        return list(self._habits.values())
    
    def update(self, habit_id: int, updates: dict) -> Optional[Habit]:
        """
        Update an existing habit with new data.
        
        Args:
            habit_id: The ID of the habit to update
            updates: Dictionary containing fields to update
            
        Returns:
            The updated Habit instance if found, None otherwise
        """
        if habit_id not in self._habits:
            return None
        
        # Get current habit data and apply updates
        current_habit = self._habits[habit_id]
        updated_data = current_habit.dict()
        updated_data.update(updates)
        
        # Create new habit instance with updated data
        updated_habit = Habit(**updated_data)
        self._habits[habit_id] = updated_habit
        return updated_habit
    
    def delete(self, habit_id: int) -> bool:
        """
        Delete a habit by its ID.
        
        Args:
            habit_id: The ID of the habit to delete
            
        Returns:
            True if the habit was deleted, False if not found
        """
        if habit_id in self._habits:
            del self._habits[habit_id]
            return True
        return False
    
    def clear(self) -> None:
        """
        Clear all habits from storage.
        
        This method is primarily for testing purposes.
        """
        self._habits.clear()
        self._next_id = 1