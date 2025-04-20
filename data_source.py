#!/usr/bin/env python3
import os
import re
import json
import pyarrow.parquet as pq

class SchemaExtractor:
    """Extract schema information from data sources"""
    
    @staticmethod
    def extract_from_parquet(file_path):
        """Extract schema information from a Parquet file"""
        try:
            parquet_file = pq.ParquetFile(file_path)
            schema = parquet_file.schema
            
            # Extract fields
            fields = []
            for field in schema:
                fields.append({
                    "name": field.name,
                    "type": str(field.type),
                    "nullable": field.nullable
                })
            
            return {
                "fields": fields,
                "num_rows": parquet_file.metadata.num_rows,
                "num_row_groups": parquet_file.metadata.num_row_groups
            }
        except Exception as e:
            print(f"Error extracting schema from Parquet file: {e}")
            return None
    
    @staticmethod
    def guess_timeseries_column(fields):
        """Guess which column is the timeseries column"""
        # Look for common date/time column names
        date_pattern = re.compile(r"date|time|day|month|year", re.IGNORECASE)
        date_fields = []
        
        for field in fields:
            field_name = field.get("name", "").lower()
            field_type = field.get("type", "").lower()
            
            # Check if field name contains date-related terms
            if date_pattern.search(field_name):
                date_fields.append(field)
            
            # Check if field type is date/timestamp related
            if "date" in field_type or "time" in field_type:
                date_fields.append(field)
        
        # Prioritize exact matches
        for field in date_fields:
            if field.get("name", "").lower() == "date":
                return field.get("name")
        
        # Return the first date field found, if any
        if date_fields:
            return date_fields[0].get("name")
        
        return None
    
    @staticmethod
    def guess_measure_columns(fields):
        """Guess which columns are likely to be measures"""
        # Look for numeric fields
        numeric_pattern = re.compile(r"int|float|double|decimal", re.IGNORECASE)
        measure_fields = []
        
        for field in fields:
            field_type = field.get("type", "").lower()
            
            # Check if field type is numeric
            if numeric_pattern.search(field_type):
                measure_fields.append(field)
        
        return measure_fields
    
    @staticmethod
    def guess_dimension_columns(fields, measure_fields, timeseries_column):
        """Guess which columns are likely to be dimensions"""
        dimension_fields = []
        
        # Measure field names
        measure_names = [field.get("name") for field in measure_fields]
        
        for field in fields:
            field_name = field.get("name")
            
            # Skip measure fields and timeseries column
            if field_name in measure_names or field_name == timeseries_column:
                continue
            
            dimension_fields.append(field)
        
        return dimension_fields
    
    @staticmethod
    def generate_metrics_yaml_from_schema(schema_info, output_file=None):
        """Generate a metrics YAML file from schema information"""
        if not schema_info or "fields" not in schema_info:
            return None
        
        fields = schema_info.get("fields", [])
        
        # Guess timeseries column
        timeseries_column = SchemaExtractor.guess_timeseries_column(fields)
        
        # Guess measure columns
        measure_fields = SchemaExtractor.guess_measure_columns(fields)
        
        # Guess dimension columns
        dimension_fields = SchemaExtractor.guess_dimension_columns(
            fields, measure_fields, timeseries_column
        )
        
        # Create metrics YAML structure
        metrics_yaml = {
            "version": 1,
            "type": "metrics_view",
            "display_name": "Auto-Generated Metrics View",
            "model": "MODEL_NAME_PLACEHOLDER",
            "timeseries": timeseries_column or "date",
            "dimensions": [],
            "measures": []
        }
        
        # Add dimensions
        for field in dimension_fields:
            field_name = field.get("name")
            metrics_yaml["dimensions"].append({
                "name": field_name.lower(),
                "display_name": field_name.replace("_", " ").title(),
                "column": field_name
            })
        
        # Add measures
        for field in measure_fields:
            field_name = field.get("name")
            metrics_yaml["measures"].append({
                "name": field_name.lower(),
                "label": field_name.replace("_", " ").title(),
                "expression": f"SUM({field_name})",
                "description": f"Sum of {field_name.replace('_', ' ')}",
                "format_preset": "humanize",
                "valid_percent_of_total": True
            })
        
        # Output to file if specified
        if output_file:
            try:
                with open(output_file, 'w') as file:
                    # Generate header
                    header = "# Metrics view YAML - Auto-generated from data source\n"
                    header += "# Reference documentation: https://docs.rilldata.com/reference/project-files/dashboards\n\n"
                    
                    file.write(header)
                    json.dump(metrics_yaml, file, indent=2)
                print(f"Metrics YAML file generated: {output_file}")
            except Exception as e:
                print(f"Error writing metrics YAML file: {e}")
                return metrics_yaml
        
        return metrics_yaml
    
    @staticmethod
    def generate_metrics_yaml_from_parquet(parquet_file, output_file=None):
        """Generate a metrics YAML file from a Parquet file"""
        schema_info = SchemaExtractor.extract_from_parquet(parquet_file)
        if schema_info:
            return SchemaExtractor.generate_metrics_yaml_from_schema(schema_info, output_file)
        return None
    
    @staticmethod
    def update_existing_yaml(existing_file, schema_info, output_file=None):
        """Update an existing YAML file with schema information"""
        try:
            # Load existing YAML
            with open(existing_file, 'r') as file:
                # Skip comments
                yaml_content = ""
                for line in file:
                    if not line.strip().startswith('#'):
                        yaml_content += line
                
                # Parse YAML content
                existing_yaml = json.loads(yaml_content)
            
            # Generate new YAML from schema
            new_yaml = SchemaExtractor.generate_metrics_yaml_from_schema(schema_info)
            
            # Compare and update
            updated_yaml = existing_yaml.copy()
            
            # Update dimensions
            existing_dimensions = {dim.get("name"): dim for dim in existing_yaml.get("dimensions", [])}
            for dim in new_yaml.get("dimensions", []):
                dim_name = dim.get("name")
                if dim_name not in existing_dimensions:
                    updated_yaml["dimensions"].append(dim)
            
            # Update measures
            existing_measures = {measure.get("name"): measure for measure in existing_yaml.get("measures", [])}
            for measure in new_yaml.get("measures", []):
                measure_name = measure.get("name")
                if measure_name not in existing_measures:
                    updated_yaml["measures"].append(measure)
            
            # Output to file if specified
            if output_file:
                try:
                    with open(output_file, 'w') as file:
                        # Generate header
                        header = "# Metrics view YAML - Updated with schema information\n"
                        header += "# Reference documentation: https://docs.rilldata.com/reference/project-files/dashboards\n\n"
                        
                        file.write(header)
                        json.dump(updated_yaml, file, indent=2)
                    print(f"Updated metrics YAML file: {output_file}")
                except Exception as e:
                    print(f"Error writing updated metrics YAML file: {e}")
                    return updated_yaml
            
            return updated_yaml
            
        except Exception as e:
            print(f"Error updating existing YAML file: {e}")
            return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        
        if file_path.endswith(".parquet"):
            SchemaExtractor.generate_metrics_yaml_from_parquet(file_path, output_path)
        else:
            print(f"Unsupported file type: {file_path}")
    else:
        print("Usage: python data_source.py <data_file> [output_file]") 