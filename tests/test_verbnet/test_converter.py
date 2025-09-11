"""Tests for VerbNet XML converter.

Tests the VerbNet XML to JSON Lines conversion functionality including
verb class parsing, inheritance handling, and cross-reference extraction.
"""

import json
import xml.etree.ElementTree as ET

import pytest

from glazing.verbnet.converter import (
    VerbNetConverter,
    convert_verbnet_directory,
    convert_verbnet_file,
)
from glazing.verbnet.models import (
    SelectionalRestriction,
    SelectionalRestrictions,
    VerbClass,
    WordNetCrossRef,
)


class TestVerbNetConverter:
    """Test VerbNet XML converter functionality."""

    @pytest.fixture
    def converter(self):
        """Create VerbNet converter instance."""
        return VerbNetConverter()

    @pytest.fixture
    def sample_verbnet_xml(self):
        """Create sample VerbNet XML content."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE VNCLASS SYSTEM "vn_class-3.dtd">
        <VNCLASS ID="give-13.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <MEMBERS>
                <MEMBER name="give" verbnet_key="give#2" wn="give%2:40:00" grouping="give.01" fn_mapping="Giving" features=""/>
                <MEMBER name="hand" verbnet_key="hand#1" wn="hand%2:35:00" grouping="hand.01" fn_mapping="None" features=""/>
            </MEMBERS>
            <THEMROLES>
                <THEMROLE type="Agent">
                    <SELRESTRS>
                        <SELRESTR Value="+" type="animate"/>
                    </SELRESTRS>
                </THEMROLE>
                <THEMROLE type="Theme">
                    <SELRESTRS>
                        <SELRESTR Value="-" type="animate"/>
                    </SELRESTRS>
                </THEMROLE>
                <THEMROLE type="Recipient">
                    <SELRESTRS>
                        <SELRESTR Value="+" type="animate"/>
                    </SELRESTRS>
                </THEMROLE>
            </THEMROLES>
            <FRAMES>
                <FRAME>
                    <DESCRIPTION descriptionNumber="0.2" primary="NP V NP to NP" secondary="Basic Transfer" xtag="0.1"/>
                    <EXAMPLES>
                        <EXAMPLE>John gave a book to Mary</EXAMPLE>
                        <EXAMPLE>She handed him the keys</EXAMPLE>
                    </EXAMPLES>
                    <SYNTAX>
                        <NP value="Agent"><SYNRESTRS/><SELRESTRS/></NP>
                        <VERB/>
                        <NP value="Theme"><SYNRESTRS/><SELRESTRS/></NP>
                        <PREP value="to"><SELRESTRS><SELRESTR Value="+" type="animate"/></SELRESTRS></PREP>
                        <NP value="Recipient"><SYNRESTRS/><SELRESTRS/></NP>
                    </SYNTAX>
                    <SEMANTICS>
                        <PRED value="motion">
                            <ARGS>
                                <ARG type="Event" value="e1"/>
                                <ARG type="ThemRole" value="Theme"/>
                                <ARG type="ThemRole" value="Agent"/>
                            </ARGS>
                        </PRED>
                        <PRED value="transfer" bool="!">
                            <ARGS>
                                <ARG type="ThemRole" value="Agent"/>
                                <ARG type="ThemRole" value="Theme"/>
                                <ARG type="ThemRole" value="Recipient"/>
                            </ARGS>
                        </PRED>
                    </SEMANTICS>
                </FRAME>
            </FRAMES>
            <SUBCLASSES>
                <VNSUBCLASS ID="give-13.1-1">
                    <MEMBERS>
                        <MEMBER name="donate" verbnet_key="donate#1" wn="donate%2:40:00" grouping="donate.01"/>
                    </MEMBERS>
                    <THEMROLES/>
                    <FRAMES/>
                </VNSUBCLASS>
            </SUBCLASSES>
        </VNCLASS>"""

    @pytest.fixture
    def sample_xml_file(self, sample_verbnet_xml, tmp_path):
        """Create temporary XML file with sample content."""
        xml_file = tmp_path / "give-13.1.xml"
        xml_file.write_text(sample_verbnet_xml, encoding="utf-8")
        return xml_file

    def test_convert_verbnet_file_basic(self, converter, sample_xml_file):
        """Test basic VerbNet XML file conversion."""
        result = converter.convert_verbnet_file(sample_xml_file)

        assert isinstance(result, VerbClass)
        assert result.id == "give-13.1"
        assert len(result.members) == 2
        assert len(result.themroles) == 3
        assert len(result.frames) == 1
        assert len(result.subclasses) == 1

    def test_convert_verbnet_file_members(self, converter, sample_xml_file):
        """Test member parsing from VerbNet XML."""
        result = converter.convert_verbnet_file(sample_xml_file)

        members = result.members
        assert len(members) == 2

        give_member = next((m for m in members if m.name == "give"), None)
        assert give_member is not None
        assert give_member.verbnet_key == "give#2"
        assert len(give_member.wordnet_mappings) == 1
        assert give_member.wordnet_mappings[0].to_percentage_notation() == "give%2:40:00"

    def test_convert_verbnet_file_themroles(self, converter, sample_xml_file):
        """Test thematic role parsing from VerbNet XML."""
        result = converter.convert_verbnet_file(sample_xml_file)

        roles = result.themroles
        assert len(roles) == 3

        agent_role = next((r for r in roles if r.type == "Agent"), None)
        assert agent_role is not None
        assert agent_role.sel_restrictions is not None

        restrictions = agent_role.sel_restrictions.flatten_restrictions()
        assert len(restrictions) == 1
        assert restrictions[0].value == "+"
        assert restrictions[0].type == "animate"

    def test_convert_verbnet_file_frames(self, converter, sample_xml_file):
        """Test frame parsing from VerbNet XML."""
        result = converter.convert_verbnet_file(sample_xml_file)

        frames = result.frames
        assert len(frames) == 1

        frame = frames[0]
        assert frame.description.description_number == "0.2"
        assert frame.description.primary == "NP V NP to NP"
        assert frame.description.secondary == "Basic Transfer"
        assert len(frame.examples) == 2
        assert len(frame.syntax.elements) == 5
        assert len(frame.semantics.predicates) == 2

    def test_convert_verbnet_file_subclasses(self, converter, sample_xml_file):
        """Test subclass parsing with inheritance."""
        result = converter.convert_verbnet_file(sample_xml_file)

        subclasses = result.subclasses
        assert len(subclasses) == 1

        subclass = subclasses[0]
        assert subclass.id == "give-13.1-1"
        assert subclass.parent_class == "give-13.1"
        assert len(subclass.members) == 1
        assert len(subclass.themroles) == 0  # Empty = inherit from parent
        assert len(subclass.frames) == 0

    def test_convert_verbnet_file_nonexistent(self, converter):
        """Test conversion of non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="VerbNet file not found"):
            converter.convert_verbnet_file("nonexistent.xml")

    def test_convert_verbnet_file_invalid_xml(self, converter, tmp_path):
        """Test conversion of invalid XML raises ValueError."""
        invalid_file = tmp_path / "invalid.xml"
        invalid_file.write_text("invalid xml content", encoding="utf-8")

        with pytest.raises(ValueError, match="XML parsing failed"):
            converter.convert_verbnet_file(invalid_file)

    def test_convert_verbnet_file_wrong_root(self, converter, tmp_path):
        """Test conversion with wrong root element raises ValueError."""
        wrong_root = tmp_path / "wrong.xml"
        wrong_root.write_text('<?xml version="1.0"?><WRONG></WRONG>', encoding="utf-8")

        with pytest.raises(ValueError, match="Expected VNCLASS root element"):
            converter.convert_verbnet_file(wrong_root)

    def test_parse_selectional_restrictions_complex(self, converter):
        """Test parsing of complex nested selectional restrictions."""
        xml_content = """
        <SELRESTRS logic="or">
            <SELRESTR Value="+" type="animate"/>
            <SELRESTRS logic="and">
                <SELRESTR Value="-" type="concrete"/>
                <SELRESTR Value="+" type="organization"/>
            </SELRESTRS>
        </SELRESTRS>
        """
        element = ET.fromstring(xml_content)
        result = converter._parse_selectional_restrictions(element)

        assert result.logic == "or"
        assert len(result.restrictions) == 2

        # First restriction should be simple
        first = result.restrictions[0]
        assert isinstance(first, SelectionalRestriction)
        assert first.value == "+"
        assert first.type == "animate"

        # Second should be nested
        second = result.restrictions[1]
        assert isinstance(second, SelectionalRestrictions)
        assert second.logic == "and"
        assert len(second.restrictions) == 2

    def test_parse_syntax_element_prep(self, converter):
        """Test parsing of PREP syntax element with restrictions."""
        xml_content = """
        <PREP value="to at">
            <SELRESTRS>
                <SELRESTR Value="+" type="animate"/>
            </SELRESTRS>
        </PREP>
        """
        element = ET.fromstring(xml_content)
        result = converter._parse_syntax_element(element)

        assert result is not None
        assert result.pos == "PREP"
        assert result.value == "to at"
        assert len(result.selrestrs) == 1
        assert result.selrestrs[0].value == "+"
        assert result.selrestrs[0].type == "animate"

    def test_parse_predicate_negated(self, converter):
        """Test parsing of negated semantic predicate."""
        xml_content = """
        <PRED value="transfer" bool="!">
            <ARGS>
                <ARG type="ThemRole" value="Agent"/>
                <ARG type="ThemRole" value="Theme"/>
            </ARGS>
        </PRED>
        """
        element = ET.fromstring(xml_content)
        result = converter._parse_predicate(element)

        assert result is not None
        assert result.value == "transfer"
        assert result.negated is True
        assert len(result.args) == 2

    def test_convert_verbnet_directory_basic(self, converter, tmp_path):
        """Test directory conversion to JSON Lines."""
        # Create test XML files
        xml1_content = """<?xml version="1.0"?>
        <!DOCTYPE VNCLASS SYSTEM "vn_class-3.dtd">
        <VNCLASS ID="test-1.0">
            <MEMBERS/>
            <THEMROLES/>
            <FRAMES/>
        </VNCLASS>"""

        xml2_content = """<?xml version="1.0"?>
        <!DOCTYPE VNCLASS SYSTEM "vn_class-3.dtd">
        <VNCLASS ID="test-2.0">
            <MEMBERS/>
            <THEMROLES/>
            <FRAMES/>
        </VNCLASS>"""

        input_dir = tmp_path / "input"
        input_dir.mkdir()

        (input_dir / "test1.xml").write_text(xml1_content, encoding="utf-8")
        (input_dir / "test2.xml").write_text(xml2_content, encoding="utf-8")

        output_file = tmp_path / "output.jsonl"

        count = converter.convert_verbnet_directory(input_dir, output_file)

        assert count == 2
        assert output_file.exists()

        # Check output content
        lines = output_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2

        # Each line should be valid JSON
        for line in lines:
            data = json.loads(line)
            assert "id" in data
            assert data["id"].startswith("test-")

    def test_convert_verbnet_directory_no_xml_files(self, converter, tmp_path):
        """Test directory with no XML files raises FileNotFoundError."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        output_file = tmp_path / "output.jsonl"

        with pytest.raises(FileNotFoundError, match="No XML files found"):
            converter.convert_verbnet_directory(empty_dir, output_file)

    def test_convert_verbnet_directory_nonexistent(self, converter, tmp_path):
        """Test conversion of non-existent directory raises FileNotFoundError."""
        output_file = tmp_path / "output.jsonl"

        with pytest.raises(FileNotFoundError, match="Input directory not found"):
            converter.convert_verbnet_directory("nonexistent", output_file)

    def test_parse_wordnet_cross_ref_from_percentage(self):
        """Test WordNet cross-reference parsing from percentage notation."""
        ref = WordNetCrossRef.from_percentage_notation("give%2:40:00")

        assert ref.lemma == "give"
        assert ref.pos == "v"  # ss_type 2 maps to verb
        assert ref.sense_key == "give%2:40:00::"

    def test_parse_wordnet_cross_ref_invalid_notation(self):
        """Test WordNet cross-reference with invalid percentage notation."""
        with pytest.raises(ValueError, match="Invalid percentage notation"):
            WordNetCrossRef.from_percentage_notation("invalid-format")

    def test_parse_frame_description_with_xtag(self, converter):
        """Test frame description parsing with XTag."""
        xml_content = """
        <DESCRIPTION descriptionNumber="2.5.1" primary="NP V NP PP" secondary="Transfer; Movement" xtag="through-PP"/>
        """
        element = ET.fromstring(xml_content)
        result = converter._parse_frame_description(element)

        assert result.description_number == "2.5.1"
        assert result.primary == "NP V NP PP"
        assert result.secondary == "Transfer; Movement"
        assert result.xtag == "through-PP"
        assert len(result.primary_elements) == 4
        assert len(result.secondary_patterns) == 2

    def test_parse_invalid_class_id(self, converter, tmp_path):
        """Test parsing with invalid class ID format."""
        invalid_xml = """<?xml version="1.0"?>
        <!DOCTYPE VNCLASS SYSTEM "vn_class-3.dtd">
        <VNCLASS ID="invalid_format">
            <MEMBERS/>
            <THEMROLES/>
            <FRAMES/>
        </VNCLASS>"""

        xml_file = tmp_path / "invalid.xml"
        xml_file.write_text(invalid_xml, encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid VerbNet class ID format"):
            converter.convert_verbnet_file(xml_file)


class TestVerbNetConverterFunctions:
    """Test VerbNet converter module functions."""

    def test_convert_verbnet_file_function(self, tmp_path):
        """Test convert_verbnet_file function."""
        xml_content = """<?xml version="1.0"?>
        <!DOCTYPE VNCLASS SYSTEM "vn_class-3.dtd">
        <VNCLASS ID="test-1.0">
            <MEMBERS/>
            <THEMROLES/>
            <FRAMES/>
        </VNCLASS>"""

        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content, encoding="utf-8")

        result = convert_verbnet_file(xml_file)

        assert isinstance(result, VerbClass)
        assert result.id == "test-1.0"

    def test_convert_verbnet_directory_function(self, tmp_path):
        """Test convert_verbnet_directory function."""
        xml_content = """<?xml version="1.0"?>
        <!DOCTYPE VNCLASS SYSTEM "vn_class-3.dtd">
        <VNCLASS ID="test-1.0">
            <MEMBERS/>
            <THEMROLES/>
            <FRAMES/>
        </VNCLASS>"""

        input_dir = tmp_path / "input"
        input_dir.mkdir()

        (input_dir / "test.xml").write_text(xml_content, encoding="utf-8")

        output_file = tmp_path / "output.jsonl"

        count = convert_verbnet_directory(input_dir, output_file)

        assert count == 1
        assert output_file.exists()
