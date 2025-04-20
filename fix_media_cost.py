#!/usr/bin/env python3
"""
Fix Media Cost References in Rill Metrics YAML Files

This script is specifically designed to fix metrics YAML files that have references to 
"media_cost" column when they should be using "total_cost" instead. This issue was 
identified in the "Gate - Summit - DisplayNative - StackAdapt" model, where measures 
were referring to a nonexistent "media_cost" column.

Usage:
    python fix_media_cost.py input_yaml_file.yaml [output_yaml_file.yaml]

If no output file is specified, the input file will be modified in place.
"""
import yaml
import os
import re
from datetime import datetime

def fix_yaml_file(input_file, output_file=None):
    """Fix media_cost references in a metrics YAML file"""
    if not output_file:
        output_file = input_file
        
    # Load the YAML file
    with open(input_file, 'r') as f:
        yaml_data = yaml.safe_load(f)
    
    # Get measures
    measures = yaml_data.get("measures", [])
    measures_updated = 0
    
    # Fix each measure
    for measure in measures:
        if "expression" in measure:
            expression = measure["expression"]
            original_expression = expression
            
            # Replace "media_cost" with "total_cost"
            expression = expression.replace('"media_cost"', '"total_cost"')
            
            if expression != original_expression:
                measure["expression"] = expression
                if "description" in measure:
                    measure["description"] = measure["description"] + " (fixed media_cost reference)"
                else:
                    measure["description"] = "Fixed media_cost reference"
                measures_updated += 1
    
    # Generate header for the output file
    header = "# Metrics view YAML - FIXED COLUMN REFERENCES\n"
    header += "# Reference documentation: https://docs.rilldata.com/reference/project-files/dashboards\n"
    header += f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += f"# Based on file: {os.path.basename(input_file)}\n"
    
    if measures_updated > 0:
        header += f"# Updated {measures_updated} measure(s) with fixed column references\n"
    
    header += "\n"
    
    # Write the output file
    with open(output_file, 'w') as f:
        f.write(header)
        yaml.dump(yaml_data, f, sort_keys=False, default_flow_style=False)
    
    return output_file, measures_updated

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python fix_media_cost.py <input_yaml> [output_yaml]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    result_file, count = fix_yaml_file(input_file, output_file)
    
    print(f"Updated {count} measure(s) in {result_file}") 