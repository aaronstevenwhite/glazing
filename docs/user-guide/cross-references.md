# Cross-References

Guide to working with cross-references between datasets.

## Overview

Glazing provides tools to find connections between FrameNet, PropBank, VerbNet, and WordNet.

## Reference Types

### PropBank → VerbNet

PropBank rolesets map to VerbNet classes:

```python
# PropBank: give.01 → VerbNet: give-13.1
```

### VerbNet → WordNet

VerbNet members link to WordNet senses:

```python
# VerbNet: give (member) → WordNet: give%2:40:00::
```

### FrameNet → WordNet

FrameNet lexical units reference WordNet:

```python
# FrameNet: give.v → WordNet: give%2:40:00::
```

## Using References

### CLI

```bash
# Find all references for a PropBank roleset
glazing search cross-ref --source propbank --id "give.01" \
    --target all --data-dir ~/.local/share/glazing/converted

# Find VerbNet classes for PropBank
glazing search cross-ref --source propbank --id "give.01" \
    --target verbnet --data-dir ~/.local/share/glazing/converted
```

### Python API

```python
from glazing.references.extractor import ReferenceExtractor
from glazing.references.resolver import ReferenceResolver
from pathlib import Path

data_dir = Path.home() / ".local/share/glazing/converted"

# Extract all references
extractor = ReferenceExtractor()
references = extractor.extract_from_datasets(data_dir)

# Resolve for specific item
resolver = ReferenceResolver(references)
related = resolver.resolve("give.01", source="propbank")

print(f"VerbNet: {related.verbnet_classes}")
print(f"WordNet: {related.wordnet_senses}")
print(f"FrameNet: {related.framenet_frames}")
```

## Reference Extraction

### Automatic Extraction

```python
from glazing.references.extractor import ReferenceExtractor

extractor = ReferenceExtractor()

# Extract from all datasets
all_refs = extractor.extract_from_datasets(data_dir)

# Extract from specific dataset
vn_refs = extractor.extract_from_verbnet(verb_classes)
```

### Manual Mapping

```python
from glazing.references.mapper import ReferenceMapper

mapper = ReferenceMapper()

# Map PropBank to VerbNet
vn_classes = mapper.propbank_to_verbnet("give.01")

# Map VerbNet to WordNet
wn_senses = mapper.verbnet_to_wordnet("give-13.1")
```

## Reference Resolution

### Simple Resolution

```python
resolver = ReferenceResolver(references)

# Get all related items
related = resolver.resolve("give.01", source="propbank")
```

### Transitive Resolution

```python
# Follow chains of references
# PropBank → VerbNet → WordNet
chain = resolver.resolve_transitive("give.01", source="propbank")
```

### Batch Resolution

```python
rolesets = ["give.01", "take.01", "run.02"]

results = {}
for roleset in rolesets:
    results[roleset] = resolver.resolve(roleset, source="propbank")
```

## Examples

### Finding Semantic Equivalents

```python
def find_semantic_equivalents(word):
    # Search all datasets
    search = UnifiedSearch()
    results = search.search_by_lemma(word)

    # Group by dataset
    by_dataset = {}
    for result in results:
        if result.dataset not in by_dataset:
            by_dataset[result.dataset] = []
        by_dataset[result.dataset].append(result)

    return by_dataset

equivalents = find_semantic_equivalents("give")
```

### Building Reference Graph

```python
import networkx as nx

def build_reference_graph(references):
    G = nx.Graph()

    for ref in references:
        # Add nodes
        G.add_node(ref.source_id, dataset=ref.source)
        G.add_node(ref.target_id, dataset=ref.target)

        # Add edge
        G.add_edge(ref.source_id, ref.target_id)

    return G
```

### Cross-Dataset Analysis

```python
def analyze_coverage(lemma):
    search = UnifiedSearch()
    resolver = ReferenceResolver(references)

    # Find in each dataset
    coverage = {
        'propbank': False,
        'verbnet': False,
        'wordnet': False,
        'framenet': False
    }

    results = search.search_by_lemma(lemma)

    for result in results:
        coverage[result.dataset] = True

        # Check cross-references
        related = resolver.resolve(result.id, source=result.dataset)
        for dataset in coverage:
            if getattr(related, f"{dataset}_ids"):
                coverage[dataset] = True

    return coverage
```

## Reference Data Model

```python
@dataclass
class Reference:
    source: str          # Source dataset
    source_id: str       # ID in source
    target: str          # Target dataset
    target_id: str       # ID in target
    confidence: float    # Match confidence

@dataclass
class ResolvedReferences:
    source_id: str
    propbank_ids: list[str]
    verbnet_classes: list[str]
    wordnet_senses: list[str]
    framenet_frames: list[str]
```

## Best Practices

1. **Cache references**: Extract once and reuse
2. **Validate IDs**: Check IDs exist before resolving
3. **Handle missing**: Not all items have cross-references
4. **Consider confidence**: Some matches are approximate
5. **Use batch operations**: Resolve multiple items together

## Limitations

- Not all entries have cross-references
- Some references may be approximate matches
- Reference quality varies by dataset pair
- Transitive references may introduce noise
