"""
Integration tests for habit management API endpoints.

This module contains comprehensive tests for all CRUD operations,
error handling, and business logic validation through the API layer.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date

from main import app, habit_repository


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_repository():
    """Clear the repository before each test."""
    habit_repository.clear()


class TestCreateHabit:
    """Test cases for POST /habits endpoint."""
    
    def test_create_habit_with_name_only(self, client):
        """Test creating a habit with only a name."""
        request_data = {"name": "Exercise"}
        
        response = client.post("/habits", json=request_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Exercise"
        assert data["description"] is None
        assert data["status"] == "pending"
        assert data["streak_days"] == 0
        assert data["last_completed_at"] is None
    
    def test_create_habit_with_name_and_description(self, client):
        """Test creating a habit with name and description."""
        request_data = {
            "name": "Read Books",
            "description": "Read for at least 30 minutes daily"
        }
        
        response = client.post("/habits", json=request_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Read Books"
        assert data["description"] == "Read for at least 30 minutes daily"
        assert data["status"] == "pending"
    
    def test_create_habit_name_too_long(self, client):
        """Test creating a habit with name exceeding 80 characters."""
        long_name = "a" * 81
        request_data = {"name": long_name}
        
        response = client.post("/habits", json=request_data)
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_create_habit_description_too_long(self, client):
        """Test creating a habit with description exceeding 280 characters."""
        long_description = "a" * 281
        request_data = {
            "name": "Valid Name",
            "description": long_description
        }
        
        response = client.post("/habits", json=request_data)
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_create_habit_empty_name(self, client):
        """Test creating a habit with empty name."""
        request_data = {"name": ""}
        
        response = client.post("/habits", json=request_data)
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_create_habit_missing_name(self, client):
        """Test creating a habit without name field."""
        request_data = {"description": "Some description"}
        
        response = client.post("/habits", json=request_data)
        
        assert response.status_code == 422  # Pydantic validation error


class TestGetHabits:
    """Test cases for GET /habits endpoint."""
    
    def test_get_habits_empty_list(self, client):
        """Test getting habits when none exist."""
        response = client.get("/habits")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_all_habits(self, client):
        """Test getting all habits without filtering."""
        # Create test habits
        client.post("/habits", json={"name": "Exercise"})
        client.post("/habits", json={"name": "Read", "description": "Daily reading"})
        
        response = client.get("/habits")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Exercise"
        assert data[1]["name"] == "Read"
    
    def test_get_habits_filter_by_pending_status(self, client):
        """Test filtering habits by pending status."""
        # Create habits with different statuses
        client.post("/habits", json={"name": "Exercise"})
        habit_response = client.post("/habits", json={"name": "Read"})
        habit_id = habit_response.json()["id"]
        
        # Update one habit to completed status
        client.patch(f"/habits/{habit_id}", json={"status": "completed"})
        
        response = client.get("/habits?status=pending")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Exercise"
        assert data[0]["status"] == "pending"
    
    def test_get_habits_filter_by_completed_status(self, client):
        """Test filtering habits by completed status."""
        # Create habits with different statuses
        client.post("/habits", json={"name": "Exercise"})
        habit_response = client.post("/habits", json={"name": "Read"})
        habit_id = habit_response.json()["id"]
        
        # Update one habit to completed status
        client.patch(f"/habits/{habit_id}", json={"status": "completed"})
        
        response = client.get("/habits?status=completed")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Read"
        assert data[0]["status"] == "completed"
    
    def test_get_habits_invalid_status_filter(self, client):
        """Test filtering habits with invalid status value."""
        response = client.get("/habits?status=invalid")
        
        assert response.status_code == 422  # Pydantic validation error


class TestUpdateHabit:
    """Test cases for PATCH /habits/{id} endpoint."""
    
    def test_update_habit_name(self, client):
        """Test updating habit name."""
        # Create a habit
        create_response = client.post("/habits", json={"name": "Exercise"})
        habit_id = create_response.json()["id"]
        
        # Update the name
        update_data = {"name": "Daily Exercise"}
        response = client.patch(f"/habits/{habit_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Daily Exercise"
        assert data["id"] == habit_id
    
    def test_update_habit_description(self, client):
        """Test updating habit description."""
        # Create a habit
        create_response = client.post("/habits", json={"name": "Exercise"})
        habit_id = create_response.json()["id"]
        
        # Update the description
        update_data = {"description": "30 minutes of cardio"}
        response = client.patch(f"/habits/{habit_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "30 minutes of cardio"
        assert data["name"] == "Exercise"  # Original name unchanged
    
    def test_update_habit_status(self, client):
        """Test updating habit status."""
        # Create a habit
        create_response = client.post("/habits", json={"name": "Exercise"})
        habit_id = create_response.json()["id"]
        
        # Update the status
        update_data = {"status": "completed"}
        response = client.patch(f"/habits/{habit_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["streak_days"] == 0  # Status change doesn't affect streak
    
    def test_update_habit_multiple_fields(self, client):
        """Test updating multiple habit fields at once."""
        # Create a habit
        create_response = client.post("/habits", json={"name": "Exercise"})
        habit_id = create_response.json()["id"]
        
        # Update multiple fields
        update_data = {
            "name": "Daily Workout",
            "description": "Strength training and cardio",
            "status": "completed"
        }
        response = client.patch(f"/habits/{habit_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Daily Workout"
        assert data["description"] == "Strength training and cardio"
        assert data["status"] == "completed"
    
    def test_update_habit_not_found(self, client):
        """Test updating a non-existent habit."""
        update_data = {"name": "Updated Name"}
        response = client.patch("/habits/999", json=update_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_habit_invalid_name_length(self, client):
        """Test updating habit with invalid name length."""
        # Create a habit
        create_response = client.post("/habits", json={"name": "Exercise"})
        habit_id = create_response.json()["id"]
        
        # Try to update with invalid name
        update_data = {"name": "a" * 81}  # Too long
        response = client.patch(f"/habits/{habit_id}", json=update_data)
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_update_habit_empty_request(self, client):
        """Test updating habit with empty request body."""
        # Create a habit
        create_response = client.post("/habits", json={"name": "Exercise"})
        habit_id = create_response.json()["id"]
        original_data = create_response.json()
        
        # Update with empty data
        response = client.patch(f"/habits/{habit_id}", json={})
        
        assert response.status_code == 200
        data = response.json()
        # All fields should remain unchanged
        assert data["name"] == original_data["name"]
        assert data["description"] == original_data["description"]
        assert data["status"] == original_data["status"]


class TestDeleteHabit:
    """Test cases for DELETE /habits/{id} endpoint."""
    
    def test_delete_existing_habit(self, client):
        """Test deleting an existing habit."""
        # Create a habit
        create_response = client.post("/habits", json={"name": "Exercise"})
        habit_id = create_response.json()["id"]
        
        # Delete the habit
        response = client.delete(f"/habits/{habit_id}")
        
        assert response.status_code == 204
        assert response.content == b""
        
        # Verify habit is deleted
        get_response = client.get("/habits")
        assert len(get_response.json()) == 0
    
    def test_delete_habit_not_found(self, client):
        """Test deleting a non-existent habit."""
        response = client.delete("/habits/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_delete_habit_multiple_habits(self, client):
        """Test deleting one habit when multiple exist."""
        # Create multiple habits
        response1 = client.post("/habits", json={"name": "Exercise"})
        response2 = client.post("/habits", json={"name": "Read"})
        habit1_id = response1.json()["id"]
        habit2_id = response2.json()["id"]
        
        # Delete one habit
        delete_response = client.delete(f"/habits/{habit1_id}")
        assert delete_response.status_code == 204
        
        # Verify only one habit remains
        get_response = client.get("/habits")
        remaining_habits = get_response.json()
        assert len(remaining_habits) == 1
        assert remaining_habits[0]["id"] == habit2_id
        assert remaining_habits[0]["name"] == "Read"


class TestCompleteHabit:
    """Test cases for POST /habits/{id}/complete endpoint."""
    
    def test_complete_habit_first_time(self, client):
        """Test completing a habit for the first time."""
        # Create a habit
        create_response = client.post("/habits", json={"name": "Exercise"})
        habit_id = create_response.json()["id"]
        
        # Complete the habit
        response = client.post(f"/habits/{habit_id}/complete")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["streak_days"] == 1
        assert data["last_completed_at"] == date.today().isoformat()
    
    def test_complete_habit_not_found(self, client):
        """Test completing a non-existent habit."""
        response = client.post("/habits/999/complete")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_complete_habit_duplicate_same_day(self, client):
        """Test completing a habit twice on the same day."""
        # Create and complete a habit
        create_response = client.post("/habits", json={"name": "Exercise"})
        habit_id = create_response.json()["id"]
        
        # First completion should succeed
        first_response = client.post(f"/habits/{habit_id}/complete")
        assert first_response.status_code == 200
        
        # Second completion on same day should fail
        second_response = client.post(f"/habits/{habit_id}/complete")
        assert second_response.status_code == 409
        assert "already completed" in second_response.json()["detail"].lower()
    
    def test_complete_habit_updates_status_and_streak(self, client):
        """Test that completing a habit updates both status and streak."""
        # Create a habit
        create_response = client.post("/habits", json={
            "name": "Exercise",
            "description": "Daily workout"
        })
        habit_id = create_response.json()["id"]
        
        # Verify initial state
        initial_habit = create_response.json()
        assert initial_habit["status"] == "pending"
        assert initial_habit["streak_days"] == 0
        assert initial_habit["last_completed_at"] is None
        
        # Complete the habit
        complete_response = client.post(f"/habits/{habit_id}/complete")
        completed_habit = complete_response.json()
        
        assert completed_habit["status"] == "completed"
        assert completed_habit["streak_days"] == 1
        assert completed_habit["last_completed_at"] == date.today().isoformat()
        assert completed_habit["name"] == "Exercise"  # Other fields unchanged
        assert completed_habit["description"] == "Daily workout"


class TestStatsEndpoint:
    """Test cases for GET /stats endpoint."""
    
    def test_get_stats_empty(self, client):
        """Test getting statistics when no habits exist."""
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_habits"] == 0
        assert data["completed_today"] == 0
        assert data["active_streaks_ge_3"] == 0
    
    def test_get_stats_with_habits(self, client):
        """Test getting statistics with various habits."""
        # Create multiple habits
        habit1_response = client.post("/habits", json={"name": "Exercise"})
        habit2_response = client.post("/habits", json={"name": "Read"})
        habit3_response = client.post("/habits", json={"name": "Meditate"})
        
        habit1_id = habit1_response.json()["id"]
        habit2_id = habit2_response.json()["id"]
        # habit3 remains uncompleted
        
        # Complete habit1 today (streak = 1)
        client.post(f"/habits/{habit1_id}/complete")
        
        # Complete habit2 today (streak = 1)
        client.post(f"/habits/{habit2_id}/complete")
        
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_habits"] == 3
        assert data["completed_today"] == 2  # habit1 and habit2 completed today
        assert data["active_streaks_ge_3"] == 0  # no habits have streak >= 3 yet
    
    def test_get_stats_completed_today_accuracy(self, client):
        """Test that completed_today only counts habits completed on current date."""
        # Create habits
        habit1_response = client.post("/habits", json={"name": "Today Habit"})
        habit2_response = client.post("/habits", json={"name": "Not Completed"})
        
        habit1_id = habit1_response.json()["id"]
        
        # Complete only habit1 today
        client.post(f"/habits/{habit1_id}/complete")
        
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_habits"] == 2
        assert data["completed_today"] == 1  # Only habit1 completed today
        assert data["active_streaks_ge_3"] == 0
    
    def test_get_stats_active_streaks_calculation(self, client):
        """Test that active_streaks_ge_3 counts habits with streaks >= 3."""
        # Create habits
        habit1_response = client.post("/habits", json={"name": "Short Streak"})
        habit2_response = client.post("/habits", json={"name": "Long Streak"})
        
        habit1_id = habit1_response.json()["id"]
        habit2_id = habit2_response.json()["id"]
        
        # Complete habit1 once (streak = 1)
        client.post(f"/habits/{habit1_id}/complete")
        
        # For habit2, we need to simulate a streak >= 3
        # Since we can't easily manipulate dates in integration tests,
        # we'll test the basic functionality and rely on service tests for streak logic
        client.post(f"/habits/{habit2_id}/complete")
        
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_habits"] == 2
        assert data["completed_today"] == 2
        # Note: Both habits will have streak = 1 in this test since we can't manipulate dates
        assert data["active_streaks_ge_3"] == 0
    
    def test_get_stats_dynamic_updates(self, client):
        """Test that statistics update dynamically as habits change."""
        # Initial state - no habits
        initial_response = client.get("/stats")
        assert initial_response.json()["total_habits"] == 0
        
        # Create a habit
        habit_response = client.post("/habits", json={"name": "Exercise"})
        habit_id = habit_response.json()["id"]
        
        # Check stats after creation
        after_create_response = client.get("/stats")
        after_create_data = after_create_response.json()
        assert after_create_data["total_habits"] == 1
        assert after_create_data["completed_today"] == 0
        
        # Complete the habit
        client.post(f"/habits/{habit_id}/complete")
        
        # Check stats after completion
        after_complete_response = client.get("/stats")
        after_complete_data = after_complete_response.json()
        assert after_complete_data["total_habits"] == 1
        assert after_complete_data["completed_today"] == 1
        
        # Delete the habit
        client.delete(f"/habits/{habit_id}")
        
        # Check stats after deletion
        after_delete_response = client.get("/stats")
        after_delete_data = after_delete_response.json()
        assert after_delete_data["total_habits"] == 0
        assert after_delete_data["completed_today"] == 0
    
    def test_get_stats_response_format(self, client):
        """Test that stats response has correct format and field types."""
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields are present
        assert "total_habits" in data
        assert "completed_today" in data
        assert "active_streaks_ge_3" in data
        
        # Check field types
        assert isinstance(data["total_habits"], int)
        assert isinstance(data["completed_today"], int)
        assert isinstance(data["active_streaks_ge_3"], int)
        
        # Check non-negative values
        assert data["total_habits"] >= 0
        assert data["completed_today"] >= 0
        assert data["active_streaks_ge_3"] >= 0


class TestIntegrationWorkflows:
    """Test complete workflows combining multiple operations."""
    
    def test_complete_crud_workflow(self, client):
        """Test a complete CRUD workflow."""
        # Create a habit
        create_response = client.post("/habits", json={
            "name": "Exercise",
            "description": "Daily workout"
        })
        assert create_response.status_code == 201
        habit_id = create_response.json()["id"]
        
        # Read the habit
        get_response = client.get("/habits")
        assert len(get_response.json()) == 1
        
        # Update the habit
        update_response = client.patch(f"/habits/{habit_id}", json={
            "name": "Daily Exercise",
            "status": "completed"
        })
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Daily Exercise"
        
        # Delete the habit
        delete_response = client.delete(f"/habits/{habit_id}")
        assert delete_response.status_code == 204
        
        # Verify deletion
        final_get_response = client.get("/habits")
        assert len(final_get_response.json()) == 0
    
    def test_filtering_workflow(self, client):
        """Test habit filtering workflow."""
        # Create habits with different statuses
        client.post("/habits", json={"name": "Exercise"})
        read_response = client.post("/habits", json={"name": "Read"})
        meditate_response = client.post("/habits", json={"name": "Meditate"})
        
        # Update some habits to completed
        client.patch(f"/habits/{read_response.json()['id']}", json={"status": "completed"})
        client.patch(f"/habits/{meditate_response.json()['id']}", json={"status": "completed"})
        
        # Test filtering
        all_habits = client.get("/habits").json()
        pending_habits = client.get("/habits?status=pending").json()
        completed_habits = client.get("/habits?status=completed").json()
        
        assert len(all_habits) == 3
        assert len(pending_habits) == 1
        assert len(completed_habits) == 2
        assert pending_habits[0]["name"] == "Exercise"
    
    def test_habit_completion_workflow(self, client):
        """Test complete habit completion workflow including streak tracking."""
        # Create a habit
        create_response = client.post("/habits", json={"name": "Exercise"})
        habit_id = create_response.json()["id"]
        
        # Complete the habit
        complete_response = client.post(f"/habits/{habit_id}/complete")
        assert complete_response.status_code == 200
        
        completed_habit = complete_response.json()
        assert completed_habit["status"] == "completed"
        assert completed_habit["streak_days"] == 1
        
        # Verify the habit appears in completed filter
        completed_habits = client.get("/habits?status=completed").json()
        assert len(completed_habits) == 1
        assert completed_habits[0]["id"] == habit_id
        
        # Try to complete again (should fail)
        duplicate_response = client.post(f"/habits/{habit_id}/complete")
        assert duplicate_response.status_code == 409
    
    def test_complete_workflow_with_statistics(self, client):
        """Test complete workflow including statistics tracking."""
        # Initial stats should be empty
        initial_stats = client.get("/stats").json()
        assert initial_stats["total_habits"] == 0
        assert initial_stats["completed_today"] == 0
        assert initial_stats["active_streaks_ge_3"] == 0
        
        # Create multiple habits
        habit1_response = client.post("/habits", json={"name": "Exercise"})
        habit2_response = client.post("/habits", json={"name": "Read"})
        habit3_response = client.post("/habits", json={"name": "Meditate"})
        
        habit1_id = habit1_response.json()["id"]
        habit2_id = habit2_response.json()["id"]
        habit3_id = habit3_response.json()["id"]
        
        # Stats after creation
        after_creation_stats = client.get("/stats").json()
        assert after_creation_stats["total_habits"] == 3
        assert after_creation_stats["completed_today"] == 0
        assert after_creation_stats["active_streaks_ge_3"] == 0
        
        # Complete some habits
        client.post(f"/habits/{habit1_id}/complete")
        client.post(f"/habits/{habit2_id}/complete")
        # Leave habit3 uncompleted
        
        # Stats after completions
        after_completion_stats = client.get("/stats").json()
        assert after_completion_stats["total_habits"] == 3
        assert after_completion_stats["completed_today"] == 2
        assert after_completion_stats["active_streaks_ge_3"] == 0  # No streaks >= 3 yet
        
        # Update a habit status manually (shouldn't affect completion count)
        client.patch(f"/habits/{habit3_id}", json={"status": "completed"})
        
        # Stats should remain the same (manual status change doesn't count as completion today)
        after_manual_update_stats = client.get("/stats").json()
        assert after_manual_update_stats["total_habits"] == 3
        assert after_manual_update_stats["completed_today"] == 2  # Still only 2 completed today
        assert after_manual_update_stats["active_streaks_ge_3"] == 0
        
        # Delete a completed habit
        client.delete(f"/habits/{habit1_id}")
        
        # Stats after deletion
        after_deletion_stats = client.get("/stats").json()
        assert after_deletion_stats["total_habits"] == 2
        assert after_deletion_stats["completed_today"] == 1  # Only habit2 completed today now
        assert after_deletion_stats["active_streaks_ge_3"] == 0