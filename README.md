# Glazing

[![PyPI version](https://img.shields.io/pypi/v/glazing)](https://pypi.org/project/glazing/)
[![Python versions](https://img.shields.io/pypi/pyversions/glazing)](https://pypi.org/project/glazing/)
[![License](https://img.shields.io/pypi/l/glazing)](https://github.com/aaronstevenwhite/glazing/blob/main/LICENSE)
[![CI](https://github.com/aaronstevenwhite/glazing/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/aaronstevenwhite/glazing/actions/workflows/ci.yml)
[![Documentation](https://readthedocs.org/projects/glazing/badge/?version=latest)](https://glazing.readthedocs.io/en/latest/?badge=latest)

A unified Python interface for FrameNet, PropBank, VerbNet, and WordNet with automatic data management.

## Features

- 🚀 **One-command setup**: `glazing init` downloads and prepares all datasets
- 📦 **Type-safe models**: Pydantic v2 validation for all data structures
- 🔍 **Unified search**: Query across all datasets with consistent API
- 🔗 **Cross-references**: Automatic mapping between resources
- 💾 **Efficient storage**: JSON Lines format with streaming support
- 🐍 **Modern Python**: Full type hints, Python 3.13+ support

## Installation

```bash
pip install glazing
```

## Quick Start

Initialize all datasets (one-time setup, ~120MB download):

```bash
glazing init
```

Then start using the data:

```python
from glazing.search import UnifiedSearch

search = UnifiedSearch()
results = search.search_by_query("give")

for result in results[:5]:
    print(f"{result.dataset}: {result.name} - {result.description}")
```

## CLI Usage

Search across datasets:

```bash
# Search all datasets
glazing search query "abandon"

# Search specific dataset
glazing search query "run" --dataset verbnet

# Find cross-references
glazing search cross-ref --source propbank --id "give.01" --target verbnet
```

## Python API

Load and work with individual datasets:

```python
from glazing.framenet.loader import FrameNetLoader
from glazing.verbnet.loader import VerbNetLoader
from pathlib import Path

# Load datasets
data_dir = Path.home() / ".local/share/glazing/converted"

fn_loader = FrameNetLoader()
frames = fn_loader.load_frames(data_dir / "framenet.jsonl")

vn_loader = VerbNetLoader()
verb_classes = vn_loader.load_verb_classes(data_dir / "verbnet.jsonl")
```

Cross-reference resolution:

```python
from glazing.references.resolver import ReferenceResolver
from glazing.references.extractor import ReferenceExtractor

# Extract and resolve references
extractor = ReferenceExtractor()
references = extractor.extract_from_datasets(data_dir)

resolver = ReferenceResolver(references)
related = resolver.resolve("give.01", source="propbank")
print(f"VerbNet classes: {related.verbnet_classes}")
```

## Supported Datasets

- **FrameNet 1.7**: Semantic frames and frame elements
- **PropBank 3.4**: Predicate-argument structures
- **VerbNet 3.4**: Verb classes with thematic roles
- **WordNet 3.1**: Synsets and lexical relations

## Documentation

Full documentation available at [https://glazing.readthedocs.io](https://glazing.readthedocs.io).

- [Installation Guide](https://glazing.readthedocs.io/en/latest/installation/)
- [Quick Start Tutorial](https://glazing.readthedocs.io/en/latest/quick-start/)
- [API Reference](https://glazing.readthedocs.io/en/latest/api/)
- [CLI Documentation](https://glazing.readthedocs.io/en/latest/user-guide/cli/)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Development setup
git clone https://github.com/aaronstevenwhite/glazing
cd glazing
pip install -e ".[dev]"
```

## Citation

If you use Glazing in your research, please cite:

```bibtex
@software{glazing2025,
  author = {White, Aaron Steven},
  title = {Glazing: A Unified Interface for Linguistic Resources},
  year = {2025},
  url = {https://github.com/aaronstevenwhite/glazing}
}
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- [GitHub Repository](https://github.com/aaronstevenwhite/glazing)
- [PyPI Package](https://pypi.org/project/glazing/)
- [Documentation](https://glazing.readthedocs.io)
- [Issue Tracker](https://github.com/aaronstevenwhite/glazing/issues)
