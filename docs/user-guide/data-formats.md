# Data Formats

Glazing uses [JSON Lines](https://jsonlines.org/) format for all datasets. Each line in a dataset-specific `.jsonl` file conforms to a specific [JSON schema](https://json-schema.org/), which is validated using [Pydantic v2](https://docs.pydantic.dev/2.0/). These files are converted from the native format of the dataset.

## Data Location

Default locations after `glazing init`:

```
~/.local/share/glazing/
├── raw/                 # Original format
│   ├── verbnet-3.4/
│   ├── propbank-frames/
│   ├── wn31-dict/
│   └── framenet_v17/
└── converted/           # JSON Lines
    ├── verbnet.jsonl
    ├── propbank.jsonl
    ├── wordnet.jsonl
    └── framenet.jsonl
```

## Dataset Schemas

### VerbNet

**JSON Schema**:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["id", "members", "themroles", "frames", "subclasses"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^[a-z_]+-\\d+(\\.\\d+)*(-\\d+)?$",
      "description": "VerbNet class ID (e.g., 'give-13.1')"
    },
    "members": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "verbnet_key"],
        "properties": {
          "name": {"type": "string"},
          "verbnet_key": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_\\-\\.\\s]*#\\d+$"
          },
          "framenet_mappings": {"type": "array", "items": {"type": "object"}},
          "propbank_mappings": {"type": "array", "items": {"type": "object"}},
          "wordnet_mappings": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "sense_key": {"type": ["string", "null"]},
                "synset_offset": {"type": ["string", "null"]},
                "lemma": {"type": "string"},
                "pos": {"type": "string"},
                "sense_number": {"type": ["integer", "null"]}
              }
            }
          },
          "features": {"type": "object"},
          "mapping_metadata": {"type": ["object", "null"]},
          "inherited_from_class": {"type": ["string", "null"]}
        }
      }
    },
    "themroles": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["type"],
        "properties": {
          "type": {"type": "string"},
          "sel_restrictions": {
            "type": "object",
            "properties": {
              "logic": {"type": ["string", "null"]},
              "restrictions": {"type": "array"}
            }
          }
        }
      }
    },
    "frames": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["description", "examples", "syntax", "semantics"],
        "properties": {
          "description": {
            "type": "object",
            "properties": {
              "description_number": {"type": "string"},
              "primary": {"type": "string"},
              "secondary": {"type": "string"}
            }
          },
          "examples": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {"text": {"type": "string"}}
            }
          },
          "syntax": {
            "type": "object",
            "properties": {
              "elements": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "pos": {"type": "string"},
                    "value": {"type": ["string", "null"]},
                    "synrestrs": {"type": "array"},
                    "selrestrs": {"type": "array"}
                  }
                }
              }
            }
          },
          "semantics": {
            "type": "object",
            "properties": {
              "predicates": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "value": {"type": "string"},
                    "args": {"type": "array"},
                    "negated": {"type": "boolean"}
                  }
                }
              }
            }
          }
        }
      }
    },
    "subclasses": {"type": "array"},
    "parent_class": {"type": ["string", "null"]}
  }
}
```

**Example Entry**:

```json
{
  "id": "give-13.1-1",
  "members": [
    {
      "name": "give",
      "verbnet_key": "give#3",
      "framenet_mappings": [],
      "propbank_mappings": [],
      "wordnet_mappings": [
        {"sense_key": "give%2:40:03::", "synset_offset": null, "lemma": "give", "pos": "v", "sense_number": null},
        {"sense_key": "give%2:40:00::", "synset_offset": null, "lemma": "give", "pos": "v", "sense_number": null}
      ],
      "features": {},
      "mapping_metadata": null,
      "inherited_from_class": null
    }
  ],
  "themroles": [
    {"type": "Agent", "sel_restrictions": {"logic": null, "restrictions": []}},
    {"type": "Theme", "sel_restrictions": {"logic": null, "restrictions": []}},
    {"type": "Recipient", "sel_restrictions": {"logic": null, "restrictions": []}}
  ],
  "frames": [
    {
      "description": {
        "description_number": "0.0",
        "primary": "NP V NP NP",
        "secondary": "Basic Transitive"
      },
      "examples": [{"text": "Carmen handed the pirate the treasure."}],
      "syntax": {
        "elements": [
          {"pos": "NP", "value": "Agent", "synrestrs": [], "selrestrs": []},
          {"pos": "VERB", "value": null, "synrestrs": [], "selrestrs": []},
          {"pos": "NP", "value": "Recipient", "synrestrs": [], "selrestrs": []},
          {"pos": "NP", "value": "Theme", "synrestrs": [], "selrestrs": []}
        ]
      },
      "semantics": {
        "predicates": [
          {"value": "has_possession", "args": [{"type": "Event", "value": "e1"}, {"type": "ThemRole", "value": "Agent"}, {"type": "ThemRole", "value": "Theme"}], "negated": false},
          {"value": "transfer", "args": [{"type": "Event", "value": "e3"}, {"type": "ThemRole", "value": "Agent"}, {"type": "ThemRole", "value": "Theme"}, {"type": "ThemRole", "value": "Recipient"}], "negated": false}
        ]
      }
    }
  ],
  "subclasses": [],
  "parent_class": "give-13.1"
}
```

### PropBank

**JSON Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["predicate_lemma", "rolesets"],
  "properties": {
    "predicate_lemma": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_\\-\\.]*$",
      "description": "The predicate lemma (e.g., 'give', 'abandon')"
    },
    "rolesets": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "roles"],
        "properties": {
          "id": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9_\\-\\.]+\\.(\\d{2}|LV)$",
            "description": "Roleset ID (e.g., 'give.01')"
          },
          "name": {"type": ["string", "null"]},
          "aliases": {
            "type": "object",
            "properties": {
              "alias": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "text": {"type": "string"},
                    "pos": {"type": "string", "enum": ["n", "v", "j", "l", "m"]}
                  }
                }
              },
              "argalias": {"type": "array"}
            }
          },
          "roles": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["n", "f", "descr"],
              "properties": {
                "n": {
                  "type": "string",
                  "pattern": "^([0-7]|A|M)$",
                  "description": "Argument number"
                },
                "f": {
                  "type": "string",
                  "description": "Function tag"
                },
                "descr": {"type": "string"},
                "rolelinks": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "class_name": {"type": "string"},
                      "resource": {"type": "string"},
                      "version": {"type": "string"},
                      "role": {"type": "string"}
                    }
                  }
                }
              }
            }
          },
          "examples": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["text"],
              "properties": {
                "name": {"type": ["string", "null"]},
                "text": {"type": "string"},
                "propbank": {
                  "type": "object",
                  "properties": {
                    "args": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "type": {"type": "string"},
                          "start": {"type": ["integer", "string"]},
                          "end": {"type": ["integer", "string"]},
                          "text": {"type": "string"}
                        }
                      }
                    },
                    "rel": {
                      "type": "object",
                      "properties": {
                        "relloc": {"type": "string"},
                        "text": {"type": "string"}
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    },
    "notes": {"type": "array", "items": {"type": "string"}}
  }
}
```

**Example Entry**:

```json
{
  "predicate_lemma": "give",
  "rolesets": [
    {
      "id": "give.01",
      "name": "transfer",
      "aliases": {
        "alias": [
          {"text": "giving", "pos": "n"},
          {"text": "give", "pos": "v"}
        ],
        "argalias": []
      },
      "roles": [
        {
          "n": "0",
          "f": "PAG",
          "descr": "giver",
          "rolelinks": [
            {"class_name": "give-13.1-1", "resource": "VerbNet", "version": "verbnet3.4", "role": "agent"},
            {"class_name": "Giving", "resource": "FrameNet", "version": "1.7", "role": "donor"}
          ]
        },
        {
          "n": "1",
          "f": "PPT",
          "descr": "thing given",
          "rolelinks": [
            {"class_name": "give-13.1-1", "resource": "VerbNet", "version": "verbnet3.4", "role": "theme"},
            {"class_name": "Giving", "resource": "FrameNet", "version": "1.7", "role": "theme"}
          ]
        },
        {
          "n": "2",
          "f": "GOL",
          "descr": "entity given to",
          "rolelinks": [
            {"class_name": "give-13.1-1", "resource": "VerbNet", "version": "verbnet3.4", "role": "recipient"},
            {"class_name": "Giving", "resource": "FrameNet", "version": "1.7", "role": "recipient"}
          ]
        }
      ],
      "examples": [
        {
          "name": "give-v: double object",
          "text": "The executives gave the chefs a standing ovation.",
          "propbank": {
            "args": [
              {"type": "ARG0", "start": 0, "end": 1, "text": "The executives"},
              {"type": "ARG2", "start": 3, "end": 4, "text": "the chefs"},
              {"type": "ARG1", "start": 5, "end": 7, "text": "a standing ovation"}
            ],
            "rel": {"relloc": "2", "text": "gave"}
          }
        }
      ]
    }
  ]
}
```

### WordNet

**JSON Schema**:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["offset", "lex_filenum", "lex_filename", "ss_type", "words", "pointers", "gloss"],
  "properties": {
    "offset": {
      "type": "string",
      "pattern": "^\\d{8}$",
      "description": "8-digit synset identifier"
    },
    "lex_filenum": {
      "type": "integer",
      "minimum": 0,
      "maximum": 44
    },
    "lex_filename": {
      "type": "string",
      "description": "Lexical file name (e.g., 'verb.perception')"
    },
    "ss_type": {
      "type": "string",
      "enum": ["n", "v", "a", "r", "s"],
      "description": "Synset type"
    },
    "words": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["lemma", "lex_id"],
        "properties": {
          "lemma": {"type": "string"},
          "lex_id": {
            "type": "integer",
            "minimum": 0,
            "maximum": 15
          }
        }
      }
    },
    "pointers": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["symbol", "offset", "pos", "source", "target"],
        "properties": {
          "symbol": {"type": "string"},
          "offset": {"type": "string", "pattern": "^\\d{8}$"},
          "pos": {"type": "string", "enum": ["n", "v", "a", "r", "s"]},
          "source": {"type": "integer", "minimum": 0},
          "target": {"type": "integer", "minimum": 0}
        }
      }
    },
    "frames": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "frame_number": {"type": "integer", "minimum": 1, "maximum": 35},
          "word_indices": {"type": "array", "items": {"type": "integer"}}
        }
      }
    },
    "gloss": {
      "type": "string",
      "description": "Definition and examples"
    }
  }
}
```

**Example Entry**:

```json
{
  "offset": "02204104",
  "lex_filenum": 40,
  "lex_filename": "verb.perception",
  "ss_type": "v",
  "words": [
    {"lemma": "give", "lex_id": 0}
  ],
  "pointers": [
    {"symbol": ">", "offset": "02208144", "pos": "v", "source": 0, "target": 0},
    {"symbol": "@", "offset": "02225243", "pos": "v", "source": 0, "target": 0},
    {"symbol": "+", "offset": "10045455", "pos": "n", "source": 1, "target": 2}
  ],
  "frames": [],
  "gloss": "transfer possession of something concrete or abstract to somebody; \"I gave her my money\"; \"can you give me lessons?\"; \"She gave the children lots of love and tender loving care\""
}
```

### FrameNet

**JSON Schema**:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["id", "name", "definition", "frame_elements"],
  "properties": {
    "id": {
      "type": "integer",
      "minimum": 1,
      "description": "Unique frame identifier"
    },
    "name": {
      "type": "string",
      "pattern": "^[A-Z][A-Za-z0-9_]*$",
      "description": "Frame name (e.g., 'Giving')"
    },
    "definition": {
      "type": "object",
      "properties": {
        "raw_text": {"type": "string"},
        "plain_text": {"type": "string"},
        "annotations": {"type": "array"}
      }
    },
    "frame_elements": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name", "abbrev", "definition", "core_type", "bg_color", "fg_color"],
        "properties": {
          "id": {"type": "integer", "minimum": 1},
          "name": {
            "type": "string",
            "pattern": "^[A-Z][A-Za-z0-9_]*$"
          },
          "abbrev": {
            "type": "string",
            "pattern": "^[A-Z][A-Za-z0-9]{0,4}$"
          },
          "definition": {
            "type": "object",
            "properties": {
              "raw_text": {"type": "string"},
              "plain_text": {"type": "string"},
              "annotations": {"type": "array"}
            }
          },
          "core_type": {
            "type": "string",
            "enum": ["Core", "Core-Unexpressed", "Peripheral", "Extra-Thematic"]
          },
          "bg_color": {
            "type": "string",
            "pattern": "^[0-9A-F]{6}$"
          },
          "fg_color": {
            "type": "string",
            "pattern": "^[0-9A-F]{6}$"
          },
          "requires_fe": {"type": "array", "items": {"type": "string"}},
          "excludes_fe": {"type": "array", "items": {"type": "string"}},
          "semtype_refs": {"type": "array", "items": {"type": "integer"}}
        }
      }
    },
    "lexical_units": {"type": "array"},
    "frame_relations": {"type": "array"},
    "created_by": {"type": ["string", "null"]},
    "created_date": {"type": ["string", "null"], "format": "date-time"}
  }
}
```

**Example Entry**:

```json
{
  "id": 139,
  "name": "Giving",
  "definition": {
    "plain_text": "A Donor transfers a Theme from a Donor to a Recipient. This frame includes only actions that are initiated by the Donor (the one that starts out owning the Theme). Sentences (even metaphorical ones) must meet the following entailments: the Donor first has possession of the Theme. Following the transfer the Donor no longer has the Theme and the Recipient does. Barney gave the beer to Moe. $300 was endowed to the university to build a new performing arts building."
  },
  "frame_elements": [
    {
      "id": 1052,
      "name": "Donor",
      "abbrev": "Donor",
      "definition": {
        "plain_text": "The person that begins in possession of the Theme and causes it to be in the possession of the Recipient."
      },
      "core_type": "Core",
      "bg_color": "FF0000",
      "fg_color": "FFFFFF"
    },
    {
      "id": 1053,
      "name": "Recipient",
      "abbrev": "Rec",
      "definition": {
        "plain_text": "The entity that ends up in possession of the Theme."
      },
      "core_type": "Core",
      "bg_color": "0000FF",
      "fg_color": "FFFFFF"
    },
    {
      "id": 1054,
      "name": "Theme",
      "abbrev": "Thm",
      "definition": {
        "plain_text": "The object that changes ownership."
      },
      "core_type": "Core",
      "bg_color": "9400D3",
      "fg_color": "FFFFFF"
    }
  ],
  "lexical_units": [],
  "frame_relations": [],
  "created_by": "MJE",
  "created_date": "2001-06-23T08:15:16Z"
}
```

## Source Formats

### XML Sources

VerbNet, PropBank, and FrameNet use XML format:

**VerbNet Example** (give-13.1.xml):
```xml
<!DOCTYPE VNCLASS SYSTEM "vn_class-3.dtd">
<VNCLASS ID="give-13.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="vn_schema-3.xsd">
  <MEMBERS>
    <MEMBER fn_mapping="None" grouping="deal.04" name="deal" verbnet_key="deal#2" wn="deal%2:40:01 deal%2:40:02 deal%2:40:07 deal%2:40:06" features=""/>
    <MEMBER fn_mapping="None" grouping="lend.02" name="lend" verbnet_key="lend#1" wn="lend%2:40:00" features=""/>
    <MEMBER fn_mapping="Giving" grouping="pass.04" name="pass" verbnet_key="pass#3" wn="pass%2:40:00 pass%2:40:01 pass%2:40:13 pass%2:38:04" features=""/>
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
        <!-- ... more syntax elements ... -->
      </SYNTAX>
    </FRAME>
  </FRAMES>
</VNCLASS>
```

**PropBank Example** (give.xml):
```xml
<?xml version="1.0" encoding="utf-8" standalone="no"?>
<!DOCTYPE frameset PUBLIC "-//PB//PropBank Frame v3.4 Transitional//EN" "http://propbank.org/specification/dtds/v3.4/frameset.dtd">
<frameset>
  <predicate lemma="give">
    <roleset id="give.01" name="transfer">
      <aliases>
        <alias pos="n">giving</alias>
        <alias pos="v">give</alias>
      </aliases>
      <roles>
        <role descr="giver" f="PAG" n="0">
          <rolelinks>
            <rolelink class="give-13.1-1" resource="VerbNet" version="verbnet3.4">agent</rolelink>
            <rolelink class="Giving" resource="FrameNet" version="1.7">donor</rolelink>
          </rolelinks>
        </role>
        <role descr="thing given" f="PPT" n="1">
          <rolelinks>
            <rolelink class="give-13.1-1" resource="VerbNet" version="verbnet3.4">theme</rolelink>
            <rolelink class="Giving" resource="FrameNet" version="1.7">theme</rolelink>
          </rolelinks>
        </role>
        <role descr="entity given to" f="GOL" n="2">
          <rolelinks>
            <rolelink class="give-13.1-1" resource="VerbNet" version="verbnet3.4">recipient</rolelink>
            <rolelink class="Giving" resource="FrameNet" version="1.7">recipient</rolelink>
          </rolelinks>
        </role>
      </roles>
      <example name="give-v: double object" src="">
        <text>The executives gave the chefs a standing ovation.</text>
        <propbank>
          <rel relloc="2">gave</rel>
          <arg type="ARG0" start="0" end="1">The executives</arg>
          <arg type="ARG2" start="3" end="4">the chefs</arg>
          <arg type="ARG1" start="5" end="7">a standing ovation</arg>
        </propbank>
      </example>
    </roleset>
  </predicate>
</frameset>
```

**FrameNet Example** (Giving.xml):
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<frame cBy="MJE" cDate="06/23/2001 08:15:16 PDT Sat" name="Giving" ID="139" xmlns="http://framenet.icsi.berkeley.edu">
  <definition>&lt;def-root&gt;A &lt;fen&gt;Donor&lt;/fen&gt; transfers a &lt;fen&gt;Theme&lt;/fen&gt; from a &lt;fen&gt;Donor&lt;/fen&gt; to a &lt;fen&gt;Recipient&lt;/fen&gt;.
  This frame includes only actions that are initiated by the &lt;fen&gt;Donor&lt;/fen&gt; (the one that starts out owning the &lt;fen&gt;Theme&lt;/fen&gt;).&lt;/def-root&gt;</definition>
  <FE bgColor="FF0000" fgColor="FFFFFF" coreType="Core" cBy="MJE" cDate="06/23/2001 08:17:21 PDT Sat" abbrev="Donor" name="Donor" ID="1052">
    <definition>&lt;def-root&gt;The person that begins in possession of the &lt;fen&gt;Theme&lt;/fen&gt; and causes it to be in the possession of the &lt;fen&gt;Recipient&lt;/fen&gt;.&lt;/def-root&gt;</definition>
  </FE>
  <FE bgColor="0000FF" fgColor="FFFFFF" coreType="Core" cBy="MJE" cDate="06/23/2001 08:18:41 PDT Sat" abbrev="Rec" name="Recipient" ID="1053">
    <definition>&lt;def-root&gt;The entity that ends up in possession of the &lt;fen&gt;Theme&lt;/fen&gt;.&lt;/def-root&gt;</definition>
  </FE>
  <FE bgColor="9400D3" fgColor="FFFFFF" coreType="Core" cBy="MJE" cDate="06/23/2001 08:19:30 PDT Sat" abbrev="Thm" name="Theme" ID="1054">
    <definition>&lt;def-root&gt;The object that changes ownership.&lt;/def-root&gt;</definition>
    <semType name="Physical_object" ID="68"/>
  </FE>
  <!-- ... more frame elements ... -->
</frame>
```

### WordNet Database Format

WordNet uses a custom text-based database format (data.verb):

```
00675490 31 v 01 give 0 001 @ 00674352 v 0000 01 + 14 00 | estimate the duration or outcome of something; "He gave the patient three months to live"; "I gave him a very good chance at success"
00734247 31 v 03 give 2 pay 0 devote 0 002 @ 00630153 v 0000 $ 02348591 v 0000 02 + 15 00 + 21 00 | dedicate; "give thought to"; "give priority to"; "pay attention to"
00750978 32 v 01 give 7 001 @ 00803980 v 0000 01 + 15 00 | allow to have or take; "I give you two minutes to respond"
```

Each line contains: synset offset, lexical file number, synset type, word count, words with lexical IDs, pointer count, pointers, and gloss.
