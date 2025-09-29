"""Test PropBank syntax search integration."""

from glazing.propbank.models import Arg, Example, Frameset, PropBankAnnotation, Rel, Role, Roleset
from glazing.propbank.search import PropBankSearch
from glazing.syntax.parser import SyntaxParser


class TestPropBankSyntaxIntegration:
    """Test PropBank syntax search integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.search = PropBankSearch()
        self.parser = SyntaxParser()

    def test_by_syntax_method_exists(self):
        """Test that by_syntax method exists and is callable."""
        assert hasattr(self.search, "by_syntax")
        assert callable(self.search.by_syntax)

    def test_by_syntax_empty_search(self):
        """Test syntax search on empty search index."""
        results = self.search.by_syntax("NP V NP")

        # Should return empty list for empty index
        assert isinstance(results, list)
        assert len(results) == 0

    def test_extract_pattern_basic_transitive(self):
        """Test pattern extraction from basic transitive example."""
        # Create example with ARG0 V ARG1 pattern
        propbank_annotation = PropBankAnnotation(
            args=[
                Arg(type="ARG0", start=0, end=1, text="John"),
                Arg(type="ARG1", start=2, end=3, text="book"),
            ],
            rel=Rel(relloc="1", text="read"),
        )

        example = Example(text="John read book", propbank=propbank_annotation)

        pattern = self.search._extract_pattern_from_example(example)

        assert pattern is not None
        assert len(pattern.elements) == 3  # NP V NP
        assert pattern.elements[0].constituent == "NP"
        assert pattern.elements[1].constituent == "VERB"
        assert pattern.elements[2].constituent == "NP"

    def test_extract_pattern_with_pp_location(self):
        """Test pattern extraction with locative PP."""
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

        pattern = self.search._extract_pattern_from_example(example)

        assert pattern is not None
        assert len(pattern.elements) == 4  # NP V NP PP
        assert pattern.elements[0].constituent == "NP"
        assert pattern.elements[1].constituent == "VERB"
        assert pattern.elements[2].constituent == "NP"
        assert pattern.elements[3].constituent == "PP"
        assert pattern.elements[3].semantic_role == "location"

    def test_extract_pattern_with_pp_temporal(self):
        """Test pattern extraction with temporal PP."""
        propbank_annotation = PropBankAnnotation(
            args=[
                Arg(type="ARG0", start=0, end=1, text="John"),
                Arg(type="ARG1", start=2, end=3, text="book"),
                Arg(type="ARGM-TMP", start=4, end=5, text="yesterday"),
            ],
            rel=Rel(relloc="1", text="read"),
        )

        example = Example(text="John read book yesterday", propbank=propbank_annotation)

        pattern = self.search._extract_pattern_from_example(example)

        assert pattern is not None
        assert len(pattern.elements) == 4
        assert pattern.elements[3].constituent == "PP"
        assert pattern.elements[3].semantic_role == "temporal"

    def test_extract_pattern_various_modifiers(self):
        """Test pattern extraction with various modifier types."""
        modifier_tests = [
            ("ARGM-MNR", "manner"),
            ("ARGM-PRP", "purpose"),
            ("ARGM-CAU", "cause"),
            ("ARGM-DIR", "location"),  # Direction maps to location
            ("ARGM-GOL", "location"),  # Goal maps to location
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

            pattern = self.search._extract_pattern_from_example(example)

            assert pattern is not None, f"Failed for {argm_type}"
            assert len(pattern.elements) == 3, f"Wrong length for {argm_type}"
            assert pattern.elements[2].constituent == "PP", f"Not PP for {argm_type}"
            assert pattern.elements[2].semantic_role == expected_role, (
                f"Wrong role for {argm_type}: {pattern.elements[2].semantic_role}"
            )

    def test_extract_pattern_unknown_positions(self):
        """Test pattern extraction with unknown positions ('?')."""
        propbank_annotation = PropBankAnnotation(
            args=[
                Arg(type="ARG0", start="?", end="?", text="someone"),
                Arg(type="ARG1", start="?", end="?", text="something"),
            ],
            rel=Rel(relloc="?", text="do"),
        )

        example = Example(text="Someone does something", propbank=propbank_annotation)

        pattern = self.search._extract_pattern_from_example(example)

        # Should still create a pattern even with unknown positions
        assert pattern is not None
        assert len(pattern.elements) == 3  # NP V NP

    def test_by_syntax_with_mock_data(self):
        """Test syntax search with mock PropBank data."""
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

        self.search.add_frameset(frameset)

        # Search for NP V NP pattern - should match example1
        results_transitive = self.search.by_syntax("NP V NP")
        assert len(results_transitive) == 1
        assert results_transitive[0] == roleset

        # Search for NP V NP PP pattern - should match example2
        results_with_pp = self.search.by_syntax("NP V NP PP")
        assert len(results_with_pp) == 1
        assert results_with_pp[0] == roleset

    def test_by_syntax_hierarchical_matching(self):
        """Test hierarchical matching in syntax search."""
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

        self.search.add_frameset(frameset)

        # General PP should match specific PP.location with perfect confidence
        results = self.search.by_syntax("NP V NP PP")
        assert len(results) == 1
        assert results[0] == roleset

    def test_by_syntax_no_propbank_annotation(self):
        """Test with examples that have no PropBank annotation."""
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

        self.search.add_frameset(frameset)

        # Should not match any pattern since no PropBank annotation
        results = self.search.by_syntax("NP V NP")
        assert len(results) == 0

    def test_by_syntax_empty_args(self):
        """Test with PropBank annotation that has empty args."""
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

        self.search.add_frameset(frameset)

        # Should not match patterns that require arguments
        results = self.search.by_syntax("NP V NP")
        assert len(results) == 0

    def test_by_syntax_duplicate_removal(self):
        """Test that duplicate rolesets are removed from results."""
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

        self.search.add_frameset(frameset)

        # Should return roleset only once despite multiple matching examples
        results = self.search.by_syntax("NP V NP")
        assert len(results) == 1
        assert results[0] == roleset

    def test_by_syntax_results_sorted(self):
        """Test that results are sorted by roleset ID."""
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

            self.search.add_frameset(frameset)

        results = self.search.by_syntax("NP V NP")

        # Should be sorted by roleset ID
        assert len(results) == 3
        assert results[0].id == "verb.01"
        assert results[1].id == "verb.02"
        assert results[2].id == "verb.03"

    def test_get_arg_position_helper(self):
        """Test _get_arg_position helper method."""
        # Normal position
        arg1 = Arg(type="ARG0", start=5, end=6, text="test")
        assert self.search._get_arg_position(arg1) == 5

        # Unknown position
        arg2 = Arg(type="ARG0", start="?", end="?", text="test")
        assert self.search._get_arg_position(arg2) == 999

    def test_get_rel_position_helper(self):
        """Test _get_rel_position helper method."""
        # Normal position
        rel1 = Rel(relloc="3", text="verb")
        assert self.search._get_rel_position(rel1) == 3

        # Unknown position
        rel2 = Rel(relloc="?", text="verb")
        assert self.search._get_rel_position(rel2) is None

        # None rel
        assert self.search._get_rel_position(None) is None
