# Python API

Comprehensive guide to using Glazing's Python API.

## Installation

```python
pip install glazing
```

## Basic Usage

### Unified Search

```python
from glazing.search import UnifiedSearch

# Initialize with default data directory
search = UnifiedSearch()

# Search across all datasets
results = search.search_by_query("abandon")

# Search with filters
results = search.search_by_lemma("run", pos="verb")
```

### Loading Datasets

```python
from pathlib import Path
from glazing.framenet.loader import FrameNetLoader
from glazing.propbank.loader import PropBankLoader
from glazing.verbnet.loader import VerbNetLoader
from glazing.wordnet.loader import WordNetLoader

data_dir = Path.home() / ".local/share/glazing/converted"

# Load individual datasets
fn_loader = FrameNetLoader()
frames = fn_loader.load_frames(data_dir / "framenet.jsonl")

pb_loader = PropBankLoader()
framesets = pb_loader.load_framesets(data_dir / "propbank.jsonl")

vn_loader = VerbNetLoader()
verb_classes = vn_loader.load_verb_classes(data_dir / "verbnet.jsonl")

wn_loader = WordNetLoader()
synsets = wn_loader.load_synsets(data_dir / "wordnet.jsonl")
```

## Advanced Features

### Streaming Large Files

```python
from glazing.verbnet.loader import VerbNetLoader

loader = VerbNetLoader()
# Process one at a time without loading all into memory
for verb_class in loader.stream_verb_classes(path):
    if "run" in [m.name for m in verb_class.members]:
        print(f"Found in: {verb_class.id}")
        break
```

### Cross-Reference Resolution

```python
from glazing.references.extractor import ReferenceExtractor
from glazing.references.resolver import ReferenceResolver

# Extract references
extractor = ReferenceExtractor()
references = extractor.extract_from_datasets(data_dir)

# Resolve for a specific item
resolver = ReferenceResolver(references)
related = resolver.resolve("give.01", source="propbank")
```

### Custom Searching

```python
from glazing.verbnet.search import VerbNetSearch

search = VerbNetSearch(data_dir / "verbnet.jsonl")

# Find by member
classes = search.find_by_member("run")

# Find by thematic role
agent_classes = search.find_by_themrole("Agent")

# Find by frame description
motion_frames = search.find_by_frame_description("motion")
```

## Data Models

All models use Pydantic v2 for validation:

```python
from glazing.verbnet.models import VerbClass, Member

# Models are validated
member = Member(name="run", grouping="run.01")

# Access attributes with IDE support
print(member.name)
print(member.grouping)

# Export to dict/JSON
data = member.model_dump()
json_str = member.model_dump_json()
```

## Error Handling

```python
from pydantic import ValidationError

try:
    frames = loader.load_frames(path)
except FileNotFoundError:
    print("Data not found - run 'glazing init'")
except ValidationError as e:
    print(f"Invalid data format: {e}")
```

## Performance Tips

### Use Caching

```python
from glazing.utils.cache import cached_search

# Results are cached automatically
@cached_search
def find_related(lemma):
    return search.search_by_lemma(lemma)
```

### Batch Processing

```python
# Process multiple items efficiently
lemmas = ["give", "take", "run", "walk"]
all_results = {}

for lemma in lemmas:
    all_results[lemma] = search.search_by_lemma(lemma)
```

### Memory Management

```python
# Use generators for large datasets
def process_large_dataset(path):
    loader = VerbNetLoader()
    for verb_class in loader.stream_verb_classes(path):
        yield process_class(verb_class)
```

## Integration Examples

### Flask Web API

```python
from flask import Flask, jsonify
from glazing.search import UnifiedSearch

app = Flask(__name__)
search = UnifiedSearch()

@app.route('/api/search/<query>')
def search_endpoint(query):
    results = search.search_by_query(query)
    return jsonify([r.__dict__ for r in results[:10]])
```

### Pandas DataFrames

```python
import pandas as pd
from glazing.wordnet.loader import WordNetLoader

loader = WordNetLoader()
synsets = loader.load_synsets(path)

# Convert to DataFrame
df = pd.DataFrame([
    {
        'id': s.id,
        'pos': s.pos,
        'definition': s.definition,
        'lemmas': ', '.join([l.lemma for l in s.lemmas])
    }
    for s in synsets
])
```

### NLP Pipelines

```python
import spacy
from glazing.search import UnifiedSearch

nlp = spacy.load("en_core_web_sm")
search = UnifiedSearch()

def enrich_with_frames(text):
    doc = nlp(text)
    enriched = []

    for token in doc:
        if token.pos_ == "VERB":
            results = search.search_by_lemma(token.lemma_, pos="verb")
            enriched.append({
                'token': token.text,
                'lemma': token.lemma_,
                'frames': [r.name for r in results[:3]]
            })

    return enriched
```

## Best Practices

1. **Initialize once**: Create loaders/searchers once and reuse
2. **Use type hints**: Leverage IDE support and type checking
3. **Handle errors**: Always handle file and validation errors
4. **Stream when possible**: Use streaming for large datasets
5. **Cache results**: Cache expensive operations

## API Reference

See the [API Reference](../api/index.md) for complete documentation.
