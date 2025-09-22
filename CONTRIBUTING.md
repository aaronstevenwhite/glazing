# Contributing to Glazing

Thank you for your interest in contributing to Glazing! We welcome contributions from the community.

## Quick Start

1. Fork the repository on GitHub
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/glazing.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Install development dependencies: `pip install -e ".[dev]"`
5. Make your changes with tests
6. Run tests: `pytest`
7. Submit a pull request

## Development Setup

```bash
# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev,docs]"

# Install pre-commit hooks
pre-commit install

# Initialize test data
glazing init
```

## Code Style

We use `ruff` for code quality:

```bash
# Format code
ruff format src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy --strict src/
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=glazing

# Run specific test
pytest tests/test_verbnet/
```

## Documentation

```bash
# Build and serve docs
mkdocs serve

# Build static docs
mkdocs build
```

## Pull Request Process

1. Ensure tests pass
2. Update documentation if needed
3. Add entry to CHANGELOG.md
4. Create PR with clear description
5. Link related issues

## Project Structure

- `src/glazing/` - Main package code
- `tests/` - Test suite
- `docs/` - Documentation source
- `pyproject.toml` - Project configuration

## Areas to Contribute

- **Bug fixes** - Check issues labeled `bug`
- **Features** - See `enhancement` issues
- **Documentation** - Improve clarity, add examples
- **Tests** - Increase coverage, add edge cases
- **Performance** - Optimize data loading/searching

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive feedback
- Focus on project improvement

## Getting Help

- Open an issue for bugs
- Start a discussion for questions
- Check existing issues first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

For more detailed information, see the [full contributing guide](https://glazing.readthedocs.io/en/latest/contributing/).
