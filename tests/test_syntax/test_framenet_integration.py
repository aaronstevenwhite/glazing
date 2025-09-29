"""Test FrameNet syntax search integration."""

from glazing.framenet.models import (
    AnnotatedText,
    FERealization,
    Frame,
    FrameElement,
    Lexeme,
    LexicalUnit,
    SentenceCount,
    ValencePattern,
    ValenceRealizationPattern,
    ValenceUnit,
)
from glazing.framenet.search import FrameNetSearch
from glazing.syntax.parser import SyntaxParser


class TestFrameNetSyntaxIntegration:
    """Test FrameNet syntax search integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.search = FrameNetSearch()
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

    def test_map_fe_to_semantic_role(self):
        """Test FE to semantic role mapping."""
        mappings = [
            ("Location", "location"),
            ("Place", "location"),
            ("Source", "location"),
            ("Goal", "location"),
            ("Time", "temporal"),
            ("Duration", "temporal"),
            ("Manner", "manner"),
            ("Means", "manner"),
            ("Instrument", "instrument"),
            ("Purpose", "purpose"),
            ("Reason", "cause"),
            ("Cause", "cause"),
            ("Beneficiary", "beneficiary"),
            ("Recipient", "beneficiary"),
            ("UnknownFE", None),  # Should return None for unmapped FEs
        ]

        for fe_name, expected_role in mappings:
            result = self.search._map_fe_to_semantic_role(fe_name)
            assert result == expected_role, (
                f"Failed for FE {fe_name}: got {result}, expected {expected_role}"
            )

    def test_extract_pattern_basic_transitive(self):
        """Test pattern extraction from basic transitive valence."""
        # Create a basic NP V NP pattern
        agent_unit = ValenceUnit(gf="Ext", pt="NP", fe="Agent")
        theme_unit = ValenceUnit(gf="Obj", pt="NP", fe="Theme")

        agent_pattern = ValenceRealizationPattern(
            valence_units=[agent_unit], anno_set_ids=[1], total=1
        )
        theme_pattern = ValenceRealizationPattern(
            valence_units=[theme_unit], anno_set_ids=[2], total=1
        )

        agent_realization = FERealization(fe_name="Agent", total=1, patterns=[agent_pattern])
        theme_realization = FERealization(fe_name="Theme", total=1, patterns=[theme_pattern])

        valence_pattern = ValencePattern(
            total_annotated=2, fe_realizations=[agent_realization, theme_realization], patterns=[]
        )

        pattern = self.search._extract_pattern_from_valence(valence_pattern)

        assert pattern is not None
        assert len(pattern.elements) == 3  # NP V NP
        assert pattern.elements[0].constituent == "NP"  # Agent (Ext)
        assert pattern.elements[1].constituent == "VERB"
        assert pattern.elements[2].constituent == "NP"  # Theme (Obj)

    def test_extract_pattern_with_pp_location(self):
        """Test pattern extraction with PP location."""
        # Create NP V NP PP.location pattern
        agent_unit = ValenceUnit(gf="Ext", pt="NP", fe="Agent")
        theme_unit = ValenceUnit(gf="Obj", pt="NP", fe="Theme")
        location_unit = ValenceUnit(gf="Dep", pt="PP", fe="Location")

        agent_pattern = ValenceRealizationPattern(
            valence_units=[agent_unit], anno_set_ids=[1], total=1
        )
        theme_pattern = ValenceRealizationPattern(
            valence_units=[theme_unit], anno_set_ids=[2], total=1
        )
        location_pattern = ValenceRealizationPattern(
            valence_units=[location_unit], anno_set_ids=[3], total=1
        )

        agent_realization = FERealization(fe_name="Agent", total=1, patterns=[agent_pattern])
        theme_realization = FERealization(fe_name="Theme", total=1, patterns=[theme_pattern])
        location_realization = FERealization(
            fe_name="Location", total=1, patterns=[location_pattern]
        )

        valence_pattern = ValencePattern(
            total_annotated=3,
            fe_realizations=[agent_realization, theme_realization, location_realization],
            patterns=[],
        )

        pattern = self.search._extract_pattern_from_valence(valence_pattern)

        assert pattern is not None
        assert len(pattern.elements) == 4  # NP V NP PP
        assert pattern.elements[0].constituent == "NP"  # Agent (Ext)
        assert pattern.elements[1].constituent == "VERB"
        assert pattern.elements[2].constituent == "NP"  # Theme (Obj)
        assert pattern.elements[3].constituent == "PP"  # Location (Dep)
        assert pattern.elements[3].semantic_role == "location"

    def test_by_syntax_with_mock_data(self):
        """Test syntax search with mock FrameNet data."""
        # Create a mock frame with valence patterns

        # Create Agent FE
        agent_fe = FrameElement(
            id=1,
            name="Agent",
            abbrev="Agt",
            core_type="Core",
            definition=AnnotatedText.parse("The agent"),
            bg_color="FF0000",
            fg_color="FFFFFF",
            requires_fe=[],
        )

        # Create Theme FE
        theme_fe = FrameElement(
            id=2,
            name="Theme",
            abbrev="Thm",
            core_type="Core",
            definition=AnnotatedText.parse("The theme"),
            bg_color="00FF00",
            fg_color="000000",
            requires_fe=[],
        )

        # Create valence pattern (NP V NP)
        agent_unit = ValenceUnit(gf="Ext", pt="NP", fe="Agent")
        theme_unit = ValenceUnit(gf="Obj", pt="NP", fe="Theme")

        agent_realization_pattern = ValenceRealizationPattern(
            valence_units=[agent_unit], anno_set_ids=[1], total=1
        )
        theme_realization_pattern = ValenceRealizationPattern(
            valence_units=[theme_unit], anno_set_ids=[2], total=1
        )

        agent_realization = FERealization(
            fe_name="Agent", total=1, patterns=[agent_realization_pattern]
        )
        theme_realization = FERealization(
            fe_name="Theme", total=1, patterns=[theme_realization_pattern]
        )

        valence_pattern = ValencePattern(
            total_annotated=2, fe_realizations=[agent_realization, theme_realization], patterns=[]
        )

        # Create lexical unit with valence patterns
        lu = LexicalUnit(
            id=1,
            name="test.v",
            pos="V",
            definition="To test",
            frame_id=1,
            frame_name="Testing",
            sentence_count=SentenceCount(annotated=0, total=0),
            lexemes=[Lexeme(name="test", pos="V", headword=True)],
            valence_patterns=[valence_pattern],
        )

        # Create frame
        frame = Frame(
            id=1,
            name="Testing",
            creation_date="2023-01-01T00:00:00Z",
            definition=AnnotatedText.parse("A test frame"),
            frame_elements=[agent_fe, theme_fe],
            lexical_units=[lu],
            frame_relations=[],
        )

        self.search.add_frame(frame)

        # Search for NP V NP pattern - should match
        results = self.search.by_syntax("NP V NP")
        assert len(results) == 1
        assert results[0] == frame

    def test_by_syntax_no_valence_patterns(self):
        """Test with lexical units that have no valence patterns."""
        # Create frame with LU but no valence patterns
        fe = FrameElement(
            id=1,
            name="Agent",
            abbrev="Agt",
            core_type="Core",
            definition=AnnotatedText.parse("The agent"),
            bg_color="FF0000",
            fg_color="FFFFFF",
            requires_fe=[],
        )

        lu = LexicalUnit(
            id=1,
            name="test.v",
            pos="V",
            definition="To test",
            frame_id=1,
            frame_name="Testing",
            sentence_count=SentenceCount(annotated=0, total=0),
            lexemes=[Lexeme(name="test", pos="V", headword=True)],
            valence_patterns=[],  # No valence patterns
        )

        frame = Frame(
            id=1,
            name="Testing",
            creation_date="2023-01-01T00:00:00Z",
            definition=AnnotatedText.parse("A test frame"),
            frame_elements=[fe],
            lexical_units=[lu],
            frame_relations=[],
        )

        self.search.add_frame(frame)

        # Should not match any pattern since no valence patterns
        results = self.search.by_syntax("NP V NP")
        assert len(results) == 0

    def test_by_syntax_results_sorted(self):
        """Test that results are sorted by frame name."""
        # Create multiple frames with different names
        frames_data = [("Zeta_Frame", 3), ("Alpha_Frame", 1), ("Beta_Frame", 2)]

        for frame_name, frame_id in frames_data:
            # Create basic NP V NP valence pattern
            agent_unit = ValenceUnit(gf="Ext", pt="NP", fe="Agent")
            theme_unit = ValenceUnit(gf="Obj", pt="NP", fe="Theme")

            agent_pattern = ValenceRealizationPattern(
                valence_units=[agent_unit], anno_set_ids=[1], total=1
            )
            theme_pattern = ValenceRealizationPattern(
                valence_units=[theme_unit], anno_set_ids=[2], total=1
            )

            agent_realization = FERealization(fe_name="Agent", total=1, patterns=[agent_pattern])
            theme_realization = FERealization(fe_name="Theme", total=1, patterns=[theme_pattern])

            valence_pattern = ValencePattern(
                total_annotated=2,
                fe_realizations=[agent_realization, theme_realization],
                patterns=[],
            )

            lu = LexicalUnit(
                id=frame_id,
                name="test.v",
                pos="V",
                definition="To test",
                frame_id=frame_id,
                frame_name=frame_name,
                sentence_count=SentenceCount(annotated=0, total=0),
                lexemes=[Lexeme(name="test", pos="V", headword=True)],
                valence_patterns=[valence_pattern],
            )

            # Create FEs
            agent_fe = FrameElement(
                id=frame_id * 10 + 1,
                name="Agent",
                abbrev="Agt",
                core_type="Core",
                definition=AnnotatedText.parse("The agent"),
                bg_color="FF0000",
                fg_color="FFFFFF",
                requires_fe=[],
            )
            theme_fe = FrameElement(
                id=frame_id * 10 + 2,
                name="Theme",
                abbrev="Thm",
                core_type="Core",
                definition=AnnotatedText.parse("The theme"),
                bg_color="00FF00",
                fg_color="000000",
                requires_fe=[],
            )

            frame = Frame(
                id=frame_id,
                name=frame_name,
                creation_date="2023-01-01T00:00:00Z",
                definition=AnnotatedText.parse("A test frame"),
                frame_elements=[agent_fe, theme_fe],
                lexical_units=[lu],
                frame_relations=[],
            )

            self.search.add_frame(frame)

        results = self.search.by_syntax("NP V NP")

        # Should be sorted by frame name
        assert len(results) == 3
        assert results[0].name == "Alpha_Frame"
        assert results[1].name == "Beta_Frame"
        assert results[2].name == "Zeta_Frame"

    def test_by_syntax_duplicate_removal(self):
        """Test that duplicate frames are removed from results."""
        # Create frame with LU that has multiple valence patterns matching same syntax

        # Create Agent and Theme FEs
        agent_fe = FrameElement(
            id=1,
            name="Agent",
            abbrev="Agt",
            core_type="Core",
            definition=AnnotatedText.parse("The agent"),
            bg_color="FF0000",
            fg_color="FFFFFF",
            requires_fe=[],
        )
        theme_fe = FrameElement(
            id=2,
            name="Theme",
            abbrev="Thm",
            core_type="Core",
            definition=AnnotatedText.parse("The theme"),
            bg_color="00FF00",
            fg_color="000000",
            requires_fe=[],
        )

        # Create two different valence patterns that both yield NP V NP
        # Pattern 1: Agent(Ext:NP), Theme(Obj:NP)
        agent_unit1 = ValenceUnit(gf="Ext", pt="NP", fe="Agent")
        theme_unit1 = ValenceUnit(gf="Obj", pt="NP", fe="Theme")

        pattern1 = ValencePattern(
            total_annotated=2,
            fe_realizations=[
                FERealization(
                    fe_name="Agent",
                    total=1,
                    patterns=[
                        ValenceRealizationPattern(
                            valence_units=[agent_unit1], anno_set_ids=[1], total=1
                        )
                    ],
                ),
                FERealization(
                    fe_name="Theme",
                    total=1,
                    patterns=[
                        ValenceRealizationPattern(
                            valence_units=[theme_unit1], anno_set_ids=[2], total=1
                        )
                    ],
                ),
            ],
            patterns=[],
        )

        # Pattern 2: Different realization but same syntax
        agent_unit2 = ValenceUnit(gf="Ext", pt="NP", fe="Agent")
        theme_unit2 = ValenceUnit(gf="Obj", pt="NP", fe="Theme")

        pattern2 = ValencePattern(
            total_annotated=2,
            fe_realizations=[
                FERealization(
                    fe_name="Agent",
                    total=1,
                    patterns=[
                        ValenceRealizationPattern(
                            valence_units=[agent_unit2], anno_set_ids=[3], total=1
                        )
                    ],
                ),
                FERealization(
                    fe_name="Theme",
                    total=1,
                    patterns=[
                        ValenceRealizationPattern(
                            valence_units=[theme_unit2], anno_set_ids=[4], total=1
                        )
                    ],
                ),
            ],
            patterns=[],
        )

        # LU with both patterns
        lu = LexicalUnit(
            id=1,
            name="test.v",
            pos="V",
            definition="To test",
            frame_id=1,
            frame_name="Testing",
            sentence_count=SentenceCount(annotated=0, total=0),
            lexemes=[Lexeme(name="test", pos="V", headword=True)],
            valence_patterns=[pattern1, pattern2],  # Both patterns match NP V NP
        )

        frame = Frame(
            id=1,
            name="Testing",
            creation_date="2023-01-01T00:00:00Z",
            definition=AnnotatedText.parse("A test frame"),
            frame_elements=[agent_fe, theme_fe],
            lexical_units=[lu],
            frame_relations=[],
        )

        self.search.add_frame(frame)

        # Should return frame only once despite multiple matching patterns
        results = self.search.by_syntax("NP V NP")
        assert len(results) == 1
        assert results[0] == frame
