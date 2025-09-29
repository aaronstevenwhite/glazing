"""Test WordNet syntax search integration."""

from glazing.syntax.parser import SyntaxParser
from glazing.wordnet.models import Synset, VerbFrame, Word
from glazing.wordnet.search import WordNetSearch


class TestWordNetSyntaxIntegration:
    """Test WordNet syntax search integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.search = WordNetSearch()
        self.parser = SyntaxParser()

    def test_frame_number_mapping_np_v(self):
        """Test mapping for NP V pattern (frame 1)."""
        pattern = self.parser.parse("NP V")
        frame_numbers = self.search._get_frame_numbers_for_pattern(pattern)

        # Frame 1 and 35 both map to "NP V"
        assert 1 in frame_numbers or 35 in frame_numbers
        assert len(frame_numbers) >= 1

    def test_frame_number_mapping_np_v_np(self):
        """Test mapping for NP V NP pattern (frame 8, 13)."""
        pattern = self.parser.parse("NP V NP")
        frame_numbers = self.search._get_frame_numbers_for_pattern(pattern)

        # Frames 8 and 13 both map to "NP V NP"
        expected_frames = {8, 13}
        assert expected_frames.issubset(frame_numbers)

    def test_frame_number_mapping_np_v_pp(self):
        """Test mapping for NP V PP pattern (frame 2, 30)."""
        pattern = self.parser.parse("NP V PP")
        frame_numbers = self.search._get_frame_numbers_for_pattern(pattern)

        # Frames 2 and 30 both map to "NP V PP"
        expected_frames = {2, 30}
        assert expected_frames.issubset(frame_numbers)

    def test_frame_number_mapping_np_v_np_pp(self):
        """Test mapping for NP V NP PP pattern (frame 9, 31)."""
        pattern = self.parser.parse("NP V NP PP")
        frame_numbers = self.search._get_frame_numbers_for_pattern(pattern)

        # Frames 9 and 31 both map to "NP V NP PP"
        expected_frames = {9, 31}
        assert expected_frames.issubset(frame_numbers)

    def test_frame_number_mapping_ditransitive(self):
        """Test mapping for ditransitive patterns (frame 10, 11)."""
        pattern = self.parser.parse("NP V NP NP")
        frame_numbers = self.search._get_frame_numbers_for_pattern(pattern)

        # Frames 10 and 11 both map to "NP V NP NP"
        expected_frames = {10, 11}
        assert expected_frames.issubset(frame_numbers)

    def test_pattern_to_string_conversion(self):
        """Test pattern to string conversion."""
        pattern = self.parser.parse("NP V PP.instrument")
        pattern_str = self.search._pattern_to_string(pattern)

        # Should convert back to a readable string format
        assert "NP" in pattern_str
        assert "VERB" in pattern_str or "V" in pattern_str
        assert "PP" in pattern_str

    def test_patterns_match_exact(self):
        """Test exact pattern matching."""
        search_pattern = self.parser.parse("NP V NP")

        # Should match exactly with frame pattern "NP V NP"
        matches = self.search._patterns_match("NP VERB NP", "NP V NP", search_pattern)
        assert matches is True

    def test_patterns_match_hierarchical(self):
        """Test hierarchical pattern matching."""
        # General PP should match specific PP patterns
        general_pattern = self.parser.parse("NP V PP")

        # Test against a more specific frame pattern
        matches = self.search._patterns_match("NP VERB PP", "NP V PP", general_pattern)
        assert matches is True

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

    def test_by_syntax_with_mock_data(self):
        """Test syntax search with mock synset data."""
        # Create a mock verb synset with frames
        mock_verb_frame = VerbFrame(frame_number=8, word_indices=[0])
        mock_word = Word(lemma="give", lex_id=0)
        mock_synset = Synset(
            offset="01234567",
            lex_filenum=29,  # verb.possession
            lex_filename="verb.possession",
            ss_type="v",
            words=[mock_word],
            pointers=[],
            frames=[mock_verb_frame],  # Frames at synset level
            gloss="to transfer possession",
        )

        # Add to search index
        self.search.add_synset(mock_synset)

        # Search for pattern that matches frame 8 (NP V NP)
        results = self.search.by_syntax("NP V NP")

        # Should find the mock synset
        assert len(results) == 1
        assert results[0] == mock_synset

    def test_by_syntax_non_verb_synsets_ignored(self):
        """Test that non-verb synsets are ignored in syntax search."""
        # Create a mock noun synset (should be ignored)
        mock_word = Word(lemma="dog", lex_id=0, pos="n")
        mock_noun_synset = Synset(
            offset="01234567",
            lex_filenum=2,  # noun.animal
            lex_filename="noun.animal",
            ss_type="n",
            words=[mock_word],
            pointers=[],
            gloss="a domestic animal",
        )

        # Add to search index
        self.search.add_synset(mock_noun_synset)

        # Search for any pattern
        results = self.search.by_syntax("NP V NP")

        # Should return empty since only noun synsets exist
        assert len(results) == 0

    def test_by_syntax_multiple_frames_per_word(self):
        """Test synset with word having multiple frames."""
        mock_frames = [
            VerbFrame(frame_number=8, word_indices=[0]),  # NP V NP
            VerbFrame(frame_number=9, word_indices=[0]),  # NP V NP PP
        ]
        mock_word = Word(lemma="give", lex_id=0)
        mock_synset = Synset(
            offset="01234567",
            lex_filenum=29,  # verb.possession
            lex_filename="verb.possession",
            ss_type="v",
            words=[mock_word],
            pointers=[],
            frames=mock_frames,  # Frames at synset level
            gloss="to transfer possession",
        )

        self.search.add_synset(mock_synset)

        # Should match both frame 8 and frame 9 patterns
        results_8 = self.search.by_syntax("NP V NP")  # matches frame 8
        results_9 = self.search.by_syntax("NP V NP PP")  # matches frame 9

        assert len(results_8) == 1
        assert len(results_9) == 1
        assert results_8[0] == mock_synset
        assert results_9[0] == mock_synset

    def test_by_syntax_no_matching_frames(self):
        """Test search with no matching verb frames."""
        # Create synset with frame that doesn't match search pattern
        mock_frame = VerbFrame(frame_number=1, word_indices=[0])  # NP V
        mock_word = Word(lemma="sleep", lex_id=0)
        mock_synset = Synset(
            offset="01234567",
            lex_filenum=30,  # verb.body
            lex_filename="verb.body",
            ss_type="v",
            words=[mock_word],
            pointers=[],
            frames=[mock_frame],  # Frames at synset level
            gloss="to rest",
        )

        self.search.add_synset(mock_synset)

        # Search for pattern that doesn't match frame 1
        results = self.search.by_syntax("NP V NP NP")  # ditransitive, no match

        assert len(results) == 0

    def test_by_syntax_word_without_frames(self):
        """Test synset with verb word that has no frames."""
        mock_word = Word(lemma="test", lex_id=0)
        mock_synset = Synset(
            offset="01234567",
            lex_filenum=31,  # verb.cognition
            lex_filename="verb.cognition",
            ss_type="v",
            words=[mock_word],
            pointers=[],
            frames=None,  # No frames
            gloss="to examine",
        )

        self.search.add_synset(mock_synset)

        # Should not match any pattern since no frames exist
        results = self.search.by_syntax("NP V NP")
        assert len(results) == 0

    def test_by_syntax_invalid_pattern(self):
        """Test syntax search with invalid pattern."""
        # Test with various invalid patterns
        invalid_patterns = ["", "   ", "INVALID"]

        for pattern in invalid_patterns:
            try:
                results = self.search.by_syntax(pattern)
                # If it doesn't raise an error, should return empty list
                assert isinstance(results, list)
            except (ValueError, AttributeError):
                # Expected for invalid patterns
                pass

    def test_by_syntax_results_sorted(self):
        """Test that results are sorted by synset offset."""
        # Create multiple mock synsets with different offsets
        synsets_data = [
            ("99999999", VerbFrame(frame_number=8, word_indices=[0])),
            ("11111111", VerbFrame(frame_number=8, word_indices=[0])),
            ("55555555", VerbFrame(frame_number=8, word_indices=[0])),
        ]

        for offset, frame in synsets_data:
            mock_word = Word(lemma="test", lex_id=0)
            mock_synset = Synset(
                offset=offset,
                lex_filenum=29,  # verb.test
                lex_filename="verb.cognition",
                ss_type="v",
                words=[mock_word],
                pointers=[],
                frames=[frame],  # Frames at synset level
                gloss="test verb",
            )
            self.search.add_synset(mock_synset)

        results = self.search.by_syntax("NP V NP")

        # Should be sorted by offset
        assert len(results) == 3
        assert results[0].offset == "11111111"
        assert results[1].offset == "55555555"
        assert results[2].offset == "99999999"
