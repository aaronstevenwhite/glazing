"""Tests for WordNet search functionality."""

import pytest

from glazing.syntax.parser import SyntaxParser
from glazing.wordnet.models import Pointer, Sense, Synset, VerbFrame, Word
from glazing.wordnet.search import WordNetSearch


class TestWordNetSearch:
    """Tests for WordNetSearch class."""

    @pytest.fixture
    def sample_synsets(self):
        """Create sample synsets for testing."""
        # Create dog synset (noun)
        dog_synset = Synset(
            offset="02084442",
            lex_filenum=5,
            lex_filename="noun.animal",
            ss_type="n",
            words=[
                Word(lemma="dog", lex_id=0),
                Word(lemma="domestic_dog", lex_id=1),
                Word(lemma="canis_familiaris", lex_id=2),
            ],
            pointers=[
                Pointer(symbol="@", offset="02083346", pos="n", source=0, target=0),  # hypernym
                Pointer(symbol="~", offset="01317541", pos="n", source=0, target=0),  # hyponym
                Pointer(
                    symbol="#m", offset="02085443", pos="n", source=0, target=0
                ),  # member holonym
            ],
            gloss="a member of the genus Canis that has been domesticated by man",
        )

        # Create cat synset (noun)
        cat_synset = Synset(
            offset="02121620",
            lex_filenum=5,
            lex_filename="noun.animal",
            ss_type="n",
            words=[Word(lemma="cat", lex_id=0), Word(lemma="true_cat", lex_id=1)],
            pointers=[
                Pointer(symbol="@", offset="02120997", pos="n", source=0, target=0),  # hypernym
                Pointer(symbol="~", offset="02122298", pos="n", source=0, target=0),  # hyponym
            ],
            gloss="feline mammal usually having thick soft fur",
        )

        # Create run synset (verb)
        run_synset = Synset(
            offset="02092002",
            lex_filenum=30,
            lex_filename="verb.motion",
            ss_type="v",
            words=[Word(lemma="run", lex_id=0)],
            pointers=[
                Pointer(symbol="@", offset="01835496", pos="v", source=0, target=0),  # hypernym
                Pointer(symbol="*", offset="02092309", pos="v", source=0, target=0),  # entailment
                Pointer(symbol=">", offset="02093321", pos="v", source=0, target=0),  # cause
            ],
            frames=[
                VerbFrame(frame_number=1, word_indices=[0]),
                VerbFrame(frame_number=2, word_indices=[0]),
            ],
            gloss="move fast by using one's feet",
        )

        # Create walk synset (verb)
        walk_synset = Synset(
            offset="01904930",
            lex_filenum=30,
            lex_filename="verb.motion",
            ss_type="v",
            words=[Word(lemma="walk", lex_id=0), Word(lemma="take_a_walk", lex_id=1)],
            pointers=[
                Pointer(symbol="@", offset="01835496", pos="v", source=0, target=0),  # hypernym
                Pointer(symbol="!", offset="02092002", pos="v", source=1, target=1),  # antonym
            ],
            gloss="use one's feet to advance; advance by steps",
        )

        # Create good synset (adjective)
        good_synset = Synset(
            offset="01123148",
            lex_filenum=0,
            lex_filename="adj.all",
            ss_type="a",
            words=[Word(lemma="good", lex_id=0)],
            pointers=[
                Pointer(
                    symbol="!", offset="01125429", pos="a", source=1, target=1
                ),  # antonym to bad
                Pointer(symbol="&", offset="01124073", pos="a", source=0, target=0),  # similar to
            ],
            gloss="having desirable or positive qualities",
        )

        return [dog_synset, cat_synset, run_synset, walk_synset, good_synset]

    @pytest.fixture
    def sample_senses(self):
        """Create sample senses for testing."""
        return [
            Sense(
                sense_key="dog%1:05:00::",
                lemma="dog",
                ss_type="n",
                lex_filenum=5,
                lex_id=0,
                synset_offset="02084442",
                sense_number=1,
                tag_count=10,
            ),
            Sense(
                sense_key="cat%1:05:00::",
                lemma="cat",
                ss_type="n",
                lex_filenum=5,
                lex_id=0,
                synset_offset="02121620",
                sense_number=1,
                tag_count=8,
            ),
            Sense(
                sense_key="run%2:30:00::",
                lemma="run",
                ss_type="v",
                lex_filenum=30,
                lex_id=0,
                synset_offset="02092002",
                sense_number=1,
                tag_count=15,
            ),
            Sense(
                sense_key="run%2:30:01::",
                lemma="run",
                ss_type="v",
                lex_filenum=30,
                lex_id=0,
                synset_offset="02092003",
                sense_number=2,
                tag_count=5,
            ),
            Sense(
                sense_key="walk%2:30:00::",
                lemma="walk",
                ss_type="v",
                lex_filenum=30,
                lex_id=0,
                synset_offset="01904930",
                sense_number=1,
                tag_count=12,
            ),
        ]

    def test_init_empty(self):
        """Test initialization with empty search."""
        search = WordNetSearch()
        stats = search.get_statistics()
        assert stats["synset_count"] == 0
        assert stats["sense_count"] == 0
        assert search.get_all_lemmas() == []
        assert search.get_all_domains() == []

    def test_init_with_synsets(self, sample_synsets, sample_senses):
        """Test initialization with synsets and senses."""
        search = WordNetSearch(synsets=sample_synsets, senses=sample_senses)
        stats = search.get_statistics()
        assert stats["synset_count"] == 5
        assert stats["sense_count"] == 5
        assert (
            stats["unique_lemmas"] == 9
        )  # dog, domestic_dog, canis_familiaris, cat, true_cat, run, walk, take_a_walk, good
        assert stats["domain_count"] == 3  # noun.animal, verb.motion, adj.all

    def test_add_synset(self, sample_synsets):
        """Test adding synsets to search."""
        search = WordNetSearch()
        search.add_synset(sample_synsets[0])

        assert search.get_statistics()["synset_count"] == 1
        assert "dog" in search.get_all_lemmas()
        assert "domestic_dog" in search.get_all_lemmas()

    def test_add_duplicate_synset(self, sample_synsets):
        """Test adding duplicate synset raises error."""
        search = WordNetSearch()
        search.add_synset(sample_synsets[0])

        with pytest.raises(ValueError, match="already exists"):
            search.add_synset(sample_synsets[0])

    def test_add_sense(self, sample_senses):
        """Test adding senses to search."""
        search = WordNetSearch()
        search.add_sense(sample_senses[0])

        assert search.get_statistics()["sense_count"] == 1

    def test_add_duplicate_sense(self, sample_senses):
        """Test adding duplicate sense raises error."""
        search = WordNetSearch()
        search.add_sense(sample_senses[0])

        with pytest.raises(ValueError, match="already exists"):
            search.add_sense(sample_senses[0])

    def test_by_offset(self, sample_synsets):
        """Test finding synset by offset."""
        search = WordNetSearch(synsets=sample_synsets)

        # Find dog synset
        synset = search.by_offset("02084442")
        assert synset is not None
        assert "dog" in [w.lemma for w in synset.words]

        # Find with POS filter
        synset = search.by_offset("02084442", pos="n")
        assert synset is not None

        # Wrong POS
        synset = search.by_offset("02084442", pos="v")
        assert synset is None

        # Non-existent offset
        synset = search.by_offset("99999999")
        assert synset is None

    def test_by_lemma(self, sample_synsets):
        """Test finding synsets by lemma."""
        search = WordNetSearch(synsets=sample_synsets)

        # Find synsets for "dog"
        synsets = search.by_lemma("dog")
        assert len(synsets) == 1
        assert synsets[0].offset == "02084442"

        # Find synsets for "run"
        synsets = search.by_lemma("run")
        assert len(synsets) == 1
        assert synsets[0].ss_type == "v"

        # With POS filter
        synsets = search.by_lemma("run", pos="v")
        assert len(synsets) == 1

        synsets = search.by_lemma("run", pos="n")
        assert len(synsets) == 0

        # Multi-word lemma
        synsets = search.by_lemma("domestic_dog")
        assert len(synsets) == 1

        # Space conversion
        synsets = search.by_lemma("domestic dog")
        assert len(synsets) == 1

        # Non-existent lemma
        synsets = search.by_lemma("nonexistent")
        assert len(synsets) == 0

    def test_by_sense_key(self, sample_synsets, sample_senses):
        """Test finding synset by sense key."""
        search = WordNetSearch(synsets=sample_synsets, senses=sample_senses)

        # Find synset for dog sense
        synset = search.by_sense_key("dog%1:05:00::")
        assert synset is not None
        assert synset.offset == "02084442"

        # Non-existent sense key
        synset = search.by_sense_key("nonexistent%1:00:00::")
        assert synset is None

    def test_by_pattern(self, sample_synsets):
        """Test finding synsets by pattern."""
        search = WordNetSearch(synsets=sample_synsets)

        # Pattern matching "dog"
        synsets = search.by_pattern("dog")
        assert len(synsets) == 1

        # Pattern matching ending with "cat"
        synsets = search.by_pattern(".*cat$")
        assert len(synsets) == 1

        # Pattern matching "run" or "walk"
        synsets = search.by_pattern("run|walk")
        assert len(synsets) == 2

        # With POS filter
        synsets = search.by_pattern(".*", pos="v")
        assert len(synsets) == 2  # run and walk synsets

        # Case insensitive
        synsets = search.by_pattern("DOG", case_sensitive=False)
        assert len(synsets) == 1

        # Case sensitive
        synsets = search.by_pattern("DOG", case_sensitive=True)
        assert len(synsets) == 0

    def test_by_domain(self, sample_synsets):
        """Test finding synsets by domain."""
        search = WordNetSearch(synsets=sample_synsets)

        # Find animal nouns
        synsets = search.by_domain("noun.animal")
        assert len(synsets) == 2
        offsets = [s.offset for s in synsets]
        assert "02084442" in offsets  # dog
        assert "02121620" in offsets  # cat

        # Find motion verbs
        synsets = search.by_domain("verb.motion")
        assert len(synsets) == 2

        # Non-existent domain
        synsets = search.by_domain("noun.nonexistent")
        assert len(synsets) == 0

    def test_by_gloss_pattern(self, sample_synsets):
        """Test finding synsets by gloss pattern."""
        search = WordNetSearch(synsets=sample_synsets)

        # Search for "domesticated"
        synsets = search.by_gloss_pattern("domesticated")
        assert len(synsets) == 1
        assert synsets[0].offset == "02084442"  # dog

        # Search for "feet"
        synsets = search.by_gloss_pattern("feet")
        assert len(synsets) == 2  # run and walk

        # With POS filter
        synsets = search.by_gloss_pattern("feet", pos="v")
        assert len(synsets) == 2

        synsets = search.by_gloss_pattern("feet", pos="n")
        assert len(synsets) == 0

        # Case insensitive
        synsets = search.by_gloss_pattern("FEET", case_sensitive=False)
        assert len(synsets) == 2

    def test_get_lemma_senses(self, sample_senses):
        """Test getting senses for a lemma."""
        search = WordNetSearch(senses=sample_senses)

        # Get senses for "run"
        senses = search.get_lemma_senses("run")
        assert len(senses) == 2
        assert senses[0].sense_number == 1
        assert senses[1].sense_number == 2

        # With POS filter
        senses = search.get_lemma_senses("run", pos="v")
        assert len(senses) == 2

        senses = search.get_lemma_senses("run", pos="n")
        assert len(senses) == 0

        # Non-existent lemma
        senses = search.get_lemma_senses("nonexistent")
        assert len(senses) == 0

    def test_get_all_lemmas(self, sample_synsets):
        """Test getting all lemmas."""
        search = WordNetSearch(synsets=sample_synsets)

        lemmas = search.get_all_lemmas()
        assert len(lemmas) == 9
        assert "cat" in lemmas
        assert "dog" in lemmas
        assert "domestic_dog" in lemmas
        assert "good" in lemmas
        assert "run" in lemmas
        assert "take_a_walk" in lemmas
        assert "true_cat" in lemmas
        assert "walk" in lemmas

        # Check sorted
        assert lemmas == sorted(lemmas)

        # With POS filter
        noun_lemmas = search.get_all_lemmas(pos="n")
        assert len(noun_lemmas) == 5
        assert "dog" in noun_lemmas
        assert "run" not in noun_lemmas

    def test_get_all_domains(self, sample_synsets):
        """Test getting all domains."""
        search = WordNetSearch(synsets=sample_synsets)

        domains = search.get_all_domains()
        assert len(domains) == 3
        assert "adj.all" in domains
        assert "noun.animal" in domains
        assert "verb.motion" in domains

        # Check sorted
        assert domains == sorted(domains)

    def test_get_statistics(self, sample_synsets, sample_senses):
        """Test getting search statistics."""
        search = WordNetSearch(synsets=sample_synsets, senses=sample_senses)

        stats = search.get_statistics()
        assert stats["synset_count"] == 5
        assert stats["sense_count"] == 5
        assert stats["unique_lemmas"] == 9
        assert stats["total_words"] == 9  # Total Word objects across all synsets
        assert stats["domain_count"] == 3
        assert stats["n_synsets"] == 2
        assert stats["v_synsets"] == 2
        assert stats["a_synsets"] == 1

    # Syntax-related tests moved from test_syntax/test_wordnet_integration.py
    def test_frame_number_mapping_np_v(self):
        """Test mapping for NP V pattern (frame 1)."""
        search = WordNetSearch()
        parser = SyntaxParser()
        pattern = parser.parse("NP V")
        frame_numbers = search._get_frame_numbers_for_pattern(pattern)

        # Frame 1 and 35 both map to "NP V"
        assert 1 in frame_numbers or 35 in frame_numbers
        assert len(frame_numbers) >= 1

    def test_frame_number_mapping_np_v_np(self):
        """Test mapping for NP V NP pattern (frame 8, 13)."""
        search = WordNetSearch()
        parser = SyntaxParser()
        pattern = parser.parse("NP V NP")
        frame_numbers = search._get_frame_numbers_for_pattern(pattern)

        # Frames 8 and 13 both map to "NP V NP"
        expected_frames = {8, 13}
        assert expected_frames.issubset(frame_numbers)

    def test_frame_number_mapping_np_v_pp(self):
        """Test mapping for NP V PP pattern (frame 2, 30)."""
        search = WordNetSearch()
        parser = SyntaxParser()
        pattern = parser.parse("NP V PP")
        frame_numbers = search._get_frame_numbers_for_pattern(pattern)

        # Frames 2 and 30 both map to "NP V PP"
        expected_frames = {2, 30}
        assert expected_frames.issubset(frame_numbers)

    def test_frame_number_mapping_np_v_np_pp(self):
        """Test mapping for NP V NP PP pattern (frame 9, 31)."""
        search = WordNetSearch()
        parser = SyntaxParser()
        pattern = parser.parse("NP V NP PP")
        frame_numbers = search._get_frame_numbers_for_pattern(pattern)

        # Frames 9 and 31 both map to "NP V NP PP"
        expected_frames = {9, 31}
        assert expected_frames.issubset(frame_numbers)

    def test_frame_number_mapping_ditransitive(self):
        """Test mapping for ditransitive patterns."""
        search = WordNetSearch()
        parser = SyntaxParser()
        # Test frame 10: NP V NP NP (double object)
        pattern = parser.parse("NP V NP NP")
        frame_numbers = search._get_frame_numbers_for_pattern(pattern)
        assert 10 in frame_numbers

        # Test frame 11: NP V NP PP (to-dative)
        pattern = parser.parse("NP V NP PP")
        frame_numbers = search._get_frame_numbers_for_pattern(pattern)
        assert 11 in frame_numbers

    def test_pattern_to_string_conversion(self):
        """Test pattern to string conversion."""
        search = WordNetSearch()
        parser = SyntaxParser()
        pattern = parser.parse("NP V PP.instrument")
        pattern_str = search._pattern_to_string(pattern)

        # Should convert back to a readable string format
        assert "NP" in pattern_str
        assert "VERB" in pattern_str or "V" in pattern_str
        assert "PP" in pattern_str

    def test_patterns_match_exact(self):
        """Test exact pattern matching."""
        search = WordNetSearch()
        parser = SyntaxParser()
        search_pattern = parser.parse("NP V NP")

        # Should match exactly with frame pattern "NP V NP"
        matches = search._patterns_match("NP VERB NP", "NP V NP", search_pattern)
        assert matches is True

    def test_patterns_match_hierarchical(self):
        """Test hierarchical pattern matching."""
        search = WordNetSearch()
        parser = SyntaxParser()
        # General PP should match specific PP patterns
        general_pattern = parser.parse("NP V PP")

        # Test against a more specific frame pattern
        matches = search._patterns_match("NP VERB PP", "NP V PP", general_pattern)
        assert matches is True

    def test_by_syntax_method_exists(self):
        """Test that by_syntax method exists and is callable."""
        search = WordNetSearch()
        assert hasattr(search, "by_syntax")
        assert callable(search.by_syntax)

    def test_by_syntax_empty_search(self):
        """Test syntax search on empty search index."""
        search = WordNetSearch()
        results = search.by_syntax("NP V NP")

        # Should return empty list for empty index
        assert isinstance(results, list)
        assert len(results) == 0

    def test_by_syntax_with_mock_data(self):
        """Test syntax search with mock synset data."""
        search = WordNetSearch()
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
        search.add_synset(mock_synset)

        # Search for pattern that matches frame 8 (NP V NP)
        results = search.by_syntax("NP V NP")

        # Should find the mock synset
        assert len(results) == 1
        assert results[0] == mock_synset

    def test_by_syntax_non_verb_synsets_ignored(self):
        """Test that non-verb synsets are ignored in syntax search."""
        search = WordNetSearch()
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
        search.add_synset(mock_noun_synset)

        # Search for any pattern
        results = search.by_syntax("NP V NP")

        # Should return empty since only noun synsets exist
        assert len(results) == 0

    def test_by_syntax_multiple_frames_per_word(self):
        """Test synset with word having multiple frames."""
        search = WordNetSearch()
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

        search.add_synset(mock_synset)

        # Should match both frame 8 and frame 9 patterns
        results_8 = search.by_syntax("NP V NP")  # matches frame 8
        results_9 = search.by_syntax("NP V NP PP")  # matches frame 9

        assert len(results_8) == 1
        assert len(results_9) == 1
        assert results_8[0] == mock_synset
        assert results_9[0] == mock_synset

    def test_by_syntax_no_matching_frames(self):
        """Test search with no matching verb frames."""
        search = WordNetSearch()
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

        search.add_synset(mock_synset)

        # Search for pattern that doesn't match frame 1
        results = search.by_syntax("NP V NP NP")  # ditransitive, no match

        assert len(results) == 0

    def test_by_syntax_word_without_frames(self):
        """Test synset with verb word that has no frames."""
        search = WordNetSearch()
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

        search.add_synset(mock_synset)

        # Should not match any pattern since no frames exist
        results = search.by_syntax("NP V NP")
        assert len(results) == 0

    def test_by_syntax_invalid_pattern(self):
        """Test syntax search with invalid pattern."""
        search = WordNetSearch()
        # Test with various invalid patterns
        invalid_patterns = ["", "   ", "INVALID"]

        for pattern in invalid_patterns:
            try:
                results = search.by_syntax(pattern)
                # If it doesn't raise an error, should return empty list
                assert isinstance(results, list)
            except (ValueError, AttributeError):
                # Expected for invalid patterns
                pass

    def test_by_syntax_results_sorted(self):
        """Test that results are sorted by synset offset."""
        search = WordNetSearch()
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
            search.add_synset(mock_synset)

        results = search.by_syntax("NP V NP")

        # Should be sorted by offset
        assert len(results) == 3
        assert results[0].offset == "11111111"
        assert results[1].offset == "55555555"
        assert results[2].offset == "99999999"
