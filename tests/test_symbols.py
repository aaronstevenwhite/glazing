"""Tests for base symbol models.

This module tests the BaseSymbol class and normalization utilities
from the symbols module.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from glazing.symbols import BaseSymbol


class TestBaseSymbol:
    """Test the BaseSymbol base class."""

    def test_basic_creation(self) -> None:
        """Test creating a basic symbol."""
        symbol = BaseSymbol(
            raw_string="Test Symbol",
            normalized="test_symbol",
            symbol_type="frame",
            dataset="framenet",
        )
        assert symbol.raw_string == "Test Symbol"
        assert symbol.normalized == "test_symbol"
        assert symbol.symbol_type == "frame"
        assert symbol.dataset == "framenet"
        assert symbol.confidence == 1.0

    def test_custom_confidence(self) -> None:
        """Test creating symbol with custom confidence."""
        symbol = BaseSymbol(
            raw_string="Test",
            normalized="test",
            symbol_type="synset",
            dataset="wordnet",
            confidence=0.85,
        )
        assert symbol.confidence == 0.85

    def test_invalid_normalized_uppercase(self) -> None:
        """Test that uppercase in normalized field raises error."""
        with pytest.raises(ValidationError, match="must be lowercase"):
            BaseSymbol(
                raw_string="Test",
                normalized="Test",  # Should be lowercase
                symbol_type="frame",
                dataset="framenet",
            )

    def test_invalid_normalized_spaces(self) -> None:
        """Test that spaces in normalized field raises error."""
        with pytest.raises(ValidationError, match="cannot contain spaces"):
            BaseSymbol(
                raw_string="Test Symbol",
                normalized="test symbol",  # Should use underscores
                symbol_type="frame",
                dataset="framenet",
            )

    def test_invalid_normalized_consecutive_underscores(self) -> None:
        """Test that consecutive underscores raise error."""
        with pytest.raises(ValidationError, match="cannot have consecutive underscores"):
            BaseSymbol(
                raw_string="Test",
                normalized="test__symbol",  # Double underscore
                symbol_type="frame",
                dataset="framenet",
            )

    def test_invalid_normalized_leading_underscore(self) -> None:
        """Test that leading underscore raises error."""
        with pytest.raises(ValidationError, match="cannot start/end with underscore"):
            BaseSymbol(
                raw_string="Test",
                normalized="_test",
                symbol_type="frame",
                dataset="framenet",
            )

    def test_invalid_normalized_trailing_underscore(self) -> None:
        """Test that trailing underscore raises error."""
        with pytest.raises(ValidationError, match="cannot start/end with underscore"):
            BaseSymbol(
                raw_string="Test",
                normalized="test_",
                symbol_type="frame",
                dataset="framenet",
            )

    def test_invalid_confidence_too_high(self) -> None:
        """Test that confidence > 1.0 raises error."""
        with pytest.raises(ValidationError):
            BaseSymbol(
                raw_string="Test",
                normalized="test",
                symbol_type="frame",
                dataset="framenet",
                confidence=1.5,
            )

    def test_invalid_confidence_negative(self) -> None:
        """Test that negative confidence raises error."""
        with pytest.raises(ValidationError):
            BaseSymbol(
                raw_string="Test",
                normalized="test",
                symbol_type="frame",
                dataset="framenet",
                confidence=-0.1,
            )

    def test_empty_raw_string(self) -> None:
        """Test that empty raw_string raises error."""
        with pytest.raises(ValidationError):
            BaseSymbol(
                raw_string="",  # Empty not allowed
                normalized="test",
                symbol_type="frame",
                dataset="framenet",
            )

    def test_empty_normalized(self) -> None:
        """Test that empty normalized raises error."""
        with pytest.raises(ValidationError):
            BaseSymbol(
                raw_string="Test",
                normalized="",  # Empty not allowed
                symbol_type="frame",
                dataset="framenet",
            )


class TestNormalizeString:
    """Test the normalize_string class method."""

    def test_simple_normalization(self) -> None:
        """Test basic string normalization."""
        assert BaseSymbol.normalize_string("Test") == "test"
        assert BaseSymbol.normalize_string("TEST") == "test"
        assert BaseSymbol.normalize_string("test") == "test"

    def test_space_normalization(self) -> None:
        """Test normalizing spaces to underscores."""
        assert BaseSymbol.normalize_string("Test Symbol") == "test_symbol"
        assert BaseSymbol.normalize_string("Multi Word String") == "multi_word_string"

    def test_hyphen_normalization(self) -> None:
        """Test normalizing hyphens to underscores."""
        assert BaseSymbol.normalize_string("test-symbol") == "test_symbol"
        assert BaseSymbol.normalize_string("multi-part-name") == "multi_part_name"

    def test_multiple_spaces(self) -> None:
        """Test collapsing multiple spaces."""
        assert BaseSymbol.normalize_string("test  symbol") == "test_symbol"
        assert BaseSymbol.normalize_string("test   symbol") == "test_symbol"

    def test_multiple_underscores(self) -> None:
        """Test collapsing multiple underscores."""
        assert BaseSymbol.normalize_string("test__symbol") == "test_symbol"
        assert BaseSymbol.normalize_string("test___symbol") == "test_symbol"

    def test_leading_trailing_spaces(self) -> None:
        """Test stripping leading/trailing spaces."""
        assert BaseSymbol.normalize_string(" test ") == "test"
        assert BaseSymbol.normalize_string("  test  ") == "test"

    def test_leading_trailing_underscores(self) -> None:
        """Test stripping leading/trailing underscores."""
        assert BaseSymbol.normalize_string("_test_") == "test"
        assert BaseSymbol.normalize_string("__test__") == "test"

    def test_mixed_separators(self) -> None:
        """Test normalizing mixed spaces and hyphens."""
        assert BaseSymbol.normalize_string("test-symbol name") == "test_symbol_name"
        assert BaseSymbol.normalize_string("test - symbol") == "test_symbol"

    def test_real_world_examples(self) -> None:
        """Test normalization with real-world examples."""
        # FrameNet examples
        assert BaseSymbol.normalize_string("Cause_motion") == "cause_motion"
        assert BaseSymbol.normalize_string("Being_born") == "being_born"

        # PropBank examples
        assert BaseSymbol.normalize_string("give.01") == "give.01"
        assert BaseSymbol.normalize_string("ARG0-PPT") == "arg0_ppt"

        # VerbNet examples
        assert BaseSymbol.normalize_string("Agent") == "agent"
        assert BaseSymbol.normalize_string("?Theme_I") == "?theme_i"

        # WordNet examples
        assert BaseSymbol.normalize_string("physical_entity") == "physical_entity"
        assert BaseSymbol.normalize_string("living thing") == "living_thing"

    def test_empty_string_raises_error(self) -> None:
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="normalizes to empty"):
            BaseSymbol.normalize_string("")

    def test_only_spaces_raises_error(self) -> None:
        """Test that string with only spaces raises ValueError."""
        with pytest.raises(ValueError, match="normalizes to empty"):
            BaseSymbol.normalize_string("   ")

    def test_only_underscores_raises_error(self) -> None:
        """Test that string with only underscores raises ValueError."""
        with pytest.raises(ValueError, match="normalizes to empty"):
            BaseSymbol.normalize_string("___")

    def test_only_hyphens_raises_error(self) -> None:
        """Test that string with only hyphens raises ValueError."""
        with pytest.raises(ValueError, match="normalizes to empty"):
            BaseSymbol.normalize_string("---")


class TestValidSymbolTypes:
    """Test that only valid symbol types are accepted."""

    def test_valid_symbol_types(self) -> None:
        """Test all valid symbol types."""
        valid_types = [
            "frame",
            "frame_element",
            "frame_relation",
            "roleset",
            "argument",
            "verb_class",
            "thematic_role",
            "synset",
            "sense_key",
            "lemma_key",
        ]

        for symbol_type in valid_types:
            symbol = BaseSymbol(
                raw_string="test",
                normalized="test",
                symbol_type=symbol_type,  # type: ignore[arg-type]
                dataset="framenet",
            )
            assert symbol.symbol_type == symbol_type

    def test_invalid_symbol_type(self) -> None:
        """Test that invalid symbol type raises error."""
        with pytest.raises(ValidationError):
            BaseSymbol(
                raw_string="test",
                normalized="test",
                symbol_type="invalid_type",  # type: ignore[arg-type]
                dataset="framenet",
            )


class TestValidDatasetNames:
    """Test that only valid dataset names are accepted."""

    def test_valid_dataset_names(self) -> None:
        """Test all valid dataset names."""
        valid_datasets = ["framenet", "propbank", "verbnet", "wordnet"]

        for dataset in valid_datasets:
            symbol = BaseSymbol(
                raw_string="test",
                normalized="test",
                symbol_type="frame",
                dataset=dataset,  # type: ignore[arg-type]
            )
            assert symbol.dataset == dataset

    def test_invalid_dataset_name(self) -> None:
        """Test that invalid dataset name raises error."""
        with pytest.raises(ValidationError):
            BaseSymbol(
                raw_string="test",
                normalized="test",
                symbol_type="frame",
                dataset="invalid_dataset",  # type: ignore[arg-type]
            )
