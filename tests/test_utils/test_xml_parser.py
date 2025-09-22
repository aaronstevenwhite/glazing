"""Tests for XML parsing utilities.

Tests the high-performance lxml-based XML parsing utilities using real XML
from FrameNet, PropBank, VerbNet, and WordNet datasets.
"""

import pytest
from lxml import etree

from glazing.utils.xml_parser import (
    MarkupExtractor,
    StreamingParser,
    clear_element,
    compile_xpath,
    extract_text_with_markup,
    fragment_to_annotations,
    iterparse_elements,
    parse_attributes,
    parse_with_schema,
)


@pytest.fixture
def framenet_definition_element():
    """Real FrameNet definition with embedded markup."""
    xml = """<definition>&lt;def-root&gt;An &lt;fex name="Agent"&gt;Agent&lt;/fex&gt; leaves behind a &lt;fex name="Theme"&gt;Theme&lt;/fex&gt; effectively rendering it no longer within their control or of the normal security as one's property.

&lt;ex&gt;&lt;fex name="Agent"&gt;Carolyn&lt;/fex&gt; &lt;t&gt;abandoned&lt;/t&gt; &lt;fex name="Theme"&gt;her car&lt;/fex&gt; and jumped on a red double decker bus.&lt;/ex&gt;

&lt;ex&gt;Perhaps &lt;fex name="Agent"&gt;he&lt;/fex&gt; &lt;t&gt;left&lt;/t&gt; &lt;fex name="Theme"&gt;the key&lt;/fex&gt; in the ignition&lt;/ex&gt;&lt;/def-root&gt;</definition>"""
    # First decode the HTML entities
    xml_decoded = xml.replace("&lt;", "<").replace("&gt;", ">")
    return etree.fromstring(xml_decoded)


@pytest.fixture
def framenet_fe_element():
    """Real FrameNet frame element."""
    xml = """<FE bgColor="FF0000" fgColor="FFFFFF" coreType="Core" cBy="KmG" cDate="03/05/2008 03:51:37 PST Wed" abbrev="Age" name="Agent" ID="12338">
        <definition>&lt;def-root&gt;The &lt;fex name="Agent"&gt;Agent&lt;/fex&gt; is the person who acts to leave behind the &lt;fen&gt;Theme&lt;/fen&gt;.&lt;/def-root&gt;</definition>
    </FE>"""
    return etree.fromstring(xml)


@pytest.fixture
def propbank_role_element():
    """Real PropBank role element with rolelinks."""
    xml = """<role descr="abandoner" f="PPT" n="0">
      <rolelinks>
        <rolelink class="leave-51.2" resource="VerbNet" version="verbnet3.3">theme</rolelink>
        <rolelink class="Departing" resource="FrameNet" version="1.7">theme</rolelink>
        <rolelink class="Quitting_a_place" resource="FrameNet" version="1.7">self_mover</rolelink>
      </rolelinks>
    </role>"""
    return etree.fromstring(xml)


@pytest.fixture
def verbnet_themrole_element():
    """Real VerbNet thematic role with selectional restrictions."""
    xml = """<THEMROLE type="Agent">
      <SELRESTRS logic="or">
        <SELRESTR Value="+" type="animate"/>
        <SELRESTR Value="+" type="organization"/>
      </SELRESTRS>
    </THEMROLE>"""
    return etree.fromstring(xml)


@pytest.fixture
def verbnet_member_element():
    """Real VerbNet member with cross-references."""
    xml = """<MEMBER fn_mapping="Giving" grouping="give.01 give.02" name="give" verbnet_key="give#2" wn="give%2:40:00 give%2:40:01 give%2:40:02 give%2:41:00 give%2:41:10 give%2:41:11 give%2:29:11 give%2:36:02" features=""/>"""
    return etree.fromstring(xml)


class TestIterparseElements:
    """Test iterparse_elements function."""

    def test_framenet_frame_iteration(self, framenet_frame_xml):
        """Test iterating through FrameNet frame elements."""
        frame_elements = []
        # FrameNet uses namespace, need to specify full tag
        for _event, elem in iterparse_elements(
            framenet_frame_xml, tag="{http://framenet.icsi.berkeley.edu}FE"
        ):
            frame_elements.append(elem.get("name"))
            clear_element(elem)

        # The test fixture has 5 FE elements
        assert len(frame_elements) == 5
        assert "Agent" in frame_elements
        assert "Theme" in frame_elements
        assert "Place" in frame_elements
        assert "Time" in frame_elements
        assert "Manner" in frame_elements

    def test_propbank_role_iteration(self, propbank_frameset_xml):
        """Test iterating through PropBank roles."""
        roles = []
        for _event, elem in iterparse_elements(propbank_frameset_xml, tag="role"):
            roles.append(elem.get("n"))
            clear_element(elem)

        assert roles == ["0", "1", "2"]

    def test_verbnet_member_iteration(self, verbnet_class_xml):
        """Test iterating through VerbNet members."""
        members = []
        for _event, elem in iterparse_elements(verbnet_class_xml, tag="MEMBER"):
            members.append(elem.get("name"))
            clear_element(elem)

        # Should get both main class and subclass members
        assert "give" in members
        assert "deal" in members
        assert "sell" in members  # From subclass


class TestParseWithSchema:
    """Test schema validation."""

    def test_well_formed_framenet(self, framenet_frame_xml):
        """Test parsing well-formed FrameNet XML."""
        root = parse_with_schema(framenet_frame_xml)
        assert root.tag == "{http://framenet.icsi.berkeley.edu}frame"
        assert root.get("name") == "Abandonment"
        assert root.get("ID") == "2031"

    def test_well_formed_propbank(self, propbank_frameset_xml):
        """Test parsing well-formed PropBank XML."""
        root = parse_with_schema(propbank_frameset_xml)
        assert root.tag == "frameset"
        predicate = root.find("predicate")
        assert predicate is not None
        assert predicate.get("lemma") == "abandon"

    def test_well_formed_verbnet(self, verbnet_class_xml):
        """Test parsing well-formed VerbNet XML."""
        root = parse_with_schema(verbnet_class_xml)
        assert root.tag == "VNCLASS"
        assert root.get("ID") == "give-13.1"


class TestExtractTextWithMarkup:
    """Test markup extraction."""

    def test_framenet_definition_markup(self, framenet_definition_element):
        """Test extracting FrameNet definition with embedded markup."""
        # The fixture creates a <definition> with a <def-root> child
        # We need to extract from the def-root element which contains the actual markup
        def_root = framenet_definition_element.find("def-root")
        assert def_root is not None

        _text, annotations = extract_text_with_markup(def_root, preserve_tags={"fex", "ex", "t"})

        # Check that we found FE references
        fex_annos = [a for a in annotations if a["tag"] == "fex"]
        assert len(fex_annos) > 0

        # Check specific FE references
        agent_annos = [a for a in fex_annos if a.get("name") == "Agent"]
        assert len(agent_annos) > 0
        theme_annos = [a for a in fex_annos if a.get("name") == "Theme"]
        assert len(theme_annos) > 0

    def test_framenet_fe_definition(self, framenet_fe_element):
        """Test extracting FrameNet FE definition."""
        definition = framenet_fe_element.find("definition")
        # First decode HTML entities in the text
        decoded_text = definition.text.replace("&lt;", "<").replace("&gt;", ">")
        # Parse as a def-root element
        decoded_elem = etree.fromstring(f"<wrapper>{decoded_text}</wrapper>")
        def_root = decoded_elem.find("def-root")
        elem_to_parse = def_root if def_root is not None else decoded_elem

        _text, annotations = extract_text_with_markup(elem_to_parse, preserve_tags={"fex", "fen"})

        # Should find FE and FEN references
        assert any(a["tag"] == "fex" for a in annotations)
        assert any(a["tag"] == "fen" for a in annotations)


class TestCompileXpath:
    """Test XPath compilation."""

    def test_framenet_xpath(self, framenet_frame_xml):
        """Test XPath on FrameNet XML."""
        root = parse_with_schema(framenet_frame_xml)

        # Need to handle namespace
        ns = {"fn": "http://framenet.icsi.berkeley.edu"}
        xpath = compile_xpath("//fn:FE[@coreType='Core']", namespaces=ns)
        results = xpath(root)

        assert len(results) == 2  # Agent and Theme are Core
        names = [elem.get("name") for elem in results]
        assert "Agent" in names
        assert "Theme" in names

    def test_propbank_xpath(self, propbank_frameset_xml):
        """Test XPath on PropBank XML."""
        root = parse_with_schema(propbank_frameset_xml)

        xpath = compile_xpath("//rolelink[@resource='VerbNet']")
        results = xpath(root)

        assert len(results) > 0
        assert results[0].get("class") == "leave-51.2"

    def test_verbnet_xpath(self, verbnet_class_xml):
        """Test XPath on VerbNet XML."""
        root = parse_with_schema(verbnet_class_xml)

        xpath = compile_xpath("//MEMBER[@fn_mapping!='None']")
        results = xpath(root)

        # Should find members with FrameNet mappings
        assert len(results) > 0
        for elem in results:
            assert elem.get("fn_mapping") != "None"


class TestParseAttributes:
    """Test attribute parsing."""

    def test_framenet_fe_attributes(self, framenet_fe_element):
        """Test parsing FrameNet FE attributes."""
        type_map = {
            "ID": int,
        }

        attrs = parse_attributes(framenet_fe_element, type_map)

        assert attrs["bgColor"] == "FF0000"
        assert attrs["fgColor"] == "FFFFFF"
        assert attrs["coreType"] == "Core"
        assert attrs["name"] == "Agent"
        assert attrs["ID"] == 12338
        assert isinstance(attrs["ID"], int)

    def test_verbnet_member_attributes(self, verbnet_member_element):
        """Test parsing VerbNet member attributes."""
        attrs = parse_attributes(verbnet_member_element)

        assert attrs["fn_mapping"] == "Giving"
        assert attrs["grouping"] == "give.01 give.02"
        assert attrs["name"] == "give"
        assert attrs["verbnet_key"] == "give#2"
        assert "give%2:40:00" in attrs["wn"]

    def test_bool_conversion(self):
        """Test various boolean conversions."""
        xml = '<elem a="true" b="false" c="1" d="0" e="yes" f="no"/>'
        elem = etree.fromstring(xml)

        type_map = dict.fromkeys("abcdef", bool)
        attrs = parse_attributes(elem, type_map)

        assert attrs["a"] is True
        assert attrs["b"] is False
        assert attrs["c"] is True
        assert attrs["d"] is False
        assert attrs["e"] is True
        assert attrs["f"] is False

    def test_invalid_conversion(self):
        """Test handling invalid type conversions."""
        xml = '<elem id="not_a_number"/>'
        elem = etree.fromstring(xml)

        # Should raise ValueError on invalid conversion
        with pytest.raises(ValueError) as exc_info:
            parse_attributes(elem, {"id": int})

        assert "Failed to convert attribute 'id'" in str(exc_info.value)
        assert "not_a_number" in str(exc_info.value)
        assert "to type int" in str(exc_info.value)


class TestClearElement:
    """Test element clearing."""

    def test_clear_framenet_element(self, framenet_fe_element):
        """Test clearing FrameNet FE element."""
        # Element should have attributes and children initially
        assert framenet_fe_element.get("name") == "Agent"
        assert len(framenet_fe_element) > 0  # Has definition child

        clear_element(framenet_fe_element)

        # After clearing, should be empty
        assert framenet_fe_element.text is None
        assert len(framenet_fe_element) == 0
        assert framenet_fe_element.attrib == {}

    def test_clear_verbnet_element(self, verbnet_themrole_element):
        """Test clearing VerbNet thematic role."""
        # Element should have SELRESTRS child
        assert verbnet_themrole_element.get("type") == "Agent"
        assert len(verbnet_themrole_element) > 0

        clear_element(verbnet_themrole_element)

        assert verbnet_themrole_element.text is None
        assert len(verbnet_themrole_element) == 0


class TestFragmentToAnnotations:
    """Test fragment parsing."""

    def test_framenet_fragments(self):
        """Test parsing FrameNet-style fragments."""
        text = 'An <fex name="Agent">Agent</fex> leaves behind a <fex name="Theme">Theme</fex>.'
        plain, annotations = fragment_to_annotations(text)

        assert "Agent leaves behind a Theme" in plain
        assert len(annotations) == 2

        # Check FE annotations
        agent = next(a for a in annotations if a.get("name") == "Agent")
        assert agent["tag"] == "fex"
        assert agent["text"] == "Agent"

        theme = next(a for a in annotations if a.get("name") == "Theme")
        assert theme["tag"] == "fex"
        assert theme["text"] == "Theme"

    def test_mixed_framenet_tags(self):
        """Test multiple FrameNet tag types."""
        text = (
            'The <fex name="Agent">person</fex> <t>abandoned</t> the <fex name="Theme">car</fex>.'
        )
        plain, annotations = fragment_to_annotations(text)

        assert "person abandoned the car" in plain
        assert len(annotations) == 3

        # Check target annotation
        target = next(a for a in annotations if a["tag"] == "t")
        assert target["text"] == "abandoned"


class TestMarkupExtractor:
    """Test MarkupExtractor class."""

    def test_framenet_extractor(self, framenet_definition_element):
        """Test extracting FrameNet markup."""
        extractor = MarkupExtractor({"fex", "ex", "t", "def-root"})
        _text, annotations = extractor.extract(framenet_definition_element)

        # Should find various tag types
        tag_types = {a["tag"] for a in annotations}
        assert "fex" in tag_types or "def-root" in tag_types

        # Check FE references
        fex_annos = [a for a in annotations if a["tag"] == "fex"]
        if fex_annos:
            assert any(a.get("name") == "Agent" for a in fex_annos)

    def test_nested_framenet_markup(self):
        """Test nested FrameNet markup extraction."""
        # FrameNet has nested structures like ex containing fex and t
        xml = """<wrapper><ex>The <fex name="Agent">person</fex> <t>left</t> the <fex name="Theme">house</fex>.</ex></wrapper>"""
        elem = etree.fromstring(xml)

        extractor = MarkupExtractor({"ex", "fex", "t"}, nested=True)
        _text, annotations = extractor._extract_recursive(elem)

        # Should have all levels of annotations
        tags = [a["tag"] for a in annotations]
        assert "ex" in tags
        assert "fex" in tags
        assert "t" in tags


class TestStreamingParser:
    """Test StreamingParser class."""

    def test_iter_framenet_elements(self, framenet_frame_xml):
        """Test iterating FrameNet elements."""
        parser = StreamingParser(framenet_frame_xml)
        # FrameNet uses namespace
        fes = list(parser.iter_elements("{http://framenet.icsi.berkeley.edu}FE"))

        assert len(fes) == 5
        # Elements should be cleared after iteration
        for fe in fes:
            assert len(fe) == 0

    def test_count_propbank_elements(self, propbank_frameset_xml):
        """Test counting PropBank elements."""
        parser = StreamingParser(propbank_frameset_xml)

        role_count = parser.count_elements("role")
        assert role_count == 3

        rolelink_count = parser.count_elements("rolelink")
        assert rolelink_count > 0

    def test_parse_verbnet_with_handler(self, verbnet_class_xml):
        """Test parsing VerbNet with custom handler."""
        parser = StreamingParser(verbnet_class_xml, target_tags={"MEMBER"})
        member_names = []

        def handler(elem):
            member_names.append(elem.get("name"))

        parser.parse(handler)
        assert "give" in member_names
        assert "deal" in member_names
