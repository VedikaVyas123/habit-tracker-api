"""
Comprehensive tests for error handling and validation.

This module contains tests for all error conditions, edge cases,
and validation scenarios to ensure proper error responses.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta

from main import app, habit_repository
from services.habit_service import (
    HabitNotFoundError,
    DuplicateCompletionError,
    InvalidHabitDataError,
    HabitOperationError
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_repository():
    """Clear the repository before each test."""
    habit_repository.clear()


class TestValidationErrors:
    """Test cases for input validation errors."""
    
    def test_create_habit_missing_name(self, client):
        """Test creating a habit without name field."""
        response = client.post("/habits", json={})
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("name" in str(error).lower() for error in error_detail)
    
    def test_create_habit_empty_name(self, client):
        """Test creating a habit with empty name."""
        response = client.post("/habits", json={"name": ""})
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("name" in str(error).lower() for error in error_detail)
    
    def test_create_habit_name_too_long(self, client):
        """Test creating a habit with name exceeding 80 characters."""
        long_name = "a" * 81
        response = client.post("/habits", json={"name": long_name})
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("80" in str(error) for error in error_detail)
    
    def test_create_habit_description_too_long(self, client):
        """Test creating a habit with description exceeding 280 characters."""
        long_description = "a" * 281
        response = client.post("/habits", json={
            "name": "Valid Name",
            "description": long_description
        })
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("280" in str(error) for error in error_detail)
    
    def test_create_habit_invalid_json(self, client):
        """Test creating a habit with invalid JSON."""
        response = client.post("/habits", data="invalid json")
        
        assert response.status_code == 422
    
    def test_update_habit_name_too_long(self, client):
        """Test updating habit with name exceeding 80 characters."""
        # Create a habit first
        create_response = client.post("/habits", json={"name": "Valid Name"})
        habit_id = create_response.json()["id"]
        
        # Try to update with invalid name
        long_name = "a" * 81
        response = client.patch(f"/habits/{habit_id}", json={"name": long_name})
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("80" in str(error) for error in error_detail)
    
    def test_update_habit_description_too_long(self, client):
        """Test updating habit with description exceeding 280 characters."""
        # Create a habit first
        create_response = client.post("/habits", json={"name": "Valid Name"})
        habit_id = create_response.json()["id"]
        
        # Try to update with invalid description
        long_description = "a" * 281
        response = client.patch(f"/habits/{habit_id}", json={"description": long_description})
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("280" in str(error) for error in error_detail)
    
    def test_update_habit_invalid_status(self, client):
        """Test updating habit with invalid status value."""
        # Create a habit first
        create_response = client.post("/habits", json={"name": "Valid Name"})
        habit_id = create_response.json()["id"]
        
        # Try to update with invalid status
        response = client.patch(f"/habits/{habit_id}", json={"status": "invalid_status"})
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("status" in str(error).lower() for error in error_detail)
    
    def test_get_habits_invalid_status_filter(self, client):
        """Test filtering habits with invalid status value."""
        response = client.get("/habits?status=invalid_status")
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("status" in str(error).lower() for error in error_detail)


class TestNotFoundErrors:
    """Test cases for resource not found errors."""
    
    def test_update_nonexistent_habit(self, client):
        """Test updating a habit that doesn't exist."""
        response = client.patch("/habits/999", json={"name": "Updated Name"})
        
        assert response.status_code == 404
        error_data = response.json()
        assert "error" in error_data
        assert "error_code" in error_data
        assert error_data["error_code"] == "HABIT_NOT_FOUND"
        assert "999" in error_data["error"]
        assert "habit_id" in error_data
        assert error_data["habit_id"] == 999
    
    def test_delete_nonexistent_habit(self, client):
        """Test deleting a habit that doesn't exist."""
        response = client.delete("/habits/999")
        
        assert response.status_code == 404
        error_data = response.json()
        assert "error" in error_data
        assert "error_code" in error_data
        assert error_data["error_code"] == "HABIT_NOT_FOUND"
        assert "999" in error_data["error"]
        assert "habit_id" in error_data
        assert error_data["habit_id"] == 999
    
    def test_complete_nonexistent_habit(self, client):
        """Test completing a habit that doesn't exist."""
        response = client.post("/habits/999/complete")
        
        assert response.status_code == 404
        error_data = response.json()
        assert "error" in error_data
        assert "error_code" in error_data
        assert error_data["error_code"] == "HABIT_NOT_FOUND"
        assert "999" in error_data["error"]
        assert "habit_id" in error_data
        assert error_data["habit_id"] == 999
    
    def test_update_habit_with_zero_id(self, client):
        """Test updating a habit with ID 0."""
        response = client.patch("/habits/0", json={"name": "Updated Name"})
        
        assert response.status_code == 400
        error_data = response.json()
        assert "error" in error_data
        assert "error_code" in error_data
        assert error_data["error_code"] == "INVALID_HABIT_DATA"
        assert "positive integer" in error_data["error"]
    
    def test_update_habit_with_negative_id(self, client):
        """Test updating a habit with negative ID."""
        response = client.patch("/habits/-1", json={"name": "Updated Name"})
        
        assert response.status_code == 400
        error_data = response.json()
        assert "error" in error_data
        assert "error_code" in error_data
        assert error_data["error_code"] == "INVALID_HABIT_DATA"
        assert "positive integer" in error_data["error"]


class TestDuplicateCompletionErrors:
    """Test cases for duplicate completion errors."""
    
    def test_complete_habit_twice_same_day(self, client):
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
        error_data = second_response.json()
        assert "error" in error_data
        assert "error_code" in error_data
        assert error_data["error_code"] == "DUPLICATE_COMPLETION"
        assert "already completed" in error_data["error"]
        assert "habit_name" in error_data
        assert error_data["habit_name"] == "Exercise"
        assert "completion_date" in error_data
        assert error_data["completion_date"] == date.today().isoformat()
    
    def test_complete_habit_multiple_attempts_same_day(self, client):
        """Test multiple completion attempts on the same day."""
        # Create and complete a habit
        create_response = client.post("/habits", json={"name": "Read"})
        habit_id = create_response.json()["id"]
        
        # Complete once
        client.post(f"/habits/{habit_id}/complete")
        
        # Try to complete multiple times
        for _ in range(3):
            response = client.post(f"/habits/{habit_id}/complete")
            assert response.status_code == 409
            error_data = response.json()
            assert error_data["error_code"] == "DUPLICATE_COMPLETION"
            assert "Read" in error_data["habit_name"]


class TestInvalidDataErrors:
    """Test cases for invalid data errors."""
    
    def test_update_habit_with_string_id_in_url(self, client):
        """Test updating a habit with string ID in URL."""
        response = client.patch("/habits/abc", json={"name": "Updated Name"})
        
        assert response.status_code == 422  # FastAPI validation error
    
    def test_complete_habit_with_string_id_in_url(self, client):
        """Test completing a habit with string ID in URL."""
        response = client.post("/habits/abc/complete")
        
        assert response.status_code == 422  # FastAPI validation error
    
    def test_delete_habit_with_string_id_in_url(self, client):
        """Test deleting a habit with string ID in URL."""
        response = client.delete("/habits/abc")
        
        assert response.status_code == 422  # FastAPI validation error


class TestBusinessLogicErrors:
    """Test cases for business logic validation errors."""
    
    def test_create_habit_with_null_name(self, client):
        """Test creating a habit with null name."""
        response = client.post("/habits", json={"name": None})
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("name" in str(error).lower() for error in error_detail)
    
    def test_create_habit_with_whitespace_only_name(self, client):
        """Test creating a habit with whitespace-only name."""
        response = client.post("/habits", json={"name": "   "})
        
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        # Pydantic should catch this as it violates min_length after stripping
        assert any("name" in str(error).lower() for error in error_detail)
    
    def test_update_habit_with_null_values(self, client):
        """Test updating a habit with explicit null values."""
        # Create a habit first
        create_response = client.post("/habits", json={
            "name": "Original Name",
            "description": "Original Description"
        })
        habit_id = create_response.json()["id"]
        
        # Update with null values (should be allowed for optional fields)
        response = client.patch(f"/habits/{habit_id}", json={
            "description": None
        })
        
        assert response.status_code == 200
        updated_habit = response.json()
        assert updated_habit["description"] is None
        assert updated_habit["name"] == "Original Name"  # Unchanged


class TestErrorResponseFormat:
    """Test cases for error response format consistency."""
    
    def test_not_found_error_format(self, client):
        """Test that not found errors have consistent format."""
        response = client.get("/habits/999")
        
        # This should be a 404 from FastAPI since the endpoint doesn't exist
        assert response.status_code == 404
    
    def test_validation_error_format(self, client):
        """Test that validation errors have consistent format."""
        response = client.post("/habits", json={"name": ""})
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)
    
    def test_duplicate_completion_error_format(self, client):
        """Test that duplicate completion errors have consistent format."""
        # Create and complete a habit
        create_response = client.post("/habits", json={"name": "Test Habit"})
        habit_id = create_response.json()["id"]
        client.post(f"/habits/{habit_id}/complete")
        
        # Try to complete again
        response = client.post(f"/habits/{habit_id}/complete")
        
        assert response.status_code == 409
        error_data = response.json()
        
        # Check required fields
        required_fields = ["error", "error_code", "habit_name", "completion_date"]
        for field in required_fields:
            assert field in error_data
        
        # Check field types
        assert isinstance(error_data["error"], str)
        assert isinstance(error_data["error_code"], str)
        assert isinstance(error_data["habit_name"], str)
        assert isinstance(error_data["completion_date"], str)
    
    def test_habit_not_found_error_format(self, client):
        """Test that habit not found errors have consistent format."""
        response = client.patch("/habits/999", json={"name": "Updated"})
        
        assert response.status_code == 404
        error_data = response.json()
        
        # Check required fields
        required_fields = ["error", "error_code", "habit_id"]
        for field in required_fields:
            assert field in error_data
        
        # Check field types and values
        assert isinstance(error_data["error"], str)
        assert error_data["error_code"] == "HABIT_NOT_FOUND"
        assert error_data["habit_id"] == 999
    
    def test_invalid_data_error_format(self, client):
        """Test that invalid data errors have consistent format."""
        response = client.patch("/habits/0", json={"name": "Updated"})
        
        assert response.status_code == 400
        error_data = response.json()
        
        # Check required fields
        required_fields = ["error", "error_code", "field", "value", "constraint"]
        for field in required_fields:
            assert field in error_data
        
        # Check field types
        assert isinstance(error_data["error"], str)
        assert error_data["error_code"] == "INVALID_HABIT_DATA"
        assert isinstance(error_data["field"], str)
        assert isinstance(error_data["value"], str)
        assert isinstance(error_data["constraint"], str)


class TestEdgeCases:
    """Test cases for edge cases and boundary conditions."""
    
    def test_create_habit_exact_name_length_limit(self, client):
        """Test creating a habit with exactly 80 character name."""
        exact_length_name = "a" * 80
        response = client.post("/habits", json={"name": exact_length_name})
        
        assert response.status_code == 201
        habit = response.json()
        assert habit["name"] == exact_length_name
    
    def test_create_habit_exact_description_length_limit(self, client):
        """Test creating a habit with exactly 280 character description."""
        exact_length_description = "a" * 280
        response = client.post("/habits", json={
            "name": "Valid Name",
            "description": exact_length_description
        })
        
        assert response.status_code == 201
        habit = response.json()
        assert habit["description"] == exact_length_description
    
    def test_update_habit_with_empty_request_body(self, client):
        """Test updating a habit with completely empty request body."""
        # Create a habit first
        create_response = client.post("/habits", json={"name": "Original Name"})
        habit_id = create_response.json()["id"]
        original_habit = create_response.json()
        
        # Update with empty body
        response = client.patch(f"/habits/{habit_id}", json={})
        
        assert response.status_code == 200
        updated_habit = response.json()
        
        # All fields should remain unchanged
        assert updated_habit["name"] == original_habit["name"]
        assert updated_habit["description"] == original_habit["description"]
        assert updated_habit["status"] == original_habit["status"]
    
    def test_multiple_error_conditions_in_sequence(self, client):
        """Test multiple error conditions in sequence."""
        # Try to update non-existent habit
        response1 = client.patch("/habits/999", json={"name": "Test"})
        assert response1.status_code == 404
        
        # Create a habit
        create_response = client.post("/habits", json={"name": "Test Habit"})
        habit_id = create_response.json()["id"]
        
        # Complete it
        complete_response = client.post(f"/habits/{habit_id}/complete")
        assert complete_response.status_code == 200
        
        # Try to complete again (should fail)
        duplicate_response = client.post(f"/habits/{habit_id}/complete")
        assert duplicate_response.status_code == 409
        
        # Delete the habit
        delete_response = client.delete(f"/habits/{habit_id}")
        assert delete_response.status_code == 204
        
        # Try to update deleted habit (should fail)
        update_deleted_response = client.patch(f"/habits/{habit_id}", json={"name": "Updated"})
        assert update_deleted_response.status_code == 404


class TestConcurrentErrorScenarios:
    """Test cases for concurrent error scenarios."""
    
    def test_multiple_habits_error_isolation(self, client):
        """Test that errors with one habit don't affect others."""
        # Create multiple habits
        habit1_response = client.post("/habits", json={"name": "Habit 1"})
        habit2_response = client.post("/habits", json={"name": "Habit 2"})
        
        habit1_id = habit1_response.json()["id"]
        habit2_id = habit2_response.json()["id"]
        
        # Complete habit1
        client.post(f"/habits/{habit1_id}/complete")
        
        # Try to complete habit1 again (should fail)
        duplicate_response = client.post(f"/habits/{habit1_id}/complete")
        assert duplicate_response.status_code == 409
        
        # Complete habit2 (should succeed despite habit1 error)
        habit2_complete_response = client.post(f"/habits/{habit2_id}/complete")
        assert habit2_complete_response.status_code == 200
        
        # Verify both habits exist and have correct states
        habits_response = client.get("/habits")
        habits = habits_response.json()
        assert len(habits) == 2
        
        habit1_data = next(h for h in habits if h["id"] == habit1_id)
        habit2_data = next(h for h in habits if h["id"] == habit2_id)
        
        assert habit1_data["status"] == "completed"
        assert habit2_data["status"] == "completed"
        assert habit1_data["streak_days"] == 1
        assert habit2_data["streak_days"] == 1