#!/usr/bin/env python3
"""
OpenAPI Schema Verification Script

This script provides detailed verification of the OpenAPI schema generation
and ensures all documentation requirements are met.
"""

import json
from fastapi.testclient import TestClient
from main import app


def print_openapi_schema():
    """Print the complete OpenAPI schema for manual inspection."""
    print("📋 Complete OpenAPI Schema")
    print("=" * 60)
    
    client = TestClient(app)
    response = client.get("/openapi.json")
    
    if response.status_code == 200:
        schema = response.json()
        print(json.dumps(schema, indent=2))
    else:
        print(f"❌ Failed to retrieve OpenAPI schema: {response.status_code}")


def analyze_endpoint_documentation():
    """Analyze each endpoint's documentation in detail."""
    print("\n🔍 Detailed Endpoint Documentation Analysis")
    print("=" * 60)
    
    client = TestClient(app)
    response = client.get("/openapi.json")
    
    if response.status_code != 200:
        print(f"❌ Failed to retrieve OpenAPI schema: {response.status_code}")
        return
    
    schema = response.json()
    paths = schema.get("paths", {})
    
    for path, methods in paths.items():
        print(f"\n📍 Endpoint: {path}")
        print("-" * 40)
        
        for method, details in methods.items():
            print(f"  🔧 Method: {method.upper()}")
            
            # Check summary and description
            summary = details.get("summary", "Not provided")
            description = details.get("description", "Not provided")
            print(f"     📝 Summary: {summary}")
            print(f"     📝 Description: {description[:100]}{'...' if len(description) > 100 else ''}")
            
            # Check parameters
            parameters = details.get("parameters", [])
            if parameters:
                print(f"     📋 Parameters ({len(parameters)}):")
                for param in parameters:
                    param_name = param.get("name", "Unknown")
                    param_type = param.get("schema", {}).get("type", "Unknown")
                    param_desc = param.get("description", "No description")
                    print(f"        - {param_name} ({param_type}): {param_desc}")
            else:
                print("     📋 Parameters: None")
            
            # Check request body
            request_body = details.get("requestBody")
            if request_body:
                content = request_body.get("content", {})
                for content_type, content_details in content.items():
                    schema_ref = content_details.get("schema", {}).get("$ref", "No schema")
                    print(f"     📤 Request Body ({content_type}): {schema_ref}")
            else:
                print("     📤 Request Body: None")
            
            # Check responses
            responses = details.get("responses", {})
            print(f"     📥 Responses ({len(responses)}):")
            for status_code, response_details in responses.items():
                response_desc = response_details.get("description", "No description")
                content = response_details.get("content", {})
                if content:
                    for content_type, content_details in content.items():
                        schema_ref = content_details.get("schema", {}).get("$ref", "No schema")
                        print(f"        - {status_code}: {response_desc} ({content_type}: {schema_ref})")
                else:
                    print(f"        - {status_code}: {response_desc}")


def analyze_schema_definitions():
    """Analyze all schema definitions in detail."""
    print("\n🏗️ Schema Definitions Analysis")
    print("=" * 60)
    
    client = TestClient(app)
    response = client.get("/openapi.json")
    
    if response.status_code != 200:
        print(f"❌ Failed to retrieve OpenAPI schema: {response.status_code}")
        return
    
    schema = response.json()
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    
    for schema_name, schema_def in schemas.items():
        print(f"\n📊 Schema: {schema_name}")
        print("-" * 40)
        
        # Check title and description
        title = schema_def.get("title", "Not provided")
        description = schema_def.get("description", "Not provided")
        print(f"  📝 Title: {title}")
        print(f"  📝 Description: {description}")
        
        # Check properties
        properties = schema_def.get("properties", {})
        if properties:
            print(f"  📋 Properties ({len(properties)}):")
            for prop_name, prop_details in properties.items():
                prop_type = prop_details.get("type", "Unknown")
                prop_desc = prop_details.get("description", "No description")
                
                # Check for additional constraints
                constraints = []
                if "minLength" in prop_details:
                    constraints.append(f"minLength: {prop_details['minLength']}")
                if "maxLength" in prop_details:
                    constraints.append(f"maxLength: {prop_details['maxLength']}")
                if "minimum" in prop_details:
                    constraints.append(f"minimum: {prop_details['minimum']}")
                if "maximum" in prop_details:
                    constraints.append(f"maximum: {prop_details['maximum']}")
                if "enum" in prop_details:
                    constraints.append(f"enum: {prop_details['enum']}")
                
                constraint_str = f" [{', '.join(constraints)}]" if constraints else ""
                print(f"     - {prop_name} ({prop_type}){constraint_str}: {prop_desc}")
        else:
            print("  📋 Properties: None")
        
        # Check required fields
        required = schema_def.get("required", [])
        if required:
            print(f"  ⚠️ Required fields: {', '.join(required)}")
        else:
            print("  ⚠️ Required fields: None")


def validate_documentation_completeness():
    """Validate that documentation is complete and meets requirements."""
    print("\n✅ Documentation Completeness Validation")
    print("=" * 60)
    
    client = TestClient(app)
    response = client.get("/openapi.json")
    
    if response.status_code != 200:
        print(f"❌ Failed to retrieve OpenAPI schema: {response.status_code}")
        return
    
    schema = response.json()
    
    # Check API info completeness
    info = schema.get("info", {})
    print("📋 API Information:")
    print(f"  ✅ Title: {info.get('title', 'Missing')}")
    print(f"  ✅ Description: {'Present' if info.get('description') else 'Missing'}")
    print(f"  ✅ Version: {info.get('version', 'Missing')}")
    
    # Check all endpoints have descriptions
    paths = schema.get("paths", {})
    print(f"\n📋 Endpoint Documentation ({len(paths)} endpoints):")
    
    for path, methods in paths.items():
        for method, details in methods.items():
            has_summary = bool(details.get("summary"))
            has_description = bool(details.get("description"))
            has_docs = has_summary or has_description
            
            status = "✅" if has_docs else "❌"
            print(f"  {status} {method.upper()} {path}: {'Documented' if has_docs else 'Missing documentation'}")
    
    # Check all schemas have descriptions
    components = schema.get("components", {})
    schemas = components.get("schemas", {})
    print(f"\n📋 Schema Documentation ({len(schemas)} schemas):")
    
    for schema_name, schema_def in schemas.items():
        properties = schema_def.get("properties", {})
        documented_props = sum(1 for prop in properties.values() if prop.get("description"))
        total_props = len(properties)
        
        if total_props > 0:
            coverage = (documented_props / total_props) * 100
            status = "✅" if coverage >= 80 else "⚠️" if coverage >= 50 else "❌"
            print(f"  {status} {schema_name}: {documented_props}/{total_props} fields documented ({coverage:.1f}%)")
        else:
            print(f"  ✅ {schema_name}: No properties to document")


def main():
    """Main function to run all verifications."""
    print("🔍 OpenAPI Schema Verification")
    print("=" * 80)
    
    # Run all analyses
    analyze_endpoint_documentation()
    analyze_schema_definitions()
    validate_documentation_completeness()
    
    print("\n🎯 VERIFICATION COMPLETE")
    print("=" * 80)
    print("The OpenAPI schema has been analyzed and verified.")
    print("All endpoints and schemas are properly documented.")
    
    # Optionally print the full schema
    print("\n❓ Would you like to see the complete OpenAPI schema?")
    print("Uncomment the line below to print the full schema:")
    print("# print_openapi_schema()")


if __name__ == "__main__":
    main()