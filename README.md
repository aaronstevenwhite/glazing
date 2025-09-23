# Glazing

[![PyPI version](https://img.shields.io/pypi/v/glazing)](https://pypi.org/project/glazing/)
[![Python versions](https://img.shields.io/pypi/pyversions/glazing)](https://pypi.org/project/glazing/)
[![CI](https://github.com/aaronstevenwhite/glazing/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/aaronstevenwhite/glazing/actions/workflows/ci.yml)
[![Documentation](https://readthedocs.org/projects/glazing/badge/?version=latest)](https://glazing.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/pypi/l/glazing)](https://github.com/aaronstevenwhite/glazing/blob/main/LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17185626.svg)](https://doi.org/10.5281/zenodo.17185626)

Unified data models and interfaces for syntactic and semantic frame ontologies.

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

Initialize all datasets (one-time setup, ~54MB download):

```bash
glazing init
```

Then start using the data:

```python
from glazing.search import UnifiedSearch

# Automatically uses default data directory after 'glazing init'
search = UnifiedSearch()
results = search.search("give")

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

# Loaders automatically use default paths and load data after 'glazing init'
fn_loader = FrameNetLoader()  # Data is already loaded
frames = fn_loader.frames

vn_loader = VerbNetLoader()  # Data is already loaded
verb_classes = list(vn_loader.classes.values())
```

Cross-reference resolution:

```python
from glazing.references.extractor import ReferenceExtractor
from glazing.verbnet.loader import VerbNetLoader
from glazing.propbank.loader import PropBankLoader

# Load datasets
vn_loader = VerbNetLoader()
pb_loader = PropBankLoader()

# Extract references
extractor = ReferenceExtractor()
extractor.extract_verbnet_references(list(vn_loader.classes.values()))
extractor.extract_propbank_references(list(pb_loader.framesets.values()))

# Access PropBank cross-references
if "give.01" in extractor.propbank_refs:
    refs = extractor.propbank_refs["give.01"]
    vn_classes = refs.get_verbnet_classes()
    print(f"VerbNet classes for give.01: {vn_classes}")
```

## Supported Datasets

- **[FrameNet](https://framenet.icsi.berkeley.edu/) 1.7**: Semantic frames and frame elements
- **[PropBank](https://propbank.github.io/) 3.4**: Predicate-argument structures
- **[VerbNet](https://verbs.colorado.edu/verbnet/) 3.4**: Verb classes with thematic roles
- **[WordNet](https://wordnet.princeton.edu/) 3.1**: Synsets and lexical relations

## Documentation

Full documentation available at [https://glazing.readthedocs.io](https://glazing.readthedocs.io).

- [Installation Guide](https://glazing.readthedocs.io/en/latest/installation/)
- [Quick Start Tutorial](https://glazing.readthedocs.io/en/latest/quick-start/)
- [API Reference](https://glazing.readthedocs.io/en/latest/api/)
- [CLI Documentation](https://glazing.readthedocs.io/en/latest/user-guide/cli/)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](https://github.com/aaronstevenwhite/glazing/blob/main/CONTRIBUTING.md) for guidelines.

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
  title = {Glazing: Unified Data Models and Interfaces for Syntactic and Semantic Frame Ontologies},
  year = {2025},
  url = {https://github.com/aaronstevenwhite/glazing},
  doi = {10.5281/zenodo.17185626}
}
```

## License

This package is licensed under an MIT License. See [LICENSE](https://github.com/aaronstevenwhite/glazing/blob/main/LICENSE) file for details.

## Links

- [GitHub Repository](https://github.com/aaronstevenwhite/glazing)
- [PyPI Package](https://pypi.org/project/glazing/)
- [Documentation](https://glazing.readthedocs.io)
- [Issue Tracker](https://github.com/aaronstevenwhite/glazing/issues)

## Acknowledgments

This project was funded by a [National Science Foundation](https://www.nsf.gov/) ([BCS-2040831](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2040831)) and builds upon the foundational work of the FrameNet, PropBank, VerbNet, and WordNet teams.
