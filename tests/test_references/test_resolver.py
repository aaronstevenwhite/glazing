"""Tests for reference resolution functionality."""

from datetime import UTC, datetime

import pytest

from glazing.framenet.models import AnnotatedText, FERelation, Frame, FrameRelation
from glazing.propbank.models import Frameset, Roleset
from glazing.references.models import (
    CrossReference,
    MappingConfidence,
    MappingMetadata,
    VerbNetFrameNetMapping,
)
from glazing.references.resolver import ReferenceResolver
from glazing.verbnet.models import Member, VerbClass
from glazing.wordnet.models import Sense, Synset


class TestReferenceResolver:
    """Test the ReferenceResolver class."""

    def test_init(self) -> None:
        """Test resolver initialization."""
        resolver = ReferenceResolver()
        assert resolver.mapping_index is not None
        assert len(resolver.framenet_frames) == 0
        assert len(resolver.propbank_rolesets) == 0
        assert len(resolver.verbnet_classes) == 0
        assert len(resolver.wordnet_synsets) == 0
        assert len(resolver.wordnet_senses) == 0

    def test_set_datasets(self) -> None:
        """Test setting datasets for validation."""
        # Create test data
        frame = Frame(
            id=1000,
            name="Giving",
            definition=AnnotatedText.parse("Transfer of possession"),
            frame_elements=[],
            lexical_units=[],
            frame_relations=[],
        )

        frameset = Frameset(
            predicate_lemma="give",
            rolesets=[
                Roleset(
                    id="give.01",
                    roles=[],
                )
            ],
        )

        verb_class = VerbClass(
            id="give-13.1",
            members=[],
            themroles=[],
            frames=[],
            subclasses=[],
        )

        synset = Synset(
            offset="02232813",
            lex_filenum=40,
            lex_filename="verb.possession",
            ss_type="v",
            words=[],
            pointers=[],
            gloss="transfer possession",
        )

        sense = Sense(
            sense_key="give%2:40:00::",
            lemma="give",
            ss_type="v",
            lex_filenum=40,
            lex_id=1,
            synset_offset="02232813",
            sense_number=1,
            tag_count=100,
        )

        # Set datasets
        resolver = ReferenceResolver()
        resolver.set_datasets(
            framenet=[frame],
            propbank=[frameset],
            verbnet=[verb_class],
            wordnet=([synset], [sense]),
        )

        # Check indexing
        assert "Giving" in resolver.framenet_frames
        assert "give.01" in resolver.propbank_rolesets
        assert "give-13.1" in resolver.verbnet_classes
        assert "02232813" in resolver.wordnet_synsets
        assert "give%2:40:00::" in resolver.wordnet_senses

    def test_validate_reference_valid(self) -> None:
        """Test validation of valid references."""
        # Set up test data
        frame = Frame(
            id=1000,
            name="Giving",
            definition=AnnotatedText.parse("Transfer"),
            frame_elements=[],
            lexical_units=[],
            frame_relations=[],
        )

        resolver = ReferenceResolver()
        resolver.set_datasets(framenet=[frame])

        # Create valid reference
        ref = CrossReference(
            source_dataset="VerbNet",
            source_id="give#2",
            source_version="3.4",
            target_dataset="FrameNet",
            target_id="Giving",
            mapping_type="direct",
            confidence=None,
            metadata=MappingMetadata(
                created_date=datetime.now(UTC),
                created_by="test",
                version="1.0",
                validation_status="validated",
            ),
        )

        # Validate
        assert resolver.validate_reference(ref) is True

    def test_validate_reference_invalid(self) -> None:
        """Test validation of invalid references."""
        resolver = ReferenceResolver()
        resolver.set_datasets(framenet=[])  # No frames

        # Create invalid reference
        ref = CrossReference(
            source_dataset="VerbNet",
            source_id="give#2",
            source_version="3.4",
            target_dataset="FrameNet",
            target_id="NonexistentFrame",
            mapping_type="direct",
            confidence=None,
            metadata=MappingMetadata(
                created_date=datetime.now(UTC),
                created_by="test",
                version="1.0",
                validation_status="validated",
            ),
        )

        # Validate
        assert resolver.validate_reference(ref) is False

    def test_validate_reference_multiple_targets(self) -> None:
        """Test validation with multiple target IDs."""
        # Set up test data
        frameset = Frameset(
            predicate_lemma="give",
            rolesets=[
                Roleset(id="give.01", roles=[]),
                Roleset(id="give.02", roles=[]),
            ],
        )

        resolver = ReferenceResolver()
        resolver.set_datasets(propbank=[frameset])

        # Create reference with multiple targets
        ref = CrossReference(
            source_dataset="VerbNet",
            source_id="give#2",
            source_version="3.4",
            target_dataset="PropBank",
            target_id=["give.01", "give.02"],
            mapping_type="direct",
            confidence=None,
            metadata=MappingMetadata(
                created_date=datetime.now(UTC),
                created_by="test",
                version="1.0",
                validation_status="validated",
            ),
        )

        # All targets exist
        assert resolver.validate_reference(ref) is True

        # One target doesn't exist
        ref.target_id = ["give.01", "give.99"]
        assert resolver.validate_reference(ref) is False

    def test_resolve_transitive_simple(self) -> None:
        """Test simple transitive resolution through one intermediate."""
        resolver = ReferenceResolver()

        # Create mapping chain: VerbNet -> PropBank -> FrameNet
        vn_to_pb = CrossReference(
            source_dataset="VerbNet",
            source_id="give#2",
            source_version="3.4",
            target_dataset="PropBank",
            target_id="give.01",
            mapping_type="direct",
            confidence=MappingConfidence(score=0.9, method="manual", factors={}),
            metadata=MappingMetadata(
                created_date=datetime.now(UTC),
                created_by="test",
                version="1.0",
                validation_status="validated",
            ),
        )

        pb_to_fn = CrossReference(
            source_dataset="PropBank",
            source_id="give.01",
            source_version="3.0",
            target_dataset="FrameNet",
            target_id="Giving",
            mapping_type="direct",
            confidence=MappingConfidence(score=0.8, method="manual", factors={}),
            metadata=MappingMetadata(
                created_date=datetime.now(UTC),
                created_by="test",
                version="1.0",
                validation_status="validated",
            ),
        )

        # Add to index
        resolver.mapping_index.add_mapping(vn_to_pb)
        resolver.mapping_index.add_mapping(pb_to_fn)

        # Resolve transitive
        results = resolver.resolve_transitive("give#2", "VerbNet", "FrameNet")

        assert len(results) == 1
        assert results[0].source_id == "give#2"
        assert results[0].target_id == "Giving"
        assert len(results[0].path) == 2
        assert results[0].combined_confidence == pytest.approx(0.72)  # 0.9 * 0.8

    def test_resolve_transitive_max_hops(self) -> None:
        """Test transitive resolution respects max_hops."""
        resolver = ReferenceResolver()

        # Create longer chain
        mappings = [
            CrossReference(
                source_dataset="VerbNet",
                source_id="give#2",
                source_version="3.4",
                target_dataset="PropBank",
                target_id="give.01",
                mapping_type="direct",
                confidence=None,
                metadata=MappingMetadata(
                    created_date=datetime.now(UTC),
                    created_by="test",
                    version="1.0",
                    validation_status="validated",
                ),
            ),
            CrossReference(
                source_dataset="PropBank",
                source_id="give.01",
                source_version="3.0",
                target_dataset="WordNet",
                target_id="02232813",
                mapping_type="direct",
                confidence=None,
                metadata=MappingMetadata(
                    created_date=datetime.now(UTC),
                    created_by="test",
                    version="1.0",
                    validation_status="validated",
                ),
            ),
            CrossReference(
                source_dataset="WordNet",
                source_id="02232813",
                source_version="3.1",
                target_dataset="FrameNet",
                target_id="Giving",
                mapping_type="direct",
                confidence=None,
                metadata=MappingMetadata(
                    created_date=datetime.now(UTC),
                    created_by="test",
                    version="1.0",
                    validation_status="validated",
                ),
            ),
        ]

        for mapping in mappings:
            resolver.mapping_index.add_mapping(mapping)

        # With max_hops=2, should not find the path
        results = resolver.resolve_transitive("give#2", "VerbNet", "FrameNet", max_hops=2)
        assert len(results) == 0

        # With max_hops=3, should find it
        results = resolver.resolve_transitive("give#2", "VerbNet", "FrameNet", max_hops=3)
        assert len(results) == 1

    def test_resolve_verbnet_inheritance(self) -> None:
        """Test resolution of VerbNet inherited mappings."""
        # Create parent class with mappings
        parent_fn_mapping = VerbNetFrameNetMapping(
            frame_name="Giving",
            confidence=MappingConfidence(score=0.9, method="manual", factors={}),
            mapping_source="manual",
        )

        parent_member = Member(
            name="give",
            verbnet_key="give#1",
            framenet_mappings=[parent_fn_mapping],
        )

        parent_class = VerbClass(
            id="give-13.1",
            members=[parent_member],
            themroles=[],
            frames=[],
            subclasses=[],
            parent_class=None,
        )

        # Create subclass member without mappings
        sub_member = Member(
            name="give",
            verbnet_key="give#2",
            inherited_from_class="give-13.1-1",
        )

        subclass = VerbClass(
            id="give-13.1-1",
            members=[sub_member],
            themroles=[],
            frames=[],
            subclasses=[],
            parent_class="give-13.1",
        )

        # Build hierarchy
        hierarchy = {
            "give-13.1": parent_class,
            "give-13.1-1": subclass,
        }

        # Resolve inheritance
        resolver = ReferenceResolver()
        inherited = resolver.resolve_verbnet_inheritance(sub_member, hierarchy)

        assert len(inherited) == 1
        assert inherited[0].target_id == "Giving"
        assert inherited[0].mapping_type == "inferred"
        assert inherited[0].confidence is not None
        assert inherited[0].confidence.score == pytest.approx(0.81)  # 0.9 * 0.9
        assert inherited[0].inherited_from == "give-13.1"

    def test_resolve_framenet_fe_inheritance(self) -> None:
        """Test resolution of FrameNet FE inheritance."""
        # Create frame relation with FE mappings
        fe_relation = FERelation(
            sub_fe_id=101,
            sub_fe_name="Donor",
            super_fe_id=100,
            super_fe_name="Agent",
            relation_type="Inheritance",
            alignment_confidence=0.95,
            semantic_similarity=0.9,
            syntactic_similarity=0.85,
        )

        frame_relation = FrameRelation(
            id=1,
            type="Inherits from",
            sub_frame_id=2001,
            sub_frame_name="Commerce_goods_transfer",
            super_frame_id=2000,
            super_frame_name="Giving",
            fe_relations=[fe_relation],
        )

        frame = Frame(
            id=2001,
            name="Commerce_goods_transfer",
            definition=AnnotatedText.parse("Commercial transfer"),
            frame_elements=[],
            lexical_units=[],
            frame_relations=[],
        )

        # Resolve FE inheritance
        resolver = ReferenceResolver()
        alignments = resolver.resolve_framenet_fe_inheritance(frame, [frame_relation])

        assert len(alignments) == 1
        assert alignments[0].source_fe == "Donor"
        assert alignments[0].target_role == "Agent"
        assert alignments[0].alignment_type == "inherited"
        assert alignments[0].confidence.score == 0.95

    def test_trace_fe_inheritance_chain(self) -> None:
        """Test tracing FE inheritance through frame hierarchy."""
        # Create frame hierarchy
        fe_rel1 = FERelation(
            sub_fe_name="Donor",
            super_fe_name="Agent",
            relation_type="Inheritance",
        )

        relation1 = FrameRelation(
            type="Inherits from",
            super_frame_name="Transfer",
            fe_relations=[fe_rel1],
        )

        fe_rel2 = FERelation(
            sub_fe_name="Agent",
            super_fe_name="Actor",
            relation_type="Inheritance",
        )

        relation2 = FrameRelation(
            type="Inherits from",
            super_frame_name="Event",
            fe_relations=[fe_rel2],
        )

        frame1 = Frame(
            id=1,
            name="Giving",
            definition=AnnotatedText.parse(""),
            frame_elements=[],
            lexical_units=[],
            frame_relations=[relation1],
        )

        frame2 = Frame(
            id=2,
            name="Transfer",
            definition=AnnotatedText.parse(""),
            frame_elements=[],
            lexical_units=[],
            frame_relations=[relation2],
        )

        frame_index = {"Giving": frame1, "Transfer": frame2}

        # Trace chain
        resolver = ReferenceResolver()
        chain = resolver.trace_fe_inheritance_chain("Donor", "Giving", frame_index)

        assert chain.fe_name == "Donor"
        assert chain.frame_chain == ["Giving", "Transfer", "Event"]
        assert len(chain.inheritance_path) == 2

    def test_calculate_combined_confidence(self) -> None:
        """Test confidence calculation for transitive paths."""
        resolver = ReferenceResolver()

        # Path with all confidence scores
        path = [
            CrossReference(
                source_dataset="VerbNet",
                source_id="a",
                source_version="1",
                target_dataset="PropBank",
                target_id="b",
                mapping_type="direct",
                confidence=MappingConfidence(score=0.9, method="", factors={}),
                metadata=MappingMetadata(
                    created_date=datetime.now(UTC),
                    created_by="test",
                    version="1.0",
                    validation_status="validated",
                ),
            ),
            CrossReference(
                source_dataset="PropBank",
                source_id="b",
                source_version="1",
                target_dataset="FrameNet",
                target_id="c",
                mapping_type="direct",
                confidence=MappingConfidence(score=0.8, method="", factors={}),
                metadata=MappingMetadata(
                    created_date=datetime.now(UTC),
                    created_by="test",
                    version="1.0",
                    validation_status="validated",
                ),
            ),
        ]

        score = resolver.calculate_combined_confidence(path)
        assert score == pytest.approx(0.72)

        # Path with missing confidence
        path[1].confidence = None
        score = resolver.calculate_combined_confidence(path)
        assert score == pytest.approx(0.45)  # 0.9 * 0.5 (default)

        # Empty path
        assert resolver.calculate_combined_confidence([]) == 0.0

    def test_detect_conflicts(self) -> None:
        """Test detection of conflicting mappings."""
        # Create conflicting high-confidence mappings
        mappings = [
            CrossReference(
                source_dataset="VerbNet",
                source_id="give#2",
                source_version="3.4",
                target_dataset="FrameNet",
                target_id="Giving",
                mapping_type="manual",
                confidence=MappingConfidence(score=0.9, method="", factors={}),
                metadata=MappingMetadata(
                    created_date=datetime.now(UTC),
                    created_by="test",
                    version="1.0",
                    validation_status="validated",
                ),
            ),
            CrossReference(
                source_dataset="VerbNet",
                source_id="give#2",
                source_version="3.4",
                target_dataset="FrameNet",
                target_id="Transfer",
                mapping_type="automatic",
                confidence=MappingConfidence(score=0.85, method="", factors={}),
                metadata=MappingMetadata(
                    created_date=datetime.now(UTC),
                    created_by="test",
                    version="1.0",
                    validation_status="validated",
                ),
            ),
        ]

        resolver = ReferenceResolver()
        conflicts = resolver.detect_conflicts(mappings)

        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "ambiguous"
        assert conflicts[0].source_id == "give#2"
        assert len(conflicts[0].conflicting_mappings) == 2

    def test_detect_conflicts_no_conflict(self) -> None:
        """Test that low-confidence mappings don't create conflicts."""
        # One high, one low confidence
        mappings = [
            CrossReference(
                source_dataset="VerbNet",
                source_id="give#2",
                source_version="3.4",
                target_dataset="FrameNet",
                target_id="Giving",
                mapping_type="manual",
                confidence=MappingConfidence(score=0.9, method="", factors={}),
                metadata=MappingMetadata(
                    created_date=datetime.now(UTC),
                    created_by="test",
                    version="1.0",
                    validation_status="validated",
                ),
            ),
            CrossReference(
                source_dataset="VerbNet",
                source_id="give#2",
                source_version="3.4",
                target_dataset="FrameNet",
                target_id="Transfer",
                mapping_type="automatic",
                confidence=MappingConfidence(score=0.3, method="", factors={}),
                metadata=MappingMetadata(
                    created_date=datetime.now(UTC),
                    created_by="test",
                    version="1.0",
                    validation_status="validated",
                ),
            ),
        ]

        resolver = ReferenceResolver()
        conflicts = resolver.detect_conflicts(mappings)

        assert len(conflicts) == 0  # Low confidence doesn't create conflict

    def test_verbnet_class_indexing(self) -> None:
        """Test that VerbNet classes are indexed recursively."""
        # Create nested structure
        subsubclass = VerbClass(
            id="give-13.1-1-1",
            members=[],
            themroles=[],
            frames=[],
            subclasses=[],
        )

        subclass = VerbClass(
            id="give-13.1-1",
            members=[],
            themroles=[],
            frames=[],
            subclasses=[subsubclass],
        )

        parent = VerbClass(
            id="give-13.1",
            members=[],
            themroles=[],
            frames=[],
            subclasses=[subclass],
        )

        resolver = ReferenceResolver()
        resolver.set_datasets(verbnet=[parent])

        # All levels should be indexed
        assert "give-13.1" in resolver.verbnet_classes
        assert "give-13.1-1" in resolver.verbnet_classes
        assert "give-13.1-1-1" in resolver.verbnet_classes
