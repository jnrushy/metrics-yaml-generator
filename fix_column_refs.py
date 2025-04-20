#!/usr/bin/env python3
import yaml
import os
import re
from datetime import datetime

def extract_column_mappings(yaml_data):
    """Extract a mapping of column names from dimensions"""
    column_map = {}
    
    # Map from various common column names to what's actually available
    for dim in yaml_data.get("dimensions", []):
        name = dim.get("name", "")
        column = dim.get("column", "")
        
        # Create mappings for similar columns
        if column == "ssp_name":
            column_map["ssp"] = "ssp_name"
        elif column == "advertiser_name":
            column_map["advertiser"] = "advertiser_name"
        # Add more mappings as needed
    
    return column_map

def fix_column_references(yaml_data, column_map):
    """Fix column references in measure expressions"""
    measures = yaml_data.get("measures", [])
    fixed_measures = []
    measures_updated = 0
    
    # Column replacements in quoted references
    for measure in measures:
        if "expression" in measure:
            expression = measure["expression"]
            original_expression = expression
            
            # Replace column references
            for old_col, new_col in column_map.items():
                # Replace quoted column names
                expression = re.sub(f'"{old_col}"', f'"{new_col}"', expression)
                # Replace unquoted column names (with word boundaries)
                expression = re.sub(r'\b' + old_col + r'\b', new_col, expression)
            
            if expression != original_expression:
                measure["expression"] = expression
                measure["description"] = measure.get("description", "") + " (column refs fixed)"
                measures_updated += 1
        
        fixed_measures.append(measure)
    
    yaml_data["measures"] = fixed_measures
    return yaml_data, measures_updated

def check_remaining_issues(yaml_data, available_columns):
    """Check for remaining column reference issues in measures"""
    measures = yaml_data.get("measures", [])
    problematic_measures = []
    
    # Collect all column names from dimensions
    available_cols = set()
    for dim in yaml_data.get("dimensions", []):
        if "column" in dim:
            available_cols.add(dim.get("column"))
            
    # Add any explicitly provided columns
    if available_columns:
        available_cols.update(available_columns)
    
    # Check measures for references to missing columns
    for measure in measures:
        if "expression" in measure and "name" in measure:
            expression = measure["expression"]
            name = measure["name"]
            
            # Look for column references
            quoted_cols = re.findall(r'"([^"]+)"', expression)
            unquoted_cols = []
            for match in re.finditer(r'(?<!\.)(?<!\w)([a-zA-Z_][a-zA-Z0-9_]*)(?!\s*\()', expression):
                # Skip SQL keywords and function names
                if match.group(1).lower() not in ['select', 'from', 'where', 'group', 'order', 'by', 
                                               'having', 'if', 'case', 'when', 'then', 'else', 
                                               'end', 'and', 'or', 'not', 'null', 'true', 'false',
                                               'sum', 'count', 'avg', 'min', 'max', 'stddev', 
                                               'distinct', 'as', 'in', 'between', 'is', 'like']:
                    unquoted_cols.append(match.group(1))
            
            # Check if all columns exist
            all_cols = set(quoted_cols + unquoted_cols)
            missing_cols = [col for col in all_cols if col not in available_cols]
            
            if missing_cols:
                problematic_measures.append({
                    "name": name,
                    "missing_columns": missing_cols,
                    "expression": expression
                })
    
    return problematic_measures

def fix_yaml_file(input_file, output_file=None, additional_columns=None):
    """Fix column references in a metrics YAML file"""
    if not output_file:
        output_file = input_file
        
    # Load the YAML file
    with open(input_file, 'r') as f:
        yaml_data = yaml.safe_load(f)
    
    # Extract column mappings
    column_map = extract_column_mappings(yaml_data)
    
    # Fix column references
    fixed_yaml, measures_updated = fix_column_references(yaml_data, column_map)
    
    # Check for remaining issues
    issues = check_remaining_issues(fixed_yaml, additional_columns)
    
    # Generate header for the output file
    header = "# Metrics view YAML - FIXED COLUMN REFERENCES\n"
    header += "# Reference documentation: https://docs.rilldata.com/reference/project-files/dashboards\n"
    header += f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += f"# Based on file: {os.path.basename(input_file)}\n"
    
    if measures_updated > 0:
        header += f"# Updated {measures_updated} measure(s) with fixed column references\n"
    
    if issues:
        header += f"# WARNING: {len(issues)} measure(s) still have issues with column references\n"
        
        # Add details about problematic measures
        for i, measure in enumerate(issues):
            header += f"# Issue #{i+1}: {measure['name']} - Missing columns: {', '.join(measure['missing_columns'])}\n"
    
    header += "\n"
    
    # Write the output file
    with open(output_file, 'w') as f:
        f.write(header)
        yaml.dump(fixed_yaml, f, sort_keys=False, default_flow_style=False)
    
    return output_file, measures_updated, issues

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python fix_column_refs.py <input_yaml> [output_yaml]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Optional additional columns to consider as available
    additional_columns = ["media_cost", "conversions"]
    
    result_file, count, issues = fix_yaml_file(input_file, output_file, additional_columns)
    
    print(f"Updated {count} measure(s) in {result_file}")
    if issues:
        print(f"WARNING: {len(issues)} measure(s) still have issues")
        for issue in issues:
            print(f"- {issue['name']}: Missing columns: {', '.join(issue['missing_columns'])}") 