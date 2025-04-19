#!/usr/bin/env python3
import os
import yaml
import argparse
import glob
from datetime import datetime
import shutil

# Base directory for the metrics repo - DO NOT modify this directory
METRICS_DIR = "/Users/jasonrush/SWYM/metrics"

# Our new templates directory outside the repo
TEMPLATE_DIR = os.path.expanduser("~/yaml-generator/templates")

# Define DSP and media type mappings
DSP_TYPES = ["TTD", "DV360", "STACKADAPT", "YAHOO"]
MEDIA_TYPES = ["DISPLAY", "VIDEO", "CTV", "NATIVE"]

def find_example_files():
    """Find example files from the metrics directory for each DSP and media type"""
    examples = {}
    
    # Find all yaml files
    yaml_files = glob.glob(f"{METRICS_DIR}/**/*metrics.yaml", recursive=True)
    
    # Categorize files by DSP and media type
    for dsp in DSP_TYPES:
        examples[dsp] = {}
        for media_type in MEDIA_TYPES:
            examples[dsp][media_type] = []
            
            # Find files matching both DSP and media type
            for yaml_file in yaml_files:
                file_content = open(yaml_file, 'r').read().upper()
                filename = os.path.basename(yaml_file).upper()
                
                if (dsp in filename or dsp in file_content) and (media_type in filename or media_type in file_content):
                    examples[dsp][media_type].append(yaml_file)
    
    return examples

def load_yaml_file(file_path):
    """Load a YAML file, handling comments"""
    if not os.path.exists(file_path):
        return None
        
    with open(file_path, 'r') as file:
        # Skip comments at the top of the file
        yaml_content = ""
        in_comment_block = False
        
        for line in file:
            if line.strip().startswith('#'):
                continue
            yaml_content += line
        
        # Load the YAML content
        try:
            return yaml.safe_load(yaml_content)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None

def extract_template_from_file(file_path, dsp, media_type):
    """Extract a template from an example file"""
    yaml_data = load_yaml_file(file_path)
    if not yaml_data:
        return None
    
    # Create a template structure
    template = {
        "version": yaml_data.get("version", 1),
        "type": yaml_data.get("type", "metrics_view"),
        "display_name": f"TEMPLATE {dsp} {media_type} Metrics",
        "model": "MODEL_NAME_PLACEHOLDER",
        "timeseries": yaml_data.get("timeseries", "date"),
        "dimensions": yaml_data.get("dimensions", []),
        "measures": yaml_data.get("measures", [])
    }
    
    return template

def create_template(dsp, media_type, examples):
    """Create a template for a specific DSP and media type"""
    # Use the best matching example file
    template_data = None
    example_file = None
    example_files = examples.get(dsp, {}).get(media_type, [])
    
    if example_files:
        # Use the first example file
        example_file = example_files[0]
        template_data = extract_template_from_file(example_file, dsp, media_type)
        print(f"Creating template for {dsp} {media_type} based on: {example_file}")
    else:
        print(f"No example files found for {dsp} {media_type}")
        # Try to use a fallback from another media type with the same DSP
        for other_media in MEDIA_TYPES:
            if other_media != media_type and examples.get(dsp, {}).get(other_media, []):
                example_file = examples[dsp][other_media][0]
                template_data = extract_template_from_file(example_file, dsp, media_type)
                print(f"Using fallback for {dsp} {media_type} based on: {example_file}")
                break
    
    if not template_data:
        print(f"Could not create template for {dsp} {media_type}")
        return None
    
    # Ensure output directory exists
    output_dir = os.path.join(TEMPLATE_DIR, dsp.lower())
    os.makedirs(output_dir, exist_ok=True)
    
    # Define output file path
    output_file = os.path.join(output_dir, f"{media_type.lower()}_template.yaml")
    
    # Generate comment header
    header = "# Metrics view YAML - TEMPLATE\n"
    header += f"# DSP: {dsp}, Media Type: {media_type}\n"
    header += "# Reference documentation: https://docs.rilldata.com/reference/project-files/dashboards\n"
    header += f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    if example_file:
        header += f"# Based on example file: {os.path.basename(example_file)}\n\n"
    else:
        header += "# No suitable example file found, using basic template\n\n"
    
    # Write the YAML file
    with open(output_file, 'w') as file:
        file.write(header)
        yaml.dump(template_data, file, sort_keys=False, default_flow_style=False)
    
    print(f"Created template: {output_file}")
    return output_file

def generate_all_templates():
    """Generate templates for all combinations of DSP and media type"""
    example_files = find_example_files()
    
    created_templates = []
    for dsp in DSP_TYPES:
        for media_type in MEDIA_TYPES:
            template_file = create_template(dsp, media_type, example_files)
            if template_file:
                created_templates.append(template_file)
    
    return created_templates

def create_metrics_yaml(
    client_name, 
    brand_name, 
    media_type, 
    platform, 
    output_path=None
):
    """Create a new metrics YAML file based on templates"""
    # Normalize inputs
    platform_upper = platform.upper()
    media_type_upper = media_type.upper()
    
    # Map to known DSP names
    if platform_upper in ["TTD", "THE TRADE DESK"]:
        dsp_key = "TTD"
    elif platform_upper in ["DV360", "DISPLAY & VIDEO 360"]:
        dsp_key = "DV360"
    elif platform_upper in ["STACKADAPT", "STACK ADAPT"]:
        dsp_key = "STACKADAPT"
    elif platform_upper == "YAHOO":
        dsp_key = "YAHOO"
    else:
        dsp_key = "TTD"  # Default to TTD
    
    # Map to known media types
    if media_type_upper in ["DISPLAY"]:
        media_type_key = "DISPLAY"
    elif media_type_upper in ["VIDEO", "OLV"]:
        media_type_key = "VIDEO"
    elif media_type_upper in ["CTV", "CONNECTED TV"]:
        media_type_key = "CTV"
    elif media_type_upper in ["NATIVE"]:
        media_type_key = "NATIVE"
    else:
        media_type_key = "DISPLAY"  # Default
    
    # Find the appropriate template
    template_path = os.path.join(TEMPLATE_DIR, dsp_key.lower(), f"{media_type_key.lower()}_template.yaml")
    
    # If template doesn't exist, try to generate it
    if not os.path.exists(template_path):
        print(f"Template not found at {template_path}. Generating templates...")
        generate_all_templates()
    
    # Check if template exists now
    if not os.path.exists(template_path):
        print(f"Could not find or generate template for {dsp_key} {media_type_key}")
        return None
    
    # Load the template
    template_data = load_yaml_file(template_path)
    if not template_data:
        print(f"Error loading template: {template_path}")
        return None
    
    # Update with client-specific info
    model_name = f"{client_name} - {brand_name} - {media_type} - {platform}"
    template_data["display_name"] = f"{model_name} Metrics"
    template_data["model"] = model_name
    
    # Generate output filename
    file_name = f"{model_name}_metrics.yaml"
    if not output_path:
        output_path = os.path.join(os.getcwd(), file_name)
    
    # Generate comment header
    header = "# Metrics view YAML\n"
    header += "# Reference documentation: https://docs.rilldata.com/reference/project-files/dashboards\n"
    header += f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += f"# Based on template: {os.path.basename(template_path)}\n\n"
    
    # Write the output file
    with open(output_path, 'w') as file:
        file.write(header)
        yaml.dump(template_data, file, sort_keys=False, default_flow_style=False)
    
    print(f"Created metrics YAML file: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description='Generate metrics YAML files from templates')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Generate templates command
    gen_parser = subparsers.add_parser('generate-templates', help='Generate template files from examples')
    
    # Create metrics command
    metrics_parser = subparsers.add_parser('create', help='Create a metrics YAML file')
    metrics_parser.add_argument('--client', required=True, help='Client/Agency name')
    metrics_parser.add_argument('--brand', required=True, help='Brand name')
    metrics_parser.add_argument('--media-type', required=True, help='Media type (Display, Native, Video, CTV)')
    metrics_parser.add_argument('--platform', required=True, help='Platform (TTD, DV360, StackAdapt, Yahoo)')
    metrics_parser.add_argument('--output', help='Custom output path for the YAML file')
    
    args = parser.parse_args()
    
    if args.command == 'generate-templates':
        templates = generate_all_templates()
        print(f"Generated {len(templates)} template files in {TEMPLATE_DIR}")
    elif args.command == 'create':
        create_metrics_yaml(
            client_name=args.client,
            brand_name=args.brand,
            media_type=args.media_type,
            platform=args.platform,
            output_path=args.output
        )
    else:
        # Default behavior
        parser.print_help()

if __name__ == "__main__":
    main() 