#!/usr/bin/env python3
import yaml
import sys

def print_dataset_info(file_path):
    print(f"Analyzing file: {file_path}")
    
    with open(file_path, 'r') as f:
        yaml_data = yaml.safe_load(f)
    
    print('\nAvailable dimensions/columns:')
    for dim in yaml_data.get('dimensions', []):
        print(f"- {dim.get('column')} (name: {dim.get('name')})")
    
    print('\nExisting measures:')
    for measure in yaml_data.get('measures', []):
        print(f"- {measure.get('name')}: {measure.get('expression')}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print_dataset_info(sys.argv[1])
    else:
        print("Usage: python check_columns.py <yaml_file>") 