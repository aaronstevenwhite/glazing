"""Tests for reference extraction functionality."""

from datetime import UTC, datetime

from glazing.framenet.models import AnnotatedText, Frame, FrameRelation
from glazing.propbank.models import (
    Frameset,
    LexLink,
    Role,
    RoleLink,
    Roleset,
)
from glazing.references.extractor import ReferenceExtractor
from glazing.references.models import (
    CrossReference,
    MappingConfidence,
    MappingMetadata,
    VerbNetFrameNetMapping,
)
from glazing.verbnet.models import Member, VerbClass, WordNetCrossRef
from glazing.wordnet.models import Sense, Synset, Word


class TestReferenceExtractor:
    """Test the ReferenceExtractor class."""

    def test_init(self) -> None:
        """Test extractor initialization."""
        extractor = ReferenceExtractor()
        assert extractor.mapping_index is not None
        assert len(extractor.verbnet_refs) == 0
        assert len(extractor.propbank_refs) == 0
        assert len(extractor.framenet_relations) == 0
        assert len(extractor.wordnet_sense_index) == 0

    def test_extract_verbnet_references(self) -> None:
        """Test extraction of VerbNet cross-references."""
        # Create test VerbNet data
        fn_mapping = VerbNetFrameNetMapping(
            frame_name="Giving",
            confidence=MappingConfidence(
                score=0.95,
                method="manual",
                factors={"lexical": 0.9, "syntactic": 1.0},
            ),
            mapping_source="manual",
        )

        pb_mapping = CrossReference(
            source_dataset="VerbNet",
            source_id="give#2",
            source_version="3.4",
            target_dataset="PropBank",
            target_id="give.01",
            mapping_type="direct",
            confidence=None,
            metadata=MappingMetadata(
                created_date=datetime.now(UTC),
                created_by="manual",
                version="3.4",
                validation_status="validated",
            ),
        )

        wn_mapping = WordNetCrossRef(
            sense_key="give%2:40:00::",
            lemma="give",
            pos="v",
        )

        member = Member(
            name="give",
            verbnet_key="give#2",
            framenet_mappings=[fn_mapping],
            propbank_mappings=[pb_mapping],
            wordnet_mappings=[wn_mapping],
        )

        verb_class = VerbClass(
            id="give-13.1",
            members=[member],
            themroles=[],
            frames=[],
            subclasses=[],
        )

        # Extract references
        extractor = ReferenceExtractor()
        extractor.extract_verbnet_references([verb_class])

        # Check extracted references
        assert "give#2" in extractor.verbnet_refs
        vn_refs = extractor.verbnet_refs["give#2"]
        assert vn_refs.verbnet_key == "give#2"
        assert vn_refs.class_id == "give-13.1"
        assert vn_refs.lemma == "give"
        assert len(vn_refs.fn_mappings) == 1
        assert vn_refs.fn_mappings[0].frame_name == "Giving"
        assert "give.01" in vn_refs.pb_groupings
        assert len(vn_refs.wn_mappings) == 1

        # Check mapping index
        mappings = extractor.get_mappings_for_entity("give#2", "VerbNet")
        assert len(mappings) >= 2  # At least FrameNet and WordNet mappings

    def test_extract_verbnet_subclasses(self) -> None:
        """Test extraction handles VerbNet subclasses recursively."""
        # Create parent class member
        parent_member = Member(
            name="give",
            verbnet_key="give#1",
        )

        # Create subclass member
        sub_member = Member(
            name="donate",
            verbnet_key="donate#1",
        )

        subclass = VerbClass(
            id="give-13.1-1",
            members=[sub_member],
            themroles=[],
            frames=[],
            subclasses=[],
        )

        parent_class = VerbClass(
            id="give-13.1",
            members=[parent_member],
            themroles=[],
            frames=[],
            subclasses=[subclass],
        )

        # Extract references
        extractor = ReferenceExtractor()
        extractor.extract_verbnet_references([parent_class])

        # Check both parent and subclass members were extracted
        assert "give#1" in extractor.verbnet_refs
        assert "donate#1" in extractor.verbnet_refs
        assert extractor.verbnet_refs["give#1"].class_id == "give-13.1"
        assert extractor.verbnet_refs["donate#1"].class_id == "give-13.1-1"

    def test_extract_propbank_references(self) -> None:
        """Test extraction of PropBank cross-references."""
        # Create test PropBank data
        lexlink = LexLink(
            class_name="give-13.1",
            confidence=0.92,
            resource="VerbNet",
            version="3.4",
            src="manual",
        )

        rolelink = RoleLink(
            class_name="Giving",
            resource="FrameNet",
            version="1.7",
            role="Donor",
        )

        role = Role(
            n="0",
            f="PAG",
            descr="giver",
            rolelinks=[rolelink],
        )

        roleset = Roleset(
            id="give.01",
            name="transfer possession",
            roles=[role],
            lexlinks=[lexlink],
        )

        frameset = Frameset(
            predicate_lemma="give",
            rolesets=[roleset],
        )

        # Extract references
        extractor = ReferenceExtractor()
        extractor.extract_propbank_references([frameset])

        # Check extracted references
        assert "give.01" in extractor.propbank_refs
        pb_refs = extractor.propbank_refs["give.01"]
        assert pb_refs.roleset_id == "give.01"
        assert len(pb_refs.rolelinks) == 1
        assert pb_refs.rolelinks[0].class_name == "Giving"
        assert len(pb_refs.lexlinks) == 1
        assert pb_refs.lexlinks[0].class_name == "give-13.1"

        # Check mapping index
        mappings = extractor.get_mappings_for_entity("give.01", "PropBank")
        assert len(mappings) >= 2  # VerbNet and FrameNet mappings

    def test_extract_framenet_relations(self) -> None:
        """Test extraction of FrameNet frame relations."""
        # Create test FrameNet data
        frame_relation = FrameRelation(
            id=1,
            type="Inherits from",
            sub_frame_id=2001,
            sub_frame_name="Commerce_goods_transfer",
            super_frame_id=2000,
            super_frame_name="Giving",
        )

        frame = Frame(
            id=2001,
            name="Commerce_goods_transfer",
            definition=AnnotatedText.parse("Commercial transfer of goods"),
            frame_elements=[],
            lexical_units=[],
            frame_relations=[frame_relation],
        )

        # Extract references
        extractor = ReferenceExtractor()
        extractor.extract_framenet_relations([frame])

        # Check extracted relations
        assert 2001 in extractor.framenet_relations
        relations = extractor.framenet_relations[2001]
        assert len(relations) == 1
        assert relations[0].type == "Inherits from"

        # Check mapping index for inheritance
        mappings = extractor.get_mappings_for_entity("2001", "FrameNet")
        assert len(mappings) >= 1
        assert any(m.target_id == "2000" for m in mappings)

    def test_extract_wordnet_mappings(self) -> None:
        """Test extraction of WordNet sense and synset mappings."""
        # Create test WordNet data
        synset = Synset(
            offset="02232813",
            lex_filenum=40,
            lex_filename="verb.possession",
            ss_type="v",
            words=[
                Word(lemma="give", lex_id=1),
                Word(lemma="hand", lex_id=2),
            ],
            pointers=[],
            gloss="transfer possession of something",
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

        # Extract references
        extractor = ReferenceExtractor()
        extractor.extract_wordnet_mappings([synset], [sense])

        # Check sense index
        assert "give%2:40:00::" in extractor.wordnet_sense_index
        assert extractor.wordnet_sense_index["give%2:40:00::"] == "02232813"

        # Check mapping index
        mappings = extractor.get_mappings_for_entity("give%2:40:00::", "WordNet")
        assert len(mappings) >= 1
        assert any(m.target_id == "02232813" for m in mappings)

    def test_extract_all(self) -> None:
        """Test extracting from all datasets at once."""
        # Create minimal test data for each dataset
        verb_class = VerbClass(
            id="test-1.1",
            members=[],
            themroles=[],
            frames=[],
            subclasses=[],
        )

        frameset = Frameset(
            predicate_lemma="test",
            rolesets=[],
        )

        frame = Frame(
            id=1000,
            name="Testing",
            definition=AnnotatedText.parse("Test frame"),
            frame_elements=[],
            lexical_units=[],
            frame_relations=[],
        )

        synset = Synset(
            offset="00000001",
            lex_filenum=0,
            lex_filename="noun.Tops",
            ss_type="n",
            words=[],
            pointers=[],
            gloss="test",
        )

        sense = Sense(
            sense_key="test%1:00:00::",
            lemma="test",
            ss_type="n",
            lex_filenum=0,
            lex_id=0,
            synset_offset="00000001",
            sense_number=1,
            tag_count=0,
        )

        # Extract all
        extractor = ReferenceExtractor()
        extractor.extract_all(
            framenet=[frame],
            propbank=[frameset],
            verbnet=[verb_class],
            wordnet=([synset], [sense]),
        )

        # Check that all extraction methods were called
        assert 1000 in extractor.framenet_relations
        assert "test%1:00:00::" in extractor.wordnet_sense_index

    def test_get_reverse_mappings(self) -> None:
        """Test getting reverse mappings to an entity."""
        # Create a mapping
        mapping = CrossReference(
            source_dataset="VerbNet",
            source_id="give#2",
            source_version="3.4",
            target_dataset="FrameNet",
            target_id="Giving",
            mapping_type="direct",
            confidence=None,
            metadata=MappingMetadata(
                created_date=datetime.now(UTC),
                created_by="manual",
                version="3.4",
                validation_status="validated",
            ),
        )

        # Add to extractor
        extractor = ReferenceExtractor()
        extractor.mapping_index.add_mapping(mapping)

        # Get reverse mappings
        reverse = extractor.get_reverse_mappings("Giving", "FrameNet")
        assert len(reverse) == 1
        assert reverse[0].source_id == "give#2"
        assert reverse[0].source_dataset == "VerbNet"

    def test_multiple_target_mappings(self) -> None:
        """Test handling of multiple target IDs in a mapping."""
        # Create mapping with list of targets
        mapping = CrossReference(
            source_dataset="VerbNet",
            source_id="give#2",
            source_version="3.4",
            target_dataset="PropBank",
            target_id=["give.01", "give.02"],
            mapping_type="direct",
            confidence=None,
            metadata=MappingMetadata(
                created_date=datetime.now(UTC),
                created_by="manual",
                version="3.4",
                validation_status="validated",
            ),
        )

        # Add to extractor
        extractor = ReferenceExtractor()
        extractor.mapping_index.add_mapping(mapping)

        # Check reverse mappings for both targets
        reverse1 = extractor.get_reverse_mappings("give.01", "PropBank")
        reverse2 = extractor.get_reverse_mappings("give.02", "PropBank")
        assert len(reverse1) == 1
        assert len(reverse2) == 1
        assert reverse1[0].source_id == "give#2"
        assert reverse2[0].source_id == "give#2"
