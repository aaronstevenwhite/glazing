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

# Initialize search (automatically uses default data directory)
search = UnifiedSearch()

# Search across all datasets
results = search.search("abandon")

# Search with filters
results = search.search("run")

# Search by lemma with POS filter
results = search.by_lemma("run", pos="v")
```

### Loading Datasets

```python
from glazing.framenet.loader import FrameNetLoader
from glazing.propbank.loader import PropBankLoader
from glazing.verbnet.loader import VerbNetLoader
from glazing.wordnet.loader import WordNetLoader

# All loaders automatically use default paths and load data after 'glazing init'
fn_loader = FrameNetLoader()  # Data is already loaded
frames = fn_loader.frames

pb_loader = PropBankLoader()  # Data is already loaded
framesets = list(pb_loader.framesets.values())

vn_loader = VerbNetLoader()  # Data is already loaded
verb_classes = list(vn_loader.classes.values())

wn_loader = WordNetLoader()  # Data is already loaded
synsets = list(wn_loader.synsets.values())
```

## Advanced Features

### Streaming Large Files

```python
from glazing.verbnet.loader import VerbNetLoader

loader = VerbNetLoader()  # Automatically uses default path
# Process one at a time without loading all into memory
for verb_class in loader.iter_verb_classes():
    if "run" in [m.name for m in verb_class.members]:
        print(f"Found in: {verb_class.id}")
        break
```

### Cross-Reference Resolution

```python
from glazing.references.extractor import ReferenceExtractor
from glazing.references.resolver import ReferenceResolver
from glazing.initialize import get_default_data_path

# Extract references (uses default data directory)
extractor = ReferenceExtractor()
references = extractor.extract_from_datasets(get_default_data_path())

# Resolve for a specific item
resolver = ReferenceResolver(references)
related = resolver.resolve("give.01", source="propbank")
```

### Custom Searching

```python
from glazing.verbnet.search import VerbNetSearch
from glazing.verbnet.loader import VerbNetLoader
from glazing.verbnet.types import ThematicRoleType

# Loader automatically loads data
loader = VerbNetLoader()
verb_classes = list(loader.classes.values())  # Already loaded

# Initialize search with loaded data
search = VerbNetSearch(verb_classes)

# Find by members
classes = search.by_members(["run"])

# Find by thematic roles
agent_classes = search.by_themroles([ThematicRoleType.AGENT])

# Find by syntax pattern
motion_classes = search.by_syntax("NP V PP")
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
from glazing.framenet.loader import FrameNetLoader

try:
    loader = FrameNetLoader()  # Automatically loads data
    frames = loader.frames
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
    all_results[lemma] = search.by_lemma(lemma)
```

### Memory Management

```python
# Use generators for large datasets
def process_large_dataset():
    loader = VerbNetLoader()  # Automatically loads data
    for batch in loader.iter_verb_classes():
        for verb_class in batch:
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
    results = search.search(query)
    return jsonify([r.__dict__ for r in results[:10]])
```

### Pandas DataFrames

```python
import pandas as pd
from glazing.wordnet.loader import WordNetLoader

loader = WordNetLoader()  # Automatically loads data
synsets = list(loader.synsets.values())

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
            results = search.by_lemma(token.lemma_, pos="v")
            enriched.append({
                'token': token.text,
                'lemma': token.lemma_,
                'frames': [r.frames[0].name if r.frames else "" for r in results[:3]]
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
