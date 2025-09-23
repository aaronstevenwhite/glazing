"""Tests for PropBank loader module.

Tests loading framesets and rolesets from JSON Lines files,
index building, cross-reference resolution, and caching.
"""

import json
import tempfile
from pathlib import Path

import pytest

from glazing.propbank.loader import PropBankLoader, load_frameset, load_framesets


class TestPropBankLoader:
    """Test PropBankLoader functionality."""

    @pytest.fixture
    def sample_frameset_data(self):
        """Create sample frameset data."""
        return {
            "predicate_lemma": "abandon",
            "rolesets": [
                {
                    "id": "abandon.01",
                    "name": "leave behind",
                    "aliases": {
                        "alias": [
                            {"text": "abandon", "pos": "v"},
                            {"text": "abandonment", "pos": "n"},
                        ]
                    },
                    "roles": [
                        {
                            "n": "0",
                            "f": "PAG",
                            "descr": "abandoner",
                            "rolelinks": [
                                {
                                    "class_name": "leave-51.2",
                                    "resource": "VerbNet",
                                    "version": "3.4",
                                }
                            ],
                        },
                        {
                            "n": "1",
                            "f": "PPT",
                            "descr": "thing abandoned",
                            "rolelinks": [],
                        },
                    ],
                    "lexlinks": [
                        {
                            "class_name": "leave-51.2",
                            "confidence": 0.95,
                            "resource": "VerbNet",
                            "version": "3.4",
                            "src": "manual",
                        }
                    ],
                    "examples": [
                        {
                            "text": "He abandoned the project.",
                            "propbank": {
                                "args": [
                                    {"type": "ARG0", "start": 0, "end": 1},
                                    {"type": "ARG1", "start": 3, "end": 4},
                                ],
                                "rel": {"relloc": "1"},
                            },
                        }
                    ],
                }
            ],
        }

    @pytest.fixture
    def sample_jsonl_file(self, sample_frameset_data):
        """Create a temporary JSON Lines file with sample data."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            # Write multiple framesets
            json.dump(sample_frameset_data, f)
            f.write("\n")

            # Add another frameset
            give_data = {
                "predicate_lemma": "give",
                "rolesets": [
                    {
                        "id": "give.01",
                        "name": "transfer",
                        "roles": [
                            {"n": "0", "f": "PAG", "descr": "giver"},
                            {"n": "1", "f": "PPT", "descr": "thing given"},
                            {"n": "2", "f": "GOL", "descr": "recipient"},
                        ],
                        "examples": [],
                    }
                ],
            }
            json.dump(give_data, f)
            f.write("\n")

            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        temp_path.unlink(missing_ok=True)

    def test_loader_initialization(self, sample_jsonl_file):
        """Test PropBankLoader initialization without autoload."""
        loader = PropBankLoader(sample_jsonl_file, autoload=False)

        assert loader.data_path == sample_jsonl_file
        assert loader.lazy is False  # Default is now False
        assert loader.cache is None  # No cache when not lazy
        assert len(loader.frameset_index) == 2
        assert len(loader.roleset_index) == 2

    def test_loader_initialization_with_autoload(self, sample_jsonl_file):
        """Test PropBankLoader with autoload."""
        loader = PropBankLoader(sample_jsonl_file)  # autoload=True by default

        assert loader.lazy is False
        assert loader.cache is None
        assert loader.framesets_cache is not None
        assert len(loader.framesets_cache) == 2

    def test_loader_file_not_found(self):
        """Test loader with non-existent file."""
        with pytest.raises(FileNotFoundError, match="Data file not found"):
            PropBankLoader("nonexistent.jsonl")

    def test_load(self, sample_jsonl_file):
        """Test loading all framesets."""
        loader = PropBankLoader(sample_jsonl_file, autoload=False)
        framesets = loader.load()

        assert len(framesets) == 2
        assert "abandon" in framesets
        assert "give" in framesets

        abandon_frameset = framesets["abandon"]
        assert len(abandon_frameset.rolesets) == 1
        assert abandon_frameset.rolesets[0].id == "abandon.01"

    def test_get_frameset(self, sample_jsonl_file):
        """Test getting a specific frameset."""
        loader = PropBankLoader(sample_jsonl_file)

        frameset = loader.get_frameset("abandon")
        assert frameset is not None
        assert frameset.predicate_lemma == "abandon"
        assert len(frameset.rolesets) == 1

        # Test non-existent frameset
        frameset = loader.get_frameset("nonexistent")
        assert frameset is None

    def test_get_roleset(self, sample_jsonl_file):
        """Test getting a specific roleset."""
        loader = PropBankLoader(sample_jsonl_file)

        roleset = loader.get_roleset("abandon.01")
        assert roleset is not None
        assert roleset.id == "abandon.01"
        assert roleset.name == "leave behind"
        assert len(roleset.roles) == 2

        # Test another roleset
        roleset = loader.get_roleset("give.01")
        assert roleset is not None
        assert roleset.id == "give.01"
        assert len(roleset.roles) == 3

        # Test non-existent roleset
        roleset = loader.get_roleset("nonexistent.01")
        assert roleset is None

    def test_build_indices(self, sample_jsonl_file):
        """Test index building."""
        loader = PropBankLoader(sample_jsonl_file)

        # Indices should be built on initialization
        assert "abandon" in loader.frameset_index
        assert "give" in loader.frameset_index
        assert "abandon.01" in loader.roleset_index
        assert "give.01" in loader.roleset_index

        # Test that indices map correctly
        assert loader.roleset_index["abandon.01"] == "abandon"
        assert loader.roleset_index["give.01"] == "give"

    def test_caching(self, sample_jsonl_file):
        """Test caching behavior."""
        loader = PropBankLoader(sample_jsonl_file, lazy=True, cache_size=10, autoload=False)

        # First access should cache
        frameset1 = loader.get_frameset("abandon")
        assert loader.cache is not None

        # Check that cache has entries
        assert loader.cache.size() > 0

        # Second access should use cache
        frameset2 = loader.get_frameset("abandon")
        assert frameset1.predicate_lemma == frameset2.predicate_lemma

        # Test roleset caching
        roleset1 = loader.get_roleset("abandon.01")
        assert roleset1 is not None

        # Cache should have more entries now
        cache_size_after_roleset = loader.cache.size()
        assert cache_size_after_roleset >= 1

        roleset2 = loader.get_roleset("abandon.01")
        assert roleset1.id == roleset2.id

    def test_iter_framesets(self, sample_jsonl_file):
        """Test iterating over framesets in batches."""
        loader = PropBankLoader(sample_jsonl_file)

        batches = list(loader.iter_framesets(batch_size=1))
        assert len(batches) == 2
        assert len(batches[0]) == 1
        assert len(batches[1]) == 1

        # Test with larger batch size
        batches = list(loader.iter_framesets(batch_size=10))
        assert len(batches) == 1
        assert len(batches[0]) == 2

    def test_search_by_pattern(self, sample_jsonl_file):
        """Test searching framesets by pattern."""
        loader = PropBankLoader(sample_jsonl_file)

        # Search for predicates starting with 'a'
        matches = loader.search_by_pattern(r"^a")
        assert len(matches) == 1
        assert matches[0].predicate_lemma == "abandon"

        # Search for all predicates
        matches = loader.search_by_pattern(r".*")
        assert len(matches) == 2

        # Search for non-matching pattern
        matches = loader.search_by_pattern(r"^z")
        assert len(matches) == 0

    def test_get_statistics(self, sample_jsonl_file):
        """Test getting loader statistics."""
        # Test with lazy loading
        loader = PropBankLoader(sample_jsonl_file)
        stats = loader.get_statistics()

        assert stats["total_framesets"] == 2
        assert stats["total_rolesets"] == 2
        assert stats["lazy_loading"] is False  # Default is now False
        assert "total_roles" in stats
        assert "total_examples" in stats
        assert stats["total_roles"] == 5  # 2 + 3
        assert stats["total_examples"] == 1

        # Test with lazy loading
        loader = PropBankLoader(sample_jsonl_file, lazy=True, autoload=False)
        stats = loader.get_statistics()

        assert stats["total_framesets"] == 2
        assert stats["total_rolesets"] == 2
        assert stats["lazy_loading"] is True
        # In lazy mode, these stats are not available
        assert "total_roles" not in stats
        assert "total_examples" not in stats

    def test_resolve_cross_references(self, sample_jsonl_file):
        """Test cross-reference resolution."""
        loader = PropBankLoader(sample_jsonl_file)
        roleset = loader.get_roleset("abandon.01")

        # Cross-references should be resolved
        assert roleset is not None
        assert len(roleset.roles[0].rolelinks) == 1
        assert roleset.roles[0].rolelinks[0].class_name == "leave-51.2"

        assert len(roleset.lexlinks) == 1
        assert roleset.lexlinks[0].confidence == 0.95

    def test_invalid_json_handling(self):
        """Test handling of invalid JSON in file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            f.write('{"valid": "json"}\n')
            f.write("invalid json\n")
            f.write('{"another": "valid"}\n')
            temp_path = Path(f.name)

        try:
            loader = PropBankLoader(temp_path, autoload=False)
            # Should build indices despite invalid line
            assert len(loader.frameset_index) >= 0

            # Load should raise on invalid JSON
            with pytest.raises(ValueError, match="Error parsing line"):
                loader.load()
        finally:
            temp_path.unlink(missing_ok=True)

    def test_empty_file_handling(self):
        """Test handling of empty file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            temp_path = Path(f.name)

        try:
            loader = PropBankLoader(temp_path)
            assert len(loader.frameset_index) == 0
            assert len(loader.roleset_index) == 0

            framesets = loader.load()
            assert len(framesets) == 0
        finally:
            temp_path.unlink(missing_ok=True)


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    @pytest.fixture
    def sample_jsonl_file(self):
        """Create a temporary JSON Lines file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            data = {
                "predicate_lemma": "test",
                "rolesets": [
                    {
                        "id": "test.01",
                        "name": "testing",
                        "roles": [],
                        "examples": [],
                    }
                ],
            }
            json.dump(data, f)
            f.write("\n")
            temp_path = Path(f.name)

        yield temp_path
        temp_path.unlink(missing_ok=True)

    def test_load_framesets(self, sample_jsonl_file):
        """Test load_framesets convenience function."""
        framesets = load_framesets(sample_jsonl_file)

        assert len(framesets) == 1
        assert "test" in framesets
        assert framesets["test"].predicate_lemma == "test"

    def test_load_frameset(self, sample_jsonl_file):
        """Test load_frameset convenience function."""
        frameset = load_frameset(sample_jsonl_file, "test")

        assert frameset is not None
        assert frameset.predicate_lemma == "test"
        assert len(frameset.rolesets) == 1

        # Test non-existent predicate
        frameset = load_frameset(sample_jsonl_file, "nonexistent")
        assert frameset is None
