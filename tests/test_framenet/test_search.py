"""Tests for FrameNet search functionality."""

import re

import pytest

from glazing.framenet.models import (
    AnnotatedText,
    Frame,
    FrameElement,
    Lexeme,
    LexicalUnit,
    SentenceCount,
    TextAnnotation,
)
from glazing.framenet.search import FrameNetSearch


class TestFrameNetSearch:
    """Tests for FrameNetSearch class."""

    @pytest.fixture
    def sample_frames(self):
        """Create sample frames for testing."""
        # Create Abandonment frame
        abandonment_frame = Frame(
            id=2031,
            name="Abandonment",
            definition=AnnotatedText(
                raw_text=(
                    "An <fex name='Agent'>Agent</fex> leaves behind a "
                    "<fex name='Theme'>Theme</fex>."
                ),
                plain_text="An Agent leaves behind a Theme.",
                annotations=[
                    TextAnnotation(start=3, end=8, type="fex", name="Agent", text="Agent"),
                    TextAnnotation(start=24, end=29, type="fex", name="Theme", text="Theme"),
                ],
            ),
            frame_elements=[
                FrameElement(
                    id=1001,
                    name="Agent",
                    abbrev="Agt",
                    definition=AnnotatedText(
                        raw_text="The sentient entity that abandons.",
                        plain_text="The sentient entity that abandons.",
                        annotations=[],
                    ),
                    core_type="Core",
                    bg_color="FF0000",
                    fg_color="FFFFFF",
                ),
                FrameElement(
                    id=1002,
                    name="Theme",
                    abbrev="Thm",
                    definition=AnnotatedText(
                        raw_text="The entity being abandoned.",
                        plain_text="The entity being abandoned.",
                        annotations=[],
                    ),
                    core_type="Core",
                    bg_color="0000FF",
                    fg_color="FFFFFF",
                ),
                FrameElement(
                    id=1003,
                    name="Time",
                    abbrev="Tim",
                    definition=AnnotatedText(
                        raw_text="When the abandonment occurs.",
                        plain_text="When the abandonment occurs.",
                        annotations=[],
                    ),
                    core_type="Peripheral",
                    bg_color="00FF00",
                    fg_color="000000",
                ),
            ],
            lexical_units=[
                LexicalUnit(
                    id=10001,
                    name="abandon.v",
                    pos="V",
                    definition="To leave behind",
                    frame_id=2031,
                    frame_name="Abandonment",
                    sentence_count=SentenceCount(annotated=5, total=10),
                    lexemes=[Lexeme(name="abandon", pos="V", headword=True)],
                ),
                LexicalUnit(
                    id=10002,
                    name="desert.v",
                    pos="V",
                    definition="To abandon in a remote place",
                    frame_id=2031,
                    frame_name="Abandonment",
                    sentence_count=SentenceCount(annotated=3, total=8),
                    lexemes=[Lexeme(name="desert", pos="V", headword=True)],
                ),
            ],
        )

        # Create Giving frame
        giving_frame = Frame(
            id=139,
            name="Giving",
            definition=AnnotatedText(
                raw_text=(
                    "A <fex name='Donor'>Donor</fex> transfers a "
                    "<fex name='Theme'>Theme</fex> to a "
                    "<fex name='Recipient'>Recipient</fex>."
                ),
                plain_text="A Donor transfers a Theme to a Recipient.",
                annotations=[
                    TextAnnotation(start=2, end=7, type="fex", name="Donor", text="Donor"),
                    TextAnnotation(start=20, end=25, type="fex", name="Theme", text="Theme"),
                    TextAnnotation(
                        start=32, end=41, type="fex", name="Recipient", text="Recipient"
                    ),
                ],
            ),
            frame_elements=[
                FrameElement(
                    id=2001,
                    name="Donor",
                    abbrev="Don",
                    definition=AnnotatedText(
                        raw_text="The person who gives.",
                        plain_text="The person who gives.",
                        annotations=[],
                    ),
                    core_type="Core",
                    bg_color="FF0000",
                    fg_color="FFFFFF",
                ),
                FrameElement(
                    id=2002,
                    name="Theme",
                    abbrev="Thm",
                    definition=AnnotatedText(
                        raw_text="The object given.", plain_text="The object given.", annotations=[]
                    ),
                    core_type="Core",
                    bg_color="0000FF",
                    fg_color="FFFFFF",
                ),
                FrameElement(
                    id=2003,
                    name="Recipient",
                    abbrev="Rec",
                    definition=AnnotatedText(
                        raw_text="The person who receives.",
                        plain_text="The person who receives.",
                        annotations=[],
                    ),
                    core_type="Core",
                    bg_color="00FF00",
                    fg_color="000000",
                ),
                FrameElement(
                    id=2004,
                    name="Manner",
                    abbrev="Man",
                    definition=AnnotatedText(
                        raw_text="How the giving is done.",
                        plain_text="How the giving is done.",
                        annotations=[],
                    ),
                    core_type="Peripheral",
                    bg_color="FFFF00",
                    fg_color="000000",
                ),
            ],
            lexical_units=[
                LexicalUnit(
                    id=20001,
                    name="give.v",
                    pos="V",
                    definition="To transfer possession",
                    frame_id=139,
                    frame_name="Giving",
                    sentence_count=SentenceCount(annotated=20, total=50),
                    lexemes=[Lexeme(name="give", pos="V", headword=True)],
                ),
                LexicalUnit(
                    id=20002,
                    name="gift.n",
                    pos="N",
                    definition="Something given",
                    frame_id=139,
                    frame_name="Giving",
                    sentence_count=SentenceCount(annotated=10, total=25),
                    lexemes=[Lexeme(name="gift", pos="N", headword=True)],
                ),
            ],
        )

        return [abandonment_frame, giving_frame]

    def test_init_empty(self):
        """Test initialization with empty index."""
        index = FrameNetSearch()
        assert index.get_statistics()["frame_count"] == 0
        assert index.get_all_fe_names() == []
        assert index.get_all_lemmas() == []

    def test_init_with_frames(self, sample_frames):
        """Test initialization with frames."""
        index = FrameNetSearch(sample_frames)
        stats = index.get_statistics()
        assert stats["frame_count"] == 2
        assert stats["unique_fe_names"] == 6  # Agent, Theme, Time, Donor, Recipient, Manner
        assert stats["unique_lemmas"] == 4  # abandon, desert, give, gift

    def test_add_frame(self, sample_frames):
        """Test adding frames to index."""
        index = FrameNetSearch()
        index.add_frame(sample_frames[0])

        assert index.get_statistics()["frame_count"] == 1
        assert index.get_frame_by_id(2031) == sample_frames[0]
        assert index.get_frame_by_name("Abandonment") == sample_frames[0]

    def test_add_duplicate_frame(self, sample_frames):
        """Test adding duplicate frame raises error."""
        index = FrameNetSearch()
        index.add_frame(sample_frames[0])

        with pytest.raises(ValueError, match="already exists"):
            index.add_frame(sample_frames[0])

    def test_get_frame_by_id(self, sample_frames):
        """Test getting frame by ID."""
        index = FrameNetSearch(sample_frames)

        frame = index.get_frame_by_id(2031)
        assert frame is not None
        assert frame.name == "Abandonment"

        assert index.get_frame_by_id(9999) is None

    def test_get_frame_by_name(self, sample_frames):
        """Test getting frame by name."""
        index = FrameNetSearch(sample_frames)

        frame = index.get_frame_by_name("Giving")
        assert frame is not None
        assert frame.id == 139

        assert index.get_frame_by_name("NonExistent") is None

    def test_search_frames_by_name(self, sample_frames):
        """Test searching frames by name pattern."""
        index = FrameNetSearch(sample_frames)

        # Test exact match
        results = index.search_frames_by_name("Giving")
        assert len(results) == 1
        assert results[0].name == "Giving"

        # Test partial match
        results = index.search_frames_by_name(".*ing")
        assert len(results) == 1
        assert results[0].name == "Giving"

        # Test case insensitive
        results = index.search_frames_by_name("giving", case_sensitive=False)
        assert len(results) == 1

        # Test case sensitive
        results = index.search_frames_by_name("giving", case_sensitive=True)
        assert len(results) == 0

        # Test no matches
        results = index.search_frames_by_name("NoMatch")
        assert len(results) == 0

    def test_search_frames_by_definition(self, sample_frames):
        """Test searching frames by definition pattern."""
        index = FrameNetSearch(sample_frames)

        # Search for "transfers"
        results = index.search_frames_by_definition("transfers")
        assert len(results) == 1
        assert results[0].name == "Giving"

        # Search for "leaves behind"
        results = index.search_frames_by_definition("leaves behind")
        assert len(results) == 1
        assert results[0].name == "Abandonment"

        # Search with regex
        results = index.search_frames_by_definition("Agent|Donor")
        assert len(results) == 2

        # Case insensitive
        results = index.search_frames_by_definition("TRANSFERS", case_sensitive=False)
        assert len(results) == 1

    def test_find_frames_with_fe(self, sample_frames):
        """Test finding frames with specific FE."""
        index = FrameNetSearch(sample_frames)

        # Find frames with "Theme"
        results = index.find_frames_with_fe("Theme")
        assert len(results) == 2
        frame_names = [f.name for f in results]
        assert "Abandonment" in frame_names
        assert "Giving" in frame_names

        # Find frames with "Donor"
        results = index.find_frames_with_fe("Donor")
        assert len(results) == 1
        assert results[0].name == "Giving"

        # Find frames with non-existent FE
        results = index.find_frames_with_fe("NonExistent")
        assert len(results) == 0

    def test_find_frames_with_fe_by_core_type(self, sample_frames):
        """Test finding frames with FE filtered by core type."""
        index = FrameNetSearch(sample_frames)

        # Find frames with Core "Theme"
        results = index.find_frames_with_fe("Theme", core_type="Core")
        assert len(results) == 2

        # Find frames with Peripheral "Time"
        results = index.find_frames_with_fe("Time", core_type="Peripheral")
        assert len(results) == 1
        assert results[0].name == "Abandonment"

        # Find frames with Core "Time" (doesn't exist as Core)
        results = index.find_frames_with_fe("Time", core_type="Core")
        assert len(results) == 0

    def test_find_frames_by_lemma(self, sample_frames):
        """Test finding frames by lemma."""
        index = FrameNetSearch(sample_frames)

        # Find frames for "abandon"
        results = index.find_frames_by_lemma("abandon")
        assert len(results) == 1
        assert results[0].name == "Abandonment"

        # Find frames for "give"
        results = index.find_frames_by_lemma("give")
        assert len(results) == 1
        assert results[0].name == "Giving"

        # Find frames for non-existent lemma
        results = index.find_frames_by_lemma("nonexistent")
        assert len(results) == 0

    def test_find_frames_by_lemma_with_pos(self, sample_frames):
        """Test finding frames by lemma with POS filter."""
        index = FrameNetSearch(sample_frames)

        # Find frames for "give" as verb
        results = index.find_frames_by_lemma("give", pos="V")
        assert len(results) == 1
        assert results[0].name == "Giving"

        # Find frames for "gift" as noun
        results = index.find_frames_by_lemma("gift", pos="N")
        assert len(results) == 1
        assert results[0].name == "Giving"

        # Find frames for "gift" as verb (doesn't exist)
        results = index.find_frames_by_lemma("gift", pos="V")
        assert len(results) == 0

    def test_search_lexical_units(self, sample_frames):
        """Test searching lexical units."""
        index = FrameNetSearch(sample_frames)

        # Search for all verbs
        results = index.search_lexical_units(".*\\.v")
        assert len(results) == 3  # abandon.v, desert.v, give.v

        # Search for nouns
        results = index.search_lexical_units(".*\\.n")
        assert len(results) == 1  # gift.n

        # Search with POS filter
        results = index.search_lexical_units(".*", pos="V")
        assert len(results) == 3

        # Case insensitive search
        results = index.search_lexical_units("GIVE", case_sensitive=False)
        assert len(results) == 1
        assert results[0].name == "give.v"

    def test_get_fe_across_frames(self, sample_frames):
        """Test getting FE definitions across frames."""
        index = FrameNetSearch(sample_frames)

        # Get "Theme" across frames
        theme_defs = index.get_fe_across_frames("Theme")
        assert len(theme_defs) == 2
        assert "Abandonment" in theme_defs
        assert "Giving" in theme_defs

        # Check that definitions are different
        abandon_theme = theme_defs["Abandonment"]
        giving_theme = theme_defs["Giving"]
        assert abandon_theme.definition.plain_text != giving_theme.definition.plain_text

        # Get non-existent FE
        defs = index.get_fe_across_frames("NonExistent")
        assert len(defs) == 0

    def test_get_all_fe_names(self, sample_frames):
        """Test getting all FE names."""
        index = FrameNetSearch(sample_frames)

        fe_names = index.get_all_fe_names()
        assert len(fe_names) == 6
        assert "Agent" in fe_names
        assert "Donor" in fe_names
        assert "Manner" in fe_names
        assert "Recipient" in fe_names
        assert "Theme" in fe_names
        assert "Time" in fe_names

        # Check sorted
        assert fe_names == sorted(fe_names)

    def test_get_all_lemmas(self, sample_frames):
        """Test getting all lemmas."""
        index = FrameNetSearch(sample_frames)

        lemmas = index.get_all_lemmas()
        assert len(lemmas) == 4
        assert "abandon" in lemmas
        assert "desert" in lemmas
        assert "gift" in lemmas
        assert "give" in lemmas

        # Check sorted
        assert lemmas == sorted(lemmas)

    def test_get_statistics(self, sample_frames):
        """Test getting index statistics."""
        index = FrameNetSearch(sample_frames)

        stats = index.get_statistics()
        assert stats["frame_count"] == 2
        assert stats["unique_fe_names"] == 6
        assert stats["total_fes"] == 7  # 3 + 4
        assert stats["unique_lemmas"] == 4
        assert stats["total_lus"] == 4  # 2 + 2

    def test_merge_indices(self, sample_frames):
        """Test merging indices."""
        index1 = FrameNetSearch([sample_frames[0]])
        index2 = FrameNetSearch([sample_frames[1]])

        index1.merge(index2)

        assert index1.get_statistics()["frame_count"] == 2
        assert index1.get_frame_by_name("Abandonment") is not None
        assert index1.get_frame_by_name("Giving") is not None

    def test_merge_indices_conflict(self, sample_frames):
        """Test merging indices with conflicting IDs."""
        index1 = FrameNetSearch([sample_frames[0]])
        index2 = FrameNetSearch([sample_frames[0]])  # Same frame

        with pytest.raises(ValueError, match="Cannot merge"):
            index1.merge(index2)

    def test_invalid_regex_pattern(self, sample_frames):
        """Test invalid regex patterns raise error."""
        index = FrameNetSearch(sample_frames)

        with pytest.raises(re.error):
            index.search_frames_by_name("[invalid")

        with pytest.raises(re.error):
            index.search_frames_by_definition("(unclosed")

        with pytest.raises(re.error):
            index.search_lexical_units("*invalid")
