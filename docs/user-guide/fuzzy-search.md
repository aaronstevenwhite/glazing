# Fuzzy Search

Fuzzy search uses Levenshtein distance to find matches despite typos, misspellings, or partial queries.

## When to Use Fuzzy Search

Fuzzy search is useful when exact matches fail due to typos in queries, uncertain spelling, partial matches, or when searching for similar but not exact terms.

## Implementation

The system calculates Levenshtein distance between strings, measuring the minimum number of single-character edits (insertions, deletions, or substitutions) needed to transform one string into another. Text is normalized by removing accents and punctuation before comparison. Similarity scores range from 0.0 (no match) to 1.0 (exact match).

## CLI Usage

### Basic Fuzzy Search

```bash
# Enable fuzzy matching with default threshold (0.8)
glazing search query "instrment" --fuzzy

# Custom threshold (lower = more permissive)
glazing search query "giv" --fuzzy --threshold 0.6

# Combine with dataset filter
glazing search query "trasfer" --fuzzy --dataset propbank
```

### Cross-Reference Resolution

```bash
# Fuzzy match cross-references
glazing xref resolve "giv.01" --source propbank --fuzzy

# With custom threshold
glazing xref resolve "trasnsfer.01" --source propbank --fuzzy --threshold 0.7
```

## Python API

### Basic Usage

```python
from glazing.search import UnifiedSearch

search = UnifiedSearch()

# Fuzzy search with default threshold
results = search.search_with_fuzzy("instrment")

# Custom threshold
results = search.search_with_fuzzy("giv", fuzzy_threshold=0.6)

# Check match scores
for result in results[:5]:
    print(f"{result.name}: {result.score:.2f}")
```

### Cross-Reference Resolution

```python
from glazing.references.index import CrossReferenceIndex

xref = CrossReferenceIndex()

# Resolve with fuzzy matching
refs = xref.resolve("giv.01", source="propbank", fuzzy=True)

# With confidence threshold
refs = xref.resolve(
    "trasfer.01",
    source="propbank",
    fuzzy=True,
    confidence_threshold=0.7
)
```

### Direct Fuzzy Matching

```python
from glazing.utils.fuzzy_match import fuzzy_match, find_best_match

# Find multiple matches
candidates = ["instrument", "argument", "document"]
results = fuzzy_match("instrment", candidates, threshold=0.7)

# Find single best match
best = find_best_match("giv", ["give", "take", "have"])
```

## Threshold Selection

| Threshold | Use Case | Example Matches |
|-----------|----------|-----------------|
| 0.9-1.0 | Near-exact matches | "give" → "give" |
| 0.8-0.9 | Minor typos | "instrment" → "instrument" |
| 0.7-0.8 | Multiple typos | "trasfer" → "transfer" |
| 0.6-0.7 | Significant differences | "giv" → "give" |
| Below 0.6 | Very loose matching | "doc" → "document" |

## Text Normalization

Text undergoes automatic normalization before matching: accents are removed (café → cafe), case is normalized to lowercase (Give → give), punctuation is removed (give.01 → give 01), and whitespace is normalized ("give  to" → "give to").

## Examples

### Finding Misspelled Verbs

```python
search.search_with_fuzzy("recieve")  # Finds "receive"
search.search_with_fuzzy("occure")   # Finds "occur"
search.search_with_fuzzy("seperate") # Finds "separate"
```

### Partial Matches

Short queries require lower thresholds:

```python
search.search_with_fuzzy("giv", fuzzy_threshold=0.6)    # Finds "give"
search.search_with_fuzzy("tak", fuzzy_threshold=0.6)    # Finds "take"
search.search_with_fuzzy("trans", fuzzy_threshold=0.7)  # Finds "transfer"
```

### Spelling Variants

The system handles British and American spelling differences:

```python
search.search_with_fuzzy("realise")   # Finds "realize"
search.search_with_fuzzy("colour")    # Finds "color"
search.search_with_fuzzy("analyse")   # Finds "analyze"
```

## Performance

Fuzzy matching is computationally more expensive than exact matching. Lower thresholds increase search time as more candidates must be evaluated. Results are cached for repeated queries. For optimal performance, attempt exact matching first and use fuzzy matching as a fallback.

## Usage Recommendations

Start with higher thresholds (0.8+) and decrease if needed. Check confidence scores in results to evaluate match quality. Combine fuzzy matching with other filters to reduce false positives. Use exact matching when possible for better performance.

## Batch Processing

```python
from glazing.search import UnifiedSearch

search = UnifiedSearch()

# Process multiple queries
queries = ["giv", "tak", "mak"]
for query in queries:
    results = search.search_with_fuzzy(query, fuzzy_threshold=0.7)
    if results:
        print(f"{query} → {results[0].name}")
```

## Troubleshooting

- **Too Many Results**: Increase the threshold (e.g., 0.8 → 0.9), add dataset filters, or use more specific queries.
- **No Results Found**: Decrease the threshold (e.g., 0.8 → 0.6), verify text normalization is working correctly, or try partial query terms.
- **Unexpected Matches**: Review the normalization rules, adjust the threshold, and check similarity scores for match quality.
