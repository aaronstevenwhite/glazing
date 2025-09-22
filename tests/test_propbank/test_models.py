"""Tests for PropBank data models.

Tests PropBank framesets, rolesets, and annotation models for validation,
serialization, and data integrity.

Classes
-------
TestAlias
    Tests for Alias model.
TestArgAlias
    Tests for ArgAlias model.
TestAliases
    Tests for Aliases container model.
TestUsage
    Tests for Usage model.
TestUsageNotes
    Tests for UsageNotes model.
TestRoleLink
    Tests for RoleLink model.
TestRole
    Tests for Role model.
TestLexLink
    Tests for LexLink model.
TestRoleset
    Tests for Roleset model.
TestFrameset
    Tests for Frameset model.
TestArg
    Tests for Arg annotation model.
TestRel
    Tests for Rel annotation model.
TestPropBankAnnotation
    Tests for PropBankAnnotation model.
TestAMRAnnotation
    Tests for AMRAnnotation model.
TestExample
    Tests for Example model.
TestIntegration
    Integration tests for PropBank models.
"""

import pytest
from pydantic import ValidationError

from glazing.propbank.models import (
    Alias,
    Aliases,
    AMRAnnotation,
    Arg,
    ArgAlias,
    Example,
    Frameset,
    LexLink,
    PropBankAnnotation,
    Rel,
    Role,
    RoleLink,
    Roleset,
    Usage,
    UsageNotes,
)


class TestAlias:
    """Test cases for Alias model."""

    def test_valid_alias(self) -> None:
        """Test creating a valid alias."""
        alias = Alias(text="abandon", pos="v")
        assert alias.text == "abandon"
        assert alias.pos == "v"

    def test_alias_with_hyphens(self) -> None:
        """Test alias with hyphens."""
        alias = Alias(text="give-up", pos="v")
        assert alias.text == "give-up"

    def test_alias_with_underscores(self) -> None:
        """Test alias with underscores."""
        alias = Alias(text="pick_up", pos="v")
        assert alias.text == "pick_up"

    def test_invalid_alias_text(self) -> None:
        """Test invalid alias text."""
        with pytest.raises(ValidationError) as exc_info:
            Alias(text="@abandon", pos="v")
        assert "Invalid alias text" in str(exc_info.value)

    def test_invalid_pos(self) -> None:
        """Test invalid part of speech."""
        with pytest.raises(ValidationError) as exc_info:
            Alias(text="abandon", pos="z")  # type: ignore[arg-type]
        assert "Input should be" in str(exc_info.value)

    def test_all_pos_values(self) -> None:
        """Test all valid POS values."""
        pos_values = ["r", "p", "v", "n", "j", "l", "x", "m", "d", "f"]
        for pos in pos_values:
            alias = Alias(text="test", pos=pos)  # type: ignore[arg-type]
            assert alias.pos == pos


class TestArgAlias:
    """Test cases for ArgAlias model."""

    def test_valid_arg_alias(self) -> None:
        """Test creating a valid argument alias."""
        arg_alias = ArgAlias(text="giver", pos="n", arg="0")
        assert arg_alias.text == "giver"
        assert arg_alias.pos == "n"
        assert arg_alias.arg == "0"

    def test_all_arg_numbers(self) -> None:
        """Test all valid argument numbers."""
        for arg in ["0", "1", "2", "3", "4", "5", "6", "7", "M"]:
            arg_alias = ArgAlias(text="test", pos="n", arg=arg)
            assert arg_alias.arg == arg

    def test_invalid_arg_number(self) -> None:
        """Test invalid argument number."""
        with pytest.raises(ValidationError) as exc_info:
            ArgAlias(text="test", pos="n", arg="8")
        assert "Invalid argument reference" in str(exc_info.value)


class TestAliases:
    """Test cases for Aliases container model."""

    def test_empty_aliases(self) -> None:
        """Test empty aliases container."""
        aliases = Aliases()
        assert aliases.alias == []
        assert aliases.argalias == []

    def test_aliases_with_content(self) -> None:
        """Test aliases with both types."""
        aliases = Aliases(
            alias=[Alias(text="give", pos="v"), Alias(text="gift", pos="n")],
            argalias=[ArgAlias(text="giver", pos="n", arg="0")],
        )
        assert len(aliases.alias) == 2
        assert len(aliases.argalias) == 1


class TestUsage:
    """Test cases for Usage model."""

    def test_valid_usage(self) -> None:
        """Test creating valid usage information."""
        usage = Usage(resource="VerbNet", version="3.4", inuse="+")
        assert usage.resource == "VerbNet"
        assert usage.version == "3.4"
        assert usage.inuse == "+"

    def test_usage_negative(self) -> None:
        """Test usage with negative inuse."""
        usage = Usage(resource="FrameNet", version="1.7", inuse="-")
        assert usage.inuse == "-"

    def test_invalid_resource(self) -> None:
        """Test invalid resource type."""
        with pytest.raises(ValidationError):
            Usage(resource="InvalidResource", version="1.0", inuse="+")  # type: ignore[arg-type]

    def test_invalid_inuse(self) -> None:
        """Test invalid inuse value."""
        with pytest.raises(ValidationError):
            Usage(resource="VerbNet", version="3.4", inuse="x")  # type: ignore[arg-type]


class TestUsageNotes:
    """Test cases for UsageNotes model."""

    def test_usage_notes(self) -> None:
        """Test creating usage notes."""
        usage_notes = UsageNotes(
            usage=[
                Usage(resource="VerbNet", version="3.4", inuse="+"),
                Usage(resource="FrameNet", version="1.7", inuse="-"),
            ]
        )
        assert len(usage_notes.usage) == 2


class TestRoleLink:
    """Test cases for RoleLink model."""

    def test_verbnet_rolelink(self) -> None:
        """Test VerbNet role link."""
        link = RoleLink(class_name="give-13.1", resource="VerbNet", version="3.4", role="Agent")
        assert link.class_name == "give-13.1"
        assert link.role == "Agent"

    def test_framenet_rolelink(self) -> None:
        """Test FrameNet role link."""
        link = RoleLink(class_name="Giving", resource="FrameNet", version="1.7", role="Donor")
        assert link.class_name == "Giving"

    def test_rolelink_without_role(self) -> None:
        """Test role link without specific role."""
        link = RoleLink(class_name="give-13.1", resource="VerbNet", version="3.4")
        assert link.role is None


class TestRole:
    """Test cases for Role model."""

    def test_valid_role(self) -> None:
        """Test creating a valid role."""
        role = Role(n="0", f="PAG", descr="The giver")
        assert role.n == "0"
        assert role.f == "PAG"
        assert role.descr == "The giver"

    def test_role_with_links(self) -> None:
        """Test role with rolelinks."""
        role = Role(
            n="0",
            f="PAG",
            descr="The giver",
            rolelinks=[
                RoleLink(class_name="give-13.1", resource="VerbNet", version="3.4", role="Agent")
            ],
        )
        assert len(role.rolelinks) == 1

    def test_modifier_role(self) -> None:
        """Test modifier role."""
        role = Role(n="M", f="TMP", descr="When")
        assert role.n == "M"


class TestLexLink:
    """Test cases for LexLink model."""

    def test_valid_lexlink(self) -> None:
        """Test creating a valid lexical link."""
        link = LexLink(
            class_name="give-13.1",
            confidence=0.95,
            resource="VerbNet",
            version="3.4",
            src="manual",
        )
        assert link.confidence == 0.95
        assert link.src == "manual"

    def test_confidence_bounds(self) -> None:
        """Test confidence score boundaries."""
        link1 = LexLink(
            class_name="test", confidence=0.0, resource="VerbNet", version="1.0", src="auto"
        )
        assert link1.confidence == 0.0

        link2 = LexLink(
            class_name="test", confidence=1.0, resource="VerbNet", version="1.0", src="auto"
        )
        assert link2.confidence == 1.0

    def test_invalid_confidence(self) -> None:
        """Test invalid confidence values."""
        with pytest.raises(ValidationError) as exc_info:
            LexLink(
                class_name="test", confidence=1.5, resource="VerbNet", version="1.0", src="auto"
            )
        assert "Confidence must be between 0 and 1" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            LexLink(
                class_name="test", confidence=-0.1, resource="VerbNet", version="1.0", src="auto"
            )
        assert "Confidence must be between 0 and 1" in str(exc_info.value)


class TestRoleset:
    """Test cases for Roleset model."""

    def test_minimal_roleset(self) -> None:
        """Test creating a minimal roleset."""
        roleset = Roleset(
            id="give.01",
            roles=[
                Role(n="0", f="PAG", descr="giver"),
                Role(n="1", f="PPT", descr="thing given"),
            ],
        )
        assert roleset.id == "give.01"
        assert len(roleset.roles) == 2

    def test_full_roleset(self) -> None:
        """Test roleset with all fields."""
        roleset = Roleset(
            id="give.01",
            name="transfer",
            aliases=Aliases(alias=[Alias(text="give", pos="v")]),
            roles=[Role(n="0", f="PAG", descr="giver")],
            usagenotes=UsageNotes(usage=[Usage(resource="VerbNet", version="3.4", inuse="+")]),
            lexlinks=[
                LexLink(
                    class_name="give-13.1",
                    confidence=0.95,
                    resource="VerbNet",
                    version="3.4",
                    src="manual",
                )
            ],
            notes=["Transfer of possession"],
        )
        assert roleset.name == "transfer"
        assert roleset.aliases is not None
        assert len(roleset.lexlinks) == 1

    def test_invalid_roleset_id(self) -> None:
        """Test invalid roleset ID."""
        with pytest.raises(ValidationError) as exc_info:
            Roleset(id="give", roles=[])
        assert "Invalid roleset ID" in str(exc_info.value)

    def test_complex_roleset_id(self) -> None:
        """Test complex roleset IDs."""
        roleset = Roleset(id="be-located-at.91", roles=[])
        assert roleset.id == "be-located-at.91"


class TestFrameset:
    """Test cases for Frameset model."""

    def test_valid_frameset(self) -> None:
        """Test creating a valid frameset."""
        frameset = Frameset(
            predicate_lemma="give",
            rolesets=[
                Roleset(id="give.01", roles=[Role(n="0", f="PAG", descr="giver")]),
                Roleset(id="give.02", roles=[Role(n="0", f="PAG", descr="emitter")]),
            ],
        )
        assert frameset.predicate_lemma == "give"
        assert len(frameset.rolesets) == 2

    def test_invalid_predicate_lemma(self) -> None:
        """Test invalid predicate lemma."""
        with pytest.raises(ValidationError) as exc_info:
            Frameset(predicate_lemma="@Give", rolesets=[])
        assert "Invalid predicate lemma format" in str(exc_info.value)

    def test_complex_predicate_lemma(self) -> None:
        """Test complex predicate lemmas."""
        frameset = Frameset(predicate_lemma="be-located-at", rolesets=[])
        assert frameset.predicate_lemma == "be-located-at"


class TestArg:
    """Test cases for Arg annotation model."""

    def test_valid_arg(self) -> None:
        """Test creating a valid argument annotation."""
        arg = Arg(type="ARG0", start=0, end=1, text="John")
        assert arg.type == "ARG0"
        assert arg.start == 0
        assert arg.end == 1
        assert arg.text == "John"

    def test_arg_without_text(self) -> None:
        """Test argument without text."""
        arg = Arg(type="ARGM-TMP", start=5, end=6)
        assert arg.text is None

    def test_continuation_arg(self) -> None:
        """Test continuation argument."""
        arg = Arg(type="C-ARG0", start=10, end=12)
        assert arg.type == "C-ARG0"

    def test_reference_arg(self) -> None:
        """Test reference argument."""
        arg = Arg(type="R-ARGM-LOC", start=3, end=4)
        assert arg.type == "R-ARGM-LOC"

    def test_invalid_indices(self) -> None:
        """Test invalid token indices."""
        with pytest.raises(ValidationError) as exc_info:
            Arg(type="ARG0", start=-1, end=1)
        assert "Token index cannot be negative" in str(exc_info.value)


class TestRel:
    """Test cases for Rel annotation model."""

    def test_single_location(self) -> None:
        """Test relation with single location."""
        rel = Rel(relloc="2", text="gave")
        assert rel.relloc == "2"
        assert rel.text == "gave"

    def test_multiple_locations(self) -> None:
        """Test relation with multiple locations."""
        rel = Rel(relloc="2 3", text="gave up")
        assert rel.relloc == "2 3"

    def test_unknown_location(self) -> None:
        """Test relation with unknown location."""
        rel = Rel(relloc="?")
        assert rel.relloc == "?"

    def test_invalid_location(self) -> None:
        """Test invalid location format."""
        with pytest.raises(ValidationError) as exc_info:
            Rel(relloc="2a")
        assert "Invalid relloc format" in str(exc_info.value)


class TestPropBankAnnotation:
    """Test cases for PropBankAnnotation model."""

    def test_valid_annotation(self) -> None:
        """Test creating a valid PropBank annotation."""
        annotation = PropBankAnnotation(
            args=[
                Arg(type="ARG0", start=0, end=1, text="John"),
                Arg(type="ARG1", start=3, end=4, text="gift"),
            ],
            rel=Rel(relloc="2", text="gave"),
        )
        assert len(annotation.args) == 2
        assert annotation.rel.relloc == "2"

    def test_empty_args(self) -> None:
        """Test annotation with no arguments."""
        annotation = PropBankAnnotation(rel=Rel(relloc="0"))
        assert annotation.args == []

    def test_annotation_with_notes(self) -> None:
        """Test annotation with notes."""
        annotation = PropBankAnnotation(
            rel=Rel(relloc="1"), notes=["Light verb construction", "Idiomatic"]
        )
        assert len(annotation.notes) == 2


class TestAMRAnnotation:
    """Test cases for AMRAnnotation model."""

    def test_valid_amr(self) -> None:
        """Test creating a valid AMR annotation."""
        amr = AMRAnnotation(
            version="1.0", graph="(g / give-01 :ARG0 (p / person :name John) :ARG1 (g2 / gift))"
        )
        assert amr.version == "1.0"
        assert "give-01" in amr.graph


class TestExample:
    """Test cases for Example model."""

    def test_minimal_example(self) -> None:
        """Test creating a minimal example."""
        example = Example(text="John gave Mary a book")
        assert example.text == "John gave Mary a book"
        assert example.propbank is None
        assert example.amr is None

    def test_full_example(self) -> None:
        """Test example with all annotations."""
        example = Example(
            name="ex1",
            src="WSJ",
            text="John gave Mary a book",
            propbank=PropBankAnnotation(
                args=[
                    Arg(type="ARG0", start=0, end=1),
                    Arg(type="ARG2", start=2, end=3),
                    Arg(type="ARG1", start=4, end=6),
                ],
                rel=Rel(relloc="1"),
            ),
            amr=AMRAnnotation(version="1.0", graph="(g / give-01 ...)"),
            notes=["Ditransitive construction"],
        )
        assert example.name == "ex1"
        assert example.src == "WSJ"
        assert example.propbank is not None
        assert example.amr is not None
        assert len(example.notes) == 1


class TestIntegration:
    """Integration tests for PropBank models."""

    def test_complete_frameset(self) -> None:
        """Test creating a complete frameset structure."""
        frameset = Frameset(
            predicate_lemma="give",
            rolesets=[
                Roleset(
                    id="give.01",
                    name="transfer",
                    aliases=Aliases(
                        alias=[Alias(text="give", pos="v"), Alias(text="gift", pos="n")],
                        argalias=[
                            ArgAlias(text="giver", pos="n", arg="0"),
                            ArgAlias(text="gift", pos="n", arg="1"),
                            ArgAlias(text="recipient", pos="n", arg="2"),
                        ],
                    ),
                    roles=[
                        Role(
                            n="0",
                            f="PAG",
                            descr="giver",
                            rolelinks=[
                                RoleLink(
                                    class_name="give-13.1",
                                    resource="VerbNet",
                                    version="3.4",
                                    role="Agent",
                                ),
                                RoleLink(
                                    class_name="Giving",
                                    resource="FrameNet",
                                    version="1.7",
                                    role="Donor",
                                ),
                            ],
                        ),
                        Role(n="1", f="PPT", descr="thing given"),
                        Role(n="2", f="GOL", descr="entity given to"),
                    ],
                    examples=[
                        Example(
                            text="John gave Mary the book",
                            propbank=PropBankAnnotation(
                                args=[
                                    Arg(type="ARG0", start=0, end=1),
                                    Arg(type="ARG2", start=2, end=3),
                                    Arg(type="ARG1", start=4, end=6),
                                ],
                                rel=Rel(relloc="1"),
                            ),
                        )
                    ],
                )
            ],
            notes=["Core transfer predicate"],
        )

        assert frameset.predicate_lemma == "give"
        assert len(frameset.rolesets) == 1
        roleset = frameset.rolesets[0]
        assert roleset.id == "give.01"
        assert roleset.aliases is not None
        assert len(roleset.aliases.alias) == 2
        assert len(roleset.roles) == 3
        assert len(roleset.examples) == 1

    def test_jsonl_serialization(self) -> None:
        """Test JSON Lines serialization."""
        role = Role(n="0", f="PAG", descr="agent")
        jsonl = role.to_jsonl()
        assert '"n": "0"' in jsonl or '"n":"0"' in jsonl
        assert '"f": "PAG"' in jsonl or '"f":"PAG"' in jsonl

        # Test round-trip
        role2 = Role.from_jsonl(jsonl)
        assert role2.n == role.n
        assert role2.f == role.f
        assert role2.descr == role.descr

    def test_model_validation(self) -> None:
        """Test model validation constraints."""
        # Test that required fields are enforced
        with pytest.raises(ValidationError):
            Frameset(predicate_lemma="test")  # type: ignore[call-arg]

        with pytest.raises(ValidationError):
            Roleset(id="test.01")  # type: ignore[call-arg]

        with pytest.raises(ValidationError):
            Role(n="0", f="PAG")  # type: ignore[call-arg]
