# Data Formats

Understanding the data formats used by Glazing.

## JSON Lines Format

Glazing uses JSON Lines (.jsonl) as its primary format:

- One JSON object per line
- Each line is a complete, valid JSON object
- Efficient for streaming and partial reading
- Human-readable and debuggable

### Example

```json
{"id": "give-13.1", "name": "give", "members": [...], "themroles": [...]}
{"id": "take-10.5", "name": "take", "members": [...], "themroles": [...]}
```

## Dataset Schemas

### VerbNet

```json
{
  "id": "give-13.1",
  "members": [
    {"name": "give", "grouping": "give.01"}
  ],
  "themroles": [
    {"role_type": "Agent", "sel_restrictions": [...]}
  ],
  "frames": [
    {
      "description": {"primary": "NP V NP PP"},
      "examples": ["John gave Mary a book"],
      "syntax": [...],
      "semantics": [...]
    }
  ]
}
```

### PropBank

```json
{
  "lemma": "give",
  "rolesets": [
    {
      "id": "give.01",
      "name": "transfer",
      "roles": [
        {"argnum": "0", "description": "giver"},
        {"argnum": "1", "description": "thing given"},
        {"argnum": "2", "description": "recipient"}
      ]
    }
  ]
}
```

### WordNet

```json
{
  "id": "02316649-v",
  "pos": "verb",
  "lemmas": [
    {"lemma": "give", "sense_key": "give%2:40:00::"}
  ],
  "definition": "transfer possession of something",
  "relations": [
    {"type": "hypernym", "target_id": "02316050-v"}
  ]
}
```

### FrameNet

```json
{
  "id": 139,
  "name": "Giving",
  "definition": "A DONOR transfers a THEME to a RECIPIENT",
  "frame_elements": [
    {"name": "Donor", "abbrev": "Dnr", "core_type": "Core"},
    {"name": "Theme", "abbrev": "Thm", "core_type": "Core"},
    {"name": "Recipient", "abbrev": "Rec", "core_type": "Core"}
  ]
}
```

## Source Formats

### XML Sources

Original datasets use XML:

```xml
<!-- VerbNet -->
<VNCLASS ID="give-13.1">
  <MEMBERS>
    <MEMBER name="give"/>
  </MEMBERS>
</VNCLASS>

<!-- PropBank -->
<frameset id="give.01">
  <roles>
    <role descr="giver" n="0"/>
  </roles>
</frameset>
```

### WordNet Database

WordNet uses custom database format:

```
02316649 40 v 04 give 0 transfer 0 hand 0 pass_on 0 019 ...
```

## Conversion Process

1. **Parse**: Read source format (XML, database)
2. **Validate**: Check data integrity
3. **Transform**: Convert to Pydantic models
4. **Serialize**: Write as JSON Lines

## Benefits

### JSON Lines vs JSON

- **Streaming**: Read line by line
- **Append-only**: Easy to add data
- **Parallel processing**: Process lines independently
- **Error recovery**: Skip bad lines

### JSON Lines vs XML

- **Simpler**: No complex parsing required
- **Smaller**: More compact representation
- **Faster**: Direct to Python objects
- **Type-safe**: With Pydantic validation

## Working with Data

### Reading

```python
import json
from pathlib import Path

# Read entire file
with open("verbnet.jsonl") as f:
    data = [json.loads(line) for line in f]

# Stream line by line
with open("verbnet.jsonl") as f:
    for line in f:
        obj = json.loads(line)
        process(obj)
```

### Writing

```python
import json

data = [{"id": 1}, {"id": 2}]

with open("output.jsonl", "w") as f:
    for obj in data:
        f.write(json.dumps(obj) + "\n")
```

### Validation

```python
from glazing.verbnet.models import VerbClass

with open("verbnet.jsonl") as f:
    for line in f:
        data = json.loads(line)
        verb_class = VerbClass(**data)  # Validates automatically
```

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
