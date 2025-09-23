# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-09-23

Initial release of Glazing - A unified interface for FrameNet, PropBank, VerbNet, and WordNet linguistic resources.

### Added

#### Core Features
- **Unified data models** for all four linguistic resources using Pydantic v2
- **One-command initialization** with `glazing init` to download and convert all datasets
- **JSON Lines format** for efficient storage and streaming of large datasets
- **Type-safe interfaces** with comprehensive type hints for Python 3.13+
- **Cross-reference resolution** between FrameNet, PropBank, VerbNet, and WordNet
- **Memory-efficient streaming** support for processing large datasets

#### Command-Line Interface
- `glazing init` - Initialize all datasets with a single command
- `glazing download` - Download individual or all datasets
- `glazing convert` - Convert from source formats to JSON Lines
- `glazing search` - Search across datasets with various filters
- Support for custom data directories via `--data-dir` or environment variables
- JSON output mode for programmatic use

#### Python API
- `UnifiedSearch` class for searching across all datasets
- Dataset-specific loaders: `FrameNetLoader`, `PropBankLoader`, `VerbNetLoader`, `WordNetLoader`
- `ReferenceExtractor` and `ReferenceResolver` for cross-dataset mappings
- Streaming iterators for memory-efficient processing
- Comprehensive search methods: by lemma, by query, by entity ID

#### Dataset Support
- **FrameNet 1.7**: Semantic frames, frame elements, lexical units, and frame relations
- **PropBank 3.4**: Framesets, rolesets, and semantic role labels
- **VerbNet 3.4**: Verb classes, thematic roles, syntactic frames, and GL semantics
- **WordNet 3.1**: Synsets, lemmas, lexical relations, and morphological processing

#### Data Processing
- XML to JSON Lines converters for all datasets
- Automatic validation using Pydantic models
- Support for incremental and streaming conversion
- Efficient caching for repeated operations

#### Development Tools
- Comprehensive test suite with pytest
- Code quality checks with ruff and mypy
- Pre-commit hooks for consistent code style
- CI/CD pipeline with GitHub Actions
- Support for Python 3.13

#### Documentation
- Complete API documentation with mkdocstrings
- User guides for CLI and Python API usage
- Quick start tutorials
- Contributing guidelines
- Cross-reference usage examples

### Technical Details
- **Package size**: ~5MB (code only)
- **Dataset size**: ~120MB compressed, ~500MB extracted
- **Performance**: Streaming support for datasets up to several GB
- **Compatibility**: Python 3.13+, all major operating systems

### Dependencies
- `pydantic >= 2.5.0` (data validation)
- `typing-extensions >= 4.9.0` (extended type hints)
- `python-dateutil >= 2.8.2` (date/time parsing)
- `lxml >= 5.0.0` (XML parsing)
- `click >= 8.0.0` (CLI framework)
- `requests >= 2.25.0` (dataset downloading)
- `tqdm >= 4.60.0` (progress bars)
- `rich >= 13.0.0` (CLI formatting)

[0.1.0]: https://github.com/aaronstevenwhite/glazing/releases/tag/v0.1.0
