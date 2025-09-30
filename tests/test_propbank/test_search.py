"""Tests for PropBank search functionality."""

import re

import pytest

from glazing.propbank.models import (
    Alias,
    Aliases,
    Arg,
    Example,
    Frameset,
    LexLink,
    PropBankAnnotation,
    Rel,
    Role,
    Roleset,
)
from glazing.propbank.search import PropBankSearch


class TestPropBankSearch:
    """Tests for PropBankSearch class."""

    @pytest.fixture
    def sample_framesets(self):
        """Create sample framesets for testing."""
        # Create give frameset
        give_frameset = Frameset(
            predicate_lemma="give",
            rolesets=[
                Roleset(
                    id="give.01",
                    name="transfer",
                    aliases=Aliases(
                        alias=[
                            Alias(text="give", pos="v"),
                            Alias(text="giving", pos="n"),
                        ]
                    ),
                    roles=[
                        Role(n="0", f="PAG", descr="giver"),
                        Role(n="1", f="PPT", descr="thing given"),
                        Role(n="2", f="GOL", descr="entity given to"),
                    ],
                    lexlinks=[
                        LexLink(
                            class_name="give-13.1",
                            confidence=0.95,
                            resource="VerbNet",
                            version="3.4",
                            src="manual",
                        ),
                        LexLink(
                            class_name="Giving",
                            confidence=0.9,
                            resource="FrameNet",
                            version="1.7",
                            src="manual",
                        ),
                    ],
                ),
                Roleset(
                    id="give.02",
                    name="emit",
                    aliases=Aliases(alias=[Alias(text="give", pos="v")]),
                    roles=[
                        Role(n="0", f="PAG", descr="emitter"),
                        Role(n="1", f="PPT", descr="thing emitted"),
                    ],
                ),
            ],
        )

        # Create abandon frameset
        abandon_frameset = Frameset(
            predicate_lemma="abandon",
            rolesets=[
                Roleset(
                    id="abandon.01",
                    name="leave behind",
                    aliases=Aliases(
                        alias=[
                            Alias(text="abandon", pos="v"),
                            Alias(text="abandonment", pos="n"),
                        ]
                    ),
                    roles=[
                        Role(n="0", f="PAG", descr="abandoner"),
                        Role(n="1", f="PPT", descr="thing abandoned"),
                        Role(n="M", f="LOC", descr="location"),
                    ],
                    lexlinks=[
                        LexLink(
                            class_name="leave-51.2",
                            confidence=0.85,
                            resource="VerbNet",
                            version="3.4",
                            src="automatic",
                        ),
                    ],
                ),
            ],
        )

        return [give_frameset, abandon_frameset]

    def test_init_empty(self):
        """Test initialization with empty index."""
        search = PropBankSearch()
        assert search.get_statistics()["frameset_count"] == 0
        assert search.get_all_lemmas() == []
        assert search.get_all_rolesets() == []

    def test_init_with_framesets(self, sample_framesets):
        """Test initialization with framesets."""
        search = PropBankSearch(sample_framesets)
        stats = search.get_statistics()
        assert stats["frameset_count"] == 2
        assert stats["roleset_count"] == 3  # give.01, give.02, abandon.01
        assert stats["total_roles"] == 8  # 3 + 2 + 3

    def test_add_frameset(self, sample_framesets):
        """Test adding framesets to index."""
        search = PropBankSearch()
        search.add_frameset(sample_framesets[0])

        assert search.get_statistics()["frameset_count"] == 1
        assert search.by_lemma("give") == sample_framesets[0]
        assert search.by_roleset_id("give.01") is not None

    def test_add_duplicate_frameset(self, sample_framesets):
        """Test adding duplicate frameset raises error."""
        search = PropBankSearch()
        search.add_frameset(sample_framesets[0])

        with pytest.raises(ValueError, match="already exists"):
            search.add_frameset(sample_framesets[0])

    def test_by_lemma(self, sample_framesets):
        """Test getting frameset by lemma."""
        search = PropBankSearch(sample_framesets)

        frameset = search.by_lemma("give")
        assert frameset is not None
        assert frameset.predicate_lemma == "give"
        assert len(frameset.rolesets) == 2

        assert search.by_lemma("nonexistent") is None

    def test_by_roleset_id(self, sample_framesets):
        """Test getting roleset by ID."""
        search = PropBankSearch(sample_framesets)

        roleset = search.by_roleset_id("give.01")
        assert roleset is not None
        assert roleset.name == "transfer"
        assert len(roleset.roles) == 3

        assert search.by_roleset_id("give.99") is None

    def test_by_pattern(self, sample_framesets):
        """Test searching framesets by pattern."""
        search = PropBankSearch(sample_framesets)

        # Test exact match
        results = search.by_pattern("give")
        assert len(results) == 1
        assert results[0].predicate_lemma == "give"

        # Test partial match
        results = search.by_pattern(".*ive")
        assert len(results) == 1
        assert results[0].predicate_lemma == "give"

        # Test case insensitive
        results = search.by_pattern("GIVE", case_sensitive=False)
        assert len(results) == 1

        # Test case sensitive
        results = search.by_pattern("GIVE", case_sensitive=True)
        assert len(results) == 0

        # Test no matches
        results = search.by_pattern("NoMatch")
        assert len(results) == 0

    def test_by_role_arg_num(self, sample_framesets):
        """Test finding rolesets by argument number."""
        search = PropBankSearch(sample_framesets)

        # Find rolesets with ARG0
        results = search.by_role(arg_num="0")
        assert len(results) == 3  # All rolesets have ARG0

        # Find rolesets with ARG2
        results = search.by_role(arg_num="2")
        assert len(results) == 1  # Only give.01
        assert results[0].id == "give.01"

        # Find rolesets with ARGM
        results = search.by_role(arg_num="M")
        assert len(results) == 1  # Only abandon.01
        assert results[0].id == "abandon.01"

    def test_by_role_function_tag(self, sample_framesets):
        """Test finding rolesets by function tag."""
        search = PropBankSearch(sample_framesets)

        # Find rolesets with PAG (agent)
        results = search.by_role(function_tag="PAG")
        assert len(results) == 3  # All rolesets

        # Find rolesets with GOL (goal)
        results = search.by_role(function_tag="GOL")
        assert len(results) == 1  # Only give.01
        assert results[0].id == "give.01"

        # Find rolesets with LOC (location)
        results = search.by_role(function_tag="LOC")
        assert len(results) == 1  # Only abandon.01
        assert results[0].id == "abandon.01"

    def test_by_role_combined(self, sample_framesets):
        """Test finding rolesets by both arg num and function tag."""
        search = PropBankSearch(sample_framesets)

        # Find rolesets with ARG0 as PAG
        results = search.by_role(arg_num="0", function_tag="PAG")
        assert len(results) == 3  # All rolesets

        # Find rolesets with ARG2 as GOL
        results = search.by_role(arg_num="2", function_tag="GOL")
        assert len(results) == 1
        assert results[0].id == "give.01"

        # Find rolesets with ARGM as LOC
        results = search.by_role(arg_num="M", function_tag="LOC")
        assert len(results) == 1
        assert results[0].id == "abandon.01"

    def test_by_resource(self, sample_framesets):
        """Test finding rolesets by external resource."""
        search = PropBankSearch(sample_framesets)

        # Find rolesets linked to VerbNet
        results = search.by_resource("VerbNet")
        assert len(results) == 2  # give.01 and abandon.01

        # Find rolesets linked to FrameNet
        results = search.by_resource("FrameNet")
        assert len(results) == 1  # Only give.01
        assert results[0].id == "give.01"

        # Find specific VerbNet class
        results = search.by_resource("VerbNet", "give-13.1")
        assert len(results) == 1
        assert results[0].id == "give.01"

        # Find specific FrameNet frame
        results = search.by_resource("FrameNet", "Giving")
        assert len(results) == 1
        assert results[0].id == "give.01"

    def test_search_aliases(self, sample_framesets):
        """Test searching by aliases."""
        search = PropBankSearch(sample_framesets)

        # Search for "giving"
        results = search.search_aliases("giving")
        assert len(results) == 1
        assert results[0].id == "give.01"

        # Search for "abandonment"
        results = search.search_aliases("abandonment")
        assert len(results) == 1
        assert results[0].id == "abandon.01"

        # Search with pattern
        results = search.search_aliases(".*ment")
        assert len(results) == 1
        assert results[0].id == "abandon.01"

        # Case insensitive
        results = search.search_aliases("GIVING", case_sensitive=False)
        assert len(results) == 1

    def test_get_all_lemmas(self, sample_framesets):
        """Test getting all lemmas."""
        search = PropBankSearch(sample_framesets)

        lemmas = search.get_all_lemmas()
        assert len(lemmas) == 2
        assert "abandon" in lemmas
        assert "give" in lemmas
        # Check sorted
        assert lemmas == sorted(lemmas)

    def test_get_all_rolesets(self, sample_framesets):
        """Test getting all rolesets."""
        search = PropBankSearch(sample_framesets)

        rolesets = search.get_all_rolesets()
        assert len(rolesets) == 3
        roleset_ids = [r.id for r in rolesets]
        assert "abandon.01" in roleset_ids
        assert "give.01" in roleset_ids
        assert "give.02" in roleset_ids
        # Check sorted
        assert roleset_ids == sorted(roleset_ids)

    def test_get_all_function_tags(self, sample_framesets):
        """Test getting all function tags."""
        search = PropBankSearch(sample_framesets)

        tags = search.get_all_function_tags()
        assert len(tags) == 4  # PAG, PPT, GOL, LOC
        assert "GOL" in tags
        assert "LOC" in tags
        assert "PAG" in tags
        assert "PPT" in tags
        # Check sorted
        assert tags == sorted(tags)

    def test_get_statistics(self, sample_framesets):
        """Test getting index statistics."""
        search = PropBankSearch(sample_framesets)

        stats = search.get_statistics()
        assert stats["frameset_count"] == 2
        assert stats["roleset_count"] == 3
        assert stats["unique_function_tags"] == 4  # PAG, PPT, GOL, LOC
        assert stats["unique_arg_numbers"] == 4  # 0, 1, 2, M
        assert stats["total_roles"] == 8
        assert stats["total_lexlinks"] == 3  # 2 + 1

    def test_invalid_regex_pattern(self, sample_framesets):
        """Test invalid regex patterns raise error."""
        search = PropBankSearch(sample_framesets)

        with pytest.raises(re.error):
            search.by_pattern("[invalid")

        with pytest.raises(re.error):
            search.search_aliases("(unclosed")

    # Syntax-related tests moved from test_syntax/test_propbank_integration.py
    def test_by_syntax_method_exists(self):
        """Test that by_syntax method exists and is callable."""
        search = PropBankSearch()
        assert hasattr(search, "by_syntax")
        assert callable(search.by_syntax)

    def test_by_syntax_empty_search(self):
        """Test syntax search on empty search index."""
        search = PropBankSearch()
        results = search.by_syntax("NP V NP")

        # Should return empty list for empty index
        assert isinstance(results, list)
        assert len(results) == 0

    def test_extract_pattern_basic_transitive(self):
        """Test pattern extraction from basic transitive example."""
        search = PropBankSearch()
        # Create example with ARG0 V ARG1 pattern
        propbank_annotation = PropBankAnnotation(
            args=[
                Arg(type="ARG0", start=0, end=1, text="John"),
                Arg(type="ARG1", start=2, end=3, text="book"),
            ],
            rel=Rel(relloc="1", text="read"),
        )

        example = Example(text="John read book", propbank=propbank_annotation)

        pattern = search._extract_pattern_from_example(example)

        assert pattern is not None
        assert len(pattern.elements) == 3  # NP V NP
        assert pattern.elements[0].constituent == "NP"
        assert pattern.elements[1].constituent == "VERB"
        assert pattern.elements[2].constituent == "NP"

    def test_extract_pattern_with_pp_location(self):
        """Test pattern extraction with locative PP."""
        search = PropBankSearch()
        # Create example with ARG0 V ARG1 ARGM-LOC pattern
        propbank_annotation = PropBankAnnotation(
            args=[
                Arg(type="ARG0", start=0, end=1, text="John"),
                Arg(type="ARG1", start=2, end=3, text="book"),
                Arg(type="ARGM-LOC", start=4, end=6, text="in library"),
            ],
            rel=Rel(relloc="1", text="read"),
        )

        example = Example(text="John read book in library", propbank=propbank_annotation)

        pattern = search._extract_pattern_from_example(example)

        assert pattern is not None
        assert len(pattern.elements) == 4  # NP V NP PP
        assert pattern.elements[0].constituent == "NP"
        assert pattern.elements[1].constituent == "VERB"
        assert pattern.elements[2].constituent == "NP"
        assert pattern.elements[3].constituent == "PP"
        assert pattern.elements[3].semantic_role == "location"

    def test_extract_pattern_with_pp_temporal(self):
        """Test pattern extraction with temporal PP."""
        search = PropBankSearch()
        propbank_annotation = PropBankAnnotation(
            args=[
                Arg(type="ARG0", start=0, end=1, text="John"),
                Arg(type="ARG1", start=2, end=3, text="book"),
                Arg(type="ARGM-TMP", start=4, end=5, text="yesterday"),
            ],
            rel=Rel(relloc="1", text="read"),
        )

        example = Example(text="John read book yesterday", propbank=propbank_annotation)

        pattern = search._extract_pattern_from_example(example)

        assert pattern is not None
        assert len(pattern.elements) == 4
        assert pattern.elements[3].constituent == "PP"
        assert pattern.elements[3].semantic_role == "temporal"

    def test_extract_pattern_various_modifiers(self):
        """Test pattern extraction with various modifier types."""
        search = PropBankSearch()
        modifier_tests = [
            ("ARGM-MNR", "manner"),
            ("ARGM-PRP", "purpose"),
            ("ARGM-CAU", "cause"),
            ("ARGM-DIR", "direction"),  # Direction maps to direction
            ("ARGM-GOL", "goal"),  # Goal maps to goal
        ]

        for argm_type, expected_role in modifier_tests:
            propbank_annotation = PropBankAnnotation(
                args=[
                    Arg(type="ARG0", start=0, end=1, text="John"),
                    Arg(type=argm_type, start=2, end=3, text="modifier"),
                ],
                rel=Rel(relloc="1", text="verb"),
            )

            example = Example(text="John verb modifier", propbank=propbank_annotation)

            pattern = search._extract_pattern_from_example(example)

            assert pattern is not None, f"Failed for {argm_type}"
            assert len(pattern.elements) == 3, f"Wrong length for {argm_type}"
            assert pattern.elements[2].constituent == "PP", f"Not PP for {argm_type}"
            assert pattern.elements[2].semantic_role == expected_role, (
                f"Wrong role for {argm_type}: {pattern.elements[2].semantic_role}"
            )

    def test_extract_pattern_unknown_positions(self):
        """Test pattern extraction with unknown positions ('?')."""
        search = PropBankSearch()
        propbank_annotation = PropBankAnnotation(
            args=[
                Arg(type="ARG0", start="?", end="?", text="someone"),
                Arg(type="ARG1", start="?", end="?", text="something"),
            ],
            rel=Rel(relloc="?", text="do"),
        )

        example = Example(text="Someone does something", propbank=propbank_annotation)

        pattern = search._extract_pattern_from_example(example)

        # Should still create a pattern even with unknown positions
        assert pattern is not None
        assert len(pattern.elements) == 3  # NP V NP

    def test_by_syntax_with_mock_data(self):
        """Test syntax search with mock PropBank data."""
        search = PropBankSearch()

        # Create a mock roleset with examples
        role = Role(n="0", f="PAG", descr="agent")

        # Example 1: NP V NP pattern
        example1 = Example(
            text="John read book",
            propbank=PropBankAnnotation(
                args=[
                    Arg(type="ARG0", start=0, end=1, text="John"),
                    Arg(type="ARG1", start=2, end=3, text="book"),
                ],
                rel=Rel(relloc="1", text="read"),
            ),
        )

        # Example 2: NP V NP PP pattern
        example2 = Example(
            text="John read book in library",
            propbank=PropBankAnnotation(
                args=[
                    Arg(type="ARG0", start=0, end=1, text="John"),
                    Arg(type="ARG1", start=2, end=3, text="book"),
                    Arg(type="ARGM-LOC", start=4, end=6, text="in library"),
                ],
                rel=Rel(relloc="1", text="read"),
            ),
        )

        roleset = Roleset(
            id="read.01",
            name="read",
            aliases=None,
            usageNotes=None,
            roles=[role],
            lexlinks=[],
            examples=[example1, example2],
        )

        frameset = Frameset(
            predicate_lemma="read", aliases=None, usageNotes=None, rolesets=[roleset]
        )

        search.add_frameset(frameset)

        # Search for NP V NP pattern - should match example1
        results_transitive = search.by_syntax("NP V NP")
        assert len(results_transitive) == 1
        assert results_transitive[0] == roleset

        # Search for NP V NP PP pattern - should match example2
        results_with_pp = search.by_syntax("NP V NP PP")
        assert len(results_with_pp) == 1
        assert results_with_pp[0] == roleset

    def test_by_syntax_hierarchical_matching(self):
        """Test hierarchical matching in syntax search."""
        search = PropBankSearch()

        # Create example with specific PP.location
        example = Example(
            text="John put book on table",
            propbank=PropBankAnnotation(
                args=[
                    Arg(type="ARG0", start=0, end=1, text="John"),
                    Arg(type="ARG1", start=2, end=3, text="book"),
                    Arg(type="ARGM-LOC", start=4, end=6, text="on table"),
                ],
                rel=Rel(relloc="1", text="put"),
            ),
        )

        role = Role(n="0", f="PAG", descr="agent")
        roleset = Roleset(
            id="put.01",
            name="put",
            aliases=None,
            usageNotes=None,
            roles=[role],
            lexlinks=[],
            examples=[example],
        )

        frameset = Frameset(
            predicate_lemma="put", aliases=None, usageNotes=None, rolesets=[roleset]
        )

        search.add_frameset(frameset)

        # General PP should match specific PP.location with perfect confidence
        results = search.by_syntax("NP V NP PP")
        assert len(results) == 1
        assert results[0] == roleset

    def test_by_syntax_no_propbank_annotation(self):
        """Test with examples that have no PropBank annotation."""
        search = PropBankSearch()

        # Example without PropBank annotation
        example = Example(
            text="John reads",
            propbank=None,  # No PropBank annotation
        )

        role = Role(n="0", f="PAG", descr="agent")
        roleset = Roleset(
            id="read.01",
            name="read",
            aliases=None,
            usageNotes=None,
            roles=[role],
            lexlinks=[],
            examples=[example],
        )

        frameset = Frameset(
            predicate_lemma="read", aliases=None, usageNotes=None, rolesets=[roleset]
        )

        search.add_frameset(frameset)

        # Should not match any pattern since no PropBank annotation
        results = search.by_syntax("NP V NP")
        assert len(results) == 0

    def test_by_syntax_empty_args(self):
        """Test with PropBank annotation that has empty args."""
        search = PropBankSearch()

        example = Example(
            text="It rains",
            propbank=PropBankAnnotation(
                args=[],  # No arguments
                rel=Rel(relloc="1", text="rains"),
            ),
        )

        role = Role(n="0", f="PAG", descr="agent")
        roleset = Roleset(
            id="rain.01",
            name="rain",
            aliases=None,
            usageNotes=None,
            roles=[role],
            lexlinks=[],
            examples=[example],
        )

        frameset = Frameset(
            predicate_lemma="rain", aliases=None, usageNotes=None, rolesets=[roleset]
        )

        search.add_frameset(frameset)

        # Should not match patterns that require arguments
        results = search.by_syntax("NP V NP")
        assert len(results) == 0

    def test_by_syntax_duplicate_removal(self):
        """Test that duplicate rolesets are removed from results."""
        search = PropBankSearch()

        # Create two examples with same pattern in one roleset
        example1 = Example(
            text="John read book",
            propbank=PropBankAnnotation(
                args=[
                    Arg(type="ARG0", start=0, end=1, text="John"),
                    Arg(type="ARG1", start=2, end=3, text="book"),
                ],
                rel=Rel(relloc="1", text="read"),
            ),
        )

        example2 = Example(
            text="Mary read paper",
            propbank=PropBankAnnotation(
                args=[
                    Arg(type="ARG0", start=0, end=1, text="Mary"),
                    Arg(type="ARG1", start=2, end=3, text="paper"),
                ],
                rel=Rel(relloc="1", text="read"),
            ),
        )

        role = Role(n="0", f="PAG", descr="agent")
        roleset = Roleset(
            id="read.01",
            name="read",
            aliases=None,
            usageNotes=None,
            roles=[role],
            lexlinks=[],
            examples=[example1, example2],  # Both examples match NP V NP
        )

        frameset = Frameset(
            predicate_lemma="read", aliases=None, usageNotes=None, rolesets=[roleset]
        )

        search.add_frameset(frameset)

        # Should return roleset only once despite multiple matching examples
        results = search.by_syntax("NP V NP")
        assert len(results) == 1
        assert results[0] == roleset

    def test_by_syntax_results_sorted(self):
        """Test that results are sorted by roleset ID."""
        search = PropBankSearch()

        # Create multiple framesets with different IDs
        framesets_data = [("verb.03", "verb.03"), ("verb.01", "verb.01"), ("verb.02", "verb.02")]

        for lemma, roleset_id in framesets_data:
            example = Example(
                text="John verbs something",
                propbank=PropBankAnnotation(
                    args=[
                        Arg(type="ARG0", start=0, end=1, text="John"),
                        Arg(type="ARG1", start=2, end=3, text="something"),
                    ],
                    rel=Rel(relloc="1", text="verbs"),
                ),
            )

            role = Role(n="0", f="PAG", descr="agent")
            roleset = Roleset(
                id=roleset_id,
                name=lemma,
                aliases=None,
                usageNotes=None,
                roles=[role],
                lexlinks=[],
                examples=[example],
            )

            frameset = Frameset(
                predicate_lemma=lemma, aliases=None, usageNotes=None, rolesets=[roleset]
            )

            search.add_frameset(frameset)

        results = search.by_syntax("NP V NP")

        # Should be sorted by roleset ID
        assert len(results) == 3
        assert results[0].id == "verb.01"
        assert results[1].id == "verb.02"
        assert results[2].id == "verb.03"

    def test_get_arg_position_helper(self):
        """Test _get_arg_position helper method."""
        search = PropBankSearch()

        # Normal position
        arg1 = Arg(type="ARG0", start=5, end=6, text="test")
        assert search._get_arg_position(arg1) == 5

        # Unknown position
        arg2 = Arg(type="ARG0", start="?", end="?", text="test")
        assert search._get_arg_position(arg2) == 999

    def test_get_rel_position_helper(self):
        """Test _get_rel_position helper method."""
        search = PropBankSearch()

        # Normal position
        rel1 = Rel(relloc="3", text="verb")
        assert search._get_rel_position(rel1) == 3

        # Unknown position
        rel2 = Rel(relloc="?", text="verb")
        assert search._get_rel_position(rel2) is None

        # None rel
        assert search._get_rel_position(None) is None
