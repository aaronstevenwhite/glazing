# Cross-References

Glazing connects FrameNet, PropBank, VerbNet, and WordNet through their internal cross-references. While these connections exist in the original datasets, extracting and using them typically requires understanding each dataset's format. Glazing provides a unified interface to work with these references.

## How References Work

The four datasets reference each other in different ways. PropBank rolesets often specify their corresponding VerbNet classes. VerbNet members include WordNet sense keys. FrameNet lexical units sometimes reference WordNet synsets. These connections allow you to trace a concept across different linguistic representations.

For example, the PropBank roleset `give.01` maps to VerbNet class `give-13.1`, which contains members linked to WordNet senses like `give%2:40:00::`. This lets you connect PropBank's argument structure to VerbNet's thematic roles and WordNet's semantic hierarchy.

## Basic Usage

The simplest way to find cross-references is through the CLI:

```bash
# Find what VerbNet classes correspond to a PropBank roleset
glazing search cross-ref --source propbank --id "give.01" --target verbnet
```

In Python, the process requires extracting references from the loaded datasets:

```python
from glazing.references.extractor import ReferenceExtractor
from glazing.references.resolver import ReferenceResolver
from glazing.verbnet.loader import VerbNetLoader
from glazing.propbank.loader import PropBankLoader

# Load and extract references
vn_loader = VerbNetLoader()
pb_loader = PropBankLoader()

extractor = ReferenceExtractor()
extractor.extract_verbnet_references(list(vn_loader.classes.values()))
extractor.extract_propbank_references(list(pb_loader.framesets.values()))

# Resolve references
resolver = ReferenceResolver(extractor.mapping_index)
related = resolver.resolve("give.01", source="propbank")
print(f"VerbNet classes: {related.verbnet_classes}")
```

## Working with References

The extraction step scans the datasets for embedded cross-references and builds an index. This is computationally expensive, so you'll want to do it once and reuse the results. The resolver then uses this index to find connections between datasets.

When you resolve references for an item, you get back all the related items across datasets. Not every item has cross-references to all other datasets. Some connections are direct (explicitly stated in the data) while others are transitive (following chains of references).

## Practical Examples

To find semantic equivalents across datasets, search each one and collect the results:

```python
from glazing.search import UnifiedSearch

search = UnifiedSearch()
results = search.search_by_lemma("give")

# Group results by dataset
by_dataset = {}
for result in results:
    by_dataset.setdefault(result.dataset, []).append(result)
```

For analyzing coverage of a concept across datasets:

```python
def check_coverage(lemma):
    search = UnifiedSearch()
    results = search.search_by_lemma(lemma)

    coverage = set(r.dataset for r in results)
    missing = {'propbank', 'verbnet', 'wordnet', 'framenet'} - coverage

    if missing:
        print(f"{lemma} not found in: {', '.join(missing)}")
    return coverage
```

## Limitations

Cross-references in these datasets are incomplete and sometimes approximate. VerbNet members don't always have WordNet mappings. PropBank rolesets may lack VerbNet mappings. The quality and coverage of references varies between dataset pairs. Transitive references (A→B→C) can introduce errors if the intermediate mapping is incorrect.

The current API requires manual extraction before resolution, which we plan to improve in future versions to match the ergonomics of the data loaders.
