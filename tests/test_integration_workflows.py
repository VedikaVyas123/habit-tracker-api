"""
Comprehensive integration tests for complete user workflows.

This module contains end-to-end integration tests that cover complete user
workflows including habit creation, completion tracking, streak management,
and statistics reporting.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
from unittest.mock import patch

from main import app, habit_repository


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_repository():
    """Clear the repository before each test."""
    habit_repository.clear()


class TestCompleteUserWorkflows:
    """Test complete user workflows from creation to statistics."""
    
    def test_complete_habit_lifecycle_workflow(self, client):
        """Test complete habit lifecycle: create → complete → update → stats → delete."""
        # Step 1: Create a habit
        create_response = client.post("/habits", json={
            "name": "Morning Exercise",
            "description": "30 minutes of cardio"
        })
        assert create_response.status_code == 201
        habit = create_response.json()
        habit_id = habit["id"]
        
        # Verify initial state
        assert habit["name"] == "Morning Exercise"
        assert habit["description"] == "30 minutes of cardio"
        assert habit["status"] == "pending"
        assert habit["streak_days"] == 0
        assert habit["last_completed_at"] is None
        
        # Step 2: Complete the habit
        complete_response = client.post(f"/habits/{habit_id}/complete")
        assert complete_response.status_code == 200
        completed_habit = complete_response.json()
        
        # Verify completion state
        assert completed_habit["status"] == "completed"
        assert completed_habit["streak_days"] == 1
        assert completed_habit["last_completed_at"] == date.today().isoformat()
        
        # Step 3: Update habit details
        update_response = client.patch(f"/habits/{habit_id}", json={
            "name": "Morning Cardio",
            "description": "45 minutes of cardio and stretching"
        })
        assert update_response.status_code == 200
        updated_habit = update_response.json()
        
        # Verify update doesn't affect completion status
        assert updated_habit["name"] == "Morning Cardio"
        assert updated_habit["description"] == "45 minutes of cardio and stretching"
        assert updated_habit["status"] == "completed"  # Unchanged
        assert updated_habit["streak_days"] == 1  # Unchanged
        
        # Step 4: Check statistics
        stats_response = client.get("/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        assert stats["total_habits"] == 1
        assert stats["completed_today"] == 1
        assert stats["active_streaks_ge_3"] == 0  # Streak is only 1
        
        # Step 5: Delete the habit
        delete_response = client.delete(f"/habits/{habit_id}")
        assert delete_response.status_code == 204
        
        # Step 6: Verify deletion affects statistics
        final_stats_response = client.get("/stats")
        final_stats = final_stats_response.json()
        
        assert final_stats["total_habits"] == 0
        assert final_stats["completed_today"] == 0
        assert final_stats["active_streaks_ge_3"] == 0
    
    def test_multiple_habits_workflow(self, client):
        """Test workflow with multiple habits and different completion patterns."""
        # Create multiple habits
        habits_data = [
            {"name": "Exercise", "description": "Daily workout"},
            {"name": "Reading", "description": "Read for 30 minutes"},
            {"name": "Meditation", "description": "10 minutes mindfulness"},
            {"name": "Water", "description": "Drink 8 glasses of water"}
        ]
        
        habit_ids = []
        for habit_data in habits_data:
            response = client.post("/habits", json=habit_data)
            assert response.status_code == 201
            habit_ids.append(response.json()["id"])
        
        # Initial statistics
        stats = client.get("/stats").json()
        assert stats["total_habits"] == 4
        assert stats["completed_today"] == 0
        assert stats["active_streaks_ge_3"] == 0
        
        # Complete some habits
        client.post(f"/habits/{habit_ids[0]}/complete")  # Exercise
        client.post(f"/habits/{habit_ids[1]}/complete")  # Reading
        # Leave Meditation and Water uncompleted
        
        # Check statistics after partial completion
        stats = client.get("/stats").json()
        assert stats["total_habits"] == 4
        assert stats["completed_today"] == 2
        assert stats["active_streaks_ge_3"] == 0
        
        # Filter habits by status
        pending_habits = client.get("/habits?status=pending").json()
        completed_habits = client.get("/habits?status=completed").json()
        
        assert len(pending_habits) == 2
        assert len(completed_habits) == 2
        
        # Verify correct habits are in each category
        pending_names = {h["name"] for h in pending_habits}
        completed_names = {h["name"] for h in completed_habits}
        
        assert pending_names == {"Meditation", "Water"}
        assert completed_names == {"Exercise", "Reading"}
        
        # Update one pending habit to completed status (manual status change)
        meditation_id = next(h["id"] for h in pending_habits if h["name"] == "Meditation")
        client.patch(f"/habits/{meditation_id}", json={"status": "completed"})
        
        # Statistics should not change for completed_today (manual status change)
        stats = client.get("/stats").json()
        assert stats["total_habits"] == 4
        assert stats["completed_today"] == 2  # Still only 2 (Exercise and Reading)
        assert stats["active_streaks_ge_3"] == 0
        
        # Complete the last habit
        water_id = next(h["id"] for h in pending_habits if h["name"] == "Water")
        client.post(f"/habits/{water_id}/complete")
        
        # Final statistics
        final_stats = client.get("/stats").json()
        assert final_stats["total_habits"] == 4
        assert final_stats["completed_today"] == 3  # Exercise, Reading, Water
        assert final_stats["active_streaks_ge_3"] == 0
    
    def test_habit_filtering_workflow(self, client):
        """Test complete workflow for habit filtering functionality."""
        # Create habits with different initial states
        habits = [
            client.post("/habits", json={"name": "Always Pending"}).json(),
            client.post("/habits", json={"name": "Will Complete"}).json(),
            client.post("/habits", json={"name": "Manual Complete"}).json(),
            client.post("/habits", json={"name": "Another Pending"}).json()
        ]
        
        # Complete one habit through completion endpoint
        client.post(f"/habits/{habits[1]['id']}/complete")
        
        # Manually set another to completed status
        client.patch(f"/habits/{habits[2]['id']}", json={"status": "completed"})
        
        # Test filtering by pending status
        pending_response = client.get("/habits?status=pending")
        assert pending_response.status_code == 200
        pending_habits = pending_response.json()
        
        assert len(pending_habits) == 2
        pending_names = {h["name"] for h in pending_habits}
        assert pending_names == {"Always Pending", "Another Pending"}
        
        # Test filtering by completed status
        completed_response = client.get("/habits?status=completed")
        assert completed_response.status_code == 200
        completed_habits = completed_response.json()
        
        assert len(completed_habits) == 2
        completed_names = {h["name"] for h in completed_habits}
        assert completed_names == {"Will Complete", "Manual Complete"}
        
        # Test getting all habits (no filter)
        all_response = client.get("/habits")
        assert all_response.status_code == 200
        all_habits = all_response.json()
        
        assert len(all_habits) == 4
        all_names = {h["name"] for h in all_habits}
        assert all_names == {"Always Pending", "Will Complete", "Manual Complete", "Another Pending"}


class TestStreakResetScenarios:
    """Test streak reset scenarios and edge cases."""
    
    @patch('services.habit_service.date')
    def test_consecutive_day_streak_building(self, mock_date, client):
        """Test building streaks over consecutive days."""
        # Create a habit
        response = client.post("/habits", json={"name": "Daily Exercise"})
        habit_id = response.json()["id"]
        
        # Simulate completing habit over 5 consecutive days
        base_date = date(2024, 1, 15)
        
        for day_offset in range(5):
            current_date = base_date + timedelta(days=day_offset)
            mock_date.today.return_value = current_date
            
            # Complete habit for this day
            with patch('services.habit_service.HabitService.complete_habit_today') as mock_complete:
                # Mock the service method to use our date
                from services.habit_service import HabitService
                service = HabitService(habit_repository)
                completed_habit = service.complete_habit_today(habit_id, current_date)
                mock_complete.return_value = completed_habit
                
                complete_response = client.post(f"/habits/{habit_id}/complete")
                assert complete_response.status_code == 200
                
                habit_data = complete_response.json()
                expected_streak = day_offset + 1
                assert habit_data["streak_days"] == expected_streak
                assert habit_data["last_completed_at"] == current_date.isoformat()
    
    @patch('services.habit_service.date')
    def test_streak_reset_after_gap(self, mock_date, client):
        """Test that streaks reset after missing days."""
        # Create a habit
        response = client.post("/habits", json={"name": "Daily Exercise"})
        habit_id = response.json()["id"]
        
        # Complete for 3 consecutive days
        base_date = date(2024, 1, 15)
        
        for day_offset in range(3):
            current_date = base_date + timedelta(days=day_offset)
            mock_date.today.return_value = current_date
            
            with patch('services.habit_service.HabitService.complete_habit_today') as mock_complete:
                from services.habit_service import HabitService
                service = HabitService(habit_repository)
                completed_habit = service.complete_habit_today(habit_id, current_date)
                mock_complete.return_value = completed_habit
                
                complete_response = client.post(f"/habits/{habit_id}/complete")
                assert complete_response.status_code == 200
        
        # Skip 2 days and complete again
        gap_date = base_date + timedelta(days=5)  # 2-day gap
        mock_date.today.return_value = gap_date
        
        with patch('services.habit_service.HabitService.complete_habit_today') as mock_complete:
            from services.habit_service import HabitService
            service = HabitService(habit_repository)
            completed_habit = service.complete_habit_today(habit_id, gap_date)
            mock_complete.return_value = completed_habit
            
            complete_response = client.post(f"/habits/{habit_id}/complete")
            assert complete_response.status_code == 200
            
            habit_data = complete_response.json()
            assert habit_data["streak_days"] == 1  # Reset to 1 due to gap
            assert habit_data["last_completed_at"] == gap_date.isoformat()
    
    def test_streak_statistics_accuracy(self, client):
        """Test that statistics accurately reflect streak counts."""
        # Create multiple habits
        habit_responses = []
        for i in range(5):
            response = client.post("/habits", json={"name": f"Habit {i+1}"})
            habit_responses.append(response.json())
        
        # Complete habits to create different streak lengths
        # Note: In real integration tests, we can only create streak=1 
        # since we can't manipulate dates easily
        
        # Complete 3 habits today
        for i in range(3):
            client.post(f"/habits/{habit_responses[i]['id']}/complete")
        
        # Check statistics
        stats = client.get("/stats").json()
        assert stats["total_habits"] == 5
        assert stats["completed_today"] == 3
        assert stats["active_streaks_ge_3"] == 0  # All streaks are 1
        
        # To test streaks >= 3, we would need to use service layer tests
        # or mock the date functionality
    
    def test_duplicate_completion_prevention(self, client):
        """Test that duplicate completions on same day are prevented."""
        # Create a habit
        response = client.post("/habits", json={"name": "Daily Exercise"})
        habit_id = response.json()["id"]
        
        # Complete the habit
        first_complete = client.post(f"/habits/{habit_id}/complete")
        assert first_complete.status_code == 200
        
        first_habit = first_complete.json()
        assert first_habit["streak_days"] == 1
        assert first_habit["status"] == "completed"
        
        # Try to complete again on same day
        second_complete = client.post(f"/habits/{habit_id}/complete")
        assert second_complete.status_code == 409
        
        error_data = second_complete.json()
        assert error_data["error_code"] == "DUPLICATE_COMPLETION"
        assert "already completed" in error_data["error"]
        assert error_data["habit_name"] == "Daily Exercise"
        assert error_data["completion_date"] == date.today().isoformat()
        
        # Verify habit state hasn't changed
        habits = client.get("/habits").json()
        habit = next(h for h in habits if h["id"] == habit_id)
        assert habit["streak_days"] == 1  # Unchanged
        assert habit["status"] == "completed"  # Unchanged


class TestDataValidationWorkflows:
    """Test data validation and error response workflows."""
    
    def test_comprehensive_validation_error_workflow(self, client):
        """Test complete workflow for handling validation errors."""
        # Test creation validation errors
        validation_test_cases = [
            # Empty name
            ({"name": ""}, "name"),
            # Name too long
            ({"name": "a" * 81}, "name"),
            # Description too long
            ({"name": "Valid", "description": "a" * 281}, "description"),
            # Missing name
            ({}, "name")
        ]
        
        for invalid_data, expected_field in validation_test_cases:
            response = client.post("/habits", json=invalid_data)
            assert response.status_code == 422
            
            error_detail = response.json()["detail"]
            assert isinstance(error_detail, list)
            assert any(expected_field in str(error).lower() for error in error_detail)
        
        # Create a valid habit for update tests
        valid_response = client.post("/habits", json={"name": "Valid Habit"})
        habit_id = valid_response.json()["id"]
        
        # Test update validation errors
        update_test_cases = [
            # Empty name
            ({"name": ""}, "name"),
            # Name too long
            ({"name": "a" * 81}, "name"),
            # Description too long
            ({"description": "a" * 281}, "description"),
            # Invalid status
            ({"status": "invalid"}, "status")
        ]
        
        for invalid_update, expected_field in update_test_cases:
            response = client.patch(f"/habits/{habit_id}", json=invalid_update)
            assert response.status_code == 422
            
            error_detail = response.json()["detail"]
            assert isinstance(error_detail, list)
            assert any(expected_field in str(error).lower() for error in error_detail)
        
        # Test query parameter validation
        invalid_status_response = client.get("/habits?status=invalid")
        assert invalid_status_response.status_code == 422
    
    def test_error_response_consistency_workflow(self, client):
        """Test that error responses are consistent across different endpoints."""
        # Create a habit for testing
        response = client.post("/habits", json={"name": "Test Habit"})
        habit_id = response.json()["id"]
        
        # Test 404 errors across different endpoints
        not_found_endpoints = [
            ("PATCH", f"/habits/999", {"name": "Updated"}),
            ("DELETE", f"/habits/999", None),
            ("POST", f"/habits/999/complete", None)
        ]
        
        for method, endpoint, data in not_found_endpoints:
            if method == "PATCH":
                response = client.patch(endpoint, json=data)
            elif method == "DELETE":
                response = client.delete(endpoint)
            elif method == "POST":
                response = client.post(endpoint)
            
            assert response.status_code == 404
            error_data = response.json()
            
            # Check consistent error format
            assert "error" in error_data
            assert "error_code" in error_data
            assert error_data["error_code"] == "HABIT_NOT_FOUND"
            assert "habit_id" in error_data
            assert error_data["habit_id"] == 999
        
        # Test 409 error consistency
        client.post(f"/habits/{habit_id}/complete")  # Complete once
        
        duplicate_response = client.post(f"/habits/{habit_id}/complete")
        assert duplicate_response.status_code == 409
        
        error_data = duplicate_response.json()
        required_fields = ["error", "error_code", "habit_name", "completion_date"]
        for field in required_fields:
            assert field in error_data
        
        assert error_data["error_code"] == "DUPLICATE_COMPLETION"
    
    def test_boundary_value_validation_workflow(self, client):
        """Test boundary values for validation rules."""
        # Test exact boundary values that should be valid
        boundary_test_cases = [
            # Exact max name length (80 chars)
            {"name": "a" * 80, "expected_status": 201},
            # Exact max description length (280 chars)
            {"name": "Valid", "description": "a" * 280, "expected_status": 201},
            # Single character name
            {"name": "a", "expected_status": 201}
        ]
        
        for test_case in boundary_test_cases:
            test_data = {k: v for k, v in test_case.items() if k != "expected_status"}
            response = client.post("/habits", json=test_data)
            assert response.status_code == test_case["expected_status"]
            
            if response.status_code == 201:
                habit = response.json()
                assert habit["name"] == test_data["name"]
                if "description" in test_data:
                    assert habit["description"] == test_data["description"]
        
        # Test values just over the boundary (should fail)
        over_boundary_cases = [
            # Name too long by 1 char
            {"name": "a" * 81},
            # Description too long by 1 char
            {"name": "Valid", "description": "a" * 281}
        ]
        
        for invalid_data in over_boundary_cases:
            response = client.post("/habits", json=invalid_data)
            assert response.status_code == 422


class TestComplexIntegrationScenarios:
    """Test complex integration scenarios combining multiple features."""
    
    def test_habit_lifecycle_with_statistics_tracking(self, client):
        """Test complete habit lifecycle while tracking statistics changes."""
        # Track statistics at each step
        def get_current_stats():
            return client.get("/stats").json()
        
        # Initial state
        initial_stats = get_current_stats()
        assert initial_stats == {"total_habits": 0, "completed_today": 0, "active_streaks_ge_3": 0}
        
        # Create first habit
        habit1 = client.post("/habits", json={"name": "Exercise"}).json()
        stats_after_create1 = get_current_stats()
        assert stats_after_create1["total_habits"] == 1
        assert stats_after_create1["completed_today"] == 0
        assert stats_after_create1["active_streaks_ge_3"] == 0
        
        # Create second habit
        habit2 = client.post("/habits", json={"name": "Reading"}).json()
        stats_after_create2 = get_current_stats()
        assert stats_after_create2["total_habits"] == 2
        assert stats_after_create2["completed_today"] == 0
        assert stats_after_create2["active_streaks_ge_3"] == 0
        
        # Complete first habit
        client.post(f"/habits/{habit1['id']}/complete")
        stats_after_complete1 = get_current_stats()
        assert stats_after_complete1["total_habits"] == 2
        assert stats_after_complete1["completed_today"] == 1
        assert stats_after_complete1["active_streaks_ge_3"] == 0
        
        # Complete second habit
        client.post(f"/habits/{habit2['id']}/complete")
        stats_after_complete2 = get_current_stats()
        assert stats_after_complete2["total_habits"] == 2
        assert stats_after_complete2["completed_today"] == 2
        assert stats_after_complete2["active_streaks_ge_3"] == 0
        
        # Update habit status manually (shouldn't affect completed_today)
        habit3 = client.post("/habits", json={"name": "Meditation"}).json()
        client.patch(f"/habits/{habit3['id']}", json={"status": "completed"})
        
        stats_after_manual = get_current_stats()
        assert stats_after_manual["total_habits"] == 3
        assert stats_after_manual["completed_today"] == 2  # Still 2, not 3
        assert stats_after_manual["active_streaks_ge_3"] == 0
        
        # Delete a completed habit
        client.delete(f"/habits/{habit1['id']}")
        stats_after_delete = get_current_stats()
        assert stats_after_delete["total_habits"] == 2
        assert stats_after_delete["completed_today"] == 1  # Only habit2 now
        assert stats_after_delete["active_streaks_ge_3"] == 0
    
    def test_concurrent_operations_workflow(self, client):
        """Test workflow with multiple concurrent operations."""
        # Create multiple habits
        habits = []
        for i in range(5):
            response = client.post("/habits", json={"name": f"Habit {i+1}"})
            habits.append(response.json())
        
        # Perform various operations on different habits
        operations = [
            # Complete some habits
            ("complete", habits[0]["id"], None),
            ("complete", habits[1]["id"], None),
            # Update some habits
            ("update", habits[2]["id"], {"name": "Updated Habit 3"}),
            ("update", habits[3]["id"], {"status": "completed"}),
            # Delete one habit
            ("delete", habits[4]["id"], None)
        ]
        
        for operation, habit_id, data in operations:
            if operation == "complete":
                response = client.post(f"/habits/{habit_id}/complete")
                assert response.status_code == 200
            elif operation == "update":
                response = client.patch(f"/habits/{habit_id}", json=data)
                assert response.status_code == 200
            elif operation == "delete":
                response = client.delete(f"/habits/{habit_id}")
                assert response.status_code == 204
        
        # Verify final state
        final_habits = client.get("/habits").json()
        assert len(final_habits) == 4  # One deleted
        
        # Check that operations were applied correctly
        habit_by_id = {h["id"]: h for h in final_habits}
        
        # Completed habits should have streak_days = 1
        assert habit_by_id[habits[0]["id"]]["streak_days"] == 1
        assert habit_by_id[habits[1]["id"]]["streak_days"] == 1
        
        # Updated habit should have new name
        assert habit_by_id[habits[2]["id"]]["name"] == "Updated Habit 3"
        
        # Manually completed habit should have status completed but streak_days = 0
        assert habit_by_id[habits[3]["id"]]["status"] == "completed"
        assert habit_by_id[habits[3]["id"]]["streak_days"] == 0
        
        # Verify statistics
        stats = client.get("/stats").json()
        assert stats["total_habits"] == 4
        assert stats["completed_today"] == 2  # Only habits[0] and habits[1]
        assert stats["active_streaks_ge_3"] == 0
    
    def test_error_recovery_workflow(self, client):
        """Test workflow for error recovery scenarios."""
        # Create a habit
        habit_response = client.post("/habits", json={"name": "Test Habit"})
        habit_id = habit_response.json()["id"]
        
        # Complete the habit
        complete_response = client.post(f"/habits/{habit_id}/complete")
        assert complete_response.status_code == 200
        
        # Try invalid operations and verify system remains stable
        error_operations = [
            # Try to complete again (should fail)
            ("POST", f"/habits/{habit_id}/complete", 409),
            # Try to update with invalid data (should fail)
            ("PATCH", f"/habits/{habit_id}", 422, {"name": ""}),
            # Try to operate on non-existent habit (should fail)
            ("PATCH", "/habits/999", 404, {"name": "Updated"}),
            ("DELETE", "/habits/999", 404, None),
            ("POST", "/habits/999/complete", 404, None)
        ]
        
        for operation in error_operations:
            method, endpoint = operation[0], operation[1]
            expected_status = operation[2]
            data = operation[3] if len(operation) > 3 else None
            
            if method == "POST":
                response = client.post(endpoint)
            elif method == "PATCH":
                response = client.patch(endpoint, json=data)
            elif method == "DELETE":
                response = client.delete(endpoint)
            
            assert response.status_code == expected_status
        
        # Verify that the original habit is still intact after all errors
        habits = client.get("/habits").json()
        assert len(habits) == 1
        
        original_habit = habits[0]
        assert original_habit["id"] == habit_id
        assert original_habit["name"] == "Test Habit"
        assert original_habit["status"] == "completed"
        assert original_habit["streak_days"] == 1
        
        # Verify statistics are still correct
        stats = client.get("/stats").json()
        assert stats["total_habits"] == 1
        assert stats["completed_today"] == 1
        assert stats["active_streaks_ge_3"] == 0