"""Tests for PropBank symbol parser.

This module tests the parsing utilities for PropBank roleset IDs and argument
symbols, including core arguments, modifier arguments, and special prefixes.
"""

from __future__ import annotations

import pytest

from glazing.propbank.models import Role
from glazing.propbank.symbol_parser import (
    extract_arg_number,
    extract_function_tag,
    extract_modifier_type,
    filter_args_by_properties,
    is_core_argument,
    is_modifier,
    parse_argument,
    parse_roleset_id,
)


class TestParseRolesetID:
    """Test parsing of PropBank roleset IDs."""

    def test_simple_roleset(self) -> None:
        """Test parsing simple roleset IDs."""
        result = parse_roleset_id("give.01")
        assert result.raw_string == "give.01"
        assert result.normalized == "give.01"
        assert result.lemma == "give"
        assert result.sense_number == 1

    def test_various_sense_numbers(self) -> None:
        """Test parsing rolesets with different sense numbers."""
        result = parse_roleset_id("run.00")
        assert result.sense_number == 0

        result = parse_roleset_id("take.99")
        assert result.sense_number == 99

    def test_underscore_lemma(self) -> None:
        """Test parsing rolesets with underscores in lemma."""
        result = parse_roleset_id("take_over.01")
        assert result.lemma == "take_over"
        assert result.sense_number == 1
        assert result.normalized == "take_over.01"

    def test_case_normalization(self) -> None:
        """Test that roleset IDs are normalized to lowercase."""
        result = parse_roleset_id("GIVE.01")
        assert result.normalized == "give.01"
        assert result.lemma == "give"


class TestParseArgument:
    """Test parsing of PropBank argument symbols."""

    def test_core_arguments(self) -> None:
        """Test parsing core arguments ARG0-7."""
        # ARG0
        result = parse_argument("ARG0")
        assert result.raw_string == "ARG0"
        assert result.arg_number == "0"
        assert result.modifier_type is None
        assert result.prefix is None
        assert result.arg_type == "core"

        # ARG1 through ARG5 (PropBank typically uses 0-5)
        for i in range(1, 6):
            arg = f"ARG{i}"
            result = parse_argument(arg)
            assert result.arg_number == str(i)
            assert result.arg_type == "core"

    def test_special_argument(self) -> None:
        """Test parsing ARGA special argument."""
        result = parse_argument("ARGA")
        assert result.raw_string == "ARGA"
        assert result.arg_number == "a"  # ARGA has "a" as its number
        assert result.arg_type == "core"  # ARGA is treated as a core argument

    def test_modifier_arguments(self) -> None:
        """Test parsing modifier arguments ARGM-*."""
        # ARGM-LOC
        result = parse_argument("ARGM-LOC")
        assert result.raw_string == "ARGM-LOC"
        assert result.arg_number is None
        assert result.modifier_type == "loc"
        assert result.prefix is None
        assert result.arg_type == "modifier"

        # Other common modifiers
        modifiers = ["TMP", "MNR", "CAU", "PRP", "DIR", "DIS", "ADV", "MOD", "NEG"]
        for mod in modifiers:
            arg = f"ARGM-{mod}"
            result = parse_argument(arg)
            assert result.modifier_type == mod.lower()
            assert result.arg_type == "modifier"

    def test_continuation_arguments(self) -> None:
        """Test parsing continuation arguments with C- prefix."""
        # C-ARG0
        result = parse_argument("C-ARG0")
        assert result.raw_string == "C-ARG0"
        assert result.arg_number == "0"
        assert result.prefix == "c"
        assert result.arg_type == "core"

        # C-ARGM-LOC
        result = parse_argument("C-ARGM-LOC")
        assert result.modifier_type == "loc"
        assert result.prefix == "c"
        assert result.arg_type == "modifier"

    def test_reference_arguments(self) -> None:
        """Test parsing reference arguments with R- prefix."""
        # R-ARG0
        result = parse_argument("R-ARG0")
        assert result.raw_string == "R-ARG0"
        assert result.arg_number == "0"
        assert result.prefix == "r"
        assert result.arg_type == "core"

        # R-ARGM-TMP
        result = parse_argument("R-ARGM-TMP")
        assert result.modifier_type == "tmp"
        assert result.prefix == "r"
        assert result.arg_type == "modifier"

    def test_function_tags(self) -> None:
        """Test parsing arguments with function tags."""
        result = parse_argument("ARG0-PPT")
        assert result.arg_number == "0"
        assert result.function_tag == "ppt"
        assert result.arg_type == "core"

        result = parse_argument("ARG1-PAG")
        assert result.arg_number == "1"
        assert result.function_tag == "pag"

    def test_case_insensitive(self) -> None:
        """Test that parsing is case insensitive."""
        result = parse_argument("arg0")
        assert result.arg_number == "0"
        assert result.arg_type == "core"

        result = parse_argument("argm-loc")
        assert result.modifier_type == "loc"
        assert result.arg_type == "modifier"


class TestExtractFunctions:
    """Test extraction helper functions."""

    def test_extract_arg_number(self) -> None:
        """Test extracting argument number."""
        assert extract_arg_number("ARG0") == "0"
        assert extract_arg_number("ARG5") == "5"
        assert extract_arg_number("C-ARG1") == "1"
        assert extract_arg_number("ARGA") == "a"  # ARGA has "a" as its number

        # Should raise ValueError for modifiers without numbers
        with pytest.raises(ValueError, match="Argument has no number"):
            extract_arg_number("ARGM-LOC")

    def test_extract_modifier_type(self) -> None:
        """Test extracting modifier type."""
        assert extract_modifier_type("ARGM-LOC") == "loc"
        assert extract_modifier_type("ARGM-TMP") == "tmp"
        assert extract_modifier_type("C-ARGM-CAU") == "cau"

        # Should raise ValueError for non-modifiers
        with pytest.raises(ValueError, match="Argument is not a modifier"):
            extract_modifier_type("ARG0")

    def test_extract_function_tag(self) -> None:
        """Test extracting function tag."""
        assert extract_function_tag("ARG0-PPT") == "ppt"
        assert extract_function_tag("ARG1-PAG") == "pag"

        # Should raise ValueError for arguments without function tags
        with pytest.raises(ValueError, match="Argument has no function tag"):
            extract_function_tag("ARG0")
        with pytest.raises(ValueError, match="Argument has no function tag"):
            extract_function_tag("ARGM-LOC")


class TestBooleanCheckers:
    """Test boolean checking functions."""

    def test_is_core_argument(self) -> None:
        """Test checking if argument is core."""
        assert is_core_argument("ARG0") is True
        assert is_core_argument("ARG5") is True
        assert is_core_argument("ARGA") is True  # ARGA is treated as core
        assert is_core_argument("ARGM-LOC") is False
        assert is_core_argument("C-ARG0") is True
        assert is_core_argument("R-ARG1") is True

    def test_is_modifier(self) -> None:
        """Test checking if argument is a modifier."""
        assert is_modifier("ARGM-LOC") is True
        assert is_modifier("ARGM-TMP") is True
        assert is_modifier("ARG0") is False
        assert is_modifier("ARGA") is False  # ARGA is core, not modifier
        assert is_modifier("C-ARGM-LOC") is True
        assert is_modifier("R-ARGM-TMP") is True


class TestFilterArgsByProperties:
    """Test filtering arguments by properties."""

    def create_test_roles(self) -> list[Role]:
        """Create test role instances with real PropBank structure."""
        # Based on real PropBank data structure from converted data

        roles = []

        # Core arguments like in give.01
        roles.append(Role(n="0", f="pag", descr="giver"))
        roles.append(Role(n="1", f="ppt", descr="thing given"))
        roles.append(Role(n="2", f="gol", descr="entity given to"))

        # Modifier arguments (ARGM)
        roles.append(Role(n="M", f="loc", descr="location"))
        roles.append(Role(n="M", f="tmp", descr="time"))

        # For prefix tests, Role would need special n values
        # but the current model doesn't support prefixes properly
        # so we skip these for now

        return roles

    def test_filter_by_is_core(self) -> None:
        """Test filtering by core argument property."""
        roles = self.create_test_roles()

        # Filter for core arguments
        core = filter_args_by_properties(roles, is_core=True)
        assert len(core) == 3  # ARG0, ARG1, ARG2

        # Filter for non-core
        non_core = filter_args_by_properties(roles, is_core=False)
        assert len(non_core) == 2  # ARGM-LOC, ARGM-TMP

    def test_filter_by_is_modifier(self) -> None:
        """Test filtering by modifier property."""
        roles = self.create_test_roles()

        # Filter for modifiers
        modifiers = filter_args_by_properties(roles, is_modifier=True)
        assert len(modifiers) == 2  # ARGM-LOC, ARGM-TMP

        # Filter for non-modifiers
        non_modifiers = filter_args_by_properties(roles, is_modifier=False)
        assert len(non_modifiers) == 3  # ARG0, ARG1, ARG2

    def test_filter_by_has_prefix(self) -> None:
        """Test filtering by prefix property."""
        roles = self.create_test_roles()

        # Filter for arguments with prefix (none in our test data)
        with_prefix = filter_args_by_properties(roles, has_prefix=True)
        assert len(with_prefix) == 0  # No prefixes in test data

        # Filter for arguments without prefix (all of them)
        without_prefix = filter_args_by_properties(roles, has_prefix=False)
        assert len(without_prefix) == 5  # All arguments

    def test_filter_by_modifier_type(self) -> None:
        """Test filtering by specific modifier type."""
        roles = self.create_test_roles()

        # Filter for LOC modifier
        loc_mods = filter_args_by_properties(roles, modifier_type="loc")
        assert len(loc_mods) == 1
        assert loc_mods[0].f == "loc"

        # Filter for TMP modifier
        tmp_mods = filter_args_by_properties(roles, modifier_type="tmp")
        assert len(tmp_mods) == 1
        assert tmp_mods[0].f == "tmp"

    def test_filter_combined(self) -> None:
        """Test filtering with multiple criteria."""
        roles = self.create_test_roles()

        # Core arguments without prefix (all core args have no prefix)
        result = filter_args_by_properties(roles, is_core=True, has_prefix=False)
        assert len(result) == 3  # ARG0, ARG1, ARG2

        # Modifiers of type LOC
        result = filter_args_by_properties(roles, is_modifier=True, modifier_type="loc")
        assert len(result) == 1
        assert result[0].f == "loc"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_roleset_format(self) -> None:
        """Test parsing invalid roleset formats."""
        with pytest.raises(ValueError, match="Invalid roleset ID format"):
            parse_roleset_id("give")  # Missing sense number

        with pytest.raises(ValueError, match="Invalid roleset ID format"):
            parse_roleset_id("give.1.2")  # Too many parts

        with pytest.raises(ValueError, match="Invalid roleset ID format"):
            parse_roleset_id("123.01")  # Starts with number

    def test_invalid_argument_format(self) -> None:
        """Test parsing invalid argument formats."""
        with pytest.raises(ValueError, match="Invalid argument format"):
            parse_argument("ARG")  # Missing number/letter

        with pytest.raises(ValueError, match="Invalid argument format"):
            parse_argument("ARGUMENT0")  # Wrong prefix

        with pytest.raises(ValueError, match="Invalid argument format"):
            parse_argument("X-ARG0")  # Invalid prefix

    def test_uppercase_handling(self) -> None:
        """Test that uppercase input is handled correctly."""
        result = parse_argument("ARG0")
        assert result.raw_string == "ARG0"
        assert result.normalized == "0"  # Core args normalize to just the number

        result = parse_argument("ARGM-LOC")
        assert result.normalized == "m_loc"  # Modifiers normalize with m prefix

    def test_special_modifiers(self) -> None:
        """Test newer/special modifier types."""
        special_mods = ["EXT", "LVB", "REC", "GOL", "PRD", "COM", "ADJ", "DSP", "PRR", "CXN", "TOP"]

        for mod in special_mods:
            result = parse_argument(f"ARGM-{mod}")
            assert result.modifier_type == mod.lower()
            assert result.arg_type == "modifier"
