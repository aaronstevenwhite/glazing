"""Tests for PropBank XML to JSON Lines converter.

Tests the PropBankConverter class using real PropBank XML data.
"""

import json
from pathlib import Path

import pytest

from glazing.propbank.converter import PropBankConverter, convert_frameset_file


class TestPropBankConverter:
    """Test PropBankConverter class."""

    def test_convert_frameset_file(self, propbank_frameset_xml):
        """Test converting a frameset XML file."""
        converter = PropBankConverter()
        frameset = converter.convert_frameset_file(propbank_frameset_xml)

        # Check frameset attributes
        assert frameset.predicate_lemma == "abandon"
        assert len(frameset.rolesets) == 1  # Test fixture has one roleset

        # Check roleset
        roleset = frameset.rolesets[0]
        assert roleset.id == "abandon.01"
        assert roleset.name == "leave behind"

        # Check roles
        assert len(roleset.roles) == 3
        role_ns = [role.n for role in roleset.roles]
        assert "0" in role_ns
        assert "1" in role_ns
        assert "2" in role_ns

    def test_parse_role_with_rolelinks(self, propbank_frameset_xml):
        """Test parsing roles with rolelinks."""
        converter = PropBankConverter()
        frameset = converter.convert_frameset_file(propbank_frameset_xml)

        roleset = frameset.rolesets[0]

        # Check first role (arg0)
        role0 = next(r for r in roleset.roles if r.n == "0")
        assert role0.descr == "abandoner"
        assert role0.f == "PPT"
        assert len(role0.rolelinks) == 3

        # Check rolelinks
        vn_link = next((rl for rl in role0.rolelinks if rl.resource == "VerbNet"), None)
        assert vn_link is not None
        assert vn_link.class_name == "leave-51.2"
        assert vn_link.role == "theme"

        fn_links = [rl for rl in role0.rolelinks if rl.resource == "FrameNet"]
        assert len(fn_links) == 2
        fn_classes = [rl.class_name for rl in fn_links]
        assert "Departing" in fn_classes
        assert "Quitting_a_place" in fn_classes

    def test_parse_aliases(self, propbank_frameset_xml):
        """Test parsing aliases."""
        converter = PropBankConverter()
        frameset = converter.convert_frameset_file(propbank_frameset_xml)

        roleset = frameset.rolesets[0]
        assert roleset.aliases is not None

        # Check regular aliases
        assert len(roleset.aliases.alias) == 2
        alias_texts = [a.text for a in roleset.aliases.alias]
        assert "abandon" in alias_texts
        assert "abandonment" in alias_texts

        # Check POS tags
        verb_alias = next(a for a in roleset.aliases.alias if a.text == "abandon")
        assert verb_alias.pos == "v"

        noun_alias = next(a for a in roleset.aliases.alias if a.text == "abandonment")
        assert noun_alias.pos == "n"

    def test_parse_usage_notes(self, propbank_frameset_xml):
        """Test parsing usage notes."""
        converter = PropBankConverter()
        frameset = converter.convert_frameset_file(propbank_frameset_xml)

        roleset = frameset.rolesets[0]
        assert roleset.usagenotes is not None
        assert len(roleset.usagenotes.usage) > 0

        # Check for PropBank usage
        pb_usage = next((u for u in roleset.usagenotes.usage if u.resource == "PropBank"), None)
        assert pb_usage is not None
        assert pb_usage.inuse == "+"

    def test_parse_lexlinks(self, propbank_frameset_xml):
        """Test parsing lexlinks."""
        converter = PropBankConverter()
        frameset = converter.convert_frameset_file(propbank_frameset_xml)

        roleset = frameset.rolesets[0]
        assert len(roleset.lexlinks) > 0

        # Check for VerbNet link
        vn_link = next((ll for ll in roleset.lexlinks if ll.resource == "VerbNet"), None)
        assert vn_link is not None
        assert vn_link.class_name == "leave-51.2"
        assert vn_link.confidence > 0

        # Check for FrameNet links
        fn_links = [ll for ll in roleset.lexlinks if ll.resource == "FrameNet"]
        assert len(fn_links) > 0
        fn_classes = [ll.class_name for ll in fn_links]
        assert "Abandonment" in fn_classes

    def test_parse_example(self, propbank_frameset_xml):
        """Test parsing examples with PropBank annotations."""
        converter = PropBankConverter()
        frameset = converter.convert_frameset_file(propbank_frameset_xml)

        roleset = frameset.rolesets[0]
        assert len(roleset.examples) > 0

        # Check first example
        example = roleset.examples[0]
        assert example.name == "abandon-v: typical transitive"
        assert "Big Board" in example.text
        assert "abandoned" in example.text

        # Check PropBank annotation
        assert example.propbank is not None
        assert example.propbank.rel.relloc == "12"
        assert example.propbank.rel.text == "abandoned"

        # Check arguments
        assert len(example.propbank.args) > 0
        arg0 = next((a for a in example.propbank.args if a.type == "ARG0"), None)
        assert arg0 is not None
        assert arg0.text == "the Big Board"

        arg1 = next((a for a in example.propbank.args if a.type == "ARG1"), None)
        assert arg1 is not None
        assert arg1.text == "their interest"

    def test_convert_real_abandon_frameset(self):
        """Test converting the real abandon.xml frameset file if available."""
        frameset_file = Path("propbank-frames/frames/abandon.xml")
        if not frameset_file.exists():
            pytest.skip("Real PropBank data not available")

        converter = PropBankConverter()
        frameset = converter.convert_frameset_file(frameset_file)

        # Verify against known abandon frameset structure
        assert frameset.predicate_lemma == "abandon"
        assert len(frameset.rolesets) == 3  # Real file has 3 rolesets

        # Check roleset IDs
        roleset_ids = [rs.id for rs in frameset.rolesets]
        assert "abandon.01" in roleset_ids
        assert "abandon.02" in roleset_ids
        assert "abandon.03" in roleset_ids

    def test_json_serialization(self, propbank_frameset_xml):
        """Test that converted frameset can be serialized to JSON."""
        converter = PropBankConverter()
        frameset = converter.convert_frameset_file(propbank_frameset_xml)

        # Serialize to JSON
        json_str = frameset.model_dump_json(exclude_none=True)
        assert json_str

        # Parse back and verify
        data = json.loads(json_str)
        assert data["predicate_lemma"] == "abandon"
        assert len(data["rolesets"]) == 1
        assert data["rolesets"][0]["id"] == "abandon.01"

    def test_convert_framesets_directory(self, tmp_path, propbank_frameset_xml):
        """Test converting a directory of frameset files."""
        # Create test directory with frameset files
        frames_dir = tmp_path / "frames"
        frames_dir.mkdir()

        # Use the fixture's frameset file content
        test_frameset_content = propbank_frameset_xml.read_text()

        # Create a couple test files
        for i in range(2):
            frameset_file = frames_dir / f"frameset{i}.xml"
            frameset_file.write_text(test_frameset_content)

        # Convert directory
        output_file = tmp_path / "framesets.jsonl"
        converter = PropBankConverter()
        count = converter.convert_framesets_directory(frames_dir, output_file)

        assert count == 2
        assert output_file.exists()

        # Verify output
        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 2

        for line in lines:
            data = json.loads(line)
            assert data["predicate_lemma"] == "abandon"
            assert len(data["rolesets"]) == 1

    def test_convenience_function(self, propbank_frameset_xml):
        """Test the convenience function."""
        frameset = convert_frameset_file(propbank_frameset_xml)

        assert frameset.predicate_lemma == "abandon"
        assert len(frameset.rolesets) == 1
        assert frameset.rolesets[0].id == "abandon.01"
