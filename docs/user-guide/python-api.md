# Python API

After running `glazing init`, you can use the Python API to work with the linguistic datasets.

## Basic Usage

The simplest entry point is unified search, which queries all datasets at once:

```python
from glazing.search import UnifiedSearch

search = UnifiedSearch()
results = search.search("abandon")

# Filter by part of speech
verb_results = search.by_lemma("run", pos="v")
```

## Loading Individual Datasets

Each dataset has its own loader that provides access to the full data:

```python
from glazing.verbnet.loader import VerbNetLoader
from glazing.wordnet.loader import WordNetLoader

# Loaders automatically find and load data from the default location
vn_loader = VerbNetLoader()
verb_classes = list(vn_loader.classes.values())

wn_loader = WordNetLoader()
synsets = list(wn_loader.synsets.values())
```

The loaders handle the JSON Lines format transparently. For large datasets, you can iterate instead of loading everything into memory:

```python
loader = VerbNetLoader()
for verb_class in loader.iter_verb_classes():
    if "run" in [m.name for m in verb_class.members]:
        print(f"Found in class: {verb_class.id}")
        break
```

## Data Models

All data structures are Pydantic models with full type hints and validation. This gives you IDE autocomplete, type checking with mypy, and automatic JSON serialization:

```python
from glazing.verbnet.models import Member

member = Member(name="run", grouping="run.01")
print(member.name)  # IDE knows this is a string

# Export to various formats
data_dict = member.model_dump()
json_str = member.model_dump_json()
```

## Searching Within Datasets

Each dataset has specialized search capabilities beyond simple text matching. VerbNet lets you search by thematic roles or syntactic patterns:

```python
from glazing.verbnet.search import VerbNetSearch
from glazing.verbnet.loader import VerbNetLoader

loader = VerbNetLoader()
search = VerbNetSearch(list(loader.classes.values()))

# Find classes with specific thematic roles
agent_classes = search.by_themroles(["Agent", "Theme"])

# Find by syntactic pattern
motion_classes = search.by_syntax("NP V PP")
```

## Cross-References

Cross-references between datasets require extraction before use. This scans the data for embedded references and builds an index:

```python
from glazing.references.extractor import ReferenceExtractor
from glazing.references.resolver import ReferenceResolver

# Extract references (expensive operation, do once)
extractor = ReferenceExtractor()
extractor.extract_verbnet_references(verb_classes)
extractor.extract_propbank_references(framesets)

# Resolve references (fast lookup)
resolver = ReferenceResolver(extractor.mapping_index)
related = resolver.resolve("give.01", source="propbank")
```

## Integration with NLP Tools

The standardized data models make it easy to integrate with other NLP libraries. For spaCy:

```python
import spacy
from glazing.search import UnifiedSearch

nlp = spacy.load("en_core_web_sm")
search = UnifiedSearch()

doc = nlp("The dog ran quickly")
for token in doc:
    if token.pos_ == "VERB":
        results = search.by_lemma(token.lemma_, pos="v")
        # Use results to enhance token with frame information
```

For pandas users, the models convert cleanly to DataFrames:

```python
import pandas as pd

synset_data = [
    {
        'id': s.id,
        'pos': s.pos,
        'definition': s.definition,
        'lemmas': ', '.join([l.lemma for l in s.lemmas])
    }
    for s in synsets[:100]
]
df = pd.DataFrame(synset_data)
```

## Error Handling

The most common error is missing data files. The loaders raise clear exceptions:

```python
from glazing.framenet.loader import FrameNetLoader

try:
    loader = FrameNetLoader()
except FileNotFoundError:
    print("Run 'glazing init' first to download the data")
```

Validation errors from Pydantic show exactly what went wrong:

```python
from pydantic import ValidationError
from glazing.verbnet.models import Member

try:
    member = Member(name="")  # Invalid: empty name
except ValidationError as e:
    print(e)  # Shows field name and constraint violated
```

## Performance Considerations

The loaders cache data in memory after the first access. If you're processing large datasets, use iteration instead of loading everything at once. For repeated searches, consider caching results or using the built-in cache decorators in `glazing.utils.cache`.

## Further Reading

See the [API Reference](../api/index.md) for detailed documentation of all classes and methods.
