"""Tests for VerbNet core models.

This module tests VerbNet verb classes, members, thematic roles,
and selectional restrictions including inheritance logic.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from glazing.references.models import (
    CrossReference,
    MappingConfidence,
    MappingMetadata,
    VerbNetFrameNetMapping,
    VerbNetFrameNetRoleMapping,
)
from glazing.verbnet.models import (
    Member,
    SelectionalRestriction,
    SelectionalRestrictions,
    ThematicRole,
    VerbClass,
    WordNetCrossRef,
)


class TestSelectionalRestriction:
    """Test SelectionalRestriction model."""

    def test_valid_restriction(self) -> None:
        """Test creating a valid selectional restriction."""
        restriction = SelectionalRestriction(value="+", type="animate")
        assert restriction.value == "+"
        assert restriction.type == "animate"

    def test_negative_restriction(self) -> None:
        """Test creating a negative restriction."""
        restriction = SelectionalRestriction(value="-", type="abstract")
        assert restriction.value == "-"
        assert restriction.type == "abstract"

    def test_invalid_value(self) -> None:
        """Test that invalid restriction values are rejected."""
        with pytest.raises(ValidationError):
            SelectionalRestriction(
                value="*",  # Invalid value
                type="animate",
            )

    def test_invalid_type(self) -> None:
        """Test that invalid restriction types are rejected."""
        with pytest.raises(ValidationError):
            SelectionalRestriction(
                value="+",
                type="imaginary",  # Invalid type
            )


class TestSelectionalRestrictions:
    """Test SelectionalRestrictions container."""

    def test_simple_restrictions(self) -> None:
        """Test simple restrictions without nesting."""
        restrictions = SelectionalRestrictions(
            logic="or",
            restrictions=[
                SelectionalRestriction(value="+", type="animate"),
                SelectionalRestriction(value="+", type="human"),
            ],
        )
        assert restrictions.logic == "or"
        assert len(restrictions.restrictions) == 2
        assert not restrictions.is_complex()

    def test_nested_restrictions(self) -> None:
        """Test nested restriction groups."""
        inner = SelectionalRestrictions(
            logic="or",
            restrictions=[
                SelectionalRestriction(value="+", type="animate"),
                SelectionalRestriction(value="+", type="human"),
            ],
        )
        outer = SelectionalRestrictions(
            logic="and", restrictions=[SelectionalRestriction(value="+", type="concrete"), inner]
        )
        assert outer.is_complex()
        assert not inner.is_complex()

    def test_validate_logic_consistency(self) -> None:
        """Test logic consistency validation."""
        # Consistent structure
        restrictions = SelectionalRestrictions(
            logic="and",
            restrictions=[
                SelectionalRestriction(value="+", type="animate"),
                SelectionalRestrictions(
                    logic="or",
                    restrictions=[
                        SelectionalRestriction(value="+", type="human"),
                        SelectionalRestriction(value="+", type="animal"),
                    ],
                ),
            ],
        )
        assert restrictions.validate_logic_consistency()

        # Empty restrictions are consistent
        empty = SelectionalRestrictions(restrictions=[])
        assert empty.validate_logic_consistency()

    def test_flatten_restrictions(self) -> None:
        """Test flattening nested restrictions."""
        # Simple case - no nesting
        simple = SelectionalRestrictions(
            restrictions=[
                SelectionalRestriction(value="+", type="animate"),
                SelectionalRestriction(value="-", type="abstract"),
            ]
        )
        flat = simple.flatten_restrictions()
        assert len(flat) == 2
        assert all(isinstance(r, SelectionalRestriction) for r in flat)

        # Nested case
        nested = SelectionalRestrictions(
            restrictions=[
                SelectionalRestriction(value="+", type="concrete"),
                SelectionalRestrictions(
                    restrictions=[
                        SelectionalRestriction(value="+", type="animate"),
                        SelectionalRestriction(value="+", type="human"),
                    ]
                ),
            ]
        )
        flat_nested = nested.flatten_restrictions()
        assert len(flat_nested) == 3
        assert flat_nested[0].type == "concrete"
        assert flat_nested[1].type == "animate"
        assert flat_nested[2].type == "human"

    def test_check_contradiction(self) -> None:
        """Test contradiction detection in restrictions."""
        # No contradiction
        consistent = SelectionalRestrictions(
            logic="and",
            restrictions=[
                SelectionalRestriction(value="+", type="animate"),
                SelectionalRestriction(value="+", type="human"),
            ],
        )
        assert not consistent.check_contradiction()

        # Direct contradiction with AND logic
        contradictory = SelectionalRestrictions(
            logic="and",
            restrictions=[
                SelectionalRestriction(value="+", type="animate"),
                SelectionalRestriction(value="-", type="animate"),
            ],
        )
        assert contradictory.check_contradiction()

        # No contradiction with OR logic (alternatives are allowed)
        alternatives = SelectionalRestrictions(
            logic="or",
            restrictions=[
                SelectionalRestriction(value="+", type="animate"),
                SelectionalRestriction(value="-", type="animate"),
            ],
        )
        assert not alternatives.check_contradiction()

        # Contradiction in nested structure with implicit AND
        nested_contradiction = SelectionalRestrictions(
            restrictions=[
                SelectionalRestriction(value="+", type="concrete"),
                SelectionalRestrictions(
                    restrictions=[
                        SelectionalRestriction(value="+", type="concrete"),
                        SelectionalRestriction(value="-", type="concrete"),
                    ]
                ),
            ]
        )
        assert nested_contradiction.check_contradiction()

    def test_implicit_and_logic(self) -> None:
        """Test that logic can be None for implicit AND."""
        restrictions = SelectionalRestrictions(
            restrictions=[
                SelectionalRestriction(value="+", type="animate"),
                SelectionalRestriction(value="+", type="human"),
            ]
        )
        assert restrictions.logic is None


class TestThematicRole:
    """Test ThematicRole model."""

    def test_simple_role(self) -> None:
        """Test creating a simple thematic role."""
        role = ThematicRole(type="Agent")
        assert role.type == "Agent"
        assert role.sel_restrictions is None

    def test_role_with_restrictions(self) -> None:
        """Test role with selectional restrictions."""
        role = ThematicRole(
            type="Agent",
            sel_restrictions=SelectionalRestrictions(
                restrictions=[SelectionalRestriction(value="+", type="animate")]
            ),
        )
        assert role.type == "Agent"
        assert role.sel_restrictions is not None
        assert len(role.sel_restrictions.restrictions) == 1

    def test_indexed_roles(self) -> None:
        """Test indexed role variants."""
        role_i = ThematicRole(type="Agent_i")
        role_j = ThematicRole(type="Agent_j")
        assert role_i.type == "Agent_i"
        assert role_j.type == "Agent_j"

    def test_co_roles(self) -> None:
        """Test co-roles."""
        role = ThematicRole(type="Co-Agent")
        assert role.type == "Co-Agent"

    def test_class_id_method(self) -> None:
        """Test class_id method."""
        role = ThematicRole(type="Agent")
        assert role.class_id() is None
        # Simulate setting during parsing
        role._class_id = "give-13.1"
        assert role.class_id() == "give-13.1"


class TestWordNetCrossRef:
    """Test WordNetCrossRef model."""

    def test_from_percentage_notation(self) -> None:
        """Test parsing percentage notation."""
        ref = WordNetCrossRef.from_percentage_notation("give%2:40:00")
        assert ref.lemma == "give"
        assert ref.pos == "v"
        assert ref.sense_key == "give%2:40:00::"

    def test_to_percentage_notation(self) -> None:
        """Test converting to percentage notation."""
        ref = WordNetCrossRef(sense_key="give%2:40:00::", lemma="give", pos="v")
        notation = ref.to_percentage_notation()
        assert notation == "give%2:40:00"

    def test_invalid_percentage_notation(self) -> None:
        """Test that invalid notation raises error."""
        with pytest.raises(ValueError, match="Invalid percentage notation"):
            WordNetCrossRef.from_percentage_notation("invalid%notation")

    def test_incomplete_sense_key(self) -> None:
        """Test handling incomplete sense key."""
        ref = WordNetCrossRef(lemma="test", pos="v")
        assert ref.to_percentage_notation() == ""


class TestVerbNetFrameNetMapping:
    """Test VerbNet to FrameNet mapping."""

    def test_simple_mapping(self) -> None:
        """Test creating a simple mapping."""
        mapping = VerbNetFrameNetMapping(frame_name="Giving", mapping_source="manual")
        assert mapping.frame_name == "Giving"
        assert mapping.mapping_source == "manual"
        assert mapping.confidence is None

    def test_mapping_with_confidence(self) -> None:
        """Test mapping with confidence score."""
        mapping = VerbNetFrameNetMapping(
            frame_name="Giving",
            confidence=MappingConfidence(score=0.95, method="manual_validation"),
            mapping_source="manual",
        )
        assert mapping.confidence.score == 0.95

    def test_mapping_with_role_mappings(self) -> None:
        """Test mapping with role-level mappings."""
        role_mapping = VerbNetFrameNetRoleMapping(vn_role="Agent", fn_fe="Giver", confidence=0.9)
        mapping = VerbNetFrameNetMapping(
            frame_name="Giving", mapping_source="manual", role_mappings=[role_mapping]
        )
        assert len(mapping.role_mappings) == 1
        assert mapping.role_mappings[0].vn_role == "Agent"


class TestMember:
    """Test Member model."""

    def test_valid_member(self) -> None:
        """Test creating a valid member."""
        member = Member(name="give", verbnet_key="give#2")
        assert member.name == "give"
        assert member.verbnet_key == "give#2"

    def test_invalid_member_name(self) -> None:
        """Test that invalid member names are rejected."""
        with pytest.raises(ValidationError, match="Invalid member name format"):
            Member(
                name="@Give",
                verbnet_key="give#2",
            )

    def test_invalid_verbnet_key(self) -> None:
        """Test that invalid VerbNet keys are rejected."""
        with pytest.raises(ValidationError, match="Invalid verbnet_key format"):
            Member(
                name="give",
                verbnet_key="give-2",  # Should be # not -
            )

    def test_member_with_mappings(self) -> None:
        """Test member with cross-references."""
        member = Member(
            name="give",
            verbnet_key="give#2",
            framenet_mappings=[
                VerbNetFrameNetMapping(
                    frame_name="Giving",
                    mapping_source="manual",
                    confidence=MappingConfidence(score=0.9, method="manual"),
                )
            ],
            propbank_mappings=[
                CrossReference(
                    source_dataset="VerbNet",
                    source_id="give#2",
                    source_version="3.4",
                    target_dataset="PropBank",
                    target_id="give.01",
                    mapping_type="direct",
                    metadata=MappingMetadata(
                        created_date=datetime.now(UTC),
                        created_by="test",
                        version="3.4",
                        validation_status="validated",
                    ),
                )
            ],
            wordnet_mappings=[WordNetCrossRef.from_percentage_notation("give%2:40:00")],
        )
        assert len(member.framenet_mappings) == 1
        assert len(member.propbank_mappings) == 1
        assert len(member.wordnet_mappings) == 1

    def test_get_primary_framenet_frame(self) -> None:
        """Test getting highest confidence FrameNet frame."""
        member = Member(
            name="give",
            verbnet_key="give#2",
            framenet_mappings=[
                VerbNetFrameNetMapping(
                    frame_name="Giving",
                    mapping_source="manual",
                    confidence=MappingConfidence(score=0.9, method="manual"),
                ),
                VerbNetFrameNetMapping(
                    frame_name="Transfer",
                    mapping_source="automatic",
                    confidence=MappingConfidence(score=0.7, method="auto"),
                ),
            ],
        )
        assert member.get_primary_framenet_frame() == "Giving"

    def test_get_all_framenet_frames(self) -> None:
        """Test getting all FrameNet frames with scores."""
        member = Member(
            name="give",
            verbnet_key="give#2",
            framenet_mappings=[
                VerbNetFrameNetMapping(
                    frame_name="Giving",
                    mapping_source="manual",
                    confidence=MappingConfidence(score=0.9, method="manual"),
                ),
                VerbNetFrameNetMapping(frame_name="Transfer", mapping_source="automatic"),
            ],
        )
        frames = member.get_all_framenet_frames()
        assert len(frames) == 2
        assert frames[0] == ("Giving", 0.9)
        assert frames[1] == ("Transfer", None)

    def test_get_wordnet_senses(self) -> None:
        """Test getting WordNet senses in percentage notation."""
        member = Member(
            name="give",
            verbnet_key="give#2",
            wordnet_mappings=[
                WordNetCrossRef.from_percentage_notation("give%2:40:00"),
                WordNetCrossRef.from_percentage_notation("give%2:40:01"),
            ],
        )
        senses = member.get_wordnet_senses()
        assert len(senses) == 2
        assert "give%2:40:00" in senses
        assert "give%2:40:01" in senses

    def test_get_propbank_rolesets(self) -> None:
        """Test getting PropBank roleset IDs."""
        member = Member(
            name="give",
            verbnet_key="give#2",
            propbank_mappings=[
                CrossReference(
                    source_dataset="VerbNet",
                    source_id="give#2",
                    source_version="3.4",
                    target_dataset="PropBank",
                    target_id="give.01",
                    mapping_type="direct",
                    metadata=MappingMetadata(
                        created_date=datetime.now(UTC),
                        created_by="test",
                        version="3.4",
                        validation_status="validated",
                    ),
                ),
                CrossReference(
                    source_dataset="VerbNet",
                    source_id="give#2",
                    source_version="3.4",
                    target_dataset="PropBank",
                    target_id="give.02",
                    mapping_type="direct",
                    metadata=MappingMetadata(
                        created_date=datetime.now(UTC),
                        created_by="test",
                        version="3.4",
                        validation_status="validated",
                    ),
                ),
            ],
        )
        rolesets = member.get_propbank_rolesets()
        assert len(rolesets) == 2
        assert "give.01" in rolesets
        assert "give.02" in rolesets

    def test_has_mapping_conflicts(self) -> None:
        """Test detecting mapping conflicts."""
        # No conflicts - only one high confidence
        member1 = Member(
            name="give",
            verbnet_key="give#2",
            framenet_mappings=[
                VerbNetFrameNetMapping(
                    frame_name="Giving",
                    mapping_source="manual",
                    confidence=MappingConfidence(score=0.9, method="manual"),
                ),
                VerbNetFrameNetMapping(
                    frame_name="Transfer",
                    mapping_source="automatic",
                    confidence=MappingConfidence(score=0.5, method="auto"),
                ),
            ],
        )
        assert not member1.has_mapping_conflicts()

        # Has conflicts - multiple high confidence
        member2 = Member(
            name="give",
            verbnet_key="give#2",
            framenet_mappings=[
                VerbNetFrameNetMapping(
                    frame_name="Giving",
                    mapping_source="manual",
                    confidence=MappingConfidence(score=0.9, method="manual"),
                ),
                VerbNetFrameNetMapping(
                    frame_name="Transfer",
                    mapping_source="manual",
                    confidence=MappingConfidence(score=0.8, method="manual"),
                ),
            ],
        )
        assert member2.has_mapping_conflicts()


class TestVerbClass:
    """Test VerbClass model."""

    def test_valid_verb_class(self) -> None:
        """Test creating a valid verb class."""
        verb_class = VerbClass(id="give-13.1", members=[], themroles=[], frames=[], subclasses=[])
        assert verb_class.id == "give-13.1"

    def test_invalid_class_id(self) -> None:
        """Test that invalid class IDs are rejected."""
        with pytest.raises(ValidationError, match="Invalid VerbNet class ID format"):
            VerbClass(
                id="Give-13.1",  # Capital letter not allowed
                members=[],
                themroles=[],
                frames=[],
                subclasses=[],
            )

    def test_verb_class_with_subclasses(self) -> None:
        """Test verb class with subclasses."""
        subclass = VerbClass(
            id="give-13.1-1",
            members=[],
            themroles=[],
            frames=[],
            subclasses=[],
            parent_class="give-13.1",
        )
        parent = VerbClass(
            id="give-13.1", members=[], themroles=[], frames=[], subclasses=[subclass]
        )
        assert parent.has_subclasses()
        assert not subclass.has_subclasses()

    def test_get_effective_roles_no_inheritance(self) -> None:
        """Test getting roles without inheritance."""
        verb_class = VerbClass(
            id="give-13.1",
            members=[],
            themroles=[
                ThematicRole(type="Agent"),
                ThematicRole(type="Theme"),
                ThematicRole(type="Recipient"),
            ],
            frames=[],
            subclasses=[],
        )
        roles = verb_class.get_effective_roles()
        assert len(roles) == 3
        assert any(r.type == "Agent" for r in roles)
        assert any(r.type == "Theme" for r in roles)
        assert any(r.type == "Recipient" for r in roles)

    def test_get_effective_roles_full_inheritance(self) -> None:
        """Test full role inheritance from parent."""
        parent_roles = [
            ThematicRole(type="Agent"),
            ThematicRole(type="Theme"),
            ThematicRole(type="Recipient"),
        ]
        # Empty themroles means inherit all from parent
        subclass = VerbClass(
            id="give-13.1-1",
            members=[],
            themroles=[],  # Empty = inherit all
            frames=[],
            subclasses=[],
        )
        effective = subclass.get_effective_roles(parent_roles)
        assert len(effective) == 3
        assert effective == parent_roles

    def test_get_effective_roles_partial_override(self) -> None:
        """Test partial role override in subclass."""
        parent_roles = [
            ThematicRole(type="Agent"),
            ThematicRole(type="Theme"),
            ThematicRole(type="Recipient"),
        ]
        # Subclass overrides Agent but inherits others
        subclass = VerbClass(
            id="give-13.1-1",
            members=[],
            themroles=[
                ThematicRole(
                    type="Agent",
                    sel_restrictions=SelectionalRestrictions(
                        restrictions=[SelectionalRestriction(value="+", type="human")]
                    ),
                )
            ],
            frames=[],
            subclasses=[],
        )
        effective = subclass.get_effective_roles(parent_roles)
        assert len(effective) == 3
        # Agent from subclass should come first
        assert effective[0].type == "Agent"
        assert effective[0].sel_restrictions is not None
        # Theme and Recipient inherited
        assert any(r.type == "Theme" for r in effective)
        assert any(r.type == "Recipient" for r in effective)

    def test_get_all_members(self) -> None:
        """Test getting all members including subclasses."""
        member1 = Member(name="give", verbnet_key="give#1")
        member2 = Member(name="donate", verbnet_key="donate#1")
        member3 = Member(name="grant", verbnet_key="grant#1")

        subclass = VerbClass(
            id="give-13.1-1", members=[member3], themroles=[], frames=[], subclasses=[]
        )
        parent = VerbClass(
            id="give-13.1",
            members=[member1, member2],
            themroles=[],
            frames=[],
            subclasses=[subclass],
        )

        # With subclasses
        all_members = parent.get_all_members(include_subclasses=True)
        assert len(all_members) == 3
        assert member1 in all_members
        assert member2 in all_members
        assert member3 in all_members

        # Without subclasses
        parent_only = parent.get_all_members(include_subclasses=False)
        assert len(parent_only) == 2
        assert member1 in parent_only
        assert member2 in parent_only
        assert member3 not in parent_only

    def test_get_member_by_key(self) -> None:
        """Test finding member by VerbNet key."""
        member1 = Member(name="give", verbnet_key="give#1")
        member2 = Member(name="donate", verbnet_key="donate#1")
        member3 = Member(name="grant", verbnet_key="grant#1")

        subclass = VerbClass(
            id="give-13.1-1", members=[member3], themroles=[], frames=[], subclasses=[]
        )
        parent = VerbClass(
            id="give-13.1",
            members=[member1, member2],
            themroles=[],
            frames=[],
            subclasses=[subclass],
        )

        # Find in parent
        found = parent.get_member_by_key("give#1")
        assert found is member1

        # Find in subclass
        found = parent.get_member_by_key("grant#1")
        assert found is member3

        # Not found
        found = parent.get_member_by_key("nonexistent#1")
        assert found is None


class TestMappingMetadata:
    """Test MappingMetadata model."""

    def test_valid_metadata(self) -> None:
        """Test creating valid mapping metadata."""
        created_date = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        metadata = MappingMetadata(
            created_date=created_date,
            created_by="system",
            version="3.4",
            validation_status="validated",
        )
        assert metadata.created_date == created_date
        assert metadata.created_by == "system"
        assert metadata.version == "3.4"
        assert metadata.validation_status == "validated"

    def test_metadata_with_modification(self) -> None:
        """Test metadata with modification info."""
        created_date = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        modified_date = datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC)
        metadata = MappingMetadata(
            created_date=created_date,
            created_by="user1",
            modified_date=modified_date,
            modified_by="user2",
            version="3.4",
            validation_status="validated",
            validation_method="manual_review",
            notes="Updated mappings",
        )
        assert metadata.modified_date == modified_date
        assert metadata.modified_by == "user2"
        assert metadata.validation_method == "manual_review"
        assert metadata.notes == "Updated mappings"
