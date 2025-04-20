#!/usr/bin/env python3
import yaml
import sys

def print_dataset_info(file_path):
    print(f"Analyzing file: {file_path}")
    
    with open(file_path, 'r') as f:
        yaml_data = yaml.safe_load(f)
    
    print('\nAvailable dimensions/columns:')
    for dim in yaml_data.get('dimensions', []):
        if isinstance(dim, dict):
            # Handle case where dimension is a dictionary with name/column attributes
            print(f"- {dim.get('column')} (name: {dim.get('name')})")
        elif isinstance(dim, str):
            # Handle case where dimension is just a string
            print(f"- {dim} (simple dimension)")
        else:
            # Handle any other case
            print(f"- {dim} (unknown type: {type(dim)})")
    
    print('\nExisting measures:')
    for measure in yaml_data.get('measures', []):
        if isinstance(measure, dict):
            # Handle case where measure is a dictionary
            print(f"- {measure.get('name')}: {measure.get('expression')}")
        elif isinstance(measure, str):
            # Handle case where measure is just a string
            print(f"- {measure} (simple measure)")
        else:
            # Handle any other case
            print(f"- {measure} (unknown type: {type(measure)})")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print_dataset_info(sys.argv[1])
    else:
        print("Usage: python check_columns.py <yaml_file>") 