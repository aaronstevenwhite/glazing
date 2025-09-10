"""Tests for FrameNet core models.

This module contains comprehensive tests for the FrameNet data models including
validation, markup parsing, and constraint checking.
"""

from datetime import UTC, datetime

import pytest

from glazing.framenet.models import (
    AnnotatedText,
    FERelation,
    Frame,
    FrameElement,
    FrameIndexEntry,
    FrameRelation,
    SemanticType,
    TextAnnotation,
)


class TestTextAnnotation:
    """Test cases for TextAnnotation model."""

    def test_valid_annotation(self):
        """Test creating a valid text annotation."""
        annotation = TextAnnotation(
            start=0,
            end=5,
            type="fex",
            name="Agent",
            text="Agent",
        )
        assert annotation.start == 0
        assert annotation.end == 5
        assert annotation.type == "fex"
        assert annotation.name == "Agent"
        assert annotation.text == "Agent"

    def test_annotation_length(self):
        """Test annotation length calculation."""
        annotation = TextAnnotation(start=10, end=15, type="fex", name="Theme", text="theme")
        assert annotation.get_length() == 5

    def test_annotation_overlap(self):
        """Test annotation overlap detection."""
        ann1 = TextAnnotation(start=0, end=5, type="fex", name="Agent", text="Agent")
        ann2 = TextAnnotation(start=3, end=8, type="fex", name="Theme", text="Theme")
        ann3 = TextAnnotation(start=10, end=15, type="fex", name="Goal", text="Goal")

        assert ann1.overlaps_with(ann2)
        assert ann2.overlaps_with(ann1)
        assert not ann1.overlaps_with(ann3)
        assert not ann3.overlaps_with(ann1)

    def test_invalid_positions(self):
        """Test validation of invalid positions."""
        with pytest.raises(ValueError, match="End position.*must be after start position"):
            TextAnnotation(start=5, end=5, type="fex", name="Agent", text="Agent")

        with pytest.raises(ValueError, match="End position.*must be after start position"):
            TextAnnotation(start=10, end=5, type="fex", name="Agent", text="Agent")

    def test_negative_positions(self):
        """Test validation of negative positions."""
        with pytest.raises(ValueError):
            TextAnnotation(start=-1, end=5, type="fex", name="Agent", text="Agent")

    def test_fex_requires_name(self):
        """Test that fex annotations require a name."""
        with pytest.raises(ValueError, match="requires a name"):
            TextAnnotation(start=0, end=5, type="fex", text="Agent")

    def test_fen_requires_name(self):
        """Test that fen annotations require a name."""
        with pytest.raises(ValueError, match="requires a name"):
            TextAnnotation(start=0, end=5, type="fen", text="Agent")

    def test_target_no_name_required(self):
        """Test that target annotations don't require a name."""
        annotation = TextAnnotation(start=0, end=5, type="t", text="abandon")
        assert annotation.name is None
        assert annotation.type == "t"

    def test_invalid_fe_name_format(self):
        """Test validation of FE name format."""
        with pytest.raises(ValueError, match="Invalid FE name format"):
            TextAnnotation(start=0, end=5, type="fex", name="agent", text="Agent")  # lowercase

        with pytest.raises(ValueError, match="Invalid FE name format"):
            TextAnnotation(
                start=0, end=5, type="fex", name="Agent-Bad", text="Agent"
            )  # hyphen not allowed


class TestAnnotatedText:
    """Test cases for AnnotatedText model."""

    def test_empty_text(self):
        """Test parsing empty text."""
        annotated = AnnotatedText.parse("")
        assert annotated.raw_text == ""
        assert annotated.plain_text == ""
        assert len(annotated.annotations) == 0

    def test_text_without_markup(self):
        """Test parsing text without markup."""
        text = "This is plain text without markup"
        annotated = AnnotatedText.parse(text)
        assert annotated.raw_text == text
        assert annotated.plain_text == text
        assert len(annotated.annotations) == 0

    def test_single_fex_annotation(self):
        """Test parsing single fex annotation."""
        text = "An <fex>Agent</fex> performs an action"
        annotated = AnnotatedText.parse(text)

        assert annotated.raw_text == text
        assert annotated.plain_text == "An Agent performs an action"
        assert len(annotated.annotations) == 1

        annotation = annotated.annotations[0]
        assert annotation.type == "fex"
        assert annotation.name == "Agent"  # Content is used as name when not explicit
        assert annotation.text == "Agent"
        assert annotation.start == 3  # Position of "Agent" in plain text
        assert annotation.end == 8

    def test_fex_with_name_attribute(self):
        """Test parsing fex with explicit name attribute."""
        text = "The <fex name='Actor'>person</fex> walks"
        annotated = AnnotatedText.parse(text)

        assert annotated.plain_text == "The person walks"
        assert len(annotated.annotations) == 1

        annotation = annotated.annotations[0]
        assert annotation.type == "fex"
        assert annotation.name == "Actor"
        assert annotation.text == "person"
        assert annotation.start == 4
        assert annotation.end == 10

    def test_multiple_annotations(self):
        """Test parsing multiple annotations."""
        text = (
            "The <fex>Agent</fex> gives the <fex name='Theme'>book</fex> "
            "to the <fex name='Recipient'>child</fex>"
        )
        annotated = AnnotatedText.parse(text)

        expected_plain = "The Agent gives the book to the child"
        assert annotated.plain_text == expected_plain
        assert len(annotated.annotations) == 3

        # Check Agent annotation
        agent = annotated.annotations[0]
        assert agent.type == "fex"
        assert agent.name == "Agent"  # Content used as name
        assert agent.text == "Agent"
        assert agent.start == 4
        assert agent.end == 9

        # Check Theme annotation
        theme = annotated.annotations[1]
        assert theme.type == "fex"
        assert theme.name == "Theme"
        assert theme.text == "book"
        assert theme.start == 20
        assert theme.end == 24

        # Check Recipient annotation
        recipient = annotated.annotations[2]
        assert recipient.type == "fex"
        assert recipient.name == "Recipient"
        assert recipient.text == "child"
        assert recipient.start == 32
        assert recipient.end == 37

    def test_mixed_annotation_types(self):
        """Test parsing different annotation types."""
        text = "The <fex>Agent</fex> <t>abandons</t> the <fen>Theme</fen>"
        annotated = AnnotatedText.parse(text)

        assert annotated.plain_text == "The Agent abandons the Theme"
        assert len(annotated.annotations) == 3

        types = [ann.type for ann in annotated.annotations]
        assert "fex" in types
        assert "t" in types
        assert "fen" in types

    def test_get_annotations_by_type(self):
        """Test filtering annotations by type."""
        text = "The <fex>Agent</fex> <t>abandons</t> the <fex>Theme</fex>"
        annotated = AnnotatedText.parse(text)

        fex_annotations = annotated.get_annotations_by_type("fex")
        assert len(fex_annotations) == 2

        target_annotations = annotated.get_annotations_by_type("t")
        assert len(target_annotations) == 1
        assert target_annotations[0].text == "abandons"

    def test_get_fe_references(self):
        """Test getting FE references."""
        text = "The <fex>Agent</fex> does something to the <fen>Theme</fen>"
        annotated = AnnotatedText.parse(text)

        fe_refs = annotated.get_fe_references()
        assert len(fe_refs) == 2

        types = [ann.type for ann in fe_refs]
        assert "fex" in types
        assert "fen" in types

    def test_get_targets(self):
        """Test getting target annotations."""
        text = "To <t>abandon</t> means to <t>leave</t> behind"
        annotated = AnnotatedText.parse(text)

        targets = annotated.get_targets()
        assert len(targets) == 2
        assert targets[0].text == "abandon"
        assert targets[1].text == "leave"

    def test_ref_id_parsing(self):
        """Test parsing ref_id attributes."""
        text = "See <fex ref_id='123' name='Example'>text</fex>"
        annotated = AnnotatedText.parse(text)

        assert len(annotated.annotations) == 1
        annotation = annotated.annotations[0]
        assert annotation.ref_id == 123
        assert annotation.name == "Example"


class TestFrameElement:
    """Test cases for FrameElement model."""

    def test_valid_frame_element(self):
        """Test creating a valid frame element."""
        definition = AnnotatedText.parse("The entity that performs an action")

        fe = FrameElement(
            id=123,
            name="Agent",
            abbrev="Agt",
            definition=definition,
            core_type="Core",
            bg_color="FF0000",
            fg_color="FFFFFF",
        )

        assert fe.id == 123
        assert fe.name == "Agent"
        assert fe.abbrev == "Agt"
        assert fe.core_type == "Core"
        assert fe.is_core()

    def test_invalid_fe_name_format(self):
        """Test validation of FE name format."""
        definition = AnnotatedText.parse("Invalid name")

        with pytest.raises(ValueError, match="Invalid frame element name format"):
            FrameElement(
                id=123,
                name="agent",  # Should start with uppercase
                abbrev="agt",
                definition=definition,
                core_type="Core",
                bg_color="FF0000",
                fg_color="FFFFFF",
            )

    def test_invalid_color_format(self):
        """Test validation of hex color format."""
        definition = AnnotatedText.parse("Valid definition")

        with pytest.raises(ValueError, match="Invalid hex color format"):
            FrameElement(
                id=123,
                name="Agent",
                abbrev="Agt",
                definition=definition,
                core_type="Core",
                bg_color="GGGGGG",  # Invalid hex
                fg_color="FFFFFF",
            )

    def test_fe_dependencies(self):
        """Test FE dependency constraints."""
        definition = AnnotatedText.parse("A dependent FE")

        fe = FrameElement(
            id=123,
            name="Dependent",
            abbrev="Dep",
            definition=definition,
            core_type="Core",
            bg_color="FF0000",
            fg_color="FFFFFF",
            requires_fe=["Agent", "Theme"],
            excludes_fe=["Goal"],
        )

        assert fe.has_dependencies()
        assert not fe.conflicts_with("Agent")
        assert fe.conflicts_with("Goal")

    def test_self_dependency_validation(self):
        """Test that FE cannot depend on itself."""
        definition = AnnotatedText.parse("Self-dependent FE")

        with pytest.raises(ValueError, match="FE cannot require itself"):
            FrameElement(
                id=123,
                name="Agent",
                abbrev="Agt",
                definition=definition,
                core_type="Core",
                bg_color="FF0000",
                fg_color="FFFFFF",
                requires_fe=["Agent"],
            )

        with pytest.raises(ValueError, match="FE cannot exclude itself"):
            FrameElement(
                id=123,
                name="Agent",
                abbrev="Agt",
                definition=definition,
                core_type="Core",
                bg_color="FF0000",
                fg_color="FFFFFF",
                excludes_fe=["Agent"],
            )

    def test_contradictory_dependencies(self):
        """Test that FE cannot both require and exclude the same FE."""
        definition = AnnotatedText.parse("Contradictory dependencies")

        with pytest.raises(ValueError, match="cannot both require and exclude"):
            FrameElement(
                id=123,
                name="Agent",
                abbrev="Agt",
                definition=definition,
                core_type="Core",
                bg_color="FF0000",
                fg_color="FFFFFF",
                requires_fe=["Theme"],
                excludes_fe=["Theme"],
            )

    def test_peripheral_fe(self):
        """Test peripheral frame element."""
        definition = AnnotatedText.parse("A peripheral element")

        fe = FrameElement(
            id=123,
            name="Manner",
            abbrev="Man",
            definition=definition,
            core_type="Peripheral",
            bg_color="00FF00",
            fg_color="000000",
        )

        assert not fe.is_core()

    def test_username_validation(self):
        """Test username format validation."""
        definition = AnnotatedText.parse("Created by user")

        fe = FrameElement(
            id=123,
            name="Agent",
            abbrev="Agt",
            definition=definition,
            core_type="Core",
            bg_color="FF0000",
            fg_color="FFFFFF",
            created_by="JKR",
        )

        assert fe.created_by == "JKR"

        with pytest.raises(ValueError, match="Invalid username format"):
            FrameElement(
                id=123,
                name="Agent",
                abbrev="Agt",
                definition=definition,
                core_type="Core",
                bg_color="FF0000",
                fg_color="FFFFFF",
                created_by="123invalid",  # Cannot start with number
            )


class TestFrame:
    """Test cases for Frame model."""

    def test_valid_frame(self):
        """Test creating a valid frame."""
        definition = AnnotatedText.parse("An <fex>Agent</fex> leaves behind a <fex>Theme</fex>")

        agent_fe = FrameElement(
            id=1,
            name="Agent",
            abbrev="Agt",
            definition=AnnotatedText.parse("The leaver"),
            core_type="Core",
            bg_color="FF0000",
            fg_color="FFFFFF",
        )

        theme_fe = FrameElement(
            id=2,
            name="Theme",
            abbrev="Thm",
            definition=AnnotatedText.parse("What is left behind"),
            core_type="Core",
            bg_color="00FF00",
            fg_color="000000",
        )

        frame = Frame(
            id=2031,
            name="Abandonment",
            definition=definition,
            frame_elements=[agent_fe, theme_fe],
        )

        assert frame.id == 2031
        assert frame.name == "Abandonment"
        assert len(frame.frame_elements) == 2

    def test_get_fe_by_name(self):
        """Test getting FE by name."""
        definition = AnnotatedText.parse("A frame definition")

        agent_fe = FrameElement(
            id=1,
            name="Agent",
            abbrev="Agt",
            definition=AnnotatedText.parse("The agent"),
            core_type="Core",
            bg_color="FF0000",
            fg_color="FFFFFF",
        )

        frame = Frame(
            id=2031,
            name="Test_Frame",
            definition=definition,
            frame_elements=[agent_fe],
        )

        found_fe = frame.get_fe_by_name("Agent")
        assert found_fe is not None
        assert found_fe.name == "Agent"

        not_found = frame.get_fe_by_name("NonExistent")
        assert not_found is None

    def test_core_vs_peripheral_elements(self):
        """Test separation of core and peripheral elements."""
        definition = AnnotatedText.parse("Frame with mixed FE types")

        core_fe = FrameElement(
            id=1,
            name="Agent",
            abbrev="Agt",
            definition=AnnotatedText.parse("Core element"),
            core_type="Core",
            bg_color="FF0000",
            fg_color="FFFFFF",
        )

        peripheral_fe = FrameElement(
            id=2,
            name="Manner",
            abbrev="Man",
            definition=AnnotatedText.parse("Peripheral element"),
            core_type="Peripheral",
            bg_color="00FF00",
            fg_color="000000",
        )

        frame = Frame(
            id=2031,
            name="Test_Frame",
            definition=definition,
            frame_elements=[core_fe, peripheral_fe],
        )

        core_elements = frame.get_core_elements()
        assert len(core_elements) == 1
        assert core_elements[0].name == "Agent"

        peripheral_elements = frame.get_peripheral_elements()
        assert len(peripheral_elements) == 1
        assert peripheral_elements[0].name == "Manner"

    def test_duplicate_fe_names(self):
        """Test validation against duplicate FE names."""
        definition = AnnotatedText.parse("Frame with duplicate FEs")

        fe1 = FrameElement(
            id=1,
            name="Agent",
            abbrev="Agt1",
            definition=AnnotatedText.parse("First agent"),
            core_type="Core",
            bg_color="FF0000",
            fg_color="FFFFFF",
        )

        fe2 = FrameElement(
            id=2,
            name="Agent",  # Duplicate name
            abbrev="Agt2",
            definition=AnnotatedText.parse("Second agent"),
            core_type="Core",
            bg_color="00FF00",
            fg_color="000000",
        )

        with pytest.raises(ValueError, match="Duplicate frame element names"):
            Frame(
                id=2031,
                name="Test_Frame",
                definition=definition,
                frame_elements=[fe1, fe2],
            )

    def test_unknown_fe_dependencies(self):
        """Test validation of FE dependency references."""
        definition = AnnotatedText.parse("Frame with invalid dependencies")

        fe = FrameElement(
            id=1,
            name="Agent",
            abbrev="Agt",
            definition=AnnotatedText.parse("Agent with bad dependency"),
            core_type="Core",
            bg_color="FF0000",
            fg_color="FFFFFF",
            requires_fe=["NonExistent"],  # FE doesn't exist in frame
        )

        with pytest.raises(ValueError, match="requires unknown FE"):
            Frame(
                id=2031,
                name="Test_Frame",
                definition=definition,
                frame_elements=[fe],
            )

    def test_validate_fe_constraints(self):
        """Test FE constraint validation method."""
        definition = AnnotatedText.parse("Frame for constraint testing")

        agent_fe = FrameElement(
            id=1,
            name="Agent",
            abbrev="Agt",
            definition=AnnotatedText.parse("The agent"),
            core_type="Core",
            bg_color="FF0000",
            fg_color="FFFFFF",
            requires_fe=["Theme"],
        )

        theme_fe = FrameElement(
            id=2,
            name="Theme",
            abbrev="Thm",
            definition=AnnotatedText.parse("The theme"),
            core_type="Core",
            bg_color="00FF00",
            fg_color="000000",
            excludes_fe=["Goal"],
        )

        goal_fe = FrameElement(
            id=3,
            name="Goal",
            abbrev="Gol",
            definition=AnnotatedText.parse("The goal"),
            core_type="Peripheral",
            bg_color="0000FF",
            fg_color="FFFFFF",
        )

        frame = Frame(
            id=2031,
            name="Test_Frame",
            definition=definition,
            frame_elements=[agent_fe, theme_fe, goal_fe],
        )

        # Valid FE set
        result = frame.validate_fe_constraints(["Agent", "Theme"])
        assert len(result["errors"]) == 0

        # Missing required FE
        result = frame.validate_fe_constraints(["Agent"])
        assert len(result["errors"]) == 1
        assert "requires missing FEs" in result["errors"][0]

        # Conflicting FEs
        result = frame.validate_fe_constraints(["Theme", "Goal"])
        assert len(result["errors"]) == 1
        assert "conflicts with present FEs" in result["errors"][0]

        # Unknown FE
        result = frame.validate_fe_constraints(["Unknown"])
        assert len(result["errors"]) == 1
        assert "Unknown frame element" in result["errors"][0]

    def test_invalid_frame_name_format(self):
        """Test validation of frame name format."""
        definition = AnnotatedText.parse("Frame with invalid name")

        with pytest.raises(ValueError, match="Invalid frame name format"):
            Frame(
                id=2031,
                name="abandonment",  # Should start with uppercase
                definition=definition,
                frame_elements=[],
            )


class TestFERelation:
    """Test cases for FERelation model."""

    def test_valid_fe_relation(self):
        """Test creating a valid FE relation."""
        fe_rel = FERelation(
            sub_fe_name="Giver",
            super_fe_name="Agent",
            relation_type="Inheritance",
            alignment_confidence=0.95,
            semantic_similarity=0.92,
        )

        assert fe_rel.sub_fe_name == "Giver"
        assert fe_rel.super_fe_name == "Agent"
        assert fe_rel.is_inheritance()
        assert not fe_rel.is_equivalence()

    def test_combined_score_calculation(self):
        """Test combined confidence score calculation."""
        fe_rel = FERelation(
            sub_fe_name="Giver",
            super_fe_name="Agent",
            alignment_confidence=0.9,
            semantic_similarity=0.8,
            syntactic_similarity=0.85,
        )

        expected_score = (0.9 + 0.8 + 0.85) / 3
        assert abs(fe_rel.get_combined_score() - expected_score) < 0.001

    def test_missing_fe_validation(self):
        """Test validation requires at least one FE reference."""
        with pytest.raises(ValueError, match="sub_fe_id or sub_fe_name must be provided"):
            FERelation(
                super_fe_name="Agent",
                relation_type="Inheritance",
            )

        with pytest.raises(ValueError, match="super_fe_id or super_fe_name must be provided"):
            FERelation(
                sub_fe_name="Giver",
                relation_type="Inheritance",
            )


class TestFrameRelation:
    """Test cases for FrameRelation model."""

    def test_valid_frame_relation(self):
        """Test creating a valid frame relation."""
        fe_rel = FERelation(
            sub_fe_name="Giver",
            super_fe_name="Agent",
            relation_type="Inheritance",
        )

        frame_rel = FrameRelation(
            type="Inherits from",
            sub_frame_name="Giving",
            super_frame_name="Transfer",
            fe_relations=[fe_rel],
        )

        assert frame_rel.type == "Inherits from"
        assert frame_rel.is_inheritance()
        assert len(frame_rel.fe_relations) == 1

    def test_get_fe_mapping(self):
        """Test getting FE mapping by name."""
        fe_rel1 = FERelation(sub_fe_name="Giver", super_fe_name="Agent")
        fe_rel2 = FERelation(sub_fe_name="Recipient", super_fe_name="Goal")

        frame_rel = FrameRelation(
            type="Inherits from",
            sub_frame_name="Giving",
            super_frame_name="Transfer",
            fe_relations=[fe_rel1, fe_rel2],
        )

        mapping = frame_rel.get_fe_mapping("Giver")
        assert mapping is not None
        assert mapping.super_fe_name == "Agent"

        no_mapping = frame_rel.get_fe_mapping("NonExistent")
        assert no_mapping is None


class TestSemanticType:
    """Test cases for SemanticType model."""

    def test_root_semantic_type(self):
        """Test root semantic type creation."""
        sem_type = SemanticType(
            id=1,
            name="Sentient",
            abbrev="sent",
            definition="Capable of perception and feeling",
        )

        assert sem_type.is_root_type()
        assert sem_type.get_depth() == 0

    def test_semantic_type_with_parent(self):
        """Test semantic type with parent."""
        sem_type = SemanticType(
            id=2,
            name="Human",
            abbrev="hum",
            definition="A human being",
            super_type_id=1,
            super_type_name="Sentient",
        )

        assert not sem_type.is_root_type()
        assert sem_type.get_depth() == 1

    def test_incomplete_parent_info(self):
        """Test validation of parent type information."""
        with pytest.raises(ValueError, match="super_type_name required"):
            SemanticType(
                id=2,
                name="Human",
                abbrev="hum",
                definition="A human being",
                super_type_id=1,  # Missing super_type_name
            )

        with pytest.raises(ValueError, match="super_type_id required"):
            SemanticType(
                id=2,
                name="Human",
                abbrev="hum",
                definition="A human being",
                super_type_name="Sentient",  # Missing super_type_id
            )


class TestFrameIndexEntry:
    """Test cases for FrameIndexEntry model."""

    def test_valid_frame_index_entry(self):
        """Test creating a valid frame index entry."""
        entry = FrameIndexEntry(
            id=2031,
            name="Abandonment",
            modified_date=datetime.now(UTC),
        )

        assert entry.id == 2031
        assert entry.name == "Abandonment"
        assert isinstance(entry.modified_date, datetime)

    def test_invalid_frame_name_in_index(self):
        """Test validation of frame name in index entry."""
        with pytest.raises(ValueError, match="Invalid frame name format"):
            FrameIndexEntry(
                id=2031,
                name="abandonment",  # Should start with uppercase
                modified_date=datetime.now(UTC),
            )


class TestIntegration:
    """Integration tests for model interactions."""

    def test_frame_with_annotated_definition(self):
        """Test frame with properly parsed definition."""
        definition_text = "An <fex>Agent</fex> leaves behind a <fex name='Theme'>possession</fex>"
        definition = AnnotatedText.parse(definition_text)

        agent_fe = FrameElement(
            id=1,
            name="Agent",
            abbrev="Agt",
            definition=AnnotatedText.parse("The entity that abandons"),
            core_type="Core",
            bg_color="FF0000",
            fg_color="FFFFFF",
        )

        theme_fe = FrameElement(
            id=2,
            name="Theme",
            abbrev="Thm",
            definition=AnnotatedText.parse("What is abandoned"),
            core_type="Core",
            bg_color="00FF00",
            fg_color="000000",
        )

        frame = Frame(
            id=2031,
            name="Abandonment",
            definition=definition,
            frame_elements=[agent_fe, theme_fe],
        )

        # Verify definition parsing
        assert "Agent leaves behind a possession" in frame.definition.plain_text
        assert len(frame.definition.annotations) == 2

        # Verify FE references in definition match actual FEs
        fe_refs = frame.definition.get_fe_references()
        fe_names_in_def = {ann.name or ann.text for ann in fe_refs}
        actual_fe_names = {fe.name for fe in frame.frame_elements}

        # Should have some overlap (though not necessarily complete)
        assert len(fe_names_in_def & actual_fe_names) > 0

    def test_json_serialization_roundtrip(self):
        """Test that models can be serialized and deserialized."""
        definition = AnnotatedText.parse("An <fex>Agent</fex> performs an action")

        agent_fe = FrameElement(
            id=1,
            name="Agent",
            abbrev="Agt",
            definition=AnnotatedText.parse("The performer"),
            core_type="Core",
            bg_color="FF0000",
            fg_color="FFFFFF",
            requires_fe=["Theme"],
        )

        theme_fe = FrameElement(
            id=2,
            name="Theme",
            abbrev="Thm",
            definition=AnnotatedText.parse("The affected entity"),
            core_type="Core",
            bg_color="00FF00",
            fg_color="000000",
        )

        original_frame = Frame(
            id=2031,
            name="Action",
            definition=definition,
            frame_elements=[agent_fe, theme_fe],
            created_by="TestUser",
            created_date=datetime.now(UTC),
        )

        # Serialize to JSON Lines
        jsonl = original_frame.to_jsonl()
        assert isinstance(jsonl, str)

        # Deserialize back
        restored_frame = Frame.from_jsonl(jsonl)

        # Verify all data is preserved
        assert restored_frame.id == original_frame.id
        assert restored_frame.name == original_frame.name
        assert len(restored_frame.frame_elements) == 2
        assert restored_frame.frame_elements[0].requires_fe == ["Theme"]

        # Verify the annotated definition is preserved
        assert len(restored_frame.definition.annotations) == 1
        assert restored_frame.definition.annotations[0].type == "fex"
