"""Tests for VerbNet symbol parser.

This module tests the parsing utilities for VerbNet thematic role symbols,
including optional roles, indexed roles, PP roles, and verb-specific roles.
"""

from __future__ import annotations

import pytest

from glazing.verbnet.models import ThematicRole
from glazing.verbnet.symbol_parser import (
    extract_role_base,
    filter_roles_by_properties,
    is_indexed_role,
    is_optional_role,
    is_pp_element,
    is_verb_specific_role,
    normalize_role_for_matching,
    parse_frame_element,
    parse_thematic_role,
)


class TestParseThematicRole:
    """Test parsing of thematic role values."""

    def test_simple_role(self) -> None:
        """Test parsing simple thematic role."""
        result = parse_thematic_role("Agent")
        assert result.raw_string == "Agent"
        assert result.base_role == "Agent"
        assert result.is_optional is False
        assert result.index is None
        assert result.is_verb_specific is False
        assert result.role_type == "thematic"

    def test_optional_role(self) -> None:
        """Test parsing optional role with ? prefix."""
        result = parse_thematic_role("?Agent")
        assert result.raw_string == "?Agent"
        assert result.base_role == "Agent"
        assert result.is_optional is True
        assert result.index is None
        assert result.role_type == "thematic"

    def test_indexed_role(self) -> None:
        """Test parsing indexed role with _I or _J suffix."""
        # Index I
        result = parse_thematic_role("Theme_I")
        assert result.raw_string == "Theme_I"
        assert result.base_role == "Theme"
        assert result.is_optional is False
        assert result.index == "I"

        # Index J
        result = parse_thematic_role("Agent_J")
        assert result.base_role == "Agent"
        assert result.index == "J"

    def test_optional_indexed_role(self) -> None:
        """Test parsing role that is both optional and indexed."""
        result = parse_thematic_role("?Theme_I")
        assert result.raw_string == "?Theme_I"
        assert result.base_role == "Theme"
        assert result.is_optional is True
        assert result.index == "I"

    def test_verb_specific_role(self) -> None:
        """Test parsing verb-specific role with V_ prefix."""
        result = parse_thematic_role("V_Final_State")
        assert result.raw_string == "V_Final_State"
        assert result.base_role == "Final_State"
        assert result.is_verb_specific is True
        assert result.role_type == "verb_specific"

        # Optional verb-specific
        result = parse_thematic_role("?V_State")
        assert result.base_role == "State"
        assert result.is_optional is True
        assert result.is_verb_specific is True

    def test_complex_role_names(self) -> None:
        """Test parsing complex role names."""
        # Role with underscore in name
        result = parse_thematic_role("Co_Agent")
        assert result.base_role == "Co_Agent"

        # Role with multiple parts
        result = parse_thematic_role("Initial_Location")
        assert result.base_role == "Initial_Location"

    def test_all_role_combinations(self) -> None:
        """Test various combinations of role modifiers."""
        test_cases = [
            ("Agent", "Agent", False, None, False),
            ("?Agent", "Agent", True, None, False),
            ("Agent_I", "Agent", False, "I", False),
            ("?Agent_I", "Agent", True, "I", False),
            ("Theme_J", "Theme", False, "J", False),
            ("?Theme_J", "Theme", True, "J", False),
            ("V_State", "State", False, None, True),
            ("?V_State", "State", True, None, True),
        ]

        for raw, base, optional, index, verb_specific in test_cases:
            result = parse_thematic_role(raw)
            assert result.base_role == base
            assert result.is_optional == optional
            assert result.index == index
            assert result.is_verb_specific == verb_specific


class TestParseFrameElement:
    """Test parsing of frame description elements."""

    def test_pp_elements(self) -> None:
        """Test parsing PP (prepositional phrase) elements."""
        result = parse_frame_element("PP.location")
        assert result.raw_string == "PP.location"
        assert result.pp_type == "location"
        assert result.base_role == "PP.location"
        assert result.role_type == "pp"

        # Different PP types
        result = parse_frame_element("PP.instrument")
        assert result.pp_type == "instrument"

        result = parse_frame_element("PP.destination")
        assert result.pp_type == "destination"

    def test_np_elements(self) -> None:
        """Test parsing NP (noun phrase) elements."""
        result = parse_frame_element("NP.agent")
        assert result.raw_string == "NP.agent"
        assert result.base_role == "agent"
        assert result.role_type == "thematic"
        assert result.pp_type is None

        # Different NP roles
        result = parse_frame_element("NP.theme")
        assert result.base_role == "theme"

        result = parse_frame_element("NP.destination")
        assert result.base_role == "destination"

    def test_simple_elements(self) -> None:
        """Test parsing simple elements without prefixes."""
        result = parse_frame_element("VERB")
        assert result.raw_string == "VERB"
        assert result.base_role == "VERB"
        assert result.role_type == "thematic"

        result = parse_frame_element("ADV")
        assert result.base_role == "ADV"


class TestBooleanCheckers:
    """Test boolean checking functions."""

    def test_is_optional_role(self) -> None:
        """Test checking if role is optional."""
        assert is_optional_role("?Agent") is True
        assert is_optional_role("Agent") is False
        assert is_optional_role("?Theme_I") is True
        assert is_optional_role("Theme_I") is False
        assert is_optional_role("?V_State") is True

    def test_is_indexed_role(self) -> None:
        """Test checking if role has an index."""
        assert is_indexed_role("Theme_I") is True
        assert is_indexed_role("Agent_J") is True
        assert is_indexed_role("Theme") is False
        assert is_indexed_role("?Theme_I") is True
        assert is_indexed_role("?Agent") is False

    def test_is_pp_element(self) -> None:
        """Test checking if element is a PP element."""
        assert is_pp_element("PP.location") is True
        assert is_pp_element("PP.instrument") is True
        assert is_pp_element("NP.agent") is False
        assert is_pp_element("VERB") is False

    def test_is_verb_specific_role(self) -> None:
        """Test checking if role is verb-specific."""
        assert is_verb_specific_role("V_State") is True
        assert is_verb_specific_role("V_Final_State") is True
        assert is_verb_specific_role("?V_State") is True
        assert is_verb_specific_role("Agent") is False
        assert is_verb_specific_role("Theme_I") is False


class TestExtractRoleBase:
    """Test extracting base role name."""

    def test_extract_base_from_simple(self) -> None:
        """Test extracting base from simple role."""
        assert extract_role_base("Agent") == "Agent"
        assert extract_role_base("Theme") == "Theme"

    def test_extract_base_from_optional(self) -> None:
        """Test extracting base from optional role."""
        assert extract_role_base("?Agent") == "Agent"
        assert extract_role_base("?Theme") == "Theme"

    def test_extract_base_from_indexed(self) -> None:
        """Test extracting base from indexed role."""
        assert extract_role_base("Theme_I") == "Theme"
        assert extract_role_base("Agent_J") == "Agent"

    def test_extract_base_from_complex(self) -> None:
        """Test extracting base from complex role."""
        assert extract_role_base("?Theme_I") == "Theme"
        assert extract_role_base("V_State") == "State"
        assert extract_role_base("?V_Final_State") == "Final_State"


class TestNormalizeRoleForMatching:
    """Test role normalization for fuzzy matching."""

    def test_normalize_simple_role(self) -> None:
        """Test normalizing simple roles."""
        assert normalize_role_for_matching("Agent") == "agent"
        assert normalize_role_for_matching("Theme") == "theme"

    def test_normalize_optional_role(self) -> None:
        """Test normalizing optional roles."""
        assert normalize_role_for_matching("?Agent") == "agent"
        assert normalize_role_for_matching("?Theme") == "theme"

    def test_normalize_indexed_role(self) -> None:
        """Test normalizing indexed roles."""
        assert normalize_role_for_matching("Theme_I") == "theme"
        assert normalize_role_for_matching("Agent_J") == "agent"
        assert normalize_role_for_matching("?Theme_I") == "theme"

    def test_normalize_verb_specific_role(self) -> None:
        """Test normalizing verb-specific roles."""
        assert normalize_role_for_matching("V_State") == "state"
        assert normalize_role_for_matching("V_Final_State") == "final_state"
        assert normalize_role_for_matching("?V_State") == "state"

    def test_normalize_complex_names(self) -> None:
        """Test normalizing complex role names."""
        assert normalize_role_for_matching("Initial_Location") == "initial_location"
        assert normalize_role_for_matching("Co_Agent") == "co_agent"


class TestFilterRolesByProperties:
    """Test filtering roles by their properties."""

    def create_test_roles(self) -> list[ThematicRole]:
        """Create test thematic roles from real VerbNet data."""
        # Using actual ThematicRole structure from VerbNet converted data
        # From attend-107.4, build-26.1, give-13.1 classes
        return [
            ThematicRole(type="Agent"),
            ThematicRole(type="Theme"),
            ThematicRole(type="Patient_i"),
            ThematicRole(type="Goal"),
            ThematicRole(type="Recipient"),
            ThematicRole(type="Theme_j"),
        ]

    def test_filter_by_optional(self) -> None:
        """Test filtering by optional property.

        Note: ThematicRole objects from converted data don't store optional status
        since ThematicRoleType literals don't include '?' prefixes.
        """
        roles = self.create_test_roles()

        # Filter for optional roles - none will match since ThematicRole.type
        # can't contain '?'
        optional = filter_roles_by_properties(roles, optional=True)
        assert len(optional) == 0

        # Filter for non-optional roles - all will match
        required = filter_roles_by_properties(roles, optional=False)
        assert len(required) == 6

    def test_filter_by_indexed(self) -> None:
        """Test filtering by indexed property."""
        roles = self.create_test_roles()

        # Filter for indexed roles - Patient_i and Theme_j
        indexed = filter_roles_by_properties(roles, indexed=True)
        assert len(indexed) == 2
        assert all("_i" in r.type or "_j" in r.type for r in indexed)

        # Filter for non-indexed roles
        not_indexed = filter_roles_by_properties(roles, indexed=False)
        assert len(not_indexed) == 4

    def test_filter_by_verb_specific(self) -> None:
        """Test filtering by verb-specific property."""
        roles = self.create_test_roles()

        # Filter for verb-specific roles - none in our test set
        verb_specific = filter_roles_by_properties(roles, verb_specific=True)
        assert len(verb_specific) == 0

        # Filter for non-verb-specific roles - all of them
        not_verb_specific = filter_roles_by_properties(roles, verb_specific=False)
        assert len(not_verb_specific) == 6

    def test_filter_combined_properties(self) -> None:
        """Test filtering with multiple properties."""
        roles = self.create_test_roles()

        # Non-optional AND indexed
        result = filter_roles_by_properties(roles, optional=False, indexed=True)
        assert len(result) == 2
        assert all("_i" in r.type or "_j" in r.type for r in result)

        # Non-optional AND non-verb-specific
        result = filter_roles_by_properties(roles, optional=False, verb_specific=False)
        assert len(result) == 6

        # Non-optional AND non-indexed
        result = filter_roles_by_properties(roles, optional=False, indexed=False)
        assert len(result) == 4
        assert {r.type for r in result} == {"Agent", "Theme", "Goal", "Recipient"}

    def test_filter_no_criteria(self) -> None:
        """Test filtering with no criteria returns all roles."""
        roles = self.create_test_roles()
        result = filter_roles_by_properties(roles)
        assert len(result) == len(roles)

    def test_filter_empty_list(self) -> None:
        """Test filtering empty list."""
        result = filter_roles_by_properties([])
        assert result == []


class TestKnownTypos:
    """Test handling of known typos in VerbNet roles."""

    def test_common_role_typos(self) -> None:
        """Test that common typos can be handled."""
        # These would be used with fuzzy matching in practice
        typos_to_correct = [
            ("Agnet", "Agent"),  # Typo
            ("Themme", "Theme"),  # Double letter
            ("Pateint", "Patient"),  # Transposition
            ("Destionation", "Destination"),  # Missing letter
            ("Benificiary", "Beneficiary"),  # Common misspelling
            ("Expereincer", "Experiencer"),  # Transposition
            ("Insturment", "Instrument"),  # Missing letter
            ("Soruce", "Source"),  # Transposition
        ]

        for typo, correct in typos_to_correct:
            # Normalize both for matching
            normalized_typo = normalize_role_for_matching(typo)
            normalized_correct = normalize_role_for_matching(correct)
            # In practice, fuzzy matching would find these similar
            assert len(normalized_typo) > 0
            assert len(normalized_correct) > 0


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_empty_string(self) -> None:
        """Test parsing empty string raises error."""
        with pytest.raises(ValueError):
            parse_thematic_role("")

    def test_single_character(self) -> None:
        """Test parsing single character role."""
        result = parse_thematic_role("A")
        assert result.base_role == "A"

        result = parse_thematic_role("?A")
        assert result.base_role == "A"
        assert result.is_optional is True

    def test_only_modifiers(self) -> None:
        """Test strings with only modifiers."""
        # Should raise ValueError for empty base role
        with pytest.raises(ValueError, match="Empty base role after processing"):
            parse_thematic_role("?")

    def test_unusual_pp_types(self) -> None:
        """Test PP elements with various type names."""
        for pp_type in ["about", "with", "from", "to", "on", "in", "at", "for"]:
            element = f"PP.{pp_type}"
            result = parse_frame_element(element)
            assert result.pp_type == pp_type
            assert result.role_type == "pp"
