"""Tests for VerbNet frame models.

Tests the VNFrame, FrameDescription, Syntax, Semantics, and related models
for proper validation, serialization, and functionality.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from glazing.verbnet.models import (
    Example,
    FrameDescription,
    Predicate,
    PredicateArgument,
    Semantics,
    SyntacticRestriction,
    Syntax,
    SyntaxElement,
    VNFrame,
)


class TestExample:
    """Test the Example model."""

    def test_simple_example(self) -> None:
        """Test creating a simple example."""
        example = Example(text="John gave Mary a book")
        assert example.text == "John gave Mary a book"

    def test_empty_text(self) -> None:
        """Test that empty text is allowed."""
        example = Example(text="")
        assert example.text == ""

    def test_complex_example(self) -> None:
        """Test example with complex sentence."""
        text = "The teacher carefully explained the difficult concept to the students"
        example = Example(text=text)
        assert example.text == text


class TestFrameDescription:
    """Test the FrameDescription model."""

    def test_basic_description(self) -> None:
        """Test creating a basic frame description."""
        desc = FrameDescription(
            description_number="0.2", primary="NP V NP", secondary="Basic Transitive"
        )
        assert desc.description_number == "0.2"
        assert desc.primary == "NP V NP"
        assert desc.secondary == "Basic Transitive"
        assert desc.xtag == ""

    def test_description_number_validation(self) -> None:
        """Test description number format validation."""
        # Valid formats
        valid_numbers = ["0", "0.1", "2.5.1", "10.1.2.3"]
        for num in valid_numbers:
            desc = FrameDescription(description_number=num, primary="NP V", secondary="")
            assert desc.description_number == num

        # Invalid formats
        invalid_numbers = ["a.1", "1.a", "1.", ".1", "1..2"]
        for num in invalid_numbers:
            with pytest.raises(ValidationError) as exc_info:
                FrameDescription(description_number=num, primary="NP V", secondary="")
            assert "Invalid description number format" in str(exc_info.value)

    def test_xtag_validation(self) -> None:
        """Test XTag validation."""
        # Valid xtags
        valid_xtags = ["", "0.1", "0.2", "through-PP", "at-PP"]
        for xtag in valid_xtags:
            desc = FrameDescription(
                description_number="0.1", primary="NP V", secondary="", xtag=xtag
            )
            assert desc.xtag == xtag

    def test_pattern_parsing(self) -> None:
        """Test primary and secondary pattern parsing."""
        desc = FrameDescription(
            description_number="0.1", primary="NP V NP PP", secondary="Transitive with PP"
        )
        # Check that primary_elements is populated
        assert desc.primary_elements == ["NP", "V", "NP", "PP"]
        assert desc.secondary_patterns == ["Transitive with PP"]

    def test_semicolon_separated_secondary(self) -> None:
        """Test semicolon-separated secondary patterns."""
        desc = FrameDescription(
            description_number="0.1",
            primary="NP V",
            secondary="Intransitive; Basic Pattern; Simple",
        )
        assert desc.secondary_patterns == ["Intransitive", "Basic Pattern", "Simple"]

    def test_empty_patterns(self) -> None:
        """Test handling of empty patterns."""
        desc = FrameDescription(description_number="0.1", primary="", secondary="")
        assert desc.primary_elements == []
        assert desc.secondary_patterns == []


class TestSyntacticRestriction:
    """Test the SyntacticRestriction model."""

    def test_basic_restriction(self) -> None:
        """Test creating a basic syntactic restriction."""
        restriction = SyntacticRestriction(type="be_sc_ing", value="+")
        assert restriction.type == "be_sc_ing"
        assert restriction.value == "+"

    def test_negative_restriction(self) -> None:
        """Test negative restriction value."""
        restriction = SyntacticRestriction(type="to_be", value="-")
        assert restriction.type == "to_be"
        assert restriction.value == "-"


class TestSyntaxElement:
    """Test the SyntaxElement model."""

    def test_np_element(self) -> None:
        """Test creating an NP syntax element."""
        element = SyntaxElement(pos="NP", value="Agent")
        assert element.pos == "NP"
        assert element.value == "Agent"
        assert element.synrestrs == []
        assert element.selrestrs == []

    def test_verb_element(self) -> None:
        """Test creating a VERB element."""
        element = SyntaxElement(pos="VERB")
        assert element.pos == "VERB"
        assert element.value is None

    def test_prep_element_valid(self) -> None:
        """Test PREP element with valid preposition values."""
        valid_preps = [
            "to",
            "at for on",
            "to|against",
            "for_with",
            "?",
            "at-for",  # Hyphens are allowed
            "through-PP",  # Pattern like
        ]
        for prep in valid_preps:
            element = SyntaxElement(pos="PREP", value=prep)
            assert element.value == prep

    def test_prep_element_invalid(self) -> None:
        """Test PREP element with invalid preposition values."""
        invalid_preps = [
            "at  for",  # Double space
            "at,for",  # Comma not allowed
            "at;for",  # Semicolon not allowed
        ]
        for prep in invalid_preps:
            with pytest.raises(ValidationError) as exc_info:
                SyntaxElement(pos="PREP", value=prep)
            assert "Invalid preposition value format" in str(exc_info.value)

    def test_non_prep_value_not_validated(self) -> None:
        """Test that non-PREP elements don't validate value format."""
        element = SyntaxElement(pos="NP", value="Any String Is OK Here!")
        assert element.value == "Any String Is OK Here!"

    def test_element_with_restrictions(self) -> None:
        """Test element with syntactic restrictions."""
        element = SyntaxElement(
            pos="S",
            synrestrs=[
                SyntacticRestriction(type="to_be", value="+"),
                SyntacticRestriction(type="be_sc_ing", value="-"),
            ],
        )
        assert len(element.synrestrs) == 2
        assert element.synrestrs[0].type == "to_be"


class TestSyntax:
    """Test the Syntax model."""

    def test_basic_syntax(self) -> None:
        """Test creating a basic syntax structure."""
        syntax = Syntax(
            elements=[
                SyntaxElement(pos="NP", value="Agent"),
                SyntaxElement(pos="VERB"),
                SyntaxElement(pos="NP", value="Theme"),
            ]
        )
        assert len(syntax.elements) == 3
        assert syntax.elements[0].pos == "NP"
        assert syntax.elements[1].pos == "VERB"
        assert syntax.elements[2].pos == "NP"

    def test_empty_syntax(self) -> None:
        """Test syntax with no elements."""
        syntax = Syntax(elements=[])
        assert syntax.elements == []

    def test_complex_syntax(self) -> None:
        """Test complex syntax with multiple element types."""
        syntax = Syntax(
            elements=[
                SyntaxElement(pos="NP", value="Agent"),
                SyntaxElement(pos="VERB"),
                SyntaxElement(pos="NP", value="Theme"),
                SyntaxElement(pos="PREP", value="to for"),
                SyntaxElement(pos="NP", value="Recipient"),
            ]
        )
        assert len(syntax.elements) == 5


class TestPredicateArgument:
    """Test the PredicateArgument model."""

    def test_themrole_argument(self) -> None:
        """Test thematic role argument."""
        arg = PredicateArgument(type="ThemRole", value="Agent")
        assert arg.type == "ThemRole"
        assert arg.value == "Agent"

    def test_event_argument_valid(self) -> None:
        """Test valid event variable arguments."""
        valid_events = ["e1", "e2", "e10", "e999"]
        for event in valid_events:
            arg = PredicateArgument(type="Event", value=event)
            assert arg.value == event

    def test_event_argument_invalid(self) -> None:
        """Test invalid event variable formats."""
        invalid_events = ["1", "e1a", "event1", "x1"]
        for event in invalid_events:
            with pytest.raises(ValidationError) as exc_info:
                PredicateArgument(type="Event", value=event)
            assert "Invalid event variable format" in str(exc_info.value)

    def test_optional_themrole(self) -> None:
        """Test optional thematic role (with ?)."""
        arg = PredicateArgument(type="ThemRole", value="?Theme")
        assert arg.value == "?Theme"

    def test_constant_argument(self) -> None:
        """Test constant argument type."""
        arg = PredicateArgument(type="Constant", value="together")
        assert arg.type == "Constant"
        assert arg.value == "together"


class TestPredicate:
    """Test the Predicate model."""

    def test_basic_predicate(self) -> None:
        """Test creating a basic predicate."""
        pred = Predicate(
            value="motion",
            args=[
                PredicateArgument(type="Event", value="e1"),
                PredicateArgument(type="ThemRole", value="Agent"),
            ],
        )
        assert pred.value == "motion"
        assert len(pred.args) == 2
        assert not pred.negated

    def test_negated_predicate(self) -> None:
        """Test negated predicate."""
        pred = Predicate(value="has_location", args=[], negated=True)
        assert pred.negated

    def test_bool_attribute_parsing(self) -> None:
        """Test parsing of XML bool="!" attribute."""
        # String "!" should be parsed as True
        pred = Predicate(value="motion", args=[], negated="!")
        assert pred.negated is True

        # Other strings should be False
        pred = Predicate(value="motion", args=[], negated="")
        assert pred.negated is False

    def test_complex_predicate(self) -> None:
        """Test predicate with multiple argument types."""
        pred = Predicate(
            value="transfer",
            args=[
                PredicateArgument(type="Event", value="e1"),
                PredicateArgument(type="ThemRole", value="Agent"),
                PredicateArgument(type="ThemRole", value="Theme"),
                PredicateArgument(type="ThemRole", value="?Recipient"),
            ],
        )
        assert len(pred.args) == 4


class TestSemantics:
    """Test the Semantics model."""

    def test_basic_semantics(self) -> None:
        """Test creating basic semantics."""
        semantics = Semantics(
            predicates=[
                Predicate(value="motion", args=[PredicateArgument(type="Event", value="e1")])
            ]
        )
        assert len(semantics.predicates) == 1

    def test_empty_semantics(self) -> None:
        """Test semantics with no predicates."""
        semantics = Semantics(predicates=[])
        assert semantics.predicates == []

    def test_multiple_predicates(self) -> None:
        """Test semantics with multiple predicates."""
        semantics = Semantics(
            predicates=[
                Predicate(value="motion", args=[PredicateArgument(type="Event", value="e1")]),
                Predicate(
                    value="cause",
                    args=[
                        PredicateArgument(type="ThemRole", value="Agent"),
                        PredicateArgument(type="Event", value="e1"),
                    ],
                ),
                Predicate(value="has_location", args=[], negated=True),
            ]
        )
        assert len(semantics.predicates) == 3


class TestVNFrame:
    """Test the VNFrame model."""

    def test_complete_frame(self) -> None:
        """Test creating a complete VNFrame."""
        frame = VNFrame(
            description=FrameDescription(
                description_number="0.1", primary="NP V NP", secondary="Basic Transitive"
            ),
            examples=[Example(text="John hit the ball"), Example(text="Mary kicked the door")],
            syntax=Syntax(
                elements=[
                    SyntaxElement(pos="NP", value="Agent"),
                    SyntaxElement(pos="VERB"),
                    SyntaxElement(pos="NP", value="Theme"),
                ]
            ),
            semantics=Semantics(
                predicates=[
                    Predicate(
                        value="cause",
                        args=[
                            PredicateArgument(type="Event", value="e1"),
                            PredicateArgument(type="ThemRole", value="Agent"),
                            PredicateArgument(type="ThemRole", value="Theme"),
                        ],
                    )
                ]
            ),
        )

        assert frame.description.description_number == "0.1"
        assert len(frame.examples) == 2
        assert len(frame.syntax.elements) == 3
        assert len(frame.semantics.predicates) == 1

    def test_minimal_frame(self) -> None:
        """Test creating a minimal frame."""
        frame = VNFrame(
            description=FrameDescription(description_number="0", primary="", secondary=""),
            examples=[],
            syntax=Syntax(elements=[]),
            semantics=Semantics(predicates=[]),
        )

        assert frame.description.description_number == "0"
        assert frame.examples == []
        assert frame.syntax.elements == []
        assert frame.semantics.predicates == []

    def test_frame_serialization(self) -> None:
        """Test frame serialization to dict."""
        frame = VNFrame(
            description=FrameDescription(
                description_number="1.2", primary="NP V", secondary="Intransitive"
            ),
            examples=[Example(text="John ran")],
            syntax=Syntax(
                elements=[SyntaxElement(pos="NP", value="Agent"), SyntaxElement(pos="VERB")]
            ),
            semantics=Semantics(
                predicates=[
                    Predicate(value="motion", args=[PredicateArgument(type="Event", value="e1")])
                ]
            ),
        )

        data = frame.model_dump()
        assert data["description"]["description_number"] == "1.2"
        assert data["examples"][0]["text"] == "John ran"
        assert len(data["syntax"]["elements"]) == 2
        assert data["semantics"]["predicates"][0]["value"] == "motion"

    def test_frame_with_complex_syntax(self) -> None:
        """Test frame with complex syntactic structure."""
        frame = VNFrame(
            description=FrameDescription(
                description_number="2.5.1", primary="NP V S_INF", secondary="Subject Control"
            ),
            examples=[Example(text="John wants to leave")],
            syntax=Syntax(
                elements=[
                    SyntaxElement(pos="NP", value="Agent"),
                    SyntaxElement(pos="VERB"),
                    SyntaxElement(
                        pos="S", synrestrs=[SyntacticRestriction(type="to_be", value="+")]
                    ),
                ]
            ),
            semantics=Semantics(
                predicates=[
                    Predicate(
                        value="desire",
                        args=[
                            PredicateArgument(type="Event", value="e1"),
                            PredicateArgument(type="ThemRole", value="Agent"),
                            PredicateArgument(type="Event", value="e2"),
                        ],
                    )
                ]
            ),
        )

        assert frame.syntax.elements[2].synrestrs[0].type == "to_be"
