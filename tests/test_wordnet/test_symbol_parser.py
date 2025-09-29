"""Tests for WordNet symbol parser.

This module tests the parsing utilities for WordNet synset IDs,
lemma keys, and sense keys.
"""

from __future__ import annotations

import pytest

from glazing.wordnet.models import Synset, Word
from glazing.wordnet.symbol_parser import (
    extract_lemma_from_key,
    extract_pos_from_sense,
    extract_sense_number,
    extract_synset_offset,
    filter_synsets_by_pos,
    is_valid_lemma_key,
    is_valid_sense_key,
    is_valid_synset_id,
    normalize_synset_for_matching,
    parse_lemma_key,
    parse_sense_key,
    parse_synset_id,
)


class TestParseSynsetID:
    """Test parsing of WordNet synset IDs."""

    def test_noun_synset(self) -> None:
        """Test parsing noun synset IDs."""
        result = parse_synset_id("00001740-n")
        assert result.raw_string == "00001740-n"
        assert result.offset == "00001740"
        assert result.pos == "n"
        assert result.numeric_offset == 1740

    def test_verb_synset(self) -> None:
        """Test parsing verb synset IDs."""
        result = parse_synset_id("00002098-v")
        assert result.raw_string == "00002098-v"
        assert result.offset == "00002098"
        assert result.pos == "v"
        assert result.numeric_offset == 2098

    def test_adjective_synset(self) -> None:
        """Test parsing adjective synset IDs."""
        result = parse_synset_id("00003131-a")
        assert result.raw_string == "00003131-a"
        assert result.offset == "00003131"
        assert result.pos == "a"
        assert result.numeric_offset == 3131

        # Satellite adjective
        result = parse_synset_id("00003131-s")
        assert result.pos == "s"

    def test_adverb_synset(self) -> None:
        """Test parsing adverb synset IDs."""
        result = parse_synset_id("00004567-r")
        assert result.raw_string == "00004567-r"
        assert result.offset == "00004567"
        assert result.pos == "r"
        assert result.numeric_offset == 4567

    def test_all_pos_types(self) -> None:
        """Test parsing all POS types."""
        pos_types = {
            "n": "noun",
            "v": "verb",
            "a": "adjective",
            "s": "satellite adjective",
            "r": "adverb",
        }

        for pos_code, _ in pos_types.items():
            synset_id = f"00001234-{pos_code}"
            result = parse_synset_id(synset_id)
            assert result.pos == pos_code
            assert result.offset == "00001234"

    def test_different_offsets(self) -> None:
        """Test parsing various offset values."""
        offsets = ["00000001", "00001234", "12345678", "99999999"]

        for offset in offsets:
            synset_id = f"{offset}-n"
            result = parse_synset_id(synset_id)
            assert result.offset == offset
            assert result.numeric_offset == int(offset)


class TestParseSenseKey:
    """Test parsing of WordNet sense keys."""

    def test_noun_sense_key(self) -> None:
        """Test parsing noun sense keys."""
        # Real sense key from converted data: 'hood%1:15:00::'
        result = parse_sense_key("'hood%1:15:00::")
        assert result.raw_string == "'hood%1:15:00::"
        assert result.lemma == "'hood"
        assert result.ss_type == 1
        assert result.lex_filenum == 15
        assert result.lex_id == 0
        assert result.head == ""
        assert result.pos == "n"

    def test_verb_sense_key(self) -> None:
        """Test parsing verb sense keys."""
        # Real sense key from converted data: break%2:30:00::
        result = parse_sense_key("break%2:30:00::")
        assert result.lemma == "break"
        assert result.ss_type == 2
        assert result.lex_filenum == 30
        assert result.pos == "v"

    def test_adjective_sense_key(self) -> None:
        """Test parsing adjective sense keys."""
        # Real sense key from converted data: able%3:00:00::
        result = parse_sense_key("able%3:00:00::")
        assert result.lemma == "able"
        assert result.ss_type == 3
        assert result.pos == "a"

    def test_adverb_sense_key(self) -> None:
        """Test parsing adverb sense keys."""
        # Real sense key from converted data: aboard%4:02:00::
        result = parse_sense_key("aboard%4:02:00::")
        assert result.lemma == "aboard"
        assert result.ss_type == 4
        assert result.pos == "r"

    def test_satellite_sense_key(self) -> None:
        """Test parsing satellite adjective sense keys."""
        # Real sense key from converted data: ablaze%5:00:00:lighted:01
        result = parse_sense_key("ablaze%5:00:00:lighted:01")
        assert result.lemma == "ablaze"
        assert result.ss_type == 5
        assert result.head == "lighted:01"
        assert result.pos == "s"

    def test_sense_key_with_head(self) -> None:
        """Test parsing sense keys with head word."""
        # Real satellite adjective with head from converted data
        result = parse_sense_key("abloom%5:00:00:mature:01")
        assert result.lemma == "abloom"
        assert result.head == "mature:01"


class TestParseLemmaKey:
    """Test parsing of WordNet lemma keys."""

    def test_noun_lemma_key(self) -> None:
        """Test parsing noun lemma keys."""
        result = parse_lemma_key("entity#n#1")
        assert result.raw_string == "entity#n#1"
        assert result.lemma == "entity"
        assert result.pos == "n"
        assert result.sense_number == 1

    def test_verb_lemma_key(self) -> None:
        """Test parsing verb lemma keys."""
        result = parse_lemma_key("be#v#1")
        assert result.lemma == "be"
        assert result.pos == "v"
        assert result.sense_number == 1

    def test_adjective_lemma_key(self) -> None:
        """Test parsing adjective lemma keys."""
        result = parse_lemma_key("able#a#1")
        assert result.lemma == "able"
        assert result.pos == "a"
        assert result.sense_number == 1

    def test_adverb_lemma_key(self) -> None:
        """Test parsing adverb lemma keys."""
        result = parse_lemma_key("aboard#r#1")
        assert result.lemma == "aboard"
        assert result.pos == "r"
        assert result.sense_number == 1

    def test_complex_lemma(self) -> None:
        """Test parsing lemma keys with complex lemmas."""
        # Multi-word lemma
        result = parse_lemma_key("living_thing#n#1")
        assert result.lemma == "living_thing"

        # Lemma with apostrophe
        result = parse_lemma_key("'hood#n#1")
        assert result.lemma == "'hood"

    def test_different_sense_numbers(self) -> None:
        """Test parsing various sense numbers."""
        for sense_num in [1, 2, 10, 99]:
            result = parse_lemma_key(f"test#n#{sense_num}")
            assert result.sense_number == sense_num


class TestBooleanCheckers:
    """Test boolean validation functions."""

    def test_is_valid_synset_id(self) -> None:
        """Test checking valid synset IDs."""
        assert is_valid_synset_id("00001740-n") is True
        assert is_valid_synset_id("00001740n") is True
        assert is_valid_synset_id("12345678-v") is True
        assert is_valid_synset_id("invalid") is False
        assert is_valid_synset_id("00001740-x") is False

    def test_is_valid_sense_key(self) -> None:
        """Test checking valid sense keys."""
        assert is_valid_sense_key("'hood%1:15:00::") is True
        assert is_valid_sense_key("break%2:30:00::") is True
        assert is_valid_sense_key("ablaze%5:00:00:lighted:01") is True
        assert is_valid_sense_key("invalid") is False
        assert is_valid_sense_key("test%9:00:00::") is False  # Invalid ss_type

    def test_is_valid_lemma_key(self) -> None:
        """Test checking valid lemma keys."""
        assert is_valid_lemma_key("entity#n#1") is True
        assert is_valid_lemma_key("living_thing#n#1") is True
        assert is_valid_lemma_key("invalid") is False
        assert is_valid_lemma_key("test#x#1") is False  # Invalid POS


class TestExtractFunctions:
    """Test extraction helper functions."""

    def test_extract_synset_offset(self) -> None:
        """Test extracting offset from synset ID."""
        assert extract_synset_offset("00001740-n") == "00001740"
        assert extract_synset_offset("12345678-v") == "12345678"

    def test_extract_pos_from_sense(self) -> None:
        """Test extracting POS from sense key."""
        assert extract_pos_from_sense("'hood%1:15:00::") == "n"
        assert extract_pos_from_sense("break%2:30:00::") == "v"
        assert extract_pos_from_sense("able%3:00:00::") == "a"
        assert extract_pos_from_sense("aboard%4:02:00::") == "r"
        assert extract_pos_from_sense("ablaze%5:00:00:lighted:01") == "s"

    def test_extract_lemma_from_key(self) -> None:
        """Test extracting lemma from various key types."""
        assert extract_lemma_from_key("entity#n#1") == "entity"
        assert extract_lemma_from_key("'hood%1:15:00::") == "'hood"
        assert extract_lemma_from_key("living_thing#n#1") == "living_thing"

    def test_extract_sense_number(self) -> None:
        """Test extracting sense number (lex_id) from sense key."""
        # lex_id is the 4th field in sense key format
        assert extract_sense_number("'hood%1:15:00::") == 0
        assert extract_sense_number("break%2:30:01::") == 1
        assert extract_sense_number("test%1:05:02::") == 2
        assert extract_sense_number("example%3:00:99::") == 99

        # Invalid sense key raises ValueError
        with pytest.raises(ValueError, match="Cannot extract sense number"):
            extract_sense_number("invalid")
        with pytest.raises(ValueError, match="Cannot extract sense number"):
            extract_sense_number("test#n#1")  # This is a lemma key, not a sense key


class TestNormalizeSynsetForMatching:
    """Test synset normalization for fuzzy matching."""

    def test_normalize_synset_id(self) -> None:
        """Test normalizing synset IDs."""
        assert normalize_synset_for_matching("00001740-n") == "00001740-n"
        assert normalize_synset_for_matching("00001740n") == "00001740-n"

    def test_normalize_offset_only(self) -> None:
        """Test normalizing offset without POS."""
        # Should raise ValueError for invalid synset ID (missing POS)
        with pytest.raises(ValueError, match="Cannot normalize invalid synset ID"):
            normalize_synset_for_matching("00001740")


class TestFilterSynsetsByPOS:
    """Test filtering synsets by part of speech."""

    def create_test_synsets(self) -> list[Synset]:
        """Create test synsets from real WordNet data."""
        # Using actual Synset model structure
        return [
            Synset(
                offset="00001740",
                lex_filenum=3,
                lex_filename="noun.Tops",
                ss_type="n",  # noun
                words=[Word(lemma="entity", lex_id=0)],
                pointers=[],
                frames=[],
                gloss="that which is perceived or known or inferred",
            ),
            Synset(
                offset="00001930",
                lex_filenum=3,
                lex_filename="noun.Tops",
                ss_type="n",  # noun
                words=[Word(lemma="physical_entity", lex_id=0)],
                pointers=[],
                frames=[],
                gloss="an entity that has physical existence",
            ),
            Synset(
                offset="00002098",
                lex_filenum=42,
                lex_filename="verb.stative",
                ss_type="v",  # verb
                words=[Word(lemma="be", lex_id=0)],
                pointers=[],
                frames=[],
                gloss="have the quality of being",
            ),
            Synset(
                offset="00001740",
                lex_filenum=0,
                lex_filename="adj.all",
                ss_type="a",  # adjective
                words=[Word(lemma="able", lex_id=0)],
                pointers=[],
                frames=[],
                gloss="able to do something",
            ),
            Synset(
                offset="00001740",
                lex_filenum=2,
                lex_filename="adv.all",
                ss_type="r",  # adverb
                words=[Word(lemma="aboard", lex_id=0)],
                pointers=[],
                frames=[],
                gloss="on a ship, train, plane or vehicle",
            ),
        ]

    def test_filter_by_pos(self) -> None:
        """Test filtering synsets by POS."""
        synsets = self.create_test_synsets()

        # Filter for nouns (ss_type="n")
        nouns = filter_synsets_by_pos(synsets, "n")
        assert len(nouns) == 2
        assert all(s.ss_type == "n" for s in nouns)

        # Filter for verbs (ss_type="v")
        verbs = filter_synsets_by_pos(synsets, "v")
        assert len(verbs) == 1
        assert all(s.ss_type == "v" for s in verbs)

        # Filter for adjectives (ss_type="a")
        adjs = filter_synsets_by_pos(synsets, "a")
        assert len(adjs) == 1
        assert all(s.ss_type == "a" for s in adjs)

        # Filter for adverbs (ss_type="r")
        advs = filter_synsets_by_pos(synsets, "r")
        assert len(advs) == 1
        assert all(s.ss_type == "r" for s in advs)

    def test_filter_empty_list(self) -> None:
        """Test filtering empty synset list."""
        result = filter_synsets_by_pos([], "n")
        assert result == []

    def test_filter_no_matches(self) -> None:
        """Test filtering with no matching synsets."""
        synsets = self.create_test_synsets()
        # Satellite adjectives not in our test data
        result = filter_synsets_by_pos(synsets, "s")
        assert len(result) == 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_synset_id(self) -> None:
        """Test parsing invalid synset IDs."""
        with pytest.raises(ValueError, match="Invalid synset ID format"):
            parse_synset_id("invalid")

        with pytest.raises(ValueError, match="Invalid synset ID format"):
            parse_synset_id("00001740-x")  # Invalid POS

        with pytest.raises(ValueError, match="Invalid synset ID format"):
            parse_synset_id("1234-n")  # Not 8 digits

    def test_invalid_sense_key(self) -> None:
        """Test parsing invalid sense keys."""
        with pytest.raises(ValueError, match="Invalid sense key format"):
            parse_sense_key("invalid")

        with pytest.raises(ValueError, match="Invalid ss_type"):
            parse_sense_key("test%9:00:00::")  # Invalid ss_type

        with pytest.raises(ValueError, match="Invalid sense key format"):
            parse_sense_key("test%1:xx:00::")  # Non-numeric lex_filenum

    def test_invalid_lemma_key(self) -> None:
        """Test parsing invalid lemma keys."""
        with pytest.raises(ValueError, match="Invalid lemma key format"):
            parse_lemma_key("invalid")

        with pytest.raises(ValueError, match="Invalid lemma key format"):
            parse_lemma_key("test#x#1")  # Invalid POS

        with pytest.raises(ValueError, match="Invalid lemma key format"):
            parse_lemma_key("test#n#abc")  # Non-numeric sense number

    def test_special_characters_in_lemma(self) -> None:
        """Test handling special characters in lemmas."""
        # Apostrophes are valid
        result = parse_lemma_key("'hood#n#1")
        assert result.lemma == "'hood"

        # Underscores for multi-word
        result = parse_lemma_key("living_thing#n#1")
        assert result.lemma == "living_thing"

        # Hyphens
        result = parse_lemma_key("mother-in-law#n#1")
        assert result.lemma == "mother-in-law"

    def test_synset_without_hyphen(self) -> None:
        """Test parsing synset ID without hyphen."""
        result = parse_synset_id("00001740n")
        assert result.offset == "00001740"
        assert result.pos == "n"
        assert result.normalized == "00001740-n"
