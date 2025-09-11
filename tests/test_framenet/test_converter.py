"""Tests for FrameNet XML to JSON Lines converter.

Tests the FrameNetConverter class using real FrameNet XML data.
"""

import json
from pathlib import Path

import pytest

from glazing.framenet.converter import FrameNetConverter, convert_frame_file


class TestFrameNetConverter:
    """Test FrameNetConverter class."""

    def test_convert_frame_file(self, framenet_frame_xml):
        """Test converting a frame XML file."""
        converter = FrameNetConverter()
        frame = converter.convert_frame_file(framenet_frame_xml)

        # Check frame attributes
        assert frame.id == 2031
        assert frame.name == "Abandonment"
        assert "Agent" in frame.definition.raw_text
        assert "Theme" in frame.definition.raw_text

        # Check frame elements
        assert len(frame.frame_elements) == 5
        fe_names = [fe.name for fe in frame.frame_elements]
        assert "Agent" in fe_names
        assert "Theme" in fe_names
        assert "Place" in fe_names
        assert "Time" in fe_names
        assert "Manner" in fe_names

        # Check core elements
        core_elements = frame.get_core_elements()
        assert len(core_elements) == 2
        core_names = [fe.name for fe in core_elements]
        assert "Agent" in core_names
        assert "Theme" in core_names

    def test_parse_frame_element(self, framenet_frame_xml):
        """Test parsing individual frame elements."""
        converter = FrameNetConverter()
        frame = converter.convert_frame_file(framenet_frame_xml)

        # Check Agent FE
        agent = frame.get_fe_by_name("Agent")
        assert agent is not None
        assert agent.id == 12338
        assert agent.abbrev == "Age"
        assert agent.core_type == "Core"
        assert agent.bg_color == "FF0000"
        assert agent.fg_color == "FFFFFF"
        assert "Agent" in agent.definition.raw_text

        # Check Theme FE
        theme = frame.get_fe_by_name("Theme")
        assert theme is not None
        assert theme.id == 12339
        assert theme.abbrev == "The"
        assert theme.core_type == "Core"
        assert theme.bg_color == "0000FF"
        assert theme.fg_color == "FFFFFF"

    def test_parse_definition_with_markup(self, framenet_frame_xml):
        """Test parsing definition with embedded markup."""
        converter = FrameNetConverter()
        frame = converter.convert_frame_file(framenet_frame_xml)

        # Check that definition was parsed
        assert frame.definition.plain_text
        assert frame.definition.annotations

        # Check for FE references in definition
        fe_refs = frame.definition.get_fe_references()
        assert len(fe_refs) > 0

        # Check that FE names are found
        fe_names = [ref.name for ref in fe_refs if ref.name]
        assert "Agent" in fe_names or any("Agent" in (ref.text or "") for ref in fe_refs)
        assert "Theme" in fe_names or any("Theme" in (ref.text or "") for ref in fe_refs)

    def test_convert_real_abandonment_frame(self):
        """Test converting the real Abandonment.xml frame file if available."""
        frame_file = Path("framenet_v17/frame/Abandonment.xml")
        if not frame_file.exists():
            pytest.skip("Real FrameNet data not available")

        converter = FrameNetConverter()
        frame = converter.convert_frame_file(frame_file)

        # Verify against known Abandonment frame structure
        assert frame.id == 2031
        assert frame.name == "Abandonment"
        assert len(frame.frame_elements) == 12  # Real frame has 12 FEs

        # Check some known FEs
        fe_names = [fe.name for fe in frame.frame_elements]
        assert "Agent" in fe_names
        assert "Theme" in fe_names
        assert "Place" in fe_names
        assert "Time" in fe_names
        assert "Manner" in fe_names
        assert "Duration" in fe_names
        assert "Explanation" in fe_names
        assert "Depictive" in fe_names
        assert "Degree" in fe_names
        assert "Means" in fe_names
        assert "Purpose" in fe_names
        assert "Event_description" in fe_names

    def test_json_serialization(self, framenet_frame_xml):
        """Test that converted frame can be serialized to JSON."""
        converter = FrameNetConverter()
        frame = converter.convert_frame_file(framenet_frame_xml)

        # Serialize to JSON
        json_str = frame.model_dump_json(exclude_none=True)
        assert json_str

        # Parse back and verify
        data = json.loads(json_str)
        assert data["id"] == 2031
        assert data["name"] == "Abandonment"
        assert len(data["frame_elements"]) == 5

    def test_convert_frames_directory(self, tmp_path, framenet_frame_xml):
        """Test converting a directory of frame files."""
        # Create test directory with frame files
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()

        # Use the fixture's frame file content
        test_frame_content = framenet_frame_xml.read_text()

        # Create a couple test files
        for i in range(2):
            frame_file = frames_dir / f"Frame{i}.xml"
            frame_file.write_text(test_frame_content)

        # Convert directory
        output_file = tmp_path / "frames.jsonl"
        converter = FrameNetConverter()
        count = converter.convert_frames_directory(frames_dir, output_file)

        assert count == 2
        assert output_file.exists()

        # Verify output
        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 2

        for line in lines:
            data = json.loads(line)
            assert data["id"] == 2031
            assert data["name"] == "Abandonment"

    def test_convenience_function(self, framenet_frame_xml):
        """Test the convenience function."""
        frame = convert_frame_file(framenet_frame_xml)

        assert frame.id == 2031
        assert frame.name == "Abandonment"
        assert len(frame.frame_elements) == 5
