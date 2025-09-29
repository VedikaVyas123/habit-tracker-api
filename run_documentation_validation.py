#!/usr/bin/env python3
"""
Run Documentation Validation

This script imports and runs the documentation validation directly.
"""

# Import the validation functions
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

try:
    from final_documentation_test import main as run_final_test
    
    print("🚀 Running Final Documentation Validation...")
    print("=" * 80)
    
    success = run_final_test()
    
    if success:
        print("\n✨ VALIDATION COMPLETE - ALL TESTS PASSED!")
    else:
        print("\n💥 VALIDATION INCOMPLETE - SOME TESTS FAILED!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Falling back to manual validation...")
    
    # Manual validation as fallback
    from fastapi.testclient import TestClient
    from main import app
    
    client = TestClient(app)
    
    print("\n🔍 Manual Documentation Validation")
    print("=" * 50)
    
    # Test 1: OpenAPI docs endpoint
    response = client.get("/docs")
    docs_ok = response.status_code == 200
    print(f"✅ /docs endpoint: {'PASS' if docs_ok else 'FAIL'}")
    
    # Test 2: OpenAPI JSON schema
    response = client.get("/openapi.json")
    schema_ok = response.status_code == 200
    print(f"✅ OpenAPI schema: {'PASS' if schema_ok else 'FAIL'}")
    
    if schema_ok:
        schema = response.json()
        has_info = "info" in schema
        has_paths = "paths" in schema
        has_components = "components" in schema
        print(f"✅ Schema structure: {'PASS' if all([has_info, has_paths, has_components]) else 'FAIL'}")
        
        # Check API info
        info = schema.get("info", {})
        title_ok = info.get("title") == "Habit Tracker API"
        desc_ok = bool(info.get("description"))
        version_ok = info.get("version") == "1.0.0"
        print(f"✅ API metadata: {'PASS' if all([title_ok, desc_ok, version_ok]) else 'FAIL'}")
        
        # Check endpoints
        paths = schema.get("paths", {})
        expected_paths = ["/", "/habits", "/habits/{habit_id}", "/habits/{habit_id}/complete", "/stats"]
        paths_ok = all(path in paths for path in expected_paths)
        print(f"✅ All endpoints documented: {'PASS' if paths_ok else 'FAIL'}")
        
        # Check schemas
        components = schema.get("components", {})
        schemas = components.get("schemas", {})
        expected_schemas = ["Habit", "CreateHabitRequest", "UpdateHabitRequest", "StatsResponse", "ErrorResponse"]
        schemas_ok = all(schema_name in schemas for schema_name in expected_schemas)
        print(f"✅ All schemas documented: {'PASS' if schemas_ok else 'FAIL'}")
    
    # Test 3: API functionality
    response = client.get("/")
    api_ok = response.status_code == 200
    print(f"✅ API functionality: {'PASS' if api_ok else 'FAIL'}")
    
    # Test 4: Validation
    invalid_data = {"name": ""}
    response = client.post("/habits", json=invalid_data)
    validation_ok = response.status_code == 422
    print(f"✅ Pydantic validation: {'PASS' if validation_ok else 'FAIL'}")
    
    # Summary
    all_tests = [docs_ok, schema_ok, api_ok, validation_ok]
    if schema_ok:
        all_tests.extend([has_info, has_paths, has_components, title_ok, desc_ok, version_ok, paths_ok, schemas_ok])
    
    passed = sum(all_tests)
    total = len(all_tests)
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 MANUAL VALIDATION: ✅ SUCCESS")
        success = True
    else:
        print("💥 MANUAL VALIDATION: ❌ INCOMPLETE")
        success = False

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    success = False

# Final result
if success:
    print("\n🎯 TASK 10 - FINALIZE API DOCUMENTATION AND VALIDATION: ✅ COMPLETE")
else:
    print("\n🎯 TASK 10 - FINALIZE API DOCUMENTATION AND VALIDATION: ❌ NEEDS ATTENTION")

sys.exit(0 if success else 1)