# CLI Usage

Detailed command-line interface documentation for Glazing.

## Overview

The glazing CLI provides commands for downloading, converting, and searching linguistic datasets.

## Global Options

```bash
glazing [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show version
  --verbose  Enable verbose output
  --quiet    Suppress non-essential output
  --help     Show help message
```

## Commands

### init

Initialize all datasets with one command:

```bash
glazing init [OPTIONS]

Options:
  --data-dir PATH  Directory to store datasets
  --force          Force re-download even if data exists
```

### download

Download datasets from official sources:

```bash
glazing download dataset [OPTIONS]

Options:
  --dataset TEXT       Dataset to download (framenet|propbank|verbnet|wordnet|all)
  --output-dir PATH    Output directory for raw data
```

List available datasets:

```bash
glazing download list
```

Get dataset information:

```bash
glazing download info DATASET
```

### convert

Convert raw datasets to JSON Lines format:

```bash
glazing convert dataset [OPTIONS]

Options:
  --dataset TEXT       Dataset to convert
  --input-dir PATH     Directory containing raw data
  --output-dir PATH    Directory for converted data
```

### search

Search across datasets:

```bash
# Search by query
glazing search query QUERY [OPTIONS]

# Search for specific entity
glazing search entity ID [OPTIONS]

# Find cross-references
glazing search cross-ref [OPTIONS]

Common Options:
  --dataset TEXT       Limit to specific dataset
  --data-dir PATH      Directory containing converted data
  --json               Output as JSON
  --limit INTEGER      Limit number of results
```

## Examples

### Full Workflow

```bash
# 1. Initialize everything
glazing init

# 2. Search for a concept (uses default data directory)
glazing search query "give"

# 3. Find cross-references
glazing search cross-ref --source propbank --id "give.01" --target verbnet
```

### Custom Data Directory

```bash
# Set custom directory
export GLAZING_DATA_DIR=/my/data/path

# Initialize there
glazing init

# All commands will use this directory
glazing search query "run"
```

### Processing Individual Datasets

```bash
# Download only VerbNet
glazing download dataset --dataset verbnet

# Convert it
glazing convert dataset --dataset verbnet

# Search it (uses default converted directory)
glazing search query "run" --dataset verbnet
```

## Output Formats

### Default (Human-Readable)

```
Dataset: verbnet
Entity: give-13.1
Type: VerbClass
Description: Transfer of possession
```

### JSON Output

```bash
glazing search query "give" --json
```

Returns structured JSON for programmatic use.

## Environment Variables

- `GLAZING_DATA_DIR`: Default data directory
- `GLAZING_SKIP_INIT_CHECK`: Skip initialization check
- `XDG_DATA_HOME`: Base data directory (Linux/macOS)

## Troubleshooting

### Data Not Found

```bash
# Check if initialized
glazing init

# Verify data location
ls ~/.local/share/glazing/converted/
```

### Permission Issues

```bash
# Use different directory
glazing init --data-dir ~/my-data
```

### Memory Issues

Process datasets individually instead of using `--dataset all`.
