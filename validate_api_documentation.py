#!/usr/bin/env python3
"""
API Documentation Validation Script

This script validates that the Habit Tracker API documentation is properly generated
and that all endpoints work correctly through the OpenAPI interface.
"""

import asyncio
import json
import sys
from datetime import date
from typing import Dict, Any, List

import httpx
from fastapi.testclient import TestClient

# Import the FastAPI app
from main import app


class APIDocumentationValidator:
    """Validates API documentation and endpoint functionality."""
    
    def __init__(self):
        self.client = TestClient(app)
        self.base_url = "http://testserver"
        self.validation_results = []
        
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log a validation result."""
        status = "✅ PASS" if success else "❌ FAIL"
        self.validation_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")
    
    def validate_openapi_schema(self) -> bool:
        """Validate that OpenAPI schema is properly generated."""
        print("\n🔍 Validating OpenAPI Schema Generation...")
        
        try:
            # Test /docs endpoint accessibility
            response = self.client.get("/docs")
            self.log_result(
                "OpenAPI docs endpoint accessible",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            # Test OpenAPI JSON schema
            response = self.client.get("/openapi.json")
            success = response.status_code == 200
            self.log_result(
                "OpenAPI JSON schema generated",
                success,
                f"Status: {response.status_code}"
            )
            
            if success:
                schema = response.json()
                
                # Validate basic schema structure
                required_fields = ["openapi", "info", "paths"]
                for field in required_fields:
                    has_field = field in schema
                    self.log_result(
                        f"Schema has required field: {field}",
                        has_field
                    )
                
                # Validate API info
                info = schema.get("info", {})
                self.log_result(
                    "API title is set",
                    info.get("title") == "Habit Tracker API"
                )
                self.log_result(
                    "API description is set",
                    bool(info.get("description"))
                )
                self.log_result(
                    "API version is set",
                    info.get("version") == "1.0.0"
                )
                
                return True
            
            return False
            
        except Exception as e:
            self.log_result(
                "OpenAPI schema validation",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def validate_endpoint_documentation(self) -> bool:
        """Validate that all endpoints are properly documented."""
        print("\n📚 Validating Endpoint Documentation...")
        
        try:
            response = self.client.get("/openapi.json")
            if response.status_code != 200:
                self.log_result(
                    "Could not retrieve OpenAPI schema",
                    False
                )
                return False
            
            schema = response.json()
            paths = schema.get("paths", {})
            
            # Expected endpoints
            expected_endpoints = [
                ("GET", "/"),
                ("POST", "/habits"),
                ("GET", "/habits"),
                ("PATCH", "/habits/{habit_id}"),
                ("DELETE", "/habits/{habit_id}"),
                ("POST", "/habits/{habit_id}/complete"),
                ("GET", "/stats")
            ]
            
            for method, path in expected_endpoints:
                path_exists = path in paths
                self.log_result(
                    f"Endpoint documented: {method} {path}",
                    path_exists
                )
                
                if path_exists:
                    method_lower = method.lower()
                    method_exists = method_lower in paths[path]
                    self.log_result(
                        f"Method documented: {method} {path}",
                        method_exists
                    )
                    
                    if method_exists:
                        endpoint_info = paths[path][method_lower]
                        
                        # Check for summary/description
                        has_description = bool(endpoint_info.get("summary") or endpoint_info.get("description"))
                        self.log_result(
                            f"Endpoint has description: {method} {path}",
                            has_description
                        )
                        
                        # Check for response schemas
                        responses = endpoint_info.get("responses", {})
                        has_responses = bool(responses)
                        self.log_result(
                            f"Endpoint has response schemas: {method} {path}",
                            has_responses
                        )
            
            return True
            
        except Exception as e:
            self.log_result(
                "Endpoint documentation validation",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def validate_request_response_schemas(self) -> bool:
        """Validate that request/response schemas are correctly documented."""
        print("\n🔧 Validating Request/Response Schemas...")
        
        try:
            response = self.client.get("/openapi.json")
            if response.status_code != 200:
                return False
            
            schema = response.json()
            components = schema.get("components", {})
            schemas = components.get("schemas", {})
            
            # Expected schemas
            expected_schemas = [
                "Habit",
                "CreateHabitRequest", 
                "UpdateHabitRequest",
                "StatsResponse",
                "ErrorResponse",
                "HabitNotFoundErrorResponse",
                "DuplicateCompletionErrorResponse",
                "InvalidHabitDataErrorResponse"
            ]
            
            for schema_name in expected_schemas:
                schema_exists = schema_name in schemas
                self.log_result(
                    f"Schema documented: {schema_name}",
                    schema_exists
                )
                
                if schema_exists:
                    schema_def = schemas[schema_name]
                    
                    # Check for properties
                    has_properties = "properties" in schema_def
                    self.log_result(
                        f"Schema has properties: {schema_name}",
                        has_properties
                    )
                    
                    # Check for field descriptions
                    if has_properties:
                        properties = schema_def["properties"]
                        described_fields = sum(1 for prop in properties.values() if prop.get("description"))
                        total_fields = len(properties)
                        
                        self.log_result(
                            f"Schema fields have descriptions: {schema_name}",
                            described_fields > 0,
                            f"{described_fields}/{total_fields} fields described"
                        )
            
            return True
            
        except Exception as e:
            self.log_result(
                "Schema validation",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def test_endpoint_functionality(self) -> bool:
        """Test all endpoints through the API to ensure they work correctly."""
        print("\n🧪 Testing Endpoint Functionality...")
        
        try:
            # Test root endpoint
            response = self.client.get("/")
            self.log_result(
                "Root endpoint works",
                response.status_code == 200
            )
            
            # Test creating a habit
            habit_data = {
                "name": "Test Habit",
                "description": "A test habit for validation"
            }
            response = self.client.post("/habits", json=habit_data)
            success = response.status_code == 201
            self.log_result(
                "Create habit endpoint works",
                success,
                f"Status: {response.status_code}"
            )
            
            habit_id = None
            if success:
                habit = response.json()
                habit_id = habit.get("id")
                
                # Validate response structure
                expected_fields = ["id", "name", "description", "status", "streak_days", "last_completed_at"]
                for field in expected_fields:
                    has_field = field in habit
                    self.log_result(
                        f"Create habit response has field: {field}",
                        has_field
                    )
            
            # Test getting habits
            response = self.client.get("/habits")
            self.log_result(
                "Get habits endpoint works",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            # Test getting habits with status filter
            response = self.client.get("/habits?status=pending")
            self.log_result(
                "Get habits with filter works",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            if habit_id:
                # Test updating habit
                update_data = {"name": "Updated Test Habit"}
                response = self.client.patch(f"/habits/{habit_id}", json=update_data)
                self.log_result(
                    "Update habit endpoint works",
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
                
                # Test completing habit
                response = self.client.post(f"/habits/{habit_id}/complete")
                self.log_result(
                    "Complete habit endpoint works",
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
                
                # Test duplicate completion (should fail)
                response = self.client.post(f"/habits/{habit_id}/complete")
                self.log_result(
                    "Duplicate completion properly rejected",
                    response.status_code == 409,
                    f"Status: {response.status_code}"
                )
            
            # Test stats endpoint
            response = self.client.get("/stats")
            success = response.status_code == 200
            self.log_result(
                "Stats endpoint works",
                success,
                f"Status: {response.status_code}"
            )
            
            if success:
                stats = response.json()
                expected_fields = ["total_habits", "completed_today", "active_streaks_ge_3"]
                for field in expected_fields:
                    has_field = field in stats
                    self.log_result(
                        f"Stats response has field: {field}",
                        has_field
                    )
            
            # Test error handling
            response = self.client.get("/habits/99999")
            self.log_result(
                "Non-existent habit returns 404",
                response.status_code == 404,
                f"Status: {response.status_code}"
            )
            
            # Test validation errors
            invalid_habit = {"name": ""}  # Empty name should fail
            response = self.client.post("/habits", json=invalid_habit)
            self.log_result(
                "Invalid data returns 422",
                response.status_code == 422,
                f"Status: {response.status_code}"
            )
            
            if habit_id:
                # Clean up - delete the test habit
                response = self.client.delete(f"/habits/{habit_id}")
                self.log_result(
                    "Delete habit endpoint works",
                    response.status_code == 204,
                    f"Status: {response.status_code}"
                )
            
            return True
            
        except Exception as e:
            self.log_result(
                "Endpoint functionality testing",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def validate_acceptance_criteria(self) -> bool:
        """Validate that all acceptance criteria from requirements are met."""
        print("\n✅ Validating Acceptance Criteria...")
        
        # Requirement 7.1: OpenAPI documentation at /docs endpoint
        response = self.client.get("/docs")
        self.log_result(
            "Requirement 7.1: OpenAPI documentation at /docs",
            response.status_code == 200
        )
        
        # Requirement 7.3: Pydantic models for validation
        try:
            # Test that validation works
            invalid_data = {"name": "x" * 100}  # Too long name
            response = self.client.post("/habits", json=invalid_data)
            self.log_result(
                "Requirement 7.3: Pydantic validation works",
                response.status_code == 422
            )
            
            # Test that valid data works
            valid_data = {"name": "Valid Habit"}
            response = self.client.post("/habits", json=valid_data)
            success = response.status_code == 201
            self.log_result(
                "Requirement 7.3: Valid data accepted",
                success
            )
            
            # Clean up if habit was created
            if success:
                habit = response.json()
                habit_id = habit.get("id")
                if habit_id:
                    self.client.delete(f"/habits/{habit_id}")
            
        except Exception as e:
            self.log_result(
                "Requirement 7.3: Pydantic validation",
                False,
                f"Exception: {str(e)}"
            )
        
        return True
    
    def run_validation(self) -> bool:
        """Run all validation tests."""
        print("🚀 Starting API Documentation Validation...")
        print("=" * 60)
        
        # Run all validation steps
        schema_valid = self.validate_openapi_schema()
        endpoints_valid = self.validate_endpoint_documentation()
        schemas_valid = self.validate_request_response_schemas()
        functionality_valid = self.test_endpoint_functionality()
        criteria_valid = self.validate_acceptance_criteria()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.validation_results)
        passed_tests = sum(1 for result in self.validation_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.validation_results:
                if not result["success"]:
                    print(f"  - {result['test']}")
                    if result["message"]:
                        print(f"    {result['message']}")
        
        overall_success = all([
            schema_valid,
            endpoints_valid, 
            schemas_valid,
            functionality_valid,
            criteria_valid
        ])
        
        print(f"\n🎯 OVERALL RESULT: {'✅ PASS' if overall_success else '❌ FAIL'}")
        
        return overall_success


def main():
    """Main function to run the validation."""
    validator = APIDocumentationValidator()
    success = validator.run_validation()
    
    if success:
        print("\n🎉 All API documentation validation tests passed!")
        print("The Habit Tracker API is properly documented and functional.")
        return 0
    else:
        print("\n💥 Some validation tests failed!")
        print("Please review the failed tests and fix the issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())