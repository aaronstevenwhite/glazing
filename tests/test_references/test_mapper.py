"""Tests for role alignment and concept mapping functionality."""

from glazing.framenet.models import AnnotatedText, Frame, FrameElement
from glazing.propbank.models import Role, Roleset
from glazing.references.mapper import ReferenceMapper
from glazing.references.models import (
    RoleMappingTable,
)
from glazing.verbnet.models import (
    SelectionalRestriction,
    SelectionalRestrictions,
    ThematicRole,
    VerbClass,
)
from glazing.wordnet.models import Sense


class TestReferenceMapper:
    """Test the ReferenceMapper class."""

    def test_init(self) -> None:
        """Test mapper initialization."""
        mapper = ReferenceMapper()
        assert len(mapper.role_alignments) == 0
        assert len(mapper.concept_alignments) == 0
        assert len(mapper.role_mapping_tables) > 0  # Default mappings loaded

    def test_default_role_mappings(self) -> None:
        """Test that default role mappings are initialized."""
        mapper = ReferenceMapper()

        # Check for Agent mapping
        agent_table = next(
            (t for t in mapper.role_mapping_tables if t.verbnet_role == "Agent"),
            None,
        )
        assert agent_table is not None
        assert agent_table.framenet_fe == "Agent"
        assert agent_table.propbank_arg == "ARG0"

        # Check for Theme mapping
        theme_table = next(
            (t for t in mapper.role_mapping_tables if t.verbnet_role == "Theme"),
            None,
        )
        assert theme_table is not None
        assert theme_table.propbank_arg == "ARG1"

    def test_align_roles_basic(self) -> None:
        """Test basic role alignment."""
        # Create test data
        verbnet_role = ThematicRole(
            type="Agent",
            sel_restrictions=None,
        )

        verb_class = VerbClass(
            id="give-13.1",
            members=[],
            themroles=[verbnet_role],
            frames=[],
            subclasses=[],
        )

        frame = Frame(
            id=1000,
            name="Giving",
            definition=AnnotatedText.parse("Transfer"),
            frame_elements=[
                FrameElement(
                    id=1,
                    name="Agent",
                    abbrev="Agt",
                    definition=AnnotatedText.parse("The giver"),
                    core_type="Core",
                    bg_color="FF0000",
                    fg_color="FFFFFF",
                )
            ],
            lexical_units=[],
            frame_relations=[],
        )

        roleset = Roleset(
            id="give.01",
            roles=[
                Role(
                    n="0",
                    f="PAG",
                    descr="giver",
                    rolelinks=[],
                )
            ],
        )

        # Align roles
        mapper = ReferenceMapper()
        mapping = mapper.align_roles(verbnet_role, verb_class, frame, roleset)

        assert mapping.concept == "agent"
        assert ("give-13.1", "Agent") in mapping.verbnet_roles
        assert ("Giving", "Agent") in mapping.framenet_fes
        assert ("give.01", "ARG0") in mapping.propbank_args

    def test_align_roles_no_framenet(self) -> None:
        """Test role alignment without FrameNet frame."""
        verbnet_role = ThematicRole(
            type="Theme",
            sel_restrictions=None,
        )

        verb_class = VerbClass(
            id="give-13.1",
            members=[],
            themroles=[verbnet_role],
            frames=[],
            subclasses=[],
        )

        mapper = ReferenceMapper()
        mapping = mapper.align_roles(verbnet_role, verb_class, None, None)

        assert mapping.concept == "theme"
        assert len(mapping.framenet_fes) == 0
        assert len(mapping.propbank_args) == 0

    def test_align_with_framenet_fe(self) -> None:
        """Test alignment with FrameNet frame elements."""
        mapper = ReferenceMapper()

        # Test with matching FE
        role = ThematicRole(type="Recipient")
        frame = Frame(
            id=1,
            name="Giving",
            definition=AnnotatedText.parse(""),
            frame_elements=[
                FrameElement(
                    id=1,
                    name="Recipient",
                    abbrev="Rec",
                    definition=AnnotatedText.parse(""),
                    core_type="Core",
                    bg_color="000000",
                    fg_color="FFFFFF",
                )
            ],
            lexical_units=[],
            frame_relations=[],
        )

        fe_name = mapper._align_with_framenet_fe(role, frame)
        assert fe_name == "Recipient"

        # Test with no matching FE
        role = ThematicRole(type="Instrument")
        fe_name = mapper._align_with_framenet_fe(role, frame)
        assert fe_name is None

    def test_align_with_propbank_arg(self) -> None:
        """Test alignment with PropBank arguments."""
        mapper = ReferenceMapper()

        # Test Agent -> ARG0
        role = ThematicRole(type="Agent")
        roleset = Roleset(
            id="test.01",
            roles=[
                Role(
                    n="0",
                    f="PAG",
                    descr="agent",
                    rolelinks=[],
                )
            ],
        )

        arg = mapper._align_with_propbank_arg(role, roleset)
        assert arg == "ARG0"

        # Test Patient -> ARG1
        role = ThematicRole(type="Patient")
        roleset.roles.append(
            Role(
                n="1",
                f="PPT",
                descr="patient",
                rolelinks=[],
            )
        )

        arg = mapper._align_with_propbank_arg(role, roleset)
        assert arg == "ARG1"

    def test_map_concepts(self) -> None:
        """Test concept mapping across datasets."""
        mapper = ReferenceMapper()

        alignment = mapper.map_concepts(
            concept_name="transfer_possession",
            framenet_frames=["Giving", "Transfer"],
            propbank_rolesets=["give.01", "transfer.01"],
            verbnet_classes=["give-13.1", "contribute-13.2"],
            wordnet_synsets=["02232813", "02232523"],
        )

        assert alignment.concept_name == "transfer_possession"
        assert "Giving" in alignment.framenet_frames
        assert "give.01" in alignment.propbank_rolesets
        assert "give-13.1" in alignment.verbnet_classes
        assert "02232813" in alignment.wordnet_synsets
        assert alignment.confidence == 1.0  # All 4 datasets covered

    def test_concept_confidence_calculation(self) -> None:
        """Test confidence calculation for concept alignments."""
        mapper = ReferenceMapper()

        # Test with all datasets
        confidence = mapper._calculate_concept_confidence(
            ["Frame1"], ["Role1"], ["Class1"], ["Synset1"]
        )
        assert confidence == 1.0

        # Test with 2 datasets
        confidence = mapper._calculate_concept_confidence(["Frame1"], ["Role1"], None, None)
        assert confidence == 0.5

        # Test with no datasets
        confidence = mapper._calculate_concept_confidence(None, None, None, None)
        assert confidence == 0.0

    def test_calculate_similarity_same_concept(self) -> None:
        """Test similarity calculation for entities in same concept."""
        mapper = ReferenceMapper()

        # Create concept alignment
        mapper.map_concepts(
            "giving",
            framenet_frames=["Giving"],
            propbank_rolesets=["give.01"],
        )

        # Calculate similarity
        similarity = mapper.calculate_similarity("Giving", "FrameNet", "give.01", "PropBank")
        assert similarity == 0.5  # 2 datasets covered

    def test_calculate_similarity_no_alignment(self) -> None:
        """Test similarity for entities with no alignment."""
        mapper = ReferenceMapper()

        similarity = mapper.calculate_similarity("Unknown1", "FrameNet", "Unknown2", "PropBank")
        assert similarity == 0.0

    def test_build_alignment_matrix(self) -> None:
        """Test building alignment matrix between datasets."""
        mapper = ReferenceMapper()

        # Create some alignments
        mapper.map_concepts(
            "transfer",
            framenet_frames=["Giving", "Transfer"],
            propbank_rolesets=["give.01", "transfer.01"],
        )

        # Build matrix
        matrix = mapper.build_alignment_matrix(
            ["Giving", "Transfer", "Unknown"],
            "FrameNet",
            ["give.01", "transfer.01", "take.01"],
            "PropBank",
        )

        # Check structure
        assert "Giving" in matrix
        assert "give.01" in matrix["Giving"]
        assert matrix["Giving"]["give.01"] > 0

        # Unknown should have empty mappings
        assert "Unknown" in matrix
        assert len(matrix["Unknown"]) == 0

    def test_get_unified_lemma(self) -> None:
        """Test unified lemma creation."""
        mapper = ReferenceMapper()

        # Create test sense
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

        unified = mapper.get_unified_lemma(
            lemma="give",
            pos="v",
            framenet_lus=["give.v"],
            propbank_rolesets=["give.01"],
            verbnet_members=["give#2"],
            wordnet_senses=[sense],
        )

        assert unified.lemma == "give"
        assert unified.pos == "v"
        assert len(unified.wordnet_senses) == 1
        assert unified.wordnet_senses[0].lemma == "give"

    def test_role_concept_mapping(self) -> None:
        """Test mapping of role types to semantic concepts."""
        mapper = ReferenceMapper()

        assert mapper._get_role_concept("Agent") == "agent"
        assert mapper._get_role_concept("Patient") == "patient"
        assert mapper._get_role_concept("Theme") == "theme"
        assert mapper._get_role_concept("Co-Agent") == "co_agent"

    def test_extract_wordnet_restrictions(self) -> None:
        """Test extraction of WordNet restrictions from VerbNet roles."""
        mapper = ReferenceMapper()

        # Create role with selectional restrictions
        restriction = SelectionalRestriction(
            value="+",
            type="animate",
        )

        role = ThematicRole(
            type="Agent",
            sel_restrictions=SelectionalRestrictions(
                logic=None,
                restrictions=[restriction],
            ),
        )

        restrictions = mapper._extract_wordnet_restrictions(role)
        assert len(restrictions) > 0
        assert "00004258-a" in restrictions  # animate.a.01 mapping

    def test_alignment_confidence_matrix(self) -> None:
        """Test confidence matrix in unified role mapping."""
        mapper = ReferenceMapper()

        # Create and align roles
        role = ThematicRole(type="Recipient")
        verb_class = VerbClass(
            id="give-13.1",
            members=[],
            themroles=[role],
            frames=[],
            subclasses=[],
        )

        frame = Frame(
            id=1,
            name="Giving",
            definition=AnnotatedText.parse(""),
            frame_elements=[
                FrameElement(
                    id=1,
                    name="Recipient",
                    abbrev="Rec",
                    definition=AnnotatedText.parse(""),
                    core_type="Core",
                    bg_color="000000",
                    fg_color="FFFFFF",
                )
            ],
            lexical_units=[],
            frame_relations=[],
        )

        mapping = mapper.align_roles(role, verb_class, frame, None)

        # Check confidence matrix
        vn_key = f"VerbNet:give-13.1:{'Recipient'}"
        fn_key = "FrameNet:Giving:Recipient"

        assert vn_key in mapping.confidence_matrix
        assert fn_key in mapping.confidence_matrix[vn_key]
        assert mapping.confidence_matrix[vn_key][fn_key] == 0.8

    def test_role_is_agentive(self) -> None:
        """Test agentive role detection."""
        # Test Agent role
        agent_table = RoleMappingTable(
            verbnet_role="Agent",
            framenet_fe="Agent",
            propbank_arg="ARG0",
        )
        assert agent_table.is_agentive() is True

        # Test non-agentive role
        theme_table = RoleMappingTable(
            verbnet_role="Theme",
            framenet_fe="Theme",
            propbank_arg="ARG1",
        )
        assert theme_table.is_agentive() is False
