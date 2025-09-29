"""
Unit tests for the HabitRepository class.

This module contains comprehensive tests for all repository operations
including edge cases and error conditions.
"""

import pytest
from datetime import date
from repositories import HabitRepository
from models import Habit


class TestHabitRepository:
    """Test suite for HabitRepository class."""
    
    def setup_method(self):
        """Set up a fresh repository for each test."""
        self.repository = HabitRepository()
    
    def test_create_habit_success(self):
        """Test successful habit creation with auto-generated ID."""
        habit_data = {
            "name": "Exercise",
            "description": "Daily workout routine"
        }
        
        habit = self.repository.create(habit_data)
        
        assert habit.id == 1
        assert habit.name == "Exercise"
        assert habit.description == "Daily workout routine"
        assert habit.status == "pending"
        assert habit.streak_days == 0
        assert habit.last_completed_at is None
    
    def test_create_multiple_habits_auto_increment_ids(self):
        """Test that multiple habits get auto-incrementing IDs."""
        habit1 = self.repository.create({"name": "Exercise"})
        habit2 = self.repository.create({"name": "Reading"})
        habit3 = self.repository.create({"name": "Meditation"})
        
        assert habit1.id == 1
        assert habit2.id == 2
        assert habit3.id == 3
    
    def test_create_habit_with_all_fields(self):
        """Test creating habit with all possible fields."""
        habit_data = {
            "name": "Exercise",
            "description": "Daily workout",
            "status": "completed",
            "streak_days": 5,
            "last_completed_at": date(2024, 1, 15)
        }
        
        habit = self.repository.create(habit_data)
        
        assert habit.id == 1
        assert habit.name == "Exercise"
        assert habit.description == "Daily workout"
        assert habit.status == "completed"
        assert habit.streak_days == 5
        assert habit.last_completed_at == date(2024, 1, 15)
    
    def test_get_by_id_existing_habit(self):
        """Test retrieving an existing habit by ID."""
        created_habit = self.repository.create({"name": "Exercise"})
        
        retrieved_habit = self.repository.get_by_id(created_habit.id)
        
        assert retrieved_habit is not None
        assert retrieved_habit.id == created_habit.id
        assert retrieved_habit.name == "Exercise"
    
    def test_get_by_id_non_existent_habit(self):
        """Test retrieving a non-existent habit returns None."""
        result = self.repository.get_by_id(999)
        
        assert result is None
    
    def test_get_by_id_after_deletion(self):
        """Test that get_by_id returns None after habit is deleted."""
        habit = self.repository.create({"name": "Exercise"})
        self.repository.delete(habit.id)
        
        result = self.repository.get_by_id(habit.id)
        
        assert result is None
    
    def test_get_all_empty_repository(self):
        """Test get_all returns empty list when no habits exist."""
        habits = self.repository.get_all()
        
        assert habits == []
    
    def test_get_all_with_habits(self):
        """Test get_all returns all created habits."""
        habit1 = self.repository.create({"name": "Exercise"})
        habit2 = self.repository.create({"name": "Reading"})
        habit3 = self.repository.create({"name": "Meditation"})
        
        habits = self.repository.get_all()
        
        assert len(habits) == 3
        habit_names = [h.name for h in habits]
        assert "Exercise" in habit_names
        assert "Reading" in habit_names
        assert "Meditation" in habit_names
    
    def test_get_all_returns_copies(self):
        """Test that get_all returns independent copies of habits."""
        self.repository.create({"name": "Exercise"})
        
        habits1 = self.repository.get_all()
        habits2 = self.repository.get_all()
        
        # Should be different list instances but same content
        assert habits1 is not habits2
        assert habits1[0].name == habits2[0].name
    
    def test_update_existing_habit(self):
        """Test updating an existing habit."""
        habit = self.repository.create({"name": "Exercise", "description": "Old description"})
        
        updates = {
            "name": "Updated Exercise",
            "description": "New description",
            "status": "completed"
        }
        
        updated_habit = self.repository.update(habit.id, updates)
        
        assert updated_habit is not None
        assert updated_habit.id == habit.id
        assert updated_habit.name == "Updated Exercise"
        assert updated_habit.description == "New description"
        assert updated_habit.status == "completed"
    
    def test_update_partial_fields(self):
        """Test updating only some fields of a habit."""
        habit = self.repository.create({
            "name": "Exercise",
            "description": "Original description",
            "status": "pending"
        })
        
        updates = {"name": "Updated Exercise"}
        
        updated_habit = self.repository.update(habit.id, updates)
        
        assert updated_habit is not None
        assert updated_habit.name == "Updated Exercise"
        assert updated_habit.description == "Original description"  # Unchanged
        assert updated_habit.status == "pending"  # Unchanged
    
    def test_update_non_existent_habit(self):
        """Test updating a non-existent habit returns None."""
        updates = {"name": "Updated Name"}
        
        result = self.repository.update(999, updates)
        
        assert result is None
    
    def test_update_with_date_field(self):
        """Test updating habit with date field."""
        habit = self.repository.create({"name": "Exercise"})
        
        updates = {
            "last_completed_at": date(2024, 1, 15),
            "streak_days": 3
        }
        
        updated_habit = self.repository.update(habit.id, updates)
        
        assert updated_habit is not None
        assert updated_habit.last_completed_at == date(2024, 1, 15)
        assert updated_habit.streak_days == 3
    
    def test_delete_existing_habit(self):
        """Test deleting an existing habit."""
        habit = self.repository.create({"name": "Exercise"})
        
        result = self.repository.delete(habit.id)
        
        assert result is True
        assert self.repository.get_by_id(habit.id) is None
    
    def test_delete_non_existent_habit(self):
        """Test deleting a non-existent habit returns False."""
        result = self.repository.delete(999)
        
        assert result is False
    
    def test_delete_affects_get_all(self):
        """Test that deletion affects get_all results."""
        habit1 = self.repository.create({"name": "Exercise"})
        habit2 = self.repository.create({"name": "Reading"})
        
        assert len(self.repository.get_all()) == 2
        
        self.repository.delete(habit1.id)
        
        remaining_habits = self.repository.get_all()
        assert len(remaining_habits) == 1
        assert remaining_habits[0].name == "Reading"
    
    def test_clear_repository(self):
        """Test clearing all habits from repository."""
        self.repository.create({"name": "Exercise"})
        self.repository.create({"name": "Reading"})
        
        assert len(self.repository.get_all()) == 2
        
        self.repository.clear()
        
        assert len(self.repository.get_all()) == 0
        assert self.repository._next_id == 1
    
    def test_id_sequence_after_clear(self):
        """Test that ID sequence resets after clear."""
        habit1 = self.repository.create({"name": "Exercise"})
        assert habit1.id == 1
        
        self.repository.clear()
        
        habit2 = self.repository.create({"name": "Reading"})
        assert habit2.id == 1
    
    def test_id_sequence_continues_after_deletion(self):
        """Test that ID sequence continues incrementing after deletions."""
        habit1 = self.repository.create({"name": "Exercise"})
        habit2 = self.repository.create({"name": "Reading"})
        
        assert habit1.id == 1
        assert habit2.id == 2
        
        self.repository.delete(habit1.id)
        
        habit3 = self.repository.create({"name": "Meditation"})
        assert habit3.id == 3  # Should continue sequence, not reuse deleted ID
    
    def test_repository_isolation(self):
        """Test that different repository instances are isolated."""
        repo1 = HabitRepository()
        repo2 = HabitRepository()
        
        habit1 = repo1.create({"name": "Exercise"})
        habit2 = repo2.create({"name": "Reading"})
        
        assert len(repo1.get_all()) == 1
        assert len(repo2.get_all()) == 1
        assert repo1.get_all()[0].name == "Exercise"
        assert repo2.get_all()[0].name == "Reading"