#!/usr/bin/env python3
"""Quick test to verify error handling works."""

def test_basic_functionality():
    """Test basic error handling functionality."""
    try:
        # Test imports
        from services.habit_service import (
            HabitService, 
            HabitNotFoundError, 
            InvalidHabitDataError
        )
        from repositories.habit_repository import HabitRepository
        from models.habit import CreateHabitRequest
        
        print("✓ Imports successful")
        
        # Test service creation
        service = HabitService(HabitRepository())
        print("✓ Service created")
        
        # Test error creation
        error = HabitNotFoundError(123)
        assert error.habit_id == 123
        assert error.error_code == "HABIT_NOT_FOUND"
        print("✓ Custom exceptions work")
        
        # Test validation
        try:
            service.get_habit_by_id(0)
            print("✗ Should have raised error")
            return False
        except InvalidHabitDataError as e:
            assert "positive integer" in e.message
            print("✓ Validation works")
        
        # Test habit creation and completion
        habit = service.create_habit(CreateHabitRequest(name="Test"))
        completed_habit = service.complete_habit_today(habit.id)
        assert completed_habit.streak_days == 1
        print("✓ Basic functionality works")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_basic_functionality():
        print("\n🎉 Basic error handling test passed!")
    else:
        print("\n❌ Basic error handling test failed!")