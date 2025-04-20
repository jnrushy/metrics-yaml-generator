# Metrics YAML Generator

A comprehensive tool for generating Rill metrics YAML files for digital advertising dashboards. This tool creates standardized metrics view files for different DSPs and media types, using templates derived from existing examples.

## Features

- Generate metrics YAML files using templates from different DSPs and media types
- Create custom preset templates for frequently used configurations
- Extract metrics definitions directly from Parquet files
- Validate metrics YAML files against schema
- Merge measures from one metrics file into another (with column compatibility checking)
- Command-line interface for easy integration

## Prerequisites

- Python 3.6+
- Required packages:
  ```
  PyYAML==6.0.1
  jsonschema==4.23.0
  pyarrow==19.0.1
  click==8.1.8
  ```

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/jnrushy/metrics-yaml-generator.git
   cd metrics-yaml-generator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Generate template files (if not already present):
   ```bash
   python metrics_cli.py templates --generate
   ```

## Usage

The tool offers a command-line interface with several commands:

### Creating Metrics YAML Files

```bash
python metrics_cli.py create --client "ClientName" --brand "BrandName" --media-type "Display" --platform "TTD"
```

#### Required Parameters

- `--client`: Client or agency name (e.g., "CVS", "ButlerTill")
- `--brand`: Brand name (e.g., "Haleon", "StateFarm")
- `--media-type`: Media type (Display, Native, Video, CTV)
- `--platform`: Platform name (TTD, DV360, StackAdapt, Yahoo)

#### Optional Parameters

- `--output`: Custom output path for the file
- `--template`: Custom template path to use
- `--preset`: Name of a preset template to use
- `--validate/--no-validate`: Enable/disable validation (default: enabled)

### Merging Measures Between Files

Merge measures from a source file into a base file, adding only metrics that don't already exist and are compatible with the base dataset's schema:

```bash
python metrics_cli.py merge-measures base_file.yaml source_file.yaml --output merged.yaml
```

#### Required Parameters

- `base_file.yaml`: The file that will receive the measures
- `source_file.yaml`: The file containing measures to be added

#### Optional Parameters

- `--output`: Path for the output file. If not provided, the base file will be updated
- `--validate/--no-validate`: Enable/disable validation of the result (default: enabled)
- `--check-columns/--no-check-columns`: Enable/disable column compatibility checking (default: enabled)

The column compatibility checking ensures that only measures referencing columns that exist in the base dataset will be included. This prevents runtime errors in dashboards due to references to non-existent columns.

### Managing Templates

List available templates:
```bash
python metrics_cli.py templates
```

Generate template files from examples:
```bash
python metrics_cli.py templates --generate
```

### Using Presets

List available presets:
```bash
python metrics_cli.py presets
```

Initialize preset templates:
```bash
python metrics_cli.py presets --initialize
```

Create a new preset:
```bash
python metrics_cli.py create-preset --name "my_preset" --base-template "ttd/display_template.yaml" --description "My custom preset"
```

### Parquet Integration

Generate a metrics YAML file from a Parquet file:
```bash
python metrics_cli.py from-parquet my_data.parquet --output metrics_from_parquet.yaml --model-name "My Model"
```

Update an existing YAML file with schema from a Parquet file:
```bash
python metrics_cli.py update-from-parquet existing.yaml my_data.parquet --output updated.yaml
```

### Validation

Validate a metrics YAML file:
```bash
python metrics_cli.py validate my_metrics.yaml
```

## Example Commands

```bash
# Create a metrics YAML file for CVS - Haleon - Display - TTD
python metrics_cli.py create --client "CVS" --brand "Haleon" --media-type "Display" --platform "TTD"

# Create using a preset template
python metrics_cli.py create --client "GroupM" --brand "Mizkan" --media-type "CTV" --platform "TTD" --preset "video_analytics"

# Generate from a Parquet file
python metrics_cli.py from-parquet data/campaign_data.parquet --model-name "MyClient - MyCampaign"

# Merge measures from one file into another (with column compatibility checking)
python metrics_cli.py merge-measures client_a.yaml client_b.yaml --output merged.yaml

# Merge measures without column compatibility checking (if you're sure about the compatibility)
python metrics_cli.py merge-measures client_a.yaml client_b.yaml --output merged.yaml --no-check-columns
```

## How It Works

1. The tool scans existing YAML files in the metrics directory to find examples for each DSP and media type combination
2. It extracts the structure, dimensions, and measures from these examples to create template files
3. When creating a new YAML file, it uses the appropriate template based on the specified DSP and media type
4. It customizes the template with the provided client, brand, and other information
5. When merging measures, it analyzes SQL expressions to extract column references and verifies they exist in the target dataset

## Supported DSPs and Media Types

### DSPs (Demand-Side Platforms)
- TTD (The Trade Desk)
- DV360 (Display & Video 360)
- StackAdapt
- Yahoo

### Media Types
- Display
- Video
- CTV (Connected TV)
- Native

## Advanced Usage

### Creating Custom Presets

You can create custom presets by modifying existing templates:

```bash
python metrics_cli.py create-preset --name "performance_preset" --base-template "ttd/display_template.yaml" --description "Performance metrics" --override "measures=[{\"name\":\"roas\",\"label\":\"ROAS\",\"expression\":\"SUM(revenue) / SUM(total_cost)\"}]"
```

### Schema Extraction

When working with Parquet files, the tool automatically:
- Identifies time-series columns (date/time fields)
- Detects measure columns (numeric fields)
- Sets remaining fields as dimensions
- Creates appropriate expressions for measures 