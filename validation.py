#!/usr/bin/env python3
import os
import json
import yaml
import jsonschema
from jsonschema import validate

def load_schema(schema_path=None):
    """Load the JSON schema for validation"""
    if schema_path is None:
        schema_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "schema", 
            "metrics_schema.json"
        )
    
    try:
        with open(schema_path, 'r') as file:
            schema = json.load(file)
        return schema
    except Exception as e:
        print(f"Error loading schema: {e}")
        return None

def validate_yaml(data, schema=None):
    """Validate a YAML structure against the schema"""
    if schema is None:
        schema = load_schema()
        if schema is None:
            return False, ["Unable to load schema for validation"]
    
    try:
        validate(instance=data, schema=schema)
        return True, []
    except jsonschema.exceptions.ValidationError as e:
        return False, [f"Validation error: {e.message}"]
    except Exception as e:
        return False, [f"Unexpected error during validation: {str(e)}"]

def validate_yaml_file(file_path, schema=None):
    """Validate a YAML file against the schema"""
    try:
        with open(file_path, 'r') as file:
            # Skip comments
            yaml_content = ""
            for line in file:
                if not line.strip().startswith('#'):
                    yaml_content += line
            
            # Parse YAML content
            data = yaml.safe_load(yaml_content)
            
            # Validate against schema
            return validate_yaml(data, schema)
    except Exception as e:
        return False, [f"Error loading YAML file: {str(e)}"]

def validate_essential_fields(data):
    """Perform additional validation beyond schema checking"""
    errors = []
    
    # Check dimensions have unique names/identifiers
    dimension_names = set()
    for dimension in data.get("dimensions", []):
        name = dimension.get("name") or dimension.get("label")
        if name in dimension_names:
            errors.append(f"Duplicate dimension name: {name}")
        dimension_names.add(name)
    
    # Check measures have unique names
    measure_names = set()
    for measure in data.get("measures", []):
        name = measure.get("name")
        if name in measure_names:
            errors.append(f"Duplicate measure name: {name}")
        measure_names.add(name)
    
    # Check expressions for common issues
    for measure in data.get("measures", []):
        expr = measure.get("expression", "")
        if expr.count('(') != expr.count(')'):
            errors.append(f"Mismatched parentheses in expression for {measure.get('name')}")
    
    return len(errors) == 0, errors

def comprehensive_validation(data):
    """Perform both schema validation and additional field validation"""
    # First validate the schema
    schema_valid, schema_errors = validate_yaml(data)
    
    # If schema is valid, perform additional validations
    if schema_valid:
        fields_valid, field_errors = validate_essential_fields(data)
        return schema_valid and fields_valid, schema_errors + field_errors
    
    return schema_valid, schema_errors

def comprehensive_file_validation(file_path):
    """Perform comprehensive validation on a file"""
    try:
        with open(file_path, 'r') as file:
            # Skip comments
            yaml_content = ""
            for line in file:
                if not line.strip().startswith('#'):
                    yaml_content += line
            
            # Parse YAML content
            data = yaml.safe_load(yaml_content)
            
            # Perform comprehensive validation
            return comprehensive_validation(data)
    except Exception as e:
        return False, [f"Error loading YAML file: {str(e)}"]

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        valid, errors = comprehensive_file_validation(file_path)
        if valid:
            print(f"✅ {file_path} is valid!")
        else:
            print(f"❌ {file_path} has validation errors:")
            for error in errors:
                print(f"  - {error}")
    else:
        print("Usage: python validation.py <yaml_file>") 