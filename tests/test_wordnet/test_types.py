"""Tests for WordNet type definitions.

This module tests the WordNet-specific type definitions, validators, and patterns
to ensure they work correctly with WordNet 3.1 data structures.
"""

import re

import pytest
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from glazing.wordnet.types import (
    # Patterns
    PERCENTAGE_NOTATION_PATTERN,
    WORDNET_OFFSET_PATTERN,
    WORDNET_SENSE_KEY_PATTERN,
    # Type literals
    AdjPosition,
    LexFileName,
    # Annotated types
    LexID,
    PointerSymbol,
    SenseKey,
    SenseNumber,
    SynsetOffset,
    TagCount,
    VerbFrameNumber,
    WordNetPOS,
)


class TestWordNetLiterals:
    """Test WordNet literal type definitions."""

    def test_wordnet_pos_values(self):
        """Test WordNetPOS values in Pydantic model."""

        class TestModel(BaseModel):
            pos: WordNetPOS

        # Test all valid POS tags
        for pos in ["n", "v", "a", "r", "s"]:
            model = TestModel(pos=pos)
            assert model.pos == pos

        # Test invalid POS
        with pytest.raises(PydanticValidationError):
            TestModel(pos="x")

    def test_pointer_symbol_values(self):
        """Test PointerSymbol values in Pydantic model."""

        class TestModel(BaseModel):
            symbol: PointerSymbol

        # Test all valid pointer symbols
        valid_symbols = [
            "!",
            "@",
            "@i",
            "~",
            "~i",
            "#m",
            "#s",
            "#p",
            "%m",
            "%s",
            "%p",
            "=",
            "+",
            ";c",
            "-c",
            ";r",
            "-r",
            ";u",
            "-u",
            "*",
            ">",
            "^",
            "$",
            "&",
            "<",
            "\\",
        ]

        for symbol in valid_symbols:
            model = TestModel(symbol=symbol)
            assert model.symbol == symbol

        # Test invalid symbol
        with pytest.raises(PydanticValidationError):
            TestModel(symbol="X")

    def test_lex_filename_values(self):
        """Test LexFileName values in Pydantic model."""

        class TestModel(BaseModel):
            filename: LexFileName

        # Test sample valid filenames
        valid_files = [
            "noun.Tops",
            "noun.person",
            "noun.animal",
            "verb.motion",
            "verb.cognition",
            "adj.all",
            "adj.pert",
            "adv.all",
        ]

        for filename in valid_files:
            model = TestModel(filename=filename)
            assert model.filename == filename

        # Test invalid filename
        with pytest.raises(PydanticValidationError):
            TestModel(filename="noun.invalid")

    def test_verb_frame_number_values(self):
        """Test VerbFrameNumber values in Pydantic model."""

        class TestModel(BaseModel):
            frame_num: VerbFrameNumber

        # Test valid frame numbers (1-35)
        for num in [1, 15, 35]:
            model = TestModel(frame_num=num)
            assert model.frame_num == num

        # Test invalid frame numbers
        with pytest.raises(PydanticValidationError):
            TestModel(frame_num=0)
        with pytest.raises(PydanticValidationError):
            TestModel(frame_num=36)

    def test_adj_position_values(self):
        """Test AdjPosition values in Pydantic model."""

        class TestModel(BaseModel):
            position: AdjPosition

        # Test all valid positions
        for pos in ["a", "p", "ip"]:
            model = TestModel(position=pos)
            assert model.position == pos

        # Test invalid position
        with pytest.raises(PydanticValidationError):
            TestModel(position="x")


class TestWordNetAnnotatedTypes:
    """Test WordNet annotated types with constraints."""

    def test_synset_offset_validation(self):
        """Test SynsetOffset validation."""

        class TestModel(BaseModel):
            offset: SynsetOffset

        # Valid offsets (8 digits)
        assert TestModel(offset="00001740").offset == "00001740"
        assert TestModel(offset="12345678").offset == "12345678"
        assert TestModel(offset="00000000").offset == "00000000"

        # Invalid offsets
        with pytest.raises(PydanticValidationError):
            TestModel(offset="1740")  # Too short
        with pytest.raises(PydanticValidationError):
            TestModel(offset="000017400")  # Too long
        with pytest.raises(PydanticValidationError):
            TestModel(offset="0000174X")  # Non-numeric

    def test_sense_key_validation(self):
        """Test SenseKey validation."""

        class TestModel(BaseModel):
            sense_key: SenseKey

        # Valid sense keys
        valid_keys = [
            "abandon%2:40:01::",
            "dog%1:05:00::",
            "run%2:38:00::",
            "good%3:00:01::",
            "quickly%4:02:00::",
            "better%5:00:00:good:01",
        ]

        for key in valid_keys:
            model = TestModel(sense_key=key)
            assert model.sense_key == key

        # Invalid sense keys
        with pytest.raises(PydanticValidationError):
            TestModel(sense_key="abandon")  # No format
        with pytest.raises(PydanticValidationError):
            TestModel(sense_key="abandon%2")  # Incomplete
        with pytest.raises(PydanticValidationError):
            TestModel(sense_key="abandon%6:40:01::")  # Invalid POS (6)

    def test_lex_id_validation(self):
        """Test LexID validation."""

        class TestModel(BaseModel):
            lex_id: LexID

        # Valid lex IDs (0-15)
        for i in [0, 1, 15]:
            model = TestModel(lex_id=i)
            assert model.lex_id == i

        # Invalid lex IDs
        with pytest.raises(PydanticValidationError):
            TestModel(lex_id=-1)
        with pytest.raises(PydanticValidationError):
            TestModel(lex_id=16)

    def test_sense_number_validation(self):
        """Test SenseNumber validation."""

        class TestModel(BaseModel):
            sense_number: SenseNumber

        # Valid sense numbers (>=1)
        for i in [1, 2, 100]:
            model = TestModel(sense_number=i)
            assert model.sense_number == i

        # Invalid sense numbers
        with pytest.raises(PydanticValidationError):
            TestModel(sense_number=0)
        with pytest.raises(PydanticValidationError):
            TestModel(sense_number=-1)

    def test_tag_count_validation(self):
        """Test TagCount validation."""

        class TestModel(BaseModel):
            tag_count: TagCount

        # Valid tag counts (>=0)
        for i in [0, 1, 1000]:
            model = TestModel(tag_count=i)
            assert model.tag_count == i

        # Invalid tag counts
        with pytest.raises(PydanticValidationError):
            TestModel(tag_count=-1)


class TestWordNetRegexPatterns:
    """Test WordNet regex patterns."""

    def test_wordnet_offset_pattern(self):
        """Test WordNet synset offset pattern."""
        pattern = re.compile(WORDNET_OFFSET_PATTERN)

        # Valid offsets
        assert pattern.match("00001740")
        assert pattern.match("12345678")
        assert pattern.match("00000000")

        # Invalid offsets
        assert not pattern.match("1740")  # Too short
        assert not pattern.match("000017400")  # Too long
        assert not pattern.match("0000174X")  # Non-numeric

    def test_wordnet_sense_key_pattern(self):
        """Test WordNet sense key pattern."""
        pattern = re.compile(WORDNET_SENSE_KEY_PATTERN)

        # Valid sense keys
        assert pattern.match("abandon%2:40:01::")
        assert pattern.match("dog%1:05:00::")
        assert pattern.match("run%2:38:00::")
        assert pattern.match("good%3:00:01::")
        assert pattern.match("quickly%4:02:00::")
        assert pattern.match("better%5:00:00:good:01")

        # Invalid sense keys
        assert not pattern.match("abandon")
        assert not pattern.match("abandon%2")
        assert not pattern.match("abandon%6:40:01::")  # Invalid POS (6)

    def test_percentage_notation_pattern(self):
        """Test VerbNet's WordNet percentage notation pattern."""
        pattern = re.compile(PERCENTAGE_NOTATION_PATTERN)

        # Valid notations
        assert pattern.match("give%2:40:00")
        assert pattern.match("abandon%2:40:01")
        assert pattern.match("dog%1:05:00")

        # Invalid notations
        assert not pattern.match("give%2:40")  # Missing lex_id
        assert not pattern.match("give%2:40:00::")  # Extra colons
        assert not pattern.match("Give%2:40:00")  # Capital letter


class TestWordNetTypeIntegration:
    """Test WordNet type integration with Pydantic models."""

    def test_types_with_pydantic_model(self):
        """Test that WordNet types work correctly in Pydantic models."""

        class TestSynset(BaseModel):
            offset: SynsetOffset
            pos: WordNetPOS
            lex_filenum: int
            filename: LexFileName

        class TestSense(BaseModel):
            sense_key: SenseKey
            synset_offset: SynsetOffset
            sense_number: SenseNumber
            tag_count: TagCount

        class TestPointer(BaseModel):
            symbol: PointerSymbol
            offset: SynsetOffset
            pos: WordNetPOS

        # Valid synset
        synset = TestSynset(offset="00001740", pos="n", lex_filenum=5, filename="noun.animal")
        assert synset.offset == "00001740"
        assert synset.pos == "n"

        # Valid sense
        sense = TestSense(
            sense_key="dog%1:05:00::", synset_offset="00001740", sense_number=1, tag_count=15
        )
        assert sense.sense_key == "dog%1:05:00::"
        assert sense.synset_offset == "00001740"

        # Valid pointer
        pointer = TestPointer(symbol="@", offset="00002084", pos="n")
        assert pointer.symbol == "@"
        assert pointer.offset == "00002084"

        # Invalid synset offset
        with pytest.raises(PydanticValidationError):
            TestSynset(
                offset="1740",  # Too short
                pos="n",
                lex_filenum=5,
                filename="noun.animal",
            )

        # Invalid sense key
        with pytest.raises(PydanticValidationError):
            TestSense(
                sense_key="dog%6:05:00::",  # Invalid POS
                synset_offset="00001740",
                sense_number=1,
                tag_count=15,
            )
