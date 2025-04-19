# Metrics YAML Generator (External)

This tool generates Rill metrics YAML files based on templates extracted from existing examples, without modifying the original metrics repository.

## Prerequisites

- Python 3.6+
- PyYAML package: `pip install pyyaml`

## Setup

1. The files are already in place at `~/yaml-generator/`

2. Generate template files from existing examples:
   ```bash
   python generate_metrics_yaml.py generate-templates
   ```
   
   This will scan the metrics directory, find example YAML files for each DSP and media type combination, and create template files in the `~/yaml-generator/templates` directory.

## Usage

Create a new metrics YAML file using:

```bash
python generate_metrics_yaml.py create --client "ClientName" --brand "BrandName" --media-type "Display" --platform "TTD"
```

### Required Parameters

- `--client`: The client or agency name (e.g., "CVS", "ButlerTill")
- `--brand`: The brand name (e.g., "Haleon", "StateFarm")
- `--media-type`: The type of media (e.g., "Display", "Native", "Video", "CTV")
- `--platform`: The platform name (e.g., "TTD", "DV360", "StackAdapt", "Yahoo")

### Optional Parameters

- `--output`: Custom output path for the YAML file (default: current directory with auto-generated filename)

## Example Commands

```bash
# Create a metrics YAML file for CVS - Haleon - Display - TTD
python generate_metrics_yaml.py create --client "CVS" --brand "Haleon" --media-type "Display" --platform "TTD"

# Create a metrics YAML file for a CTV campaign with a custom output path
python generate_metrics_yaml.py create --client "GroupM" --brand "Mizkan" --media-type "CTV" --platform "TTD" --output "./my_metrics.yaml"
```

## How It Works

1. The tool scans existing YAML files in the metrics directory to find examples for each DSP and media type combination
2. It extracts the structure, dimensions, and measures from these examples to create template files
3. When creating a new YAML file, it uses the appropriate template based on the specified DSP and media type
4. It customizes the template with the provided client, brand, and other information

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