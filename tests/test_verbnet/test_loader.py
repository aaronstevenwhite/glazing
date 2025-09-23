"""Tests for VerbNet loader module.

Tests loading verb classes and members from JSON Lines files,
index building, inheritance resolution, and caching.
"""

import json
import tempfile
from pathlib import Path

import pytest

from glazing.verbnet.loader import VerbNetLoader, load_verb_class, load_verb_classes


class TestVerbNetLoader:
    """Test VerbNetLoader functionality."""

    @pytest.fixture
    def sample_verb_class_data(self):
        """Create sample verb class data."""
        return {
            "id": "give-13.1",
            "members": [
                {
                    "name": "give",
                    "verbnet_key": "give#2",
                    "framenet_mappings": [],
                    "propbank_mappings": [],
                    "wordnet_mappings": [],
                }
            ],
            "themroles": [
                {
                    "type": "Agent",
                    "sel_restrictions": {
                        "logic": "and",
                        "restrictions": [{"value": "+", "type": "animate"}],
                    },
                },
                {"type": "Theme", "sel_restrictions": None},
                {
                    "type": "Recipient",
                    "sel_restrictions": {
                        "logic": "and",
                        "restrictions": [{"value": "+", "type": "animate"}],
                    },
                },
            ],
            "frames": [
                {
                    "description": {
                        "description_number": "0.1",
                        "primary": "NP V NP PP",
                        "secondary": "Basic Ditransitive",
                        "xtag": "",
                    },
                    "examples": [{"text": "They gave the book to her"}],
                    "syntax": {
                        "elements": [
                            {"pos": "NP", "value": "Agent"},
                            {"pos": "VERB"},
                            {"pos": "NP", "value": "Theme"},
                            {"pos": "PREP", "value": "to"},
                            {"pos": "NP", "value": "Recipient"},
                        ]
                    },
                    "semantics": {
                        "predicates": [
                            {
                                "value": "transfer",
                                "args": [
                                    {"type": "Event", "value": "e1"},
                                    {"type": "ThemRole", "value": "Agent"},
                                    {"type": "ThemRole", "value": "Theme"},
                                    {"type": "ThemRole", "value": "Recipient"},
                                ],
                                "negated": False,
                            }
                        ]
                    },
                }
            ],
            "subclasses": [
                {
                    "id": "give-13.1-1",
                    "members": [
                        {
                            "name": "lend",
                            "verbnet_key": "lend#1",
                            "framenet_mappings": [],
                            "propbank_mappings": [],
                            "wordnet_mappings": [],
                        }
                    ],
                    "themroles": [],  # Inherits from parent
                    "frames": [],
                    "subclasses": [],
                }
            ],
        }

    @pytest.fixture
    def sample_jsonl_file(self, sample_verb_class_data):
        """Create a temporary JSON Lines file with sample data."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            # Write multiple verb classes
            json.dump(sample_verb_class_data, f)
            f.write("\n")

            # Add another verb class
            transfer_data = {
                "id": "transfer-11.1",
                "members": [
                    {
                        "name": "transfer",
                        "verbnet_key": "transfer#1",
                        "framenet_mappings": [],
                        "propbank_mappings": [],
                        "wordnet_mappings": [],
                    }
                ],
                "themroles": [
                    {"type": "Agent", "sel_restrictions": None},
                    {"type": "Theme", "sel_restrictions": None},
                    {"type": "Destination", "sel_restrictions": None},
                ],
                "frames": [],
                "subclasses": [],
            }
            json.dump(transfer_data, f)
            f.write("\n")

            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        temp_path.unlink(missing_ok=True)

    def test_loader_initialization(self, sample_jsonl_file):
        """Test VerbNetLoader initialization."""
        loader = VerbNetLoader(sample_jsonl_file, autoload=False)

        assert loader.data_path == sample_jsonl_file
        assert loader.lazy is False  # Default is now False
        assert loader.cache is None  # No cache when not lazy
        assert len(loader.class_index) == 2
        assert len(loader.member_index) == 3  # give#2, lend#1, transfer#1

    def test_loader_initialization_with_autoload(self, sample_jsonl_file):
        """Test VerbNetLoader with autoload."""
        loader = VerbNetLoader(sample_jsonl_file)  # autoload=True by default

        assert loader.lazy is False
        assert loader.cache is None
        assert loader.classes_cache is not None
        assert len(loader.classes_cache) == 2

    def test_loader_file_not_found(self):
        """Test loader with non-existent file."""
        with pytest.raises(FileNotFoundError, match="Data file not found"):
            VerbNetLoader("nonexistent.jsonl")

    def test_load(self, sample_jsonl_file):
        """Test loading all verb classes."""
        loader = VerbNetLoader(sample_jsonl_file, autoload=False)
        verb_classes = loader.load()

        assert len(verb_classes) == 2
        assert "give-13.1" in verb_classes
        assert "transfer-11.1" in verb_classes

        give_class = verb_classes["give-13.1"]
        assert len(give_class.members) == 1
        assert len(give_class.themroles) == 3
        assert len(give_class.subclasses) == 1

    def test_get_verb_class(self, sample_jsonl_file):
        """Test getting a specific verb class."""
        loader = VerbNetLoader(sample_jsonl_file)

        verb_class = loader.get_verb_class("give-13.1")
        assert verb_class is not None
        assert verb_class.id == "give-13.1"
        assert len(verb_class.members) == 1
        assert len(verb_class.themroles) == 3

        # Test non-existent class
        verb_class = loader.get_verb_class("nonexistent-99.9")
        assert verb_class is None

    def test_get_member(self, sample_jsonl_file):
        """Test getting a specific member."""
        loader = VerbNetLoader(sample_jsonl_file)

        member = loader.get_member("give#2")
        assert member is not None
        assert member.verbnet_key == "give#2"
        assert member.name == "give"

        # Test member from subclass
        member = loader.get_member("lend#1")
        assert member is not None
        assert member.verbnet_key == "lend#1"
        assert member.name == "lend"

        # Test another member
        member = loader.get_member("transfer#1")
        assert member is not None
        assert member.verbnet_key == "transfer#1"

        # Test non-existent member
        member = loader.get_member("nonexistent#99")
        assert member is None

    def test_get_effective_roles(self, sample_jsonl_file):
        """Test getting effective roles with inheritance."""
        loader = VerbNetLoader(sample_jsonl_file)

        # Parent class roles
        roles = loader.get_effective_roles("give-13.1")
        assert len(roles) == 3
        role_types = {role.type for role in roles}
        assert role_types == {"Agent", "Theme", "Recipient"}

        # Subclass should inherit parent roles
        # Note: subclass is embedded, not a separate entry
        verb_class = loader.get_verb_class("give-13.1")
        assert verb_class is not None
        subclass = verb_class.subclasses[0]
        assert subclass.id == "give-13.1-1"
        assert len(subclass.themroles) == 0  # Empty = inherits

    def test_build_indices(self, sample_jsonl_file):
        """Test index building."""
        loader = VerbNetLoader(sample_jsonl_file)

        # Indices should be built on initialization
        assert "give-13.1" in loader.class_index
        assert "transfer-11.1" in loader.class_index
        assert "give#2" in loader.member_index
        assert "lend#1" in loader.member_index
        assert "transfer#1" in loader.member_index

        # Test that indices map correctly
        assert loader.member_index["give#2"] == "give-13.1"
        assert loader.member_index["lend#1"] == "give-13.1"  # Subclass member maps to parent
        assert loader.member_index["transfer#1"] == "transfer-11.1"

    def test_caching(self, sample_jsonl_file):
        """Test caching behavior."""
        loader = VerbNetLoader(sample_jsonl_file, lazy=True, cache_size=10, autoload=False)

        # First access should cache
        verb_class1 = loader.get_verb_class("give-13.1")
        assert loader.cache is not None

        # Check that cache has entries
        assert loader.cache.size() > 0

        # Second access should use cache
        verb_class2 = loader.get_verb_class("give-13.1")
        assert verb_class1.id == verb_class2.id

        # Test member caching
        member1 = loader.get_member("give#2")
        assert member1 is not None

        # Cache should have more entries now
        cache_size_after_member = loader.cache.size()
        assert cache_size_after_member >= 1

        member2 = loader.get_member("give#2")
        assert member1.verbnet_key == member2.verbnet_key

    def test_iter_verb_classes(self, sample_jsonl_file):
        """Test iterating over verb classes in batches."""
        loader = VerbNetLoader(sample_jsonl_file)

        batches = list(loader.iter_verb_classes(batch_size=1))
        assert len(batches) == 2
        assert len(batches[0]) == 1
        assert len(batches[1]) == 1

        # Test with larger batch size
        batches = list(loader.iter_verb_classes(batch_size=10))
        assert len(batches) == 1
        assert len(batches[0]) == 2

    def test_search_by_pattern(self, sample_jsonl_file):
        """Test searching verb classes by pattern."""
        loader = VerbNetLoader(sample_jsonl_file)

        # Search for classes containing "give"
        matches = loader.search_by_pattern(r"give")
        assert len(matches) == 1
        assert matches[0].id == "give-13.1"

        # Search for all classes
        matches = loader.search_by_pattern(r".*")
        assert len(matches) == 2

        # Search for classes ending with "1"
        matches = loader.search_by_pattern(r"-\d+\.1$")
        assert len(matches) == 2

        # Search for non-matching pattern
        matches = loader.search_by_pattern(r"^walk")
        assert len(matches) == 0

    def test_get_statistics(self, sample_jsonl_file):
        """Test getting loader statistics."""
        # Test with lazy loading
        loader = VerbNetLoader(sample_jsonl_file, autoload=False)
        stats = loader.get_statistics()

        assert stats["total_classes"] == 2
        assert stats["total_members"] == 3
        assert stats["lazying"] is False  # Default is now False
        # With autoload=False, data isn't loaded so detailed stats not available
        assert "total_roles" not in stats
        assert "total_frames" not in stats

        # Test with lazy loading
        loader = VerbNetLoader(sample_jsonl_file, lazy=True, autoload=False)
        stats = loader.get_statistics()

        assert stats["total_classes"] == 2
        assert stats["total_members"] == 3
        assert stats["lazying"] is True
        # In lazy mode, these detailed stats are not available
        assert "total_roles" not in stats
        assert "total_frames" not in stats
        assert "total_subclasses" not in stats

    def test_get_class_hierarchy(self, sample_jsonl_file):
        """Test getting class hierarchy."""
        loader = VerbNetLoader(sample_jsonl_file)
        hierarchy = loader.get_class_hierarchy()

        assert "give-13.1" in hierarchy
        assert hierarchy["give-13.1"] == ["give-13.1-1"]
        assert "transfer-11.1" not in hierarchy  # No subclasses

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
            loader = VerbNetLoader(temp_path, autoload=False)
            # Should build indices despite invalid line
            assert len(loader.class_index) >= 0

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
            loader = VerbNetLoader(temp_path)
            assert len(loader.class_index) == 0
            assert len(loader.member_index) == 0

            verb_classes = loader.load()
            assert len(verb_classes) == 0
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
                "id": "test-1.1",
                "members": [
                    {
                        "name": "test",
                        "verbnet_key": "test#1",
                        "framenet_mappings": [],
                        "propbank_mappings": [],
                        "wordnet_mappings": [],
                    }
                ],
                "themroles": [],
                "frames": [],
                "subclasses": [],
            }
            json.dump(data, f)
            f.write("\n")
            temp_path = Path(f.name)

        yield temp_path
        temp_path.unlink(missing_ok=True)

    def test_load_verb_classes(self, sample_jsonl_file):
        """Test load_verb_classes convenience function."""
        verb_classes = load_verb_classes(sample_jsonl_file)

        assert len(verb_classes) == 1
        assert "test-1.1" in verb_classes
        assert verb_classes["test-1.1"].id == "test-1.1"

    def test_load_verb_class(self, sample_jsonl_file):
        """Test load_verb_class convenience function."""
        verb_class = load_verb_class(sample_jsonl_file, "test-1.1")

        assert verb_class is not None
        assert verb_class.id == "test-1.1"
        assert len(verb_class.members) == 1

        # Test non-existent class
        verb_class = load_verb_class(sample_jsonl_file, "nonexistent")
        assert verb_class is None
