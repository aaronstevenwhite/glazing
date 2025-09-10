# glazing

A Python package providing unified data models and interfaces for four linguistic resources: FrameNet, PropBank, VerbNet, and WordNet.

## Features

- Type-safe data models using Pydantic v2 for validation
- Support for FrameNet 1.7 semantic frames and annotations
- PropBank roleset and argument structure models
- VerbNet verb classes with thematic role inheritance
- WordNet 3.1 synsets and lexical relations
- Cross-dataset reference resolution and mapping
- Python 3.13+ with comprehensive type hints

## Installation

```bash
pip install glazing
```

For development installation:

```bash
git clone https://github.com/aaronstevenwhite/glazing.git
cd glazing
pip install -e ".[dev]"
```

## Basic Usage

```python
from glazing import FrameNet, PropBank, VerbNet, WordNet

# Load datasets from JSON Lines
fn = FrameNet.load("data/framenet.jsonl")
pb = PropBank.load("data/propbank.jsonl")
vn = VerbNet.load("data/verbnet.jsonl")
wn = WordNet.load("data/wordnet.jsonl")

# Query by lemma
abandon_frames = fn.get_frames_by_lemma("abandon")
abandon_rolesets = pb.get_rolesets_by_lemma("abandon")
abandon_classes = vn.get_classes_by_lemma("abandon")
abandon_synsets = wn.get_synsets_by_lemma("abandon", pos="v")
```

## Data Formats

The package uses JSON Lines as the primary data format. Original XML and database formats are converted to JSON Lines during data preparation, enabling efficient lazy loading of large datasets.

### Data Conversion

Convert source data to JSON Lines format:

```python
from glazing.converters import convert_framenet, convert_propbank, convert_verbnet, convert_wordnet

# Convert from original formats
convert_framenet("framenet_v17/", "data/framenet.jsonl")
convert_propbank("propbank-frames/", "data/propbank.jsonl")
convert_verbnet("verbnet/", "data/verbnet.jsonl")
convert_wordnet("wn3.1/", "data/wordnet.jsonl")
```

## Cross-References

The package maintains cross-references between datasets:

```python
from glazing.references import CrossRef

xref = CrossRef(fn, pb, vn, wn)

# Get related entries across datasets
related = xref.get_related("give.01", source="propbank")
print(related.verbnet_classes)  # ['give-13.1']
print(related.framenet_frames)  # ['Giving']
print(related.wordnet_senses)   # ['give%2:40:00', 'give%2:40:01']
```

## Requirements

- Python 3.13+
- pydantic >= 2.5.0
- typing-extensions >= 4.9.0
- python-dateutil >= 2.8.2

## Documentation

Full documentation is available at [https://glazing.readthedocs.io](https://glazing.readthedocs.io)

## License

MIT License - see LICENSE file for details.

## Citation

If you use this package in your research, please cite:

```bibtex
@software{glazing2025,
  author = {White, Aaron Steven},
  title = {glazing: A Unified Interface for FrameNet, PropBank, VerbNet, and WordNet},
  year = {2025},
  url = {https://github.com/aaronstevenwhite/glazing}
}
```

## Contributing

Contributions are welcome. Please ensure all tests pass and code follows the project's style guidelines:

```bash
# Run tests
pytest

# Check code style
ruff check src/ tests/

# Type checking
mypy src/
```

## Data Sources

This package provides models for data from:

- [FrameNet](https://framenet.icsi.berkeley.edu/)
- [PropBank](https://propbank.github.io/)
- [VerbNet](https://verbs.colorado.edu/verbnet/)
- [WordNet](https://wordnet.princeton.edu/)
