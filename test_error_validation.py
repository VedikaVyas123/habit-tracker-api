#!/usr/bin/env python3
"""
Simple validation script to test error handling implementation.
"""

def test_imports():
    """Test that all imports work correctly."""
    try:
        from services.habit_service import (
            HabitService, 
            HabitNotFoundError, 
            DuplicateCompletionError,
            InvalidHabitDataError,
            HabitOperationError,
            HabitServiceError
        )
        from repositories.habit_repository import HabitRepository
        from models.habit import CreateHabitRequest
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_exception_creation():
    """Test that custom exceptions can be created."""
    try:
        from services.habit_service import (
            HabitNotFoundError, 
            DuplicateCompletionError,
            InvalidHabitDataError,
            HabitOperationError
        )
        
        # Test HabitNotFoundError
        error1 = HabitNotFoundError(123)
        assert error1.habit_id == 123
        assert error1.error_code == "HABIT_NOT_FOUND"
        assert "123" in error1.message
        print("✓ HabitNotFoundError works")
        
        # Test DuplicateCompletionError
        error2 = DuplicateCompletionError("Exercise", "2024-01-01")
        assert error2.habit_name == "Exercise"
        assert error2.completion_date == "2024-01-01"
        assert error2.error_code == "DUPLICATE_COMPLETION"
        print("✓ DuplicateCompletionError works")
        
        # Test InvalidHabitDataError
        error3 = InvalidHabitDataError("habit_id", "0", "Must be positive")
        assert error3.field == "habit_id"
        assert error3.value == "0"
        assert error3.constraint == "Must be positive"
        assert error3.error_code == "INVALID_HABIT_DATA"
        print("✓ InvalidHabitDataError works")
        
        # Test HabitOperationError
        error4 = HabitOperationError("delete", "Habit is in use")
        assert error4.operation == "delete"
        assert error4.reason == "Habit is in use"
        assert error4.error_code == "HABIT_OPERATION_ERROR"
        print("✓ HabitOperationError works")
        
        return True
    except Exception as e:
        print(f"✗ Exception creation error: {e}")
        return False

def test_service_validation():
    """Test that service validation works."""
    try:
        from services.habit_service import HabitService, InvalidHabitDataError
        from repositories.habit_repository import HabitRepository
        
        service = HabitService(HabitRepository())
        
        # Test invalid habit ID
        try:
            service.get_habit_by_id(0)
            print("✗ Should have raised InvalidHabitDataError for ID 0")
            return False
        except InvalidHabitDataError as e:
            assert e.error_code == "INVALID_HABIT_DATA"
            assert "positive integer" in e.message
            print("✓ Invalid habit ID validation works")
        
        # Test negative habit ID
        try:
            service.get_habit_by_id(-1)
            print("✗ Should have raised InvalidHabitDataError for negative ID")
            return False
        except InvalidHabitDataError as e:
            assert e.error_code == "INVALID_HABIT_DATA"
            print("✓ Negative habit ID validation works")
        
        return True
    except Exception as e:
        print(f"✗ Service validation error: {e}")
        return False

def main():
    """Run all validation tests."""
    print("Testing error handling implementation...")
    print()
    
    tests = [
        test_imports,
        test_exception_creation,
        test_service_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All error handling tests passed!")
        return True
    else:
        print("✗ Some tests failed")
        return False

if __name__ == "__main__":
    main()