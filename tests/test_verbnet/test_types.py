"""Tests for VerbNet type definitions.

This module tests all VerbNet-specific type definitions to ensure they
are correctly defined and can be used for validation.
"""

import re
from typing import get_args

from glazing.verbnet.types import (
    DESCRIPTION_NUMBER_PATTERN,
    PERCENTAGE_NOTATION_PATTERN,
    VERBNET_CLASS_PATTERN,
    VERBNET_KEY_PATTERN,
    ArgumentType,
    DescriptionNumber,
    EventType,
    FrameDescriptionElement,
    OppositionType,
    PredicateType,
    PrepositionValue,
    QualiaType,
    RestrictionValue,
    SecondaryPattern,
    SelectionalRestrictionType,
    SyntacticPOS,
    SyntacticRestrictionType,
    ThematicRoleType,
    ThematicRoleValue,
    VerbClassID,
    VerbNetKey,
    WordNetSense,
)


def get_type_args(type_alias):
    """Get arguments from a type alias created with Python 3.13+ type statement."""
    if hasattr(type_alias, "__value__"):
        # Python 3.13+ type statement
        return get_args(type_alias.__value__)
    # Regular type alias
    return get_args(type_alias)


class TestThematicRoleType:
    """Test ThematicRoleType literal."""

    def test_thematic_role_count(self) -> None:
        """Test that we have 48 thematic roles."""
        roles = get_type_args(ThematicRoleType)
        assert len(roles) == 48

    def test_core_roles_present(self) -> None:
        """Test that core thematic roles are present."""
        roles = get_type_args(ThematicRoleType)
        core_roles = ["Agent", "Theme", "Patient", "Experiencer", "Beneficiary"]
        for role in core_roles:
            assert role in roles

    def test_indexed_roles_present(self) -> None:
        """Test that indexed role variants are present."""
        roles = get_type_args(ThematicRoleType)
        indexed_roles = ["Agent_i", "Agent_j", "Patient_i", "Patient_j", "Theme_i", "Theme_j"]
        for role in indexed_roles:
            assert role in roles

    def test_co_roles_present(self) -> None:
        """Test that co-roles are present."""
        roles = get_type_args(ThematicRoleType)
        co_roles = ["Co-Agent", "Co-Patient", "Co-Theme"]
        for role in co_roles:
            assert role in roles

    def test_no_question_marked_roles(self) -> None:
        """Test that ThematicRoleType doesn't include question-marked roles."""
        roles = get_type_args(ThematicRoleType)
        for role in roles:
            assert not role.startswith("?")


class TestThematicRoleValue:
    """Test ThematicRoleValue literal."""

    def test_includes_standard_roles(self) -> None:
        """Test that standard roles are included."""
        values = get_type_args(ThematicRoleValue)
        standard = ["Agent", "Theme", "Patient", "Source", "Goal"]
        for role in standard:
            assert role in values

    def test_includes_indexed_variants(self) -> None:
        """Test that indexed variants are included."""
        values = get_type_args(ThematicRoleValue)
        indexed = ["Agent_I", "Agent_J", "Theme_I", "Theme_J"]
        for role in indexed:
            assert role in values

    def test_includes_question_marked_roles(self) -> None:
        """Test that question-marked roles are included."""
        values = get_type_args(ThematicRoleValue)
        question_marked = ["?Agent", "?Theme", "?Patient", "?Location"]
        for role in question_marked:
            assert role in values

    def test_includes_verb_specific_roles(self) -> None:
        """Test that verb-specific roles are included."""
        values = get_type_args(ThematicRoleValue)
        verb_specific = ["V_Final_State", "V_Manner", "V_State", "V_Vehicle"]
        for role in verb_specific:
            assert role in values

    def test_includes_event_variables(self) -> None:
        """Test that event variables are included."""
        values = get_type_args(ThematicRoleValue)
        assert "e1" in values
        assert "e2" in values

    def test_includes_special_variants(self) -> None:
        """Test that special variants are included."""
        values = get_type_args(ThematicRoleValue)
        # Test for known quirks in the data
        assert "Theme " in values  # With trailing space
        assert "Initial_location" in values  # Lowercase variant


class TestSelectionalRestrictionType:
    """Test SelectionalRestrictionType literal."""

    def test_selectional_restriction_count(self) -> None:
        """Test that we have 42 selectional restrictions."""
        restrictions = get_type_args(SelectionalRestrictionType)
        assert len(restrictions) == 42

    def test_animacy_restrictions_present(self) -> None:
        """Test that animacy restrictions are present."""
        restrictions = get_type_args(SelectionalRestrictionType)
        animacy = ["animate", "human", "animal", "biotic"]
        for restriction in animacy:
            assert restriction in restrictions

    def test_spatial_restrictions_present(self) -> None:
        """Test that spatial restrictions are present."""
        restrictions = get_type_args(SelectionalRestrictionType)
        spatial = ["location", "path", "dest", "src", "region", "spatial"]
        for restriction in spatial:
            assert restriction in restrictions

    def test_physical_restrictions_present(self) -> None:
        """Test that physical property restrictions are present."""
        restrictions = get_type_args(SelectionalRestrictionType)
        physical = ["solid", "nonrigid", "elongated", "pointy", "substance"]
        for restriction in physical:
            assert restriction in restrictions


class TestSyntacticRestrictionType:
    """Test SyntacticRestrictionType literal."""

    def test_syntactic_restriction_count(self) -> None:
        """Test that we have 35 syntactic restrictions."""
        restrictions = get_type_args(SyntacticRestrictionType)
        assert len(restrictions) == 35

    def test_infinitive_restrictions_present(self) -> None:
        """Test that infinitive restrictions are present."""
        restrictions = get_type_args(SyntacticRestrictionType)
        infinitives = ["ac_to_inf", "np_to_inf", "oc_to_inf", "rs_to_inf", "sc_to_inf"]
        for restriction in infinitives:
            assert restriction in restrictions

    def test_ing_restrictions_present(self) -> None:
        """Test that -ing restrictions are present."""
        restrictions = get_type_args(SyntacticRestrictionType)
        ing_forms = ["ac_ing", "be_sc_ing", "np_ing", "np_omit_ing", "oc_ing", "sc_ing"]
        for restriction in ing_forms:
            assert restriction in restrictions

    def test_wh_restrictions_present(self) -> None:
        """Test that wh- restrictions are present."""
        restrictions = get_type_args(SyntacticRestrictionType)
        wh_forms = ["wh_comp", "wh_extract", "wh_inf", "wh_ing", "what_extract", "what_inf"]
        for restriction in wh_forms:
            assert restriction in restrictions


class TestRestrictionValue:
    """Test RestrictionValue literal."""

    def test_restriction_values(self) -> None:
        """Test that restriction values are + and -."""
        values = get_type_args(RestrictionValue)
        assert len(values) == 2
        assert "+" in values
        assert "-" in values


class TestSyntacticPOS:
    """Test SyntacticPOS literal."""

    def test_syntactic_pos_values(self) -> None:
        """Test that all syntactic POS values are present."""
        pos_values = get_type_args(SyntacticPOS)
        expected = ["NP", "VERB", "PREP", "ADV", "ADJ", "LEX", "ADVP", "S", "SBAR"]
        assert len(pos_values) == len(expected)
        for pos in expected:
            assert pos in pos_values


class TestArgumentType:
    """Test ArgumentType literal."""

    def test_argument_types(self) -> None:
        """Test that all argument types are present."""
        arg_types = get_type_args(ArgumentType)
        expected = ["Event", "ThemRole", "VerbSpecific", "PredSpecific", "Constant"]
        assert len(arg_types) == len(expected)
        for arg_type in expected:
            assert arg_type in arg_types


class TestPredicateType:
    """Test PredicateType literal."""

    def test_predicate_count(self) -> None:
        """Test that we have 150+ predicate types."""
        predicates = get_type_args(PredicateType)
        assert len(predicates) >= 150

    def test_motion_predicates_present(self) -> None:
        """Test that motion predicates are present."""
        predicates = get_type_args(PredicateType)
        motion = [
            "motion",
            "body_motion",
            "elliptical_motion",
            "fictive_motion",
            "intrinsic_motion",
            "rotational_motion",
            "temporal_motion",
        ]
        for pred in motion:
            assert pred in predicates

    def test_state_predicates_present(self) -> None:
        """Test that state predicates are present."""
        predicates = get_type_args(PredicateType)
        states = [
            "state",
            "has_state",
            "has_attribute",
            "has_value",
            "has_location",
            "has_possession",
        ]
        for pred in states:
            assert pred in predicates

    def test_change_predicates_present(self) -> None:
        """Test that change predicates are present."""
        predicates = get_type_args(PredicateType)
        changes = ["change", "change_value", "become", "develop", "disappear"]
        for pred in changes:
            assert pred in predicates

    def test_special_case_predicates(self) -> None:
        """Test special case predicates."""
        predicates = get_type_args(PredicateType)
        # Test for predicates with special capitalization
        assert "Find" in predicates  # Capital F


class TestEventType:
    """Test EventType literal."""

    def test_event_types(self) -> None:
        """Test that all event types are present."""
        event_types = get_type_args(EventType)
        expected = ["process", "state", "transition", "achievement"]
        assert len(event_types) == len(expected)
        for event_type in expected:
            assert event_type in event_types


class TestFrameDescriptionElement:
    """Test FrameDescriptionElement literal."""

    def test_basic_constituents_present(self) -> None:
        """Test that basic constituents are present."""
        elements = get_type_args(FrameDescriptionElement)
        basic = ["V", "NP", "PP", "S", "VP", "ADJP", "ADVP", "ADJ", "ADV"]
        for element in basic:
            assert element in elements

    def test_np_role_elements_present(self) -> None:
        """Test that NP elements with roles are present."""
        elements = get_type_args(FrameDescriptionElement)
        np_roles = [
            "NP.agent",
            "NP.theme",
            "NP.patient",
            "NP.source",
            "NP.destination",
        ]
        for element in np_roles:
            assert element in elements

    def test_pp_role_elements_present(self) -> None:
        """Test that PP elements with roles are present."""
        elements = get_type_args(FrameDescriptionElement)
        pp_roles = [
            "PP.agent",
            "PP.theme",
            "PP.source",
            "PP.destination",
            "PP.instrument",
        ]
        for element in pp_roles:
            assert element in elements

    def test_special_elements_present(self) -> None:
        """Test that special elements are present."""
        elements = get_type_args(FrameDescriptionElement)
        special = ["It", "it", "There", "there", "Passive", "(PP)"]
        for element in special:
            assert element in elements

    def test_particles_present(self) -> None:
        """Test that particles are present."""
        elements = get_type_args(FrameDescriptionElement)
        particles = ["apart", "down", "out", "together", "up"]
        for particle in particles:
            assert particle in elements


class TestSecondaryPattern:
    """Test SecondaryPattern literal."""

    def test_basic_patterns_present(self) -> None:
        """Test that basic patterns are present."""
        patterns = get_type_args(SecondaryPattern)
        basic = [
            "Basic Transitive",
            "Basic Intransitive",
            "Transitive",
            "Intransitive",
        ]
        for pattern in basic:
            assert pattern in patterns

    def test_construction_patterns_present(self) -> None:
        """Test that construction patterns are present."""
        patterns = get_type_args(SecondaryPattern)
        constructions = [
            "Dative",
            "Double Object",
            "Middle Construction",
            "Passive",
            "Reciprocal",
            "Reflexive",
        ]
        for pattern in constructions:
            assert pattern in patterns

    def test_pp_patterns_present(self) -> None:
        """Test that PP patterns are present."""
        patterns = get_type_args(SecondaryPattern)
        pp_patterns = [
            "to-PP",
            "from-PP",
            "with-PP",
            "Source-PP",
            "Goal-PP",
            "Theme-PP",
        ]
        for pattern in pp_patterns:
            assert pattern in patterns

    def test_compound_patterns_present(self) -> None:
        """Test that compound patterns with semicolons are present."""
        patterns = get_type_args(SecondaryPattern)
        compound = [
            "NP-PP; Source-PP",
            "NP-PP; to-PP",
            "Transitive; passive",
            "Double Object; Dative",
        ]
        for pattern in compound:
            assert pattern in patterns

    def test_empty_pattern_allowed(self) -> None:
        """Test that empty string is allowed."""
        patterns = get_type_args(SecondaryPattern)
        assert "" in patterns


class TestGenerativeLexiconTypes:
    """Test VerbNet-GL specific types."""

    def test_qualia_types(self) -> None:
        """Test QualiaType values."""
        qualia = get_type_args(QualiaType)
        expected = ["formal", "constitutive", "telic", "agentive"]
        assert len(qualia) == len(expected)
        for qual in expected:
            assert qual in qualia

    def test_opposition_types(self) -> None:
        """Test OppositionType values."""
        oppositions = get_type_args(OppositionType)
        expected = ["motion", "state_change", "possession_transfer", "info_transfer"]
        assert len(oppositions) == len(expected)
        for opp in expected:
            assert opp in oppositions


class TestPatternValidation:
    """Test regex pattern validation for VerbNet identifiers."""

    def test_verbnet_class_pattern(self) -> None:
        """Test VerbNet class ID pattern."""
        pattern = re.compile(VERBNET_CLASS_PATTERN)

        # Valid class IDs
        assert pattern.match("give-13.1")
        assert pattern.match("give-13.1-1")
        assert pattern.match("leave-51.2")
        assert pattern.match("transfer-11.1-1-2")
        assert pattern.match("be_located_at-47.3")

        # Invalid class IDs
        assert not pattern.match("give")
        assert not pattern.match("13.1")
        assert not pattern.match("Give-13.1")  # Capital letter
        assert not pattern.match("give-")

    def test_verbnet_key_pattern(self) -> None:
        """Test VerbNet member key pattern."""
        pattern = re.compile(VERBNET_KEY_PATTERN)

        # Valid keys
        assert pattern.match("give#2")
        assert pattern.match("abandon#1")
        assert pattern.match("run_up#3")
        assert pattern.match("be-located-at#1")

        # Invalid keys
        assert not pattern.match("give")
        assert not pattern.match("give#")
        assert not pattern.match("Give#2")  # Capital letter
        assert not pattern.match("give#two")

    def test_percentage_notation_pattern(self) -> None:
        """Test VerbNet's WordNet percentage notation pattern."""
        pattern = re.compile(PERCENTAGE_NOTATION_PATTERN)

        # Valid notations
        assert pattern.match("give%2:40:00")
        assert pattern.match("abandon%2:40:01")
        assert pattern.match("dog%1:05:00")

        # Invalid notations
        assert not pattern.match("give%2:40")  # Missing lex_id
        assert not pattern.match("give%2:40:00::")  # Extra colons
        assert not pattern.match("Give%2:40:00")  # Capital letter

    def test_description_number_pattern(self) -> None:
        """Test description number pattern."""
        pattern = re.compile(DESCRIPTION_NUMBER_PATTERN)

        # Valid numbers
        assert pattern.match("0")
        assert pattern.match("1")
        assert pattern.match("0.2")
        assert pattern.match("2.5.1")
        assert pattern.match("10.3.4.5")

        # Invalid numbers
        assert not pattern.match("")  # Empty
        assert not pattern.match(".2")  # No leading number
        assert not pattern.match("2.")  # Trailing dot
        assert not pattern.match("2..5")  # Double dot


class TestCompleteness:
    """Test that type definitions are complete."""

    def test_no_duplicate_values(self) -> None:
        """Test that there are no duplicate values in literals."""
        type_literals = [
            ThematicRoleType,
            ThematicRoleValue,
            SelectionalRestrictionType,
            SyntacticRestrictionType,
            PredicateType,
            FrameDescriptionElement,
            SecondaryPattern,
        ]

        for type_literal in type_literals:
            values = get_type_args(type_literal)
            unique_values = set(values)
            assert len(values) == len(unique_values), f"Duplicates found in {type_literal}"

    def test_type_aliases_are_strings(self) -> None:
        """Test that type aliases resolve to str."""
        # Type aliases should resolve to str
        assert VerbClassID.__value__ is str
        assert VerbNetKey.__value__ is str
        assert WordNetSense.__value__ is str
        assert DescriptionNumber.__value__ is str
        assert PrepositionValue.__value__ is str
