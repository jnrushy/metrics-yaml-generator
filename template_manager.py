#!/usr/bin/env python3
import os
import yaml
import shutil
import re
from datetime import datetime

# Template directory path
TEMPLATE_DIR = os.path.expanduser("~/yaml-generator/templates")
PRESET_DIR = os.path.expanduser("~/yaml-generator/presets")

class TemplateManager:
    """Manage templates for metrics YAML generation"""
    
    def __init__(self, template_dir=None, preset_dir=None):
        """Initialize the template manager"""
        self.template_dir = template_dir or TEMPLATE_DIR
        self.preset_dir = preset_dir or PRESET_DIR
        
        # Ensure directories exist
        os.makedirs(self.template_dir, exist_ok=True)
        os.makedirs(self.preset_dir, exist_ok=True)
    
    def list_templates(self):
        """List all available templates"""
        templates = []
        
        # List templates from the template directory
        for root, dirs, files in os.walk(self.template_dir):
            for file in files:
                if file.endswith("_template.yaml"):
                    rel_path = os.path.relpath(os.path.join(root, file), self.template_dir)
                    templates.append(rel_path)
        
        return templates
    
    def list_presets(self):
        """List all available preset templates"""
        presets = []
        
        # List templates from the preset directory
        for file in os.listdir(self.preset_dir):
            if file.endswith(".yaml"):
                presets.append(file)
        
        return presets
    
    def load_template(self, template_path):
        """Load a template file"""
        # Check if it's a preset
        if not os.path.sep in template_path and template_path.endswith(".yaml"):
            preset_path = os.path.join(self.preset_dir, template_path)
            if os.path.exists(preset_path):
                template_path = preset_path
        
        # Check if it's a relative path from the template directory
        elif not os.path.isabs(template_path):
            rel_path = os.path.join(self.template_dir, template_path)
            if os.path.exists(rel_path):
                template_path = rel_path
        
        # Load the template file
        try:
            with open(template_path, 'r') as file:
                # Skip comments
                yaml_content = ""
                for line in file:
                    if not line.strip().startswith('#'):
                        yaml_content += line
                
                # Parse YAML content
                data = yaml.safe_load(yaml_content)
                return data
        except Exception as e:
            print(f"Error loading template {template_path}: {e}")
            return None
    
    def extract_column_references(self, expression):
        """Extract column references from a SQL expression
        
        Args:
            expression: SQL expression string
            
        Returns:
            Set of column names referenced in the expression
        """
        # Find all column references in the expression - look for:
        # 1. Column names in double quotes: "column_name"
        # 2. Simple column names without quotes: column_name
        # This is a simplified approach and might not catch all cases
        quoted_columns = re.findall(r'"([^"]+)"', expression)
        
        # For unquoted columns, we need a more careful approach to avoid catching function names
        # This regex looks for identifiers that aren't preceded by a dot (to avoid table.column) 
        # and aren't followed by an opening parenthesis (to avoid functions)
        simple_columns = []
        for match in re.finditer(r'(?<!\.)(?<!\w)([a-zA-Z_][a-zA-Z0-9_]*)(?!\s*\()', expression):
            # Skip SQL keywords and function names
            if match.group(1).lower() not in ['select', 'from', 'where', 'group', 'order', 'by', 
                                             'having', 'if', 'case', 'when', 'then', 'else', 
                                             'end', 'and', 'or', 'not', 'null', 'true', 'false',
                                             'sum', 'count', 'avg', 'min', 'max', 'stddev', 
                                             'distinct', 'as', 'in', 'between', 'is', 'like']:
                simple_columns.append(match.group(1))
        
        return set(quoted_columns + simple_columns)
    
    def get_available_columns(self, dimensions):
        """Extract available columns from dimensions list
        
        Args:
            dimensions: List of dimension objects
            
        Returns:
            Set of column names available
        """
        columns = set()
        
        for dimension in dimensions:
            if "column" in dimension:
                columns.add(dimension.get("column"))
        
        return columns
    
    def merge_measures(self, base_file, source_file, output_file=None, validate_columns=True):
        """Merge measures from source_file into base_file
        
        Args:
            base_file: Path to the base YAML file that will receive new measures
            source_file: Path to the source YAML file containing measures to be added
            output_file: Optional path for the output file. If not provided, base_file will be overwritten
            validate_columns: Whether to check if columns exist in base dataset
            
        Returns:
            Tuple of (path_to_output_file, number_of_measures_added, number_of_measures_skipped)
        """
        # Default output to base file if not specified
        if not output_file:
            output_file = base_file
            
        # Load both YAML files
        with open(base_file, 'r') as f:
            base_yaml = yaml.safe_load(f)
            
        with open(source_file, 'r') as f:
            source_yaml = yaml.safe_load(f)
            
        # Get existing measure names to avoid duplicates
        base_measures = base_yaml.get("measures", [])
        source_measures = source_yaml.get("measures", [])
        
        existing_measure_names = {measure.get("name") for measure in base_measures}
        
        # Get available columns from base dimensions
        available_columns = self.get_available_columns(base_yaml.get("dimensions", []))
        
        # Also add any columns already referenced in existing measures
        for measure in base_measures:
            if "expression" in measure:
                refs = self.extract_column_references(measure.get("expression"))
                available_columns.update(refs)
        
        # Add measures from source that don't exist in base
        measures_added = 0
        measures_skipped = 0
        
        # Track incompatible measures with reasons for reporting
        incompatible_measures = []
        
        for measure in source_measures:
            # Skip if measure already exists
            if measure.get("name") in existing_measure_names:
                continue
                
            # Check if all column references exist in base dataset
            if validate_columns and "expression" in measure:
                column_refs = self.extract_column_references(measure.get("expression"))
                missing_columns = [col for col in column_refs if col not in available_columns]
                
                if missing_columns:
                    measures_skipped += 1
                    incompatible_measures.append({
                        "name": measure.get("name"),
                        "missing_columns": missing_columns,
                        "expression": measure.get("expression")
                    })
                    continue
            
            # Add measure if it passed validation
            base_measures.append(measure)
            measures_added += 1
                
        # Update the measures in the base YAML
        base_yaml["measures"] = base_measures
        
        # Generate header for the output file
        header = "# Metrics view YAML\n"
        header += "# Reference documentation: https://docs.rilldata.com/reference/project-files/dashboards\n"
        header += f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"# Base file: {os.path.basename(base_file)}\n"
        header += f"# Added measures from: {os.path.basename(source_file)}\n"
        
        if measures_skipped > 0:
            header += f"# WARNING: {measures_skipped} measures were skipped due to missing column references\n"
            
            # Add details about skipped measures
            for i, measure in enumerate(incompatible_measures):
                header += f"# Skipped measure #{i+1}: {measure['name']} - Missing columns: {', '.join(measure['missing_columns'])}\n"
        
        header += "\n"
        
        # Write the output file
        with open(output_file, 'w') as f:
            f.write(header)
            yaml.dump(base_yaml, f, sort_keys=False, default_flow_style=False)
            
        return output_file, measures_added, measures_skipped
    
    def save_preset(self, name, data, description=None):
        """Save a template as a preset"""
        if not name.endswith(".yaml"):
            name = f"{name}.yaml"
        
        preset_path = os.path.join(self.preset_dir, name)
        
        # Generate header with metadata
        header = "# Metrics view YAML - PRESET\n"
        if description:
            header += f"# Description: {description}\n"
        header += f"# Created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += "# Reference documentation: https://docs.rilldata.com/reference/project-files/dashboards\n\n"
        
        # Write the preset file
        try:
            with open(preset_path, 'w') as file:
                file.write(header)
                yaml.dump(data, file, sort_keys=False, default_flow_style=False)
            return preset_path
        except Exception as e:
            print(f"Error saving preset {name}: {e}")
            return None
    
    def customize_template(self, template_data, overrides=None):
        """Customize a template with overrides"""
        if not overrides:
            return template_data
        
        # Apply overrides to the template
        for key, value in overrides.items():
            if key in template_data:
                if isinstance(value, dict) and isinstance(template_data[key], dict):
                    # Merge dictionaries
                    template_data[key].update(value)
                elif isinstance(value, list) and isinstance(template_data[key], list):
                    # For lists, we have special handling based on key
                    if key == "dimensions" or key == "measures":
                        # For dimensions and measures, merge by name
                        existing_items = {item.get("name", ""): item for item in template_data[key]}
                        for item in value:
                            if "name" in item and item["name"] in existing_items:
                                # Update existing item
                                existing_items[item["name"]].update(item)
                            else:
                                # Add new item
                                template_data[key].append(item)
                    else:
                        # For other lists, append new items
                        template_data[key].extend(value)
                else:
                    # Replace value
                    template_data[key] = value
        
        return template_data
    
    def create_custom_preset(self, base_template, name, overrides, description=None):
        """Create a new preset based on a template with overrides"""
        # Load the base template
        template_data = self.load_template(base_template)
        if not template_data:
            return None
        
        # Apply overrides
        custom_data = self.customize_template(template_data, overrides)
        
        # Save as a preset
        return self.save_preset(name, custom_data, description)

# Preset templates for common use cases
PRESET_TEMPLATES = {
    "basic_display": {
        "description": "Basic template for display campaigns",
        "overrides": {
            "display_name": "Basic Display Campaign",
            "timeseries": "date"
        }
    },
    "video_analytics": {
        "description": "Template for video analytics with completion metrics",
        "base_template": "ttd/video_template.yaml",
        "overrides": {
            "display_name": "Video Analytics Dashboard",
            "measures": [
                {
                    "name": "video_completion_rate",
                    "label": "Video Completion Rate (%)",
                    "expression": "SUM(completed_videos) / SUM(videos_started) * 100",
                    "description": "Percentage of videos that were fully completed",
                    "format_d3": ".2f"
                }
            ]
        }
    },
    "performance_analytics": {
        "description": "Template for campaign performance analysis",
        "overrides": {
            "display_name": "Campaign Performance Analytics",
            "measures": [
                {
                    "name": "roas",
                    "label": "ROAS",
                    "expression": "SUM(revenue) / SUM(total_cost)",
                    "description": "Return on Ad Spend",
                    "format_d3": ".2f"
                }
            ]
        }
    }
}

def initialize_presets():
    """Initialize the preset templates"""
    manager = TemplateManager()
    
    # Create preset templates
    for name, config in PRESET_TEMPLATES.items():
        base_template = config.get("base_template", "ttd/display_template.yaml")
        overrides = config.get("overrides", {})
        description = config.get("description", "")
        
        # Check if preset exists
        preset_path = os.path.join(manager.preset_dir, f"{name}.yaml")
        if not os.path.exists(preset_path):
            manager.create_custom_preset(base_template, name, overrides, description)
            print(f"Created preset: {name}")

# Helper function for external usage
def merge_metrics_files(base_file, source_file, output_file=None, validate_columns=True):
    """Merge measures from source_file into base_file.
    A convenience function that uses TemplateManager internally."""
    manager = TemplateManager()
    return manager.merge_measures(base_file, source_file, output_file, validate_columns)

if __name__ == "__main__":
    # Initialize preset templates
    initialize_presets()
    
    # List templates and presets
    manager = TemplateManager()
    
    print("Available Templates:")
    for template in manager.list_templates():
        print(f"  - {template}")
    
    print("\nAvailable Presets:")
    for preset in manager.list_presets():
        print(f"  - {preset}") 