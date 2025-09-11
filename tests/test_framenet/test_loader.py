"""Tests for FrameNet JSON Lines loader.

Tests the FrameNet data loading functionality including frame loading,
indexing, and search capabilities.
"""

import json

import pytest

from glazing.framenet.loader import (
    FrameIndex,
    FrameNetLoader,
    build_frame_index,
    load_and_index_frames,
    load_frames,
    load_lexical_units,
)
from glazing.framenet.models import (
    AnnotatedText,
    Frame,
    FrameElement,
    Lexeme,
    LexicalUnit,
)


class TestFrameIndex:
    """Test FrameNet frame indexing functionality."""

    @pytest.fixture
    def sample_frames(self):
        """Create sample Frame models for testing."""
        frame1 = Frame(
            id=1,
            name="Giving",
            definition=AnnotatedText(
                raw_text="A Donor gives a Theme to a Recipient.",
                plain_text="A Donor gives a Theme to a Recipient.",
                annotations=[],
            ),
            frame_elements=[
                FrameElement(
                    id=1,
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
                    semtype_refs=[],
                ),
                FrameElement(
                    id=2,
                    name="Theme",
                    abbrev="Th",
                    definition=AnnotatedText(
                        raw_text="The thing being given.",
                        plain_text="The thing being given.",
                        annotations=[],
                    ),
                    core_type="Core",
                    bg_color="00FF00",
                    fg_color="000000",
                    semtype_refs=[],
                ),
            ],
            lexical_units=[
                LexicalUnit(
                    id=1,
                    name="give.v",
                    pos="V",
                    definition="To transfer possession",
                    frame_id=1,
                    frame_name="Giving",
                    sentence_count={"annotated": 10, "total": 15},
                    lexemes=[
                        Lexeme(name="give", pos="V", breakBefore=False, headword=True),
                    ],
                ),
                LexicalUnit(
                    id=2,
                    name="donate.v",
                    pos="V",
                    definition="To give as charity",
                    frame_id=1,
                    frame_name="Giving",
                    sentence_count={"annotated": 5, "total": 8},
                    lexemes=[
                        Lexeme(name="donate", pos="V", breakBefore=False, headword=True),
                    ],
                ),
            ],
            frame_relations=[],
            semtype_refs=[],
        )

        frame2 = Frame(
            id=2,
            name="Receiving",
            definition=AnnotatedText(
                raw_text="A Recipient receives a Theme from a Donor.",
                plain_text="A Recipient receives a Theme from a Donor.",
                annotations=[],
            ),
            frame_elements=[
                FrameElement(
                    id=3,
                    name="Recipient",
                    abbrev="Rec",
                    definition=AnnotatedText(
                        raw_text="The person who receives.",
                        plain_text="The person who receives.",
                        annotations=[],
                    ),
                    core_type="Core",
                    bg_color="0000FF",
                    fg_color="FFFFFF",
                    semtype_refs=[],
                ),
            ],
            lexical_units=[
                LexicalUnit(
                    id=3,
                    name="receive.v",
                    pos="V",
                    definition="To get something",
                    frame_id=2,
                    frame_name="Receiving",
                    sentence_count={"annotated": 8, "total": 12},
                    lexemes=[
                        Lexeme(name="receive", pos="V", breakBefore=False, headword=True),
                    ],
                ),
            ],
            frame_relations=[],
            semtype_refs=[],
        )

        return [frame1, frame2]

    @pytest.fixture
    def frame_index(self, sample_frames):
        """Create frame index with sample data."""
        return FrameIndex(sample_frames)

    def test_frame_index_initialization_empty(self):
        """Test empty frame index initialization."""
        index = FrameIndex()
        assert len(index._by_id) == 0
        assert len(index._by_name) == 0
        assert len(index._by_fe_name) == 0

    def test_frame_index_initialization_with_frames(self, sample_frames):
        """Test frame index initialization with frames."""
        index = FrameIndex(sample_frames)
        assert len(index._by_id) == 2
        assert len(index._by_name) == 2

    def test_get_frame_by_id(self, frame_index):
        """Test getting frame by ID."""
        frame = frame_index.get_frame_by_id(1)
        assert frame is not None
        assert frame.name == "Giving"

        # Non-existent ID
        frame = frame_index.get_frame_by_id(999)
        assert frame is None

    def test_get_frame_by_name(self, frame_index):
        """Test getting frame by name (case-insensitive)."""
        frame = frame_index.get_frame_by_name("Giving")
        assert frame is not None
        assert frame.id == 1

        # Case insensitive
        frame = frame_index.get_frame_by_name("giving")
        assert frame is not None
        assert frame.id == 1

        # Non-existent name
        frame = frame_index.get_frame_by_name("NonExistent")
        assert frame is None

    def test_find_frames_with_fe(self, frame_index):
        """Test finding frames by frame element."""
        frames = frame_index.find_frames_with_fe("Donor")
        assert len(frames) == 1
        assert frames[0].name == "Giving"

        # Case insensitive
        frames = frame_index.find_frames_with_fe("donor")
        assert len(frames) == 1

        # Non-existent FE
        frames = frame_index.find_frames_with_fe("NonExistent")
        assert len(frames) == 0

    def test_find_frames_with_lu(self, frame_index):
        """Test finding frames by lexical unit."""
        frames = frame_index.find_frames_with_lu("give")
        assert len(frames) == 1
        assert frames[0].name == "Giving"

        # Case insensitive
        frames = frame_index.find_frames_with_lu("GIVE")
        assert len(frames) == 1

        # Non-existent LU
        frames = frame_index.find_frames_with_lu("nonexistent")
        assert len(frames) == 0

    def test_search_definitions_single_word(self, frame_index):
        """Test searching definitions with single word."""
        frames = frame_index.search_definitions("gives")
        assert len(frames) == 1
        assert frames[0].name == "Giving"

        frames = frame_index.search_definitions("receives")
        assert len(frames) == 1
        assert frames[0].name == "Receiving"

        # Non-existent word
        frames = frame_index.search_definitions("nonexistent")
        assert len(frames) == 0

    def test_search_definitions_multi_word(self, frame_index):
        """Test searching definitions with multiple words."""
        # Both frames mention "Theme" and "Donor"
        frames = frame_index.search_definitions("Theme Donor")
        assert len(frames) == 2
        frame_names = {frame.name for frame in frames}
        assert frame_names == {"Giving", "Receiving"}

    def test_search_definitions_empty_query(self, frame_index):
        """Test searching with empty query returns no results."""
        frames = frame_index.search_definitions("")
        assert len(frames) == 0

    def test_get_all_frame_names(self, frame_index):
        """Test getting all frame names sorted."""
        names = frame_index.get_all_frame_names()
        assert names == ["Giving", "Receiving"]

    def test_get_statistics(self, frame_index):
        """Test getting index statistics."""
        stats = frame_index.get_statistics()

        assert stats["total_frames"] == 2
        assert stats["total_frame_elements"] == 3
        assert stats["total_lexical_units"] == 3
        assert stats["unique_fe_names"] == 3  # Donor, Theme, Recipient
        assert stats["unique_lu_lemmas"] == 3  # give, donate, receive
        assert stats["indexed_definition_words"] > 0

    def test_add_frame(self, frame_index, sample_frames):
        """Test adding individual frame to existing index."""
        initial_count = len(frame_index._by_id)

        # Create new frame
        new_frame = Frame(
            id=3,
            name="Testing",
            definition=AnnotatedText(
                raw_text="A test frame.",
                plain_text="A test frame.",
                annotations=[],
            ),
            frame_elements=[],
            lexical_units=[],
            frame_relations=[],
            semtype_refs=[],
        )

        frame_index.add_frame(new_frame)
        assert len(frame_index._by_id) == initial_count + 1
        assert frame_index.get_frame_by_name("Testing") is not None


class TestFrameNetLoader:
    """Test FrameNet data loader functionality."""

    @pytest.fixture
    def loader(self):
        """Create FrameNet loader instance."""
        return FrameNetLoader()

    @pytest.fixture
    def sample_frames_jsonl(self, tmp_path):
        """Create sample frames JSON Lines file."""
        frame1_data = {
            "id": 1,
            "name": "Giving",
            "definition": {
                "raw_text": "A Donor gives a Theme.",
                "plain_text": "A Donor gives a Theme.",
                "annotations": [],
            },
            "frame_elements": [
                {
                    "id": 1,
                    "name": "Donor",
                    "abbrev": "Don",
                    "definition": {
                        "raw_text": "The giver.",
                        "plain_text": "The giver.",
                        "annotations": [],
                    },
                    "core_type": "Core",
                    "bg_color": "FF0000",
                    "fg_color": "FFFFFF",
                    "semtype_refs": [],
                }
            ],
            "lexical_units": [],
            "frame_relations": [],
            "semtype_refs": [],
        }

        frame2_data = {
            "id": 2,
            "name": "Receiving",
            "definition": {
                "raw_text": "A Recipient receives.",
                "plain_text": "A Recipient receives.",
                "annotations": [],
            },
            "frame_elements": [],
            "lexical_units": [],
            "frame_relations": [],
            "semtype_refs": [],
        }

        jsonl_file = tmp_path / "frames.jsonl"
        with jsonl_file.open("w", encoding="utf-8") as f:
            f.write(json.dumps(frame1_data) + "\n")
            f.write(json.dumps(frame2_data) + "\n")

        return jsonl_file

    @pytest.fixture
    def sample_lus_jsonl(self, tmp_path):
        """Create sample lexical units JSON Lines file."""
        lu_data = {
            "id": 1,
            "name": "give.v",
            "pos": "V",
            "definition": "To transfer",
            "frame_id": 1,
            "frame_name": "Giving",
            "sentence_count": {"annotated": 10, "total": 15},
            "lexemes": [{"name": "give", "pos": "V", "breakBefore": False, "headword": True}],
        }

        jsonl_file = tmp_path / "lexical_units.jsonl"
        with jsonl_file.open("w", encoding="utf-8") as f:
            f.write(json.dumps(lu_data) + "\n")

        return jsonl_file

    @pytest.fixture
    def sample_semantic_types_jsonl(self, tmp_path):
        """Create sample semantic types JSON Lines file."""
        semtype_data = {
            "id": 1,
            "name": "Sentient",
            "abbrev": "Sent",
            "definition": "A thinking being",
        }

        jsonl_file = tmp_path / "semantic_types.jsonl"
        with jsonl_file.open("w", encoding="utf-8") as f:
            f.write(json.dumps(semtype_data) + "\n")

        return jsonl_file

    def test_load_frames_basic(self, loader, sample_frames_jsonl):
        """Test basic frame loading."""
        frames = loader.load_frames(sample_frames_jsonl)

        assert len(frames) == 2
        assert frames[0].name == "Giving"
        assert frames[1].name == "Receiving"
        assert len(frames[0].frame_elements) == 1

    def test_load_frames_nonexistent_file(self, loader):
        """Test loading from non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="FrameNet data file not found"):
            loader.load_frames("nonexistent.jsonl")

    def test_load_frames_skip_errors(self, loader, tmp_path):
        """Test frame loading with skip_errors=True."""
        # Create file with one valid and one invalid line
        jsonl_file = tmp_path / "mixed.jsonl"
        with jsonl_file.open("w", encoding="utf-8") as f:
            # Valid frame
            valid_frame = {
                "id": 1,
                "name": "ValidFrame",
                "definition": {
                    "raw_text": "Valid",
                    "plain_text": "Valid",
                    "annotations": [],
                },
                "frame_elements": [],
                "lexical_units": [],
                "frame_relations": [],
                "semtype_refs": [],
            }
            f.write(json.dumps(valid_frame) + "\n")
            # Invalid JSON
            f.write("invalid json line\n")

        # With skip_errors=True, should load only valid frame
        frames = loader.load_frames(jsonl_file, skip_errors=True)
        assert len(frames) == 1
        assert frames[0].name == "ValidFrame"

        # With skip_errors=False, should raise error
        with pytest.raises(ValueError, match="Error on line"):
            loader.load_frames(jsonl_file, skip_errors=False)

    def test_load_lexical_units_basic(self, loader, sample_lus_jsonl):
        """Test basic lexical unit loading."""
        lus = loader.load_lexical_units(sample_lus_jsonl)

        assert len(lus) == 1
        assert lus[0].name == "give.v"
        assert lus[0].frame_name == "Giving"

    def test_load_lexical_units_nonexistent_file(self, loader):
        """Test loading LUs from non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="FrameNet LU data file not found"):
            loader.load_lexical_units("nonexistent.jsonl")

    def test_load_semantic_types_basic(self, loader, sample_semantic_types_jsonl):
        """Test basic semantic type loading."""
        sem_types = loader.load_semantic_types(sample_semantic_types_jsonl)

        assert len(sem_types) == 1
        assert sem_types[0].name == "Sentient"
        assert sem_types[0].abbrev == "Sent"

    def test_load_semantic_types_nonexistent_file(self, loader):
        """Test loading semantic types from non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="FrameNet semantic types file not found"):
            loader.load_semantic_types("nonexistent.jsonl")

    def test_build_frame_index(self, loader, sample_frames_jsonl):
        """Test building frame index."""
        frames = loader.load_frames(sample_frames_jsonl)
        index = loader.build_frame_index(frames)

        assert isinstance(index, FrameIndex)
        assert len(index._by_id) == 2
        assert index.get_frame_by_name("Giving") is not None

    def test_load_and_index_frames(self, loader, sample_frames_jsonl):
        """Test loading and indexing frames in one step."""
        index = loader.load_and_index_frames(sample_frames_jsonl)

        assert isinstance(index, FrameIndex)
        assert len(index._by_id) == 2
        assert index.get_frame_by_name("Giving") is not None

    def test_validate_frame_data_valid(self, loader, sample_frames_jsonl):
        """Test validation of valid frame data."""
        result = loader.validate_frame_data(sample_frames_jsonl)

        assert result["total_lines"] == 2
        assert result["valid_lines"] == 2
        assert result["error_count"] == 0
        assert result["success_rate"] == 1.0
        assert len(result["validation_errors"]) == 0

    def test_validate_frame_data_with_errors(self, loader, tmp_path):
        """Test validation of frame data with errors."""
        # Create file with invalid JSON
        jsonl_file = tmp_path / "invalid.jsonl"
        with jsonl_file.open("w", encoding="utf-8") as f:
            f.write("invalid json line\n")
            f.write("another invalid line\n")

        result = loader.validate_frame_data(jsonl_file)

        assert result["total_lines"] == 2
        assert result["valid_lines"] == 0
        assert result["error_count"] == 2
        assert result["success_rate"] == 0.0

    def test_validate_frame_data_nonexistent_file(self, loader):
        """Test validation of non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="FrameNet data file not found"):
            loader.validate_frame_data("nonexistent.jsonl")


class TestFrameNetLoaderFunctions:
    """Test FrameNet loader module functions."""

    def test_load_frames_function(self, tmp_path):
        """Test load_frames function."""
        frame_data = {
            "id": 1,
            "name": "TestFrame",
            "definition": {
                "raw_text": "Test",
                "plain_text": "Test",
                "annotations": [],
            },
            "frame_elements": [],
            "lexical_units": [],
            "frame_relations": [],
            "semtype_refs": [],
        }

        jsonl_file = tmp_path / "frames.jsonl"
        with jsonl_file.open("w", encoding="utf-8") as f:
            f.write(json.dumps(frame_data) + "\n")

        frames = load_frames(jsonl_file)

        assert len(frames) == 1
        assert frames[0].name == "TestFrame"

    def test_load_lexical_units_function(self, tmp_path):
        """Test load_lexical_units function."""
        lu_data = {
            "id": 1,
            "name": "test.v",
            "pos": "V",
            "definition": "To test",
            "frame_id": 1,
            "frame_name": "TestFrame",
            "sentence_count": {"annotated": 1, "total": 1},
            "lexemes": [{"name": "give", "pos": "V", "breakBefore": False, "headword": True}],
        }

        jsonl_file = tmp_path / "lus.jsonl"
        with jsonl_file.open("w", encoding="utf-8") as f:
            f.write(json.dumps(lu_data) + "\n")

        lus = load_lexical_units(jsonl_file)

        assert len(lus) == 1
        assert lus[0].name == "test.v"

    def test_build_frame_index_function(self):
        """Test build_frame_index function."""
        frame = Frame(
            id=1,
            name="TestFrame",
            definition=AnnotatedText(
                raw_text="Test",
                plain_text="Test",
                annotations=[],
            ),
            frame_elements=[],
            lexical_units=[],
            frame_relations=[],
            semtype_refs=[],
        )

        index = build_frame_index([frame])

        assert isinstance(index, FrameIndex)
        assert len(index._by_id) == 1

    def test_load_and_index_frames_function(self, tmp_path):
        """Test load_and_index_frames function."""
        frame_data = {
            "id": 1,
            "name": "TestFrame",
            "definition": {
                "raw_text": "Test",
                "plain_text": "Test",
                "annotations": [],
            },
            "frame_elements": [],
            "lexical_units": [],
            "frame_relations": [],
            "semtype_refs": [],
        }

        jsonl_file = tmp_path / "frames.jsonl"
        with jsonl_file.open("w", encoding="utf-8") as f:
            f.write(json.dumps(frame_data) + "\n")

        index = load_and_index_frames(jsonl_file)

        assert isinstance(index, FrameIndex)
        assert len(index._by_id) == 1
