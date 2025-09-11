"""Pytest configuration and shared fixtures for the frames test suite.

This module provides common fixtures and configuration for testing
the frames package components, including real XML samples from
FrameNet, PropBank, VerbNet, and WordNet datasets.
"""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory.

    Returns
    -------
    Path
        Path to the fixtures directory containing test data.
    """
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_framenet_data() -> dict:
    """Provide sample FrameNet data for testing.

    Returns
    -------
    dict
        Sample FrameNet frame data.
    """
    return {
        "id": 7,
        "name": "Abandonment",
        "definition": "An Agent leaves behind a Theme.",
        "frame_elements": [
            {
                "id": 1,
                "name": "Agent",
                "abbrev": "Agt",
                "definition": "The conscious entity that leaves the Theme behind.",
                "core_type": "Core",
                "bg_color": "FF0000",
                "fg_color": "FFFFFF",
            },
            {
                "id": 2,
                "name": "Theme",
                "abbrev": "Thm",
                "definition": "The entity that is left behind by the Agent.",
                "core_type": "Core",
                "bg_color": "0000FF",
                "fg_color": "FFFFFF",
            },
        ],
    }


@pytest.fixture
def sample_propbank_data() -> dict:
    """Provide sample PropBank data for testing.

    Returns
    -------
    dict
        Sample PropBank roleset data.
    """
    return {
        "id": "abandon.01",
        "name": "leave behind",
        "roles": [
            {"n": "0", "f": "PAG", "descr": "abandoner"},
            {"n": "1", "f": "PPT", "descr": "thing abandoned"},
        ],
    }


@pytest.fixture
def sample_verbnet_data() -> dict:
    """Provide sample VerbNet data for testing.

    Returns
    -------
    dict
        Sample VerbNet class data.
    """
    return {
        "id": "leave-51.2",
        "members": [
            {
                "name": "abandon",
                "verbnet_key": "abandon#1",
                "wn": "abandon%2:40:00",
                "grouping": "abandon.01",
                "fn_mapping": "Abandonment",
            }
        ],
        "themroles": [
            {"type": "Agent", "sel_restrictions": {"value": "+", "type": "animate"}},
            {"type": "Theme", "sel_restrictions": None},
        ],
    }


@pytest.fixture
def sample_wordnet_data() -> dict:
    """Provide sample WordNet data for testing.

    Returns
    -------
    dict
        Sample WordNet synset data.
    """
    return {
        "offset": "02228111",
        "lex_filenum": 40,
        "ss_type": "v",
        "words": [
            {"lemma": "abandon", "lex_id": 0},
            {"lemma": "forsake", "lex_id": 0},
            {"lemma": "desolate", "lex_id": 0},
            {"lemma": "desert", "lex_id": 3},
        ],
        "gloss": "leave someone who needs or counts on you; leave in the lurch",
    }


@pytest.fixture
def framenet_frame_xml():
    """Real FrameNet frame XML from Abandonment.xml."""
    content = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<?xml-stylesheet type="text/xsl" href="frame.xsl"?>
<frame cBy="KmG" cDate="03/05/2008 03:50:35 PST Wed" name="Abandonment" ID="2031" xsi:schemaLocation="../schema/frame.xsd" xmlns="http://framenet.icsi.berkeley.edu" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <definition>&lt;def-root&gt;An &lt;fex name="Agent"&gt;Agent&lt;/fex&gt; leaves behind a &lt;fex name="Theme"&gt;Theme&lt;/fex&gt; effectively rendering it no longer within their control or of the normal security as one's property.

&lt;ex&gt;&lt;fex name="Agent"&gt;Carolyn&lt;/fex&gt; &lt;t&gt;abandoned&lt;/t&gt; &lt;fex name="Theme"&gt;her car&lt;/fex&gt; and jumped on a red double decker bus.&lt;/ex&gt;

&lt;ex&gt;Perhaps &lt;fex name="Agent"&gt;he&lt;/fex&gt; &lt;t&gt;left&lt;/t&gt; &lt;fex name="Theme"&gt;the key&lt;/fex&gt; in the ignition&lt;/ex&gt;

&lt;ex&gt;&lt;t&gt;Abandonment&lt;/t&gt; &lt;fex name="Theme"&gt;of a child&lt;/fex&gt; is considered to be a serious crime in many jurisdictions.&lt;/ex&gt;

There are also metaphorically used examples:

&lt;ex&gt;&lt;fex name="Agent"&gt;She&lt;/fex&gt; &lt;t&gt;left&lt;/t&gt; &lt;fex name="Theme"&gt;her old ways&lt;/fex&gt; &lt;fex name="Place"&gt;behind&lt;/fex&gt; .&lt;/ex&gt;&lt;/def-root&gt;</definition>
    <FE bgColor="FF0000" fgColor="FFFFFF" coreType="Core" cBy="KmG" cDate="03/05/2008 03:51:37 PST Wed" abbrev="Age" name="Agent" ID="12338">
        <definition>&lt;def-root&gt;The &lt;fex name="Agent"&gt;Agent&lt;/fex&gt; is the person who acts to leave behind the &lt;fen&gt;Theme&lt;/fen&gt;.&lt;/def-root&gt;</definition>
    </FE>
    <FE bgColor="0000FF" fgColor="FFFFFF" coreType="Core" cBy="KmG" cDate="03/05/2008 03:52:39 PST Wed" abbrev="The" name="Theme" ID="12339">
        <definition>&lt;def-root&gt;The &lt;fex name="Theme"&gt;Theme&lt;/fex&gt; is the entity that is relinguished to no one from the &lt;fex name="Agent"&gt;Agent&lt;/fex&gt;'s possession.&lt;/def-root&gt;</definition>
    </FE>
    <FE bgColor="008000" fgColor="FFFFFF" coreType="Peripheral" cBy="KmG" cDate="03/05/2008 04:08:59 PST Wed" abbrev="Pla" name="Place" ID="12340">
        <definition>&lt;def-root&gt;The location where the &lt;fen&gt;Agent&lt;/fen&gt; gives up the &lt;fen&gt;Theme&lt;/fen&gt;.&lt;/def-root&gt;</definition>
    </FE>
    <FE bgColor="FFA500" fgColor="FFFFFF" coreType="Peripheral" cBy="KmG" cDate="03/05/2008 04:09:33 PST Wed" abbrev="Tim" name="Time" ID="12341">
        <definition>&lt;def-root&gt;When the &lt;fen&gt;Agent&lt;/fen&gt; gives up the &lt;fen&gt;Theme&lt;/fen&gt;.&lt;/def-root&gt;</definition>
    </FE>
    <FE bgColor="FF00FF" fgColor="FFFFFF" coreType="Peripheral" cBy="KmG" cDate="03/05/2008 04:12:22 PST Wed" abbrev="Man" name="Manner" ID="12342">
        <definition>&lt;def-root&gt;The style in which the &lt;fen&gt;Agent&lt;/fen&gt; gives up the &lt;fen&gt;Theme&lt;/fen&gt;.&lt;/def-root&gt;</definition>
    </FE>
    <frameRelation type="Inherits from">
        <relatedFrame ID="2080">Intentionally_act</relatedFrame>
    </frameRelation>
    <lexUnit status="Created" POS="V" name="abandon.v" ID="14892" lemmaID="84" cBy="KmG" cDate="03/19/2008 01:49:42 PDT Wed">
        <definition>FN: leave behind</definition>
        <sentenceCount annotated="0" total="0"/>
        <lexeme order="1" headword="false" breakBefore="false" POS="V" name="abandon"/>
    </lexUnit>
    <lexUnit status="Created" POS="V" name="leave.v" ID="14893" lemmaID="21967" cBy="KmG" cDate="03/19/2008 01:52:09 PDT Wed">
        <definition>FN: abandon</definition>
        <sentenceCount annotated="0" total="0"/>
        <lexeme order="1" headword="false" breakBefore="false" POS="V" name="leave"/>
    </lexUnit>
</frame>"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
        f.write(content)
        return Path(f.name)


@pytest.fixture
def propbank_frameset_xml():
    """Real PropBank frameset XML from abandon.xml."""
    content = """<?xml version="1.0" encoding="utf-8" standalone="no"?>
<!DOCTYPE frameset PUBLIC "-//PB//PropBank Frame v3.4 Transitional//EN" "http://propbank.org/specification/dtds/v3.4/frameset.dtd">
<frameset>
  <predicate lemma="abandon">
    <roleset id="abandon.01" name="leave behind">
      <aliases>
        <alias pos="v">abandon</alias>
        <alias pos="n">abandonment</alias>
      </aliases>
      <roles>
        <role descr="abandoner" f="PPT" n="0">
          <rolelinks>
            <rolelink class="leave-51.2" resource="VerbNet" version="verbnet3.3">theme</rolelink>
            <rolelink class="Departing" resource="FrameNet" version="1.7">theme</rolelink>
            <rolelink class="Quitting_a_place" resource="FrameNet" version="1.7">self_mover</rolelink>
          </rolelinks>
        </role>
        <role descr="entity left behind" f="DIR" n="1">
          <rolelinks>
            <rolelink class="leave-51.2" resource="VerbNet" version="verbnet3.3">initial_location</rolelink>
            <rolelink class="Departing" resource="FrameNet" version="1.7">source</rolelink>
            <rolelink class="Quitting_a_place" resource="FrameNet" version="1.7">source</rolelink>
          </rolelinks>
        </role>
        <role descr="attribute of arg1" f="PRD" n="2">
          <rolelinks>
            <rolelink class="Quitting_a_place" resource="FrameNet" version="1.7">result</rolelink>
          </rolelinks>
        </role>
      </roles>
      <usagenotes>
        <usage resource="PropBank" version="1.0" inuse="+"/>
        <usage resource="PropBank" version="2.1.5" inuse="+"/>
        <usage resource="PropBank" version="3.1" inuse="+"/>
        <usage resource="PropBank" version="3.4" inuse="+"/>
        <usage resource="AMR" version="2019" inuse="+"/>
        <usage resource="PropBank" version="Flickr 1.0" inuse="+"/>
      </usagenotes>
      <lexlinks>
        <lexlink class="Quitting_a_place" confidence="0.8" resource="FrameNet" src="manual+strict-conv" version="1.7"/>
        <lexlink class="Departing" confidence="0.8" resource="FrameNet" src="manual+strict-conv" version="1.7"/>
        <lexlink class="Abandonment" confidence="0.8" resource="FrameNet" src="manual+strict-conv" version="1.7"/>
        <lexlink class="leave-51.2" confidence="0.8" resource="VerbNet" src="manual+strict-conv" version="verbnet3.3"/>
        <lexlink class="leave-51.2" confidence="1.0" resource="VerbNet" src="manualchecks" version="verbnet3.4"/>
      </lexlinks>
      <example name="abandon-v: typical transitive" src="">
        <text>And they believe the Big Board , under Mr. Phelan , has abandoned their interest .</text>
        <propbank>
          <rel relloc="12">abandoned</rel>
          <arg type="ARG0" start="3" end="5">the Big Board</arg>
          <arg type="ARGM-ADV" start="7" end="10">, under Mr. Phelan ,</arg>
          <arg type="ARG1" start="13" end="14">their interest</arg>
        </propbank>
      </example>
    </roleset>
  </predicate>
</frameset>"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
        f.write(content)
        return Path(f.name)


@pytest.fixture
def verbnet_class_xml():
    """Real VerbNet class XML from give-13.1.xml."""
    content = """<!DOCTYPE VNCLASS SYSTEM "vn_class-3.dtd">
<VNCLASS ID="give-13.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="vn_schema-3.xsd">
  <MEMBERS>
    <MEMBER fn_mapping="Giving" grouping="give.01 give.02" name="give" verbnet_key="give#2" wn="give%2:40:00 give%2:40:01 give%2:40:02 give%2:41:00 give%2:41:10 give%2:41:11 give%2:29:11 give%2:36:02" features=""/>
    <MEMBER fn_mapping="None" grouping="deal.04" name="deal" verbnet_key="deal#2" wn="deal%2:40:01 deal%2:40:02 deal%2:40:07 deal%2:40:06" features=""/>
    <MEMBER fn_mapping="None" grouping="lend.02" name="lend" verbnet_key="lend#1" wn="lend%2:40:00" features=""/>
    <MEMBER fn_mapping="None" grouping="" name="loan" verbnet_key="loan#1" wn="loan%2:40:00" features=""/>
    <MEMBER fn_mapping="Giving" grouping="pass.04" name="pass" verbnet_key="pass#3" wn="pass%2:40:00 pass%2:40:01 pass%2:40:13 pass%2:38:04" features=""/>
    <MEMBER fn_mapping="None" grouping="peddle.01" name="peddle" verbnet_key="peddle#1" wn="peddle%2:40:00" features=""/>
    <MEMBER fn_mapping="None" grouping="refund.01" name="refund" verbnet_key="refund#1" wn="refund%2:40:00" features=""/>
    <MEMBER fn_mapping="Categorization" grouping="render.02" name="render" verbnet_key="render#1" wn="render%2:40:02 render%2:40:01 render%2:40:00 render%2:40:03" features=""/>
  </MEMBERS>
  <THEMROLES>
    <THEMROLE type="Agent">
      <SELRESTRS logic="or">
        <SELRESTR Value="+" type="animate"/>
        <SELRESTR Value="+" type="organization"/>
      </SELRESTRS>
    </THEMROLE>
    <THEMROLE type="Theme">
      <SELRESTRS/>
    </THEMROLE>
    <THEMROLE type="Recipient">
      <SELRESTRS logic="or">
        <SELRESTR Value="+" type="animate"/>
        <SELRESTR Value="+" type="organization"/>
      </SELRESTRS>
    </THEMROLE>
  </THEMROLES>
  <FRAMES>
    <FRAME>
      <DESCRIPTION descriptionNumber="0.2" primary="NP V NP PP.recipient" secondary="NP-PP; Recipient-PP" xtag=""/>
      <EXAMPLES>
        <EXAMPLE>They lent a bicycle to me.</EXAMPLE>
      </EXAMPLES>
      <SYNTAX>
        <NP value="Agent">
          <SYNRESTRS/>
        </NP>
        <VERB/>
        <NP value="Theme">
          <SYNRESTRS/>
        </NP>
        <PREP value="to">
          <SELRESTRS/>
        </PREP>
        <NP value="Recipient">
          <SYNRESTRS/>
        </NP>
      </SYNTAX>
      <SEMANTICS>
        <PRED value="transfer">
          <ARGS>
            <ARG type="Event" value="during(E)"/>
            <ARG type="ThemRole" value="Agent"/>
            <ARG type="ThemRole" value="Theme"/>
            <ARG type="ThemRole" value="?Recipient"/>
          </ARGS>
        </PRED>
        <PRED value="has_possession">
          <ARGS>
            <ARG type="Event" value="start(E)"/>
            <ARG type="ThemRole" value="Agent"/>
            <ARG type="ThemRole" value="Theme"/>
          </ARGS>
        </PRED>
        <PRED value="has_possession">
          <ARGS>
            <ARG type="Event" value="end(E)"/>
            <ARG type="ThemRole" value="Recipient"/>
            <ARG type="ThemRole" value="Theme"/>
          </ARGS>
        </PRED>
        <PRED value="cause">
          <ARGS>
            <ARG type="ThemRole" value="Agent"/>
            <ARG type="Event" value="E"/>
          </ARGS>
        </PRED>
      </SEMANTICS>
    </FRAME>
  </FRAMES>
  <SUBCLASSES>
    <VNSUBCLASS ID="give-13.1-1">
      <MEMBERS>
        <MEMBER fn_mapping="None" grouping="sell.01" name="sell" verbnet_key="sell#1" wn="sell%2:40:00 sell%2:40:01 sell%2:40:02 sell%2:40:03" features=""/>
      </MEMBERS>
      <THEMROLES/>
      <FRAMES/>
    </VNSUBCLASS>
  </SUBCLASSES>
</VNCLASS>"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
        f.write(content)
        return Path(f.name)


@pytest.fixture
def wordnet_data_sample():
    """Real WordNet data file entries (verb.motion excerpt)."""
    content = """  1 This software and database is being provided to you, the LICENSEE, by
  2 Princeton University under the following license.  By obtaining, using
  3 and/or copying this software and database, you agree that you have
  4 read, understood, and will comply with these terms and conditions.:
  5
01835496 01 v 01 travel 0 008 @ 01835077 v 0000 + 09777353 n 0101 + 00308370 n 0101 ! 01846789 v 0101 ~ 01835816 v 0000 ~ 01837106 v 0000 ~ 01839793 v 0000 ~ 01847845 v 0000 | change location; move, travel, or proceed, also metaphorically; "How fast does your new car go?"; "We travelled from Rome to Naples by bus"; "The policemen went from door to door looking for the suspect"; "The soldiers moved towards the city in an attempt to take it before night fell"; "news travelled fast"
01835816 02 v 04 go 7 locomote 0 move 9 travel 0 009 @ 01835496 v 0000 + 00295701 n 0409 + 09777353 n 0101 + 00308370 n 0101 ! 01846789 v 0101 ~ 01835077 v 0000 ~ 01848465 v 0000 ~ 01847220 v 0000 ~ 02008889 v 0000 | change location; move, travel, or proceed; "How fast does your new car go?"; "We travelled from Rome to Naples by bus"; "The policemen went from door to door looking for the suspect"; "The soldiers moved towards the city in an attempt to take it before night fell"
01846789 00 v 02 stay_in_place 0 remain 0 002 ! 01835496 v 0101 ! 01835816 v 0101 | stay in the same place; "We are staying in Detroit; we are not moving to Cincinnati"; "Stay put in the corner here!"; "Stick around and you will learn something!"
01848718 00 v 06 advance 8 go_on 4 march_on 1 move_on 0 pass_on 6 progress 2 006 @ 01835496 v 0000 ~ 01850335 v 0000 ~ 01996535 v 0000 ~ 01997982 v 0000 ~ 01999170 v 0000 ~ 02679899 v 0000 | move forward, also in the metaphorical sense; "Time marches on"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        return Path(f.name)


@pytest.fixture
def wordnet_index_sample():
    """Real WordNet index file entries (index.verb excerpt)."""
    content = """  1 This software and database is being provided to you, the LICENSEE, by
  2 Princeton University under the following license.  By obtaining, using
  3 and/or copying this software and database, you agree that you have
  4 read, understood, and will comply with these terms and conditions.:
  5
abandon v 5 4 @ ~ $ + 5 5 02232813 02232523 02080923 00614907 00615748
abandoned_ship v 1 1 @ 1 0 02061360
abase v 1 1 @ 1 1 01802342
abash v 1 2 @ + 1 0 01791356
abate v 2 3 @ ~ + 2 0 00246939 02658762
abbreviate v 2 2 @ + 2 1 00243900 00980149
abdicate v 1 3 @ ~ + 1 2 02387686
abduce v 1 1 < 1 0 00060673
abduct v 2 3 @ ~ + 2 0 01472790 00060673
aberrate v 2 2 @ + 2 0 02654237 00153846
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        return Path(f.name)
