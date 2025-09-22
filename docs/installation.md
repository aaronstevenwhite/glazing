# Installation

This guide covers the installation of Glazing and its dependencies.

## Requirements

- **Python 3.13 or higher**
- pip package manager
- ~500MB disk space for all datasets
- Internet connection for dataset downloads

## Install from PyPI

The simplest way to install Glazing is via pip:

```bash
pip install glazing
```

## Install from Source

To install the latest development version:

```bash
git clone https://github.com/aaronstevenwhite/glazing.git
cd glazing
pip install -e .
```

For development with all dependencies:

```bash
pip install -e ".[dev,docs]"
```

## Initialize Datasets

After installation, initialize the datasets:

```bash
glazing init
```

This command will:
1. Download all datasets (~120MB compressed)
2. Extract and convert them to JSON Lines format
3. Store them in `~/.local/share/glazing/` (or `%LOCALAPPDATA%\glazing\` on Windows)

### Custom Data Directory

To use a custom directory for datasets:

```bash
glazing init --data-dir /path/to/your/data
```

Or set the environment variable:

```bash
export GLAZING_DATA_DIR=/path/to/your/data
glazing init
```

## Verify Installation

Check that Glazing is properly installed:

```bash
# Check version
glazing --version

# View available commands
glazing --help

# Verify datasets are initialized
python -c "from glazing.initialize import check_initialization; print('Initialized' if check_initialization() else 'Not initialized')"
```

## Optional Dependencies

### Development Tools

For contributing to Glazing:

```bash
pip install glazing[dev]
```

This installs:
- ruff (linting and formatting)
- mypy (type checking)
- pytest (testing framework)
- pre-commit (git hooks)

### Documentation Tools

For building documentation:

```bash
pip install glazing[docs]
```

This installs:
- mkdocs (documentation generator)
- mkdocs-material (theme)
- mkdocstrings (API documentation)

## Environment Variables

Glazing respects the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `GLAZING_DATA_DIR` | Directory for storing datasets | `~/.local/share/glazing/` |
| `XDG_DATA_HOME` | Base directory for user data (Linux/macOS) | `~/.local/share/` |
| `GLAZING_SKIP_INIT_CHECK` | Skip initialization check on import | `false` |

## Platform-Specific Notes

### macOS

On macOS, you might need to install Xcode Command Line Tools:

```bash
xcode-select --install
```

### Windows

On Windows, we recommend using:
- Windows Terminal for better CLI experience
- WSL2 for Unix-like environment

### Linux

Most Linux distributions come with Python pre-installed. Ensure you have Python 3.13+:

```bash
python3 --version
```

## Docker Installation

A Docker image is available for containerized usage:

```dockerfile
FROM python:3.13-slim

RUN pip install glazing && \
    glazing init

WORKDIR /app
```

## Troubleshooting

### Import Warning

If you see a warning about uninitialized datasets:

```python
Warning: Glazing datasets not initialized.
Run 'glazing init' to download and convert all datasets.
```

Simply run:

```bash
glazing init
```

### Permission Errors

If you encounter permission errors:

```bash
# Use a different directory
glazing init --data-dir ~/my-glazing-data

# Or fix permissions
sudo chown -R $USER:$USER ~/.local/share/glazing
```

### FrameNet Manual Download

FrameNet requires manual download due to licensing:

1. Visit the [FrameNet data page](https://framenet.icsi.berkeley.edu/fndrupal/framenet_data)
2. Download FrameNet 1.7
3. Convert manually:

```bash
glazing convert dataset --dataset framenet --input-dir framenet_v17/ --output-dir data/
```

### Memory Issues

If you encounter memory issues during conversion:

```bash
# Process datasets one at a time
glazing download dataset --dataset verbnet
glazing convert dataset --dataset verbnet --input-dir raw/ --output-dir data/

# Repeat for other datasets
```

## Next Steps

Once installed, proceed to the [Quick Start](quick-start.md) guide to begin using Glazing.
