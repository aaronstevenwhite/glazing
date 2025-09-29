"""Tests for PropBank type definitions.

Tests PropBank-specific type literals and validation patterns.
Validates that expected values are accepted and invalid values are rejected.

Classes
-------
TestArgumentNumber
    Tests for ArgumentNumber type literals.
TestFunctionTag
    Tests for FunctionTag type literals.
TestAliasPOS
    Tests for AliasPOS type literals.
TestArgumentTypePB
    Tests for ArgumentTypePB type literals.
TestUsageInUse
    Tests for UsageInUse type literals.
TestValidationPatterns
    Tests for regex validation patterns.
TestTypeIntegration
    Integration tests for PropBank types.
"""

import re

from glazing.propbank.types import (
    PREDICATE_LEMMA_PATTERN,
    ROLESET_ID_PATTERN,
    AliasPOS,
    ArgumentNumber,
    ArgumentTypePB,
    FunctionTag,
    PredicateLemma,
    RolesetID,
    UsageInUse,
)


class TestArgumentNumber:
    """Test cases for ArgumentNumber type."""

    def test_valid_argument_numbers(self) -> None:
        """Test all valid argument numbers."""
        valid_args = ["0", "1", "2", "3", "4", "5", "6", "m", "M"]
        for arg in valid_args:
            # This would be validated at runtime by Pydantic models
            assert arg in ArgumentNumber.__value__.__args__

    def test_argument_number_completeness(self) -> None:
        """Test that all expected argument numbers are included."""
        expected = {"0", "1", "2", "3", "4", "5", "6", "m", "M"}
        actual = set(ArgumentNumber.__value__.__args__)
        assert actual == expected


class TestFunctionTag:
    """Test cases for FunctionTag type."""

    def test_standard_function_tags(self) -> None:
        """Test standard PropBank function tags."""
        standard_tags = [
            "ADJ",
            "ADV",
            "CAU",
            "COM",
            "DIR",
            "DIS",
            "DSP",
            "EXT",
            "GOL",
            "LOC",
            "LVB",
            "MNR",
            "MOD",
            "NEG",
            "PAG",
            "PNC",
            "PPT",
            "PRD",
            "PRP",
            "PRR",
            "PRX",
            "REC",
            "RCL",
            "SLC",
            "TMP",
            "VSP",
            "CXN",
        ]

        for tag in standard_tags:
            assert tag in FunctionTag.__value__.__args__

    def test_spatial_function_tags(self) -> None:
        """Test spatial relation function tags."""
        spatial_tags = [
            "ANC",
            "ANC1",
            "ANC2",
            "ANG",
            "AXS",
            "AXSp",
            "AXSc",
            "AXS1",
            "AXS2",
            "WHL",
            "SEQ",
            "PSN",
            "SET",
            "SRC",
            "PRT",
            "DOM",
            "SCL",
            "SE1",
            "SE2",
            "SE3",
            "SE4",
            "SE5",
            "SE6",
        ]

        for tag in spatial_tags:
            assert tag in FunctionTag.__value__.__args__

    def test_lowercase_function_tags(self) -> None:
        """Test lowercase variant function tags."""
        lowercase_tags = [
            "adv",
            "tmp",
            "pag",
            "ppt",
            "gol",
            "vsp",
            "com",
            "adj",
            "cau",
            "prp",
            "rec",
            "mnr",
            "ext",
            "loc",
            "dir",
            "prd",
        ]

        for tag in lowercase_tags:
            assert tag in FunctionTag.__value__.__args__

    def test_function_tag_count(self) -> None:
        """Test that we have the expected number of function tags."""
        expected_count = 75  # Actual count from FunctionTag type
        assert len(FunctionTag.__value__.__args__) == expected_count


class TestAliasPOS:
    """Test cases for AliasPOS type."""

    def test_valid_alias_pos(self) -> None:
        """Test all valid alias POS tags."""
        valid_pos = ["r", "p", "v", "n", "j", "l", "x", "m", "d", "f"]
        for pos in valid_pos:
            assert pos in AliasPOS.__value__.__args__

    def test_alias_pos_completeness(self) -> None:
        """Test alias POS completeness."""
        expected = {"r", "p", "v", "n", "j", "l", "x", "m", "d", "f"}
        actual = set(AliasPOS.__value__.__args__)
        assert actual == expected


class TestArgumentTypePB:
    """Test cases for ArgumentTypePB type."""

    def test_core_arguments(self) -> None:
        """Test core argument types."""
        core_args = ["ARG0", "ARG1", "ARG2", "ARG3", "ARG4", "ARG5", "ARG6", "ARGA"]
        for arg in core_args:
            assert arg in ArgumentTypePB.__value__.__args__

    def test_continuation_arguments(self) -> None:
        """Test continuation argument types."""
        cont_args = ["C-ARG0", "C-ARG1", "C-ARG2", "C-ARG3", "C-ARG4", "C-ARG5", "C-ARG6"]
        for arg in cont_args:
            assert arg in ArgumentTypePB.__value__.__args__

    def test_reference_arguments(self) -> None:
        """Test reference argument types."""
        ref_args = ["R-ARG0", "R-ARG1", "R-ARG2", "R-ARG3", "R-ARG4", "R-ARG5", "R-ARG6"]
        for arg in ref_args:
            assert arg in ArgumentTypePB.__value__.__args__

    def test_modifier_arguments(self) -> None:
        """Test modifier argument types."""
        mod_args = [
            "ARGM-ADJ",
            "ARGM-ADV",
            "ARGM-CAU",
            "ARGM-COM",
            "ARGM-DIR",
            "ARGM-DIS",
            "ARGM-DSP",
            "ARGM-EXT",
            "ARGM-GOL",
            "ARGM-LOC",
            "ARGM-LVB",
            "ARGM-MNR",
            "ARGM-MOD",
            "ARGM-NEG",
            "ARGM-PNC",
            "ARGM-PRD",
            "ARGM-PRP",
            "ARGM-PRR",
            "ARGM-PRX",
            "ARGM-REC",
            "ARGM-TMP",
            "ARGM-CXN",
        ]
        for arg in mod_args:
            assert arg in ArgumentTypePB.__value__.__args__

    def test_continuation_modifiers(self) -> None:
        """Test continuation modifier types."""
        cont_mods = [
            "C-ARGM-ADJ",
            "C-ARGM-ADV",
            "C-ARGM-CAU",
            "C-ARGM-COM",
            "C-ARGM-DIR",
            "C-ARGM-DIS",
            "C-ARGM-DSP",
            "C-ARGM-EXT",
            "C-ARGM-LOC",
            "C-ARGM-MNR",
            "C-ARGM-MOD",
            "C-ARGM-NEG",
            "C-ARGM-PRP",
            "C-ARGM-TMP",
            "C-ARGM-CXN",
        ]
        for arg in cont_mods:
            assert arg in ArgumentTypePB.__value__.__args__

    def test_reference_modifiers(self) -> None:
        """Test reference modifier types."""
        ref_mods = [
            "R-ARGM-ADV",
            "R-ARGM-CAU",
            "R-ARGM-COM",
            "R-ARGM-DIR",
            "R-ARGM-EXT",
            "R-ARGM-GOL",
            "R-ARGM-LOC",
            "R-ARGM-MNR",
            "R-ARGM-MOD",
            "R-ARGM-PNC",
            "R-ARGM-PRD",
            "R-ARGM-PRP",
            "R-ARGM-TMP",
        ]
        for arg in ref_mods:
            assert arg in ArgumentTypePB.__value__.__args__

    def test_argument_type_count(self) -> None:
        """Test total argument type count."""
        expected_count = 73
        assert len(ArgumentTypePB.__value__.__args__) == expected_count


class TestUsageInUse:
    """Test cases for UsageInUse type."""

    def test_valid_usage_values(self) -> None:
        """Test valid usage status values."""
        valid_usage = ["+", "-"]
        for usage in valid_usage:
            assert usage in UsageInUse.__value__.__args__

    def test_usage_completeness(self) -> None:
        """Test usage type completeness."""
        expected = {"+", "-"}
        actual = set(UsageInUse.__value__.__args__)
        assert actual == expected


class TestValidationPatterns:
    """Test cases for validation patterns."""

    def test_roleset_id_pattern(self) -> None:
        """Test RolesetID validation pattern."""
        # Valid roleset IDs
        valid_ids = [
            "abandon.01",
            "give.01",
            "be-located-at.91",
            "multi-word.02",
            "test_id.99",
        ]

        for valid_id in valid_ids:
            assert re.match(ROLESET_ID_PATTERN, valid_id), f"Should match: {valid_id}"

        # Invalid roleset IDs
        invalid_ids = [
            "abandon",  # Missing sense number
            "abandon.01.02",  # Extra part after sense
            ".01",  # Missing predicate
            "abandon.",  # Missing sense number
            "123abandon.01",  # Starting with number
            "abandon.0a",  # Non-numeric sense
            "complex.name.03",  # Contains dots in predicate part
        ]

        for invalid_id in invalid_ids:
            assert not re.match(ROLESET_ID_PATTERN, invalid_id), f"Should not match: {invalid_id}"

    def test_predicate_lemma_pattern(self) -> None:
        """Test PredicateLemma validation pattern."""
        # Valid predicate lemmas
        valid_lemmas = [
            "abandon",
            "give",
            "be-located-at",
            "multi-word",
            "test_predicate",
            "word123",
        ]

        for valid_lemma in valid_lemmas:
            assert re.match(PREDICATE_LEMMA_PATTERN, valid_lemma), f"Should match: {valid_lemma}"

        # Invalid predicate lemmas
        invalid_lemmas = [
            "123abandon",  # Starting with number
            "abandon.01",  # Contains dot
            "-abandon",  # Starting with hyphen
            "_abandon",  # Starting with underscore
            "abandon$",  # Invalid character
        ]

        for invalid_lemma in invalid_lemmas:
            msg = f"Should not match: {invalid_lemma}"
            assert not re.match(PREDICATE_LEMMA_PATTERN, invalid_lemma), msg


class TestTypeIntegration:
    """Integration tests for PropBank types."""

    def test_type_imports(self) -> None:
        """Test that all types can be imported successfully."""
        # Test imports work correctly
        assert ArgumentNumber is not None
        assert FunctionTag is not None
        assert AliasPOS is not None
        assert ArgumentTypePB is not None
        assert UsageInUse is not None
        assert RolesetID is not None
        assert PredicateLemma is not None

    def test_pattern_constants(self) -> None:
        """Test that pattern constants are accessible."""

        assert ROLESET_ID_PATTERN is not None
        assert PREDICATE_LEMMA_PATTERN is not None
        assert isinstance(ROLESET_ID_PATTERN, str)
        assert isinstance(PREDICATE_LEMMA_PATTERN, str)

    def test_realistic_values(self) -> None:
        """Test with realistic PropBank values."""
        # Test ArgumentNumber
        for example in ["0", "1", "2", "M"]:
            assert example in ArgumentNumber.__value__.__args__

        # Test FunctionTag
        for example in ["PAG", "PPT", "TMP", "LOC", "MNR"]:
            assert example in FunctionTag.__value__.__args__

        # Test AliasPOS
        for example in ["v", "n", "j"]:
            assert example in AliasPOS.__value__.__args__

        # Test ArgumentTypePB
        for example in ["ARG0", "ARG1", "ARGM-TMP", "C-ARG0", "R-ARGM-LOC"]:
            assert example in ArgumentTypePB.__value__.__args__

        # Test UsageInUse
        for example in ["+", "-"]:
            assert example in UsageInUse.__value__.__args__
