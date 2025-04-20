#!/usr/bin/env python3
import os
import sys
import click
import yaml
import json

# Import our modules
from generate_metrics_yaml import create_metrics_yaml, generate_all_templates
from validation import comprehensive_file_validation
from template_manager import TemplateManager, initialize_presets, merge_metrics_files
from data_source import SchemaExtractor

@click.group()
def cli():
    """Metrics YAML Generator - Create and manage YAML files for Rill dashboards."""
    pass

@cli.command('create')
@click.option('--client', required=True, help='Client/Agency name')
@click.option('--brand', required=True, help='Brand name')
@click.option('--media-type', required=True, help='Media type (Display, Native, Video, CTV)')
@click.option('--platform', required=True, help='Platform (TTD, DV360, StackAdapt, Yahoo)')
@click.option('--output', help='Custom output path for the YAML file')
@click.option('--template', help='Custom template path to use')
@click.option('--preset', help='Preset template to use (e.g., basic_display, video_analytics)')
@click.option('--validate/--no-validate', default=True, help='Validate the generated YAML file')
def create_command(client, brand, media_type, platform, output, template, preset, validate):
    """Create a new metrics YAML file for a client dashboard."""
    
    # Use preset template if specified
    if preset:
        manager = TemplateManager()
        preset_path = os.path.join(manager.preset_dir, f"{preset}.yaml")
        if os.path.exists(preset_path):
            template = preset_path
        else:
            click.echo(f"Preset template '{preset}' not found. Available presets:")
            for p in manager.list_presets():
                click.echo(f"  - {p.replace('.yaml', '')}")
            return
    
    # Create the metrics YAML file
    output_path = create_metrics_yaml(
        client_name=client,
        brand_name=brand,
        media_type=media_type,
        platform=platform,
        template_path=template,
        output_path=output
    )
    
    if not output_path:
        click.echo("Failed to create metrics YAML file.")
        return
    
    click.echo(f"Created metrics YAML file: {output_path}")
    
    # Validate the generated file if requested
    if validate and output_path:
        is_valid, errors = comprehensive_file_validation(output_path)
        if is_valid:
            click.echo("✅ Validation passed!")
        else:
            click.echo("❌ Validation errors found:")
            for error in errors:
                click.echo(f"  - {error}")

@cli.command('merge-measures')
@click.argument('base_file', type=click.Path(exists=True))
@click.argument('source_file', type=click.Path(exists=True))
@click.option('--output', help='Output path for the merged YAML file. If not provided, the base file will be updated.')
@click.option('--validate/--no-validate', default=True, help='Validate the generated YAML file')
def merge_measures_command(base_file, source_file, output, validate):
    """Merge measures from SOURCE_FILE into BASE_FILE.
    
    This command takes measures defined in SOURCE_FILE and adds them to BASE_FILE,
    avoiding duplicates. The resulting file can either replace BASE_FILE or be
    written to a new file specified by --output.
    
    Example:
    metrics_cli.py merge-measures client_a.yaml client_b.yaml --output merged.yaml
    """
    click.echo(f"Merging measures from {source_file} into {base_file}...")
    
    try:
        output_path, measures_added = merge_metrics_files(base_file, source_file, output)
        
        if measures_added > 0:
            click.echo(f"✅ Added {measures_added} measure(s) to {output_path}")
        else:
            click.echo("ℹ️ No new measures were added (all measures already exist in the base file)")
            
        # Validate the generated file if requested
        if validate:
            is_valid, errors = comprehensive_file_validation(output_path)
            if is_valid:
                click.echo("✅ Validation passed!")
            else:
                click.echo("❌ Validation errors found:")
                for error in errors:
                    click.echo(f"  - {error}")
                
    except Exception as e:
        click.echo(f"❌ Error merging measures: {str(e)}")
        return

@cli.command('validate')
@click.argument('file_path', type=click.Path(exists=True))
def validate_command(file_path):
    """Validate a metrics YAML file."""
    is_valid, errors = comprehensive_file_validation(file_path)
    if is_valid:
        click.echo(f"✅ {file_path} is valid!")
    else:
        click.echo(f"❌ {file_path} has validation errors:")
        for error in errors:
            click.echo(f"  - {error}")

@cli.command('templates')
@click.option('--generate', is_flag=True, help='Generate template files from examples')
def templates_command(generate):
    """List or generate template files."""
    if generate:
        templates = generate_all_templates()
        click.echo(f"Generated {len(templates)} template files")
    
    manager = TemplateManager()
    templates = manager.list_templates()
    click.echo("Available templates:")
    for template in templates:
        click.echo(f"  - {template}")

@cli.command('presets')
@click.option('--initialize', is_flag=True, help='Initialize preset templates')
def presets_command(initialize):
    """List or initialize preset templates."""
    if initialize:
        initialize_presets()
    
    manager = TemplateManager()
    presets = manager.list_presets()
    click.echo("Available presets:")
    for preset in presets:
        click.echo(f"  - {preset}")

@cli.command('create-preset')
@click.option('--name', required=True, help='Name for the preset template')
@click.option('--base-template', required=True, help='Base template path to use')
@click.option('--description', help='Description of the preset template')
@click.option('--override', multiple=True, help='Override values in format key=value')
def create_preset_command(name, base_template, description, override):
    """Create a new preset template."""
    # Parse override values
    overrides = {}
    for o in override:
        if '=' in o:
            key, value = o.split('=', 1)
            try:
                # Try to parse as JSON
                overrides[key] = json.loads(value)
            except json.JSONDecodeError:
                # Fall back to string
                overrides[key] = value
    
    manager = TemplateManager()
    preset_path = manager.create_custom_preset(base_template, name, overrides, description)
    
    if preset_path:
        click.echo(f"Created preset template: {preset_path}")
    else:
        click.echo("Failed to create preset template.")

@cli.command('from-parquet')
@click.argument('parquet_file', type=click.Path(exists=True))
@click.option('--output', help='Output path for the YAML file')
@click.option('--model-name', help='Model name to use in the YAML file')
def from_parquet_command(parquet_file, output, model_name):
    """Generate a metrics YAML file from a Parquet file."""
    metrics_yaml = SchemaExtractor.generate_metrics_yaml_from_parquet(parquet_file, output)
    
    if metrics_yaml:
        if model_name:
            metrics_yaml["model"] = model_name
            metrics_yaml["display_name"] = f"{model_name} Metrics"
            
            # Update output file with model name if specified
            if output:
                with open(output, 'w') as file:
                    # Generate header
                    header = "# Metrics view YAML - Auto-generated from Parquet\n"
                    header += "# Reference documentation: https://docs.rilldata.com/reference/project-files/dashboards\n\n"
                    
                    file.write(header)
                    yaml.dump(metrics_yaml, file, sort_keys=False, default_flow_style=False)
        
        click.echo(f"Generated metrics YAML from Parquet file: {parquet_file}")
        if output:
            click.echo(f"Output file: {output}")
    else:
        click.echo(f"Failed to generate metrics YAML from Parquet file: {parquet_file}")

@cli.command('update-from-parquet')
@click.argument('yaml_file', type=click.Path(exists=True))
@click.argument('parquet_file', type=click.Path(exists=True))
@click.option('--output', help='Output path for the updated YAML file')
def update_from_parquet_command(yaml_file, parquet_file, output):
    """Update an existing YAML file with schema from a Parquet file."""
    schema_info = SchemaExtractor.extract_from_parquet(parquet_file)
    
    if not schema_info:
        click.echo(f"Failed to extract schema from Parquet file: {parquet_file}")
        return
    
    # Default to input file if output not specified
    if not output:
        output = yaml_file
    
    updated_yaml = SchemaExtractor.update_existing_yaml(yaml_file, schema_info, output)
    
    if updated_yaml:
        click.echo(f"Updated YAML file with schema from Parquet file: {parquet_file}")
        click.echo(f"Output file: {output}")
    else:
        click.echo(f"Failed to update YAML file: {yaml_file}")

if __name__ == "__main__":
    # Create preset directory if it doesn't exist
    preset_dir = os.path.expanduser("~/yaml-generator/presets")
    os.makedirs(preset_dir, exist_ok=True)
    
    cli() 