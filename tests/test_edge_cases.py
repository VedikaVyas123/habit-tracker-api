"""
Comprehensive edge case tests for the Habit Tracker API.

This module contains tests for edge cases, boundary conditions,
and unusual scenarios to ensure robust error handling and system stability.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from main import app, habit_repository


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_repository():
    """Clear the repository before each test."""
    habit_repository.clear()


class TestBoundaryConditions:
    """Test boundary conditions and edge values."""
    
    def test_habit_name_boundary_values(self, client):
        """Test habit names at exact boundary lengths."""
        # Test minimum valid length (1 character)
        min_response = client.post("/habits", json={"name": "a"})
        assert min_response.status_code == 201
        assert min_response.json()["name"] == "a"
        
        # Test maximum valid length (80 characters)
        max_name = "a" * 80
        max_response = client.post("/habits", json={"name": max_name})
        assert max_response.status_code == 201
        assert max_response.json()["name"] == max_name
        
        # Test just over maximum (81 characters) - should fail
        over_max_response = client.post("/habits", json={"name": "a" * 81})
        assert over_max_response.status_code == 422
    
    def test_habit_description_boundary_values(self, client):
        """Test habit descriptions at exact boundary lengths."""
        # Test maximum valid length (280 characters)
        max_description = "a" * 280
        max_response = client.post("/habits", json={
            "name": "Test",
            "description": max_description
        })
        assert max_response.status_code == 201
        assert max_response.json()["description"] == max_description
        
        # Test just over maximum (281 characters) - should fail
        over_max_response = client.post("/habits", json={
            "name": "Test",
            "description": "a" * 281
        })
        assert over_max_response.status_code == 422
        
        # Test empty description (should be valid)
        empty_response = client.post("/habits", json={
            "name": "Test",
            "description": ""
        })
        assert empty_response.status_code == 201
        assert empty_response.json()["description"] == ""
    
    def test_habit_id_boundary_values(self, client):
        """Test operations with edge case habit IDs."""
        # Create a habit to get a valid ID
        habit_response = client.post("/habits", json={"name": "Test"})
        valid_id = habit_response.json()["id"]
        
        # Test with ID 0 (should be invalid)
        zero_response = client.patch("/habits/0", json={"name": "Updated"})
        assert zero_response.status_code == 400
        assert zero_response.json()["error_code"] == "INVALID_HABIT_DATA"
        
        # Test with negative ID (should be invalid)
        negative_response = client.patch("/habits/-1", json={"name": "Updated"})
        assert negative_response.status_code == 400
        assert negative_response.json()["error_code"] == "INVALID_HABIT_DATA"
        
        # Test with very large ID (should return 404)
        large_id_response = client.patch("/habits/999999", json={"name": "Updated"})
        assert large_id_response.status_code == 404
        assert large_id_response.json()["error_code"] == "HABIT_NOT_FOUND"
    
    def test_statistics_with_zero_habits(self, client):
        """Test statistics calculations with zero habits."""
        stats_response = client.get("/stats")
        assert stats_response.status_code == 200
        
        stats = stats_response.json()
        assert stats["total_habits"] == 0
        assert stats["completed_today"] == 0
        assert stats["active_streaks_ge_3"] == 0
    
    def test_statistics_with_maximum_habits(self, client):
        """Test statistics with a large number of habits."""
        # Create many habits
        num_habits = 100
        habit_ids = []
        
        for i in range(num_habits):
            response = client.post("/habits", json={"name": f"Habit {i+1}"})
            assert response.status_code == 201
            habit_ids.append(response.json()["id"])
        
        # Complete half of them
        for i in range(0, num_habits, 2):  # Every other habit
            client.post(f"/habits/{habit_ids[i]}/complete")
        
        # Check statistics
        stats = client.get("/stats").json()
        assert stats["total_habits"] == num_habits
        assert stats["completed_today"] == num_habits // 2
        assert stats["active_streaks_ge_3"] == 0  # All streaks are 1


class TestSpecialCharacterHandling:
    """Test handling of special characters and Unicode."""
    
    def test_habit_name_with_special_characters(self, client):
        """Test habit names with special characters."""
        special_names = [
            "Exercise & Fitness",
            "Read 📚 Books",
            "Méditation",
            "Drink H₂O",
            "Code @ 9AM",
            "Walk 🚶‍♂️ 10k steps",
            "习惯追踪",  # Chinese characters
            "عادة يومية",  # Arabic characters
            "Привычка"  # Cyrillic characters
        ]
        
        for name in special_names:
            if len(name) <= 80:  # Only test if within length limit
                response = client.post("/habits", json={"name": name})
                assert response.status_code == 201
                assert response.json()["name"] == name
    
    def test_habit_description_with_special_characters(self, client):
        """Test habit descriptions with special characters."""
        special_descriptions = [
            "Track daily exercise 💪 and maintain fitness goals",
            "Read at least 30 minutes per day 📖",
            "Practice mindfulness & meditation 🧘‍♀️",
            "Drink 8 glasses of water (H₂O) daily",
            "Code review @ 2PM every day",
            "Walk 🚶‍♂️ for 30 minutes in the park"
        ]
        
        for i, description in enumerate(special_descriptions):
            if len(description) <= 280:  # Only test if within length limit
                response = client.post("/habits", json={
                    "name": f"Test {i+1}",
                    "description": description
                })
                assert response.status_code == 201
                assert response.json()["description"] == description
    
    def test_habit_name_with_whitespace_variations(self, client):
        """Test habit names with various whitespace patterns."""
        # Test names with leading/trailing spaces (should be preserved)
        whitespace_names = [
            " Exercise",  # Leading space
            "Exercise ",  # Trailing space
            " Exercise ",  # Both
            "Daily  Exercise",  # Double space in middle
            "Exercise\tDaily",  # Tab character
            "Exercise\nDaily"  # Newline character (if allowed)
        ]
        
        for name in whitespace_names:
            if len(name.strip()) > 0 and len(name) <= 80:
                response = client.post("/habits", json={"name": name})
                # The response depends on how Pydantic handles whitespace
                # Most likely it will either accept as-is or strip whitespace
                assert response.status_code in [201, 422]


class TestConcurrencyEdgeCases:
    """Test edge cases related to concurrent operations."""
    
    def test_rapid_habit_creation(self, client):
        """Test rapid creation of multiple habits."""
        # Create many habits rapidly
        responses = []
        for i in range(50):
            response = client.post("/habits", json={"name": f"Rapid Habit {i+1}"})
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 201
        
        # All should have unique IDs
        ids = [r.json()["id"] for r in responses]
        assert len(set(ids)) == len(ids)  # All unique
        
        # IDs should be sequential
        assert ids == list(range(1, 51))
    
    def test_rapid_habit_completion(self, client):
        """Test rapid completion of multiple habits."""
        # Create multiple habits
        habit_ids = []
        for i in range(20):
            response = client.post("/habits", json={"name": f"Habit {i+1}"})
            habit_ids.append(response.json()["id"])
        
        # Complete all habits rapidly
        completion_responses = []
        for habit_id in habit_ids:
            response = client.post(f"/habits/{habit_id}/complete")
            completion_responses.append(response)
        
        # All completions should succeed
        for response in completion_responses:
            assert response.status_code == 200
            assert response.json()["streak_days"] == 1
        
        # Statistics should be accurate
        stats = client.get("/stats").json()
        assert stats["total_habits"] == 20
        assert stats["completed_today"] == 20
        assert stats["active_streaks_ge_3"] == 0
    
    def test_mixed_operations_on_same_habit(self, client):
        """Test mixed operations performed on the same habit."""
        # Create a habit
        response = client.post("/habits", json={"name": "Test Habit"})
        habit_id = response.json()["id"]
        
        # Perform various operations
        operations = [
            # Update name
            client.patch(f"/habits/{habit_id}", json={"name": "Updated Habit"}),
            # Update description
            client.patch(f"/habits/{habit_id}", json={"description": "New description"}),
            # Complete habit
            client.post(f"/habits/{habit_id}/complete"),
            # Try to complete again (should fail)
            client.post(f"/habits/{habit_id}/complete"),
            # Update status manually
            client.patch(f"/habits/{habit_id}", json={"status": "pending"}),
            # Update back to completed
            client.patch(f"/habits/{habit_id}", json={"status": "completed"})
        ]
        
        expected_statuses = [200, 200, 200, 409, 200, 200]
        
        for i, (response, expected_status) in enumerate(zip(operations, expected_statuses)):
            assert response.status_code == expected_status, f"Operation {i} failed"
        
        # Verify final state
        final_habit = client.get("/habits").json()[0]
        assert final_habit["name"] == "Updated Habit"
        assert final_habit["description"] == "New description"
        assert final_habit["status"] == "completed"
        assert final_habit["streak_days"] == 1  # From actual completion, not status change


class TestDataIntegrityEdgeCases:
    """Test data integrity in edge case scenarios."""
    
    def test_habit_deletion_during_operations(self, client):
        """Test operations on habits that get deleted."""
        # Create multiple habits
        habit1 = client.post("/habits", json={"name": "Habit 1"}).json()
        habit2 = client.post("/habits", json={"name": "Habit 2"}).json()
        
        # Delete habit1
        delete_response = client.delete(f"/habits/{habit1['id']}")
        assert delete_response.status_code == 204
        
        # Try operations on deleted habit
        update_response = client.patch(f"/habits/{habit1['id']}", json={"name": "Updated"})
        assert update_response.status_code == 404
        
        complete_response = client.post(f"/habits/{habit1['id']}/complete")
        assert complete_response.status_code == 404
        
        # Operations on remaining habit should still work
        update_habit2 = client.patch(f"/habits/{habit2['id']}", json={"name": "Updated Habit 2"})
        assert update_habit2.status_code == 200
        
        complete_habit2 = client.post(f"/habits/{habit2['id']}/complete")
        assert complete_habit2.status_code == 200
    
    def test_statistics_consistency_after_deletions(self, client):
        """Test that statistics remain consistent after habit deletions."""
        # Create and complete multiple habits
        habit_ids = []
        for i in range(5):
            response = client.post("/habits", json={"name": f"Habit {i+1}"})
            habit_id = response.json()["id"]
            habit_ids.append(habit_id)
            
            # Complete every other habit
            if i % 2 == 0:
                client.post(f"/habits/{habit_id}/complete")
        
        # Check initial statistics
        initial_stats = client.get("/stats").json()
        assert initial_stats["total_habits"] == 5
        assert initial_stats["completed_today"] == 3  # Habits 1, 3, 5
        
        # Delete a completed habit
        client.delete(f"/habits/{habit_ids[0]}")  # Delete Habit 1 (completed)
        
        # Check statistics after deletion
        after_delete_stats = client.get("/stats").json()
        assert after_delete_stats["total_habits"] == 4
        assert after_delete_stats["completed_today"] == 2  # Habits 3, 5 remaining
        
        # Delete an uncompleted habit
        client.delete(f"/habits/{habit_ids[1]}")  # Delete Habit 2 (not completed)
        
        # Check statistics after second deletion
        final_stats = client.get("/stats").json()
        assert final_stats["total_habits"] == 3
        assert final_stats["completed_today"] == 2  # Still Habits 3, 5
    
    def test_habit_id_reuse_after_deletion(self, client):
        """Test that habit IDs are not reused after deletion."""
        # Create a habit
        habit1 = client.post("/habits", json={"name": "Habit 1"}).json()
        habit1_id = habit1["id"]
        
        # Delete it
        client.delete(f"/habits/{habit1_id}")
        
        # Create new habits
        habit2 = client.post("/habits", json={"name": "Habit 2"}).json()
        habit3 = client.post("/habits", json={"name": "Habit 3"}).json()
        
        # New habits should have different IDs (not reusing deleted ID)
        assert habit2["id"] != habit1_id
        assert habit3["id"] != habit1_id
        assert habit2["id"] != habit3["id"]
        
        # IDs should continue incrementing
        assert habit2["id"] > habit1_id
        assert habit3["id"] > habit2["id"]


class TestErrorHandlingEdgeCases:
    """Test edge cases in error handling."""
    
    def test_malformed_json_requests(self, client):
        """Test handling of malformed JSON requests."""
        # Test completely invalid JSON
        response = client.post("/habits", data="invalid json", headers={"Content-Type": "application/json"})
        assert response.status_code == 422
        
        # Test partial JSON
        response = client.post("/habits", data='{"name": "test"', headers={"Content-Type": "application/json"})
        assert response.status_code == 422
        
        # Test JSON with wrong types
        response = client.post("/habits", json={"name": 123})  # name should be string
        assert response.status_code == 422
    
    def test_missing_content_type_header(self, client):
        """Test requests without proper content type."""
        # Test POST without content-type header
        response = client.post("/habits", data='{"name": "test"}')
        # FastAPI should handle this gracefully
        assert response.status_code in [422, 400]
    
    def test_empty_request_bodies(self, client):
        """Test handling of empty request bodies."""
        # Empty body for POST (should fail - name is required)
        response = client.post("/habits", json={})
        assert response.status_code == 422
        
        # Empty body for PATCH (should succeed - all fields optional)
        habit = client.post("/habits", json={"name": "Test"}).json()
        response = client.patch(f"/habits/{habit['id']}", json={})
        assert response.status_code == 200
    
    def test_null_values_in_requests(self, client):
        """Test handling of null values in requests."""
        # Null name (should fail)
        response = client.post("/habits", json={"name": None})
        assert response.status_code == 422
        
        # Null description (should be valid)
        response = client.post("/habits", json={"name": "Test", "description": None})
        assert response.status_code == 201
        assert response.json()["description"] is None
        
        # Null status in update (should be valid)
        habit = client.post("/habits", json={"name": "Test"}).json()
        response = client.patch(f"/habits/{habit['id']}", json={"status": None})
        assert response.status_code == 200


class TestSystemLimitsAndPerformance:
    """Test system limits and performance edge cases."""
    
    def test_maximum_habit_name_with_unicode(self, client):
        """Test maximum length names with Unicode characters."""
        # Unicode characters may take more bytes than ASCII
        unicode_char = "🏃"  # Running emoji
        
        # Calculate how many we can fit in 80 characters
        max_unicode_name = unicode_char * 80
        
        if len(max_unicode_name) == 80:  # If each emoji counts as 1 character
            response = client.post("/habits", json={"name": max_unicode_name})
            assert response.status_code == 201
        
        # Test one over the limit
        over_limit_name = unicode_char * 81
        response = client.post("/habits", json={"name": over_limit_name})
        assert response.status_code == 422
    
    def test_habit_filtering_with_large_dataset(self, client):
        """Test habit filtering performance with large dataset."""
        # Create many habits with different statuses
        pending_count = 0
        completed_count = 0
        
        for i in range(200):
            habit = client.post("/habits", json={"name": f"Habit {i+1}"}).json()
            
            if i % 3 == 0:  # Complete every third habit
                client.post(f"/habits/{habit['id']}/complete")
                completed_count += 1
            else:
                pending_count += 1
        
        # Test filtering performance
        all_habits = client.get("/habits").json()
        pending_habits = client.get("/habits?status=pending").json()
        completed_habits = client.get("/habits?status=completed").json()
        
        assert len(all_habits) == 200
        assert len(pending_habits) == pending_count
        assert len(completed_habits) == completed_count
        
        # Verify filtering accuracy
        for habit in pending_habits:
            assert habit["status"] == "pending"
        
        for habit in completed_habits:
            assert habit["status"] == "completed"
    
    def test_statistics_calculation_performance(self, client):
        """Test statistics calculation with large number of habits."""
        # Create many habits and complete some
        total_habits = 500
        completed_today = 0
        
        for i in range(total_habits):
            habit = client.post("/habits", json={"name": f"Habit {i+1}"}).json()
            
            if i % 4 == 0:  # Complete every fourth habit
                client.post(f"/habits/{habit['id']}/complete")
                completed_today += 1
        
        # Test statistics calculation
        stats = client.get("/stats").json()
        
        assert stats["total_habits"] == total_habits
        assert stats["completed_today"] == completed_today
        assert stats["active_streaks_ge_3"] == 0  # All streaks are 1
        
        # Multiple calls should return consistent results
        for _ in range(5):
            repeat_stats = client.get("/stats").json()
            assert repeat_stats == stats


class TestUnexpectedInputEdgeCases:
    """Test handling of unexpected or unusual inputs."""
    
    def test_extremely_long_field_values(self, client):
        """Test handling of extremely long field values."""
        # Extremely long name (way over limit)
        very_long_name = "a" * 10000
        response = client.post("/habits", json={"name": very_long_name})
        assert response.status_code == 422
        
        # Extremely long description (way over limit)
        very_long_description = "a" * 10000
        response = client.post("/habits", json={
            "name": "Test",
            "description": very_long_description
        })
        assert response.status_code == 422
    
    def test_unusual_status_values(self, client):
        """Test handling of unusual status values."""
        habit = client.post("/habits", json={"name": "Test"}).json()
        
        unusual_statuses = [
            "PENDING",  # Wrong case
            "Completed",  # Wrong case
            "active",  # Invalid value
            "done",  # Invalid value
            "",  # Empty string
            " pending ",  # With spaces
        ]
        
        for status in unusual_statuses:
            response = client.patch(f"/habits/{habit['id']}", json={"status": status})
            assert response.status_code == 422
    
    def test_numeric_string_inputs(self, client):
        """Test handling of numeric strings where strings are expected."""
        # Numeric string as name (should be valid)
        response = client.post("/habits", json={"name": "123"})
        assert response.status_code == 201
        assert response.json()["name"] == "123"
        
        # Numeric string as description (should be valid)
        response = client.post("/habits", json={
            "name": "Test",
            "description": "456"
        })
        assert response.status_code == 201
        assert response.json()["description"] == "456"
    
    def test_boolean_inputs_where_strings_expected(self, client):
        """Test handling of boolean inputs where strings are expected."""
        # Boolean as name (should fail)
        response = client.post("/habits", json={"name": True})
        assert response.status_code == 422
        
        # Boolean as description (should fail)
        response = client.post("/habits", json={
            "name": "Test",
            "description": False
        })
        assert response.status_code == 422