# Quick Start

Get up and running with Glazing in minutes. This guide assumes you've already [installed](installation.md) the package.

## Initialize Datasets

Start by downloading and converting all datasets:

```bash
glazing init
```

This one-time setup downloads ~120MB of data and prepares it for use.

## CLI Usage

### Search for a Word

Find entries across all datasets:

```bash
# Search for "give" in all datasets
glazing search query "give" --data-dir ~/.local/share/glazing/converted

# Search only in VerbNet
glazing search query "give" --dataset verbnet --data-dir ~/.local/share/glazing/converted

# Get JSON output
glazing search query "give" --json --data-dir ~/.local/share/glazing/converted
```

### Find Cross-References

Discover connections between datasets:

```bash
# Find VerbNet classes for a PropBank roleset
glazing search cross-ref --source propbank --target verbnet --id "give.01" \
    --data-dir ~/.local/share/glazing/converted
```

### Get Dataset Information

Learn about available datasets:

```bash
# List all datasets
glazing download list

# Get info about VerbNet
glazing download info verbnet
```

## Python API Usage

### Basic Search

```python
from glazing.search import UnifiedSearch
from pathlib import Path

# Initialize search with default data directory
search = UnifiedSearch()

# Search across all datasets
results = search.search_by_query("abandon")

for result in results[:5]:
    print(f"{result.dataset}: {result.name}")
    print(f"  Type: {result.type}")
    print(f"  Description: {result.description[:100]}...")
    print()
```

### Load Individual Datasets

```python
from glazing.framenet.loader import FrameNetLoader
from glazing.verbnet.loader import VerbNetLoader
from pathlib import Path

data_dir = Path.home() / ".local/share/glazing/converted"

# Load FrameNet
fn_loader = FrameNetLoader()
frames = fn_loader.load_frames(data_dir / "framenet.jsonl")
print(f"Loaded {len(frames)} frames")

# Load VerbNet
vn_loader = VerbNetLoader()
verb_classes = vn_loader.load_verb_classes(data_dir / "verbnet.jsonl")
print(f"Loaded {len(verb_classes)} verb classes")
```

### Work with VerbNet Classes

```python
from glazing.verbnet.loader import VerbNetLoader
from pathlib import Path

data_dir = Path.home() / ".local/share/glazing/converted"
loader = VerbNetLoader()

# Load all verb classes
classes = loader.load_verb_classes(data_dir / "verbnet.jsonl")

# Find a specific class
give_class = next(
    (vc for vc in classes if vc.id == "give-13.1"),
    None
)

if give_class:
    print(f"Class: {give_class.id}")
    print(f"Members: {[m.name for m in give_class.members[:5]]}")
    print(f"Thematic Roles: {[tr.role_type for tr in give_class.themroles]}")

    # Examine frames
    for frame in give_class.frames[:2]:
        print(f"\nFrame: {frame.description.primary}")
        print(f"  Example: {frame.examples[0] if frame.examples else 'N/A'}")
```

### Work with PropBank

```python
from glazing.propbank.loader import PropBankLoader
from pathlib import Path

data_dir = Path.home() / ".local/share/glazing/converted"
loader = PropBankLoader()

# Load framesets
framesets = loader.load_framesets(data_dir / "propbank.jsonl")

# Find rolesets for "give"
give_framesets = [fs for fs in framesets if fs.lemma == "give"]

for frameset in give_framesets:
    print(f"Frameset: {frameset.lemma}")
    for roleset in frameset.rolesets:
        print(f"  Roleset: {roleset.id} - {roleset.name}")
        for role in roleset.roles:
            print(f"    {role.argnum}: {role.description}")
```

### Cross-Reference Resolution

```python
from glazing.references.extractor import ReferenceExtractor
from glazing.references.resolver import ReferenceResolver
from pathlib import Path

data_dir = Path.home() / ".local/share/glazing/converted"

# Extract all references
extractor = ReferenceExtractor()
references = extractor.extract_from_datasets(data_dir)

# Resolve references for a PropBank roleset
resolver = ReferenceResolver(references)
related = resolver.resolve("give.01", source="propbank")

print(f"PropBank roleset: give.01")
print(f"VerbNet classes: {related.verbnet_classes}")
print(f"FrameNet frames: {related.framenet_frames}")
print(f"WordNet senses: {related.wordnet_senses}")
```

### WordNet Synsets and Relations

```python
from glazing.wordnet.loader import WordNetLoader
from pathlib import Path

data_dir = Path.home() / ".local/share/glazing/converted"
loader = WordNetLoader()

# Load synsets
synsets = loader.load_synsets(data_dir / "wordnet.jsonl")

# Find synsets for "dog"
dog_synsets = [s for s in synsets if any(
    l.lemma == "dog" for l in s.lemmas
)]

for synset in dog_synsets[:3]:
    print(f"Synset: {synset.id}")
    print(f"  POS: {synset.pos}")
    print(f"  Definition: {synset.definition}")
    print(f"  Lemmas: {[l.lemma for l in synset.lemmas]}")

    # Show hypernyms
    if synset.relations:
        hypernyms = [r for r in synset.relations if r.type == "hypernym"]
        if hypernyms:
            print(f"  Hypernyms: {[h.target_id for h in hypernyms]}")
```

### Streaming Large Files

For memory-efficient processing:

```python
from glazing.verbnet.loader import VerbNetLoader
from pathlib import Path

data_dir = Path.home() / ".local/share/glazing/converted"
loader = VerbNetLoader()

# Stream verb classes one at a time
for verb_class in loader.stream_verb_classes(data_dir / "verbnet.jsonl"):
    # Process each class without loading all into memory
    if "run" in [m.name for m in verb_class.members]:
        print(f"Found 'run' in class: {verb_class.id}")
        break
```

## Common Patterns

### Find Semantic Roles

```python
from glazing.verbnet.search import VerbNetSearch
from pathlib import Path

data_dir = Path.home() / ".local/share/glazing/converted"
search = VerbNetSearch(data_dir / "verbnet.jsonl")

# Find all classes with an Agent role
agent_classes = []
for vc in search.verb_classes:
    if any(tr.role_type == "Agent" for tr in vc.themroles):
        agent_classes.append(vc.id)

print(f"Classes with Agent role: {len(agent_classes)}")
```

### Export to Custom Format

```python
import json
from glazing.framenet.loader import FrameNetLoader
from pathlib import Path

data_dir = Path.home() / ".local/share/glazing/converted"
loader = FrameNetLoader()

# Load frames
frames = loader.load_frames(data_dir / "framenet.jsonl")

# Export as simple JSON
simple_frames = []
for frame in frames[:10]:
    simple_frames.append({
        "id": frame.id,
        "name": frame.name,
        "definition": frame.definition.plain_text if frame.definition else "",
        "frame_elements": [fe.name for fe in frame.frame_elements]
    })

# Save to file
with open("frames_simple.json", "w") as f:
    json.dump(simple_frames, f, indent=2)
```

## Next Steps

- Explore the [CLI documentation](user-guide/cli.md) for advanced command-line usage
- Read the [Python API guide](user-guide/python-api.md) for detailed programming examples
- Check the [API Reference](api/index.md) for complete documentation
- Learn about [cross-references](user-guide/cross-references.md) between datasets
