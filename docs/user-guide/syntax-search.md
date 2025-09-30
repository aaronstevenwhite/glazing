# Syntax-Based Search

Search for frames, classes, and predicates using syntactic patterns. The system supports hierarchical matching where general patterns match specific subtypes.

**Note**: All examples assume Glazing is installed and data has been initialized with `glazing init`.

## Pattern Format

Patterns use space-separated constituent elements.

### Basic Constituents

`NP` (noun phrase), `VP` (verb phrase), `PP` (prepositional phrase), `V` or `VERB` (verb), `S` (sentence/clause), `ADJ` (adjective), `ADV` (adverb), `*` (wildcard - matches any element)

### Pattern Specifications

#### Semantic Roles
Dot notation specifies semantic roles: `NP.Agent`, `NP.Patient`, `PP.location`, `NP.ARG0` (PropBank argument). Matching is case-insensitive.

#### Prepositions
Brackets specify prepositions: `PP[with]`, `PP[at]`, `PP[from to]` (matches "from" or "to").

#### Morphological Features
Brackets also specify morphological features: `V[ING]` (gerund), `V[past]` (past tense), `VP[to]` (infinitive). Matching is case-insensitive.

#### Optional Elements
Question marks indicate optional elements: `NP V NP?` (optional second NP), `NP V PP?` (optional PP).

## Hierarchical Matching

General patterns match all specific instances. For example, `PP` matches `PP.location`, `PP.instrument`, `PP[with]`, and `PP[at]`. Similarly, `NP` matches `NP.Agent`, `NP.Theme`, and `NP.ARG0`.

## CLI Usage

### Basic Search

**Transitive verb patterns** (subject-verb-object)

Returns verbs like "give", "take", "make" across all datasets:

```bash
glazing search syntax "NP V NP"
```

**Prepositional complements in VerbNet**

Finds patterns like "rely on", "depend on", "look at":

```bash
glazing search syntax "NP V PP" --dataset verbnet
```

**Thematic role patterns**

Matches frames where an Agent acts on a Patient:

```bash
glazing search syntax "NP.Agent V NP.Patient"
```

### Advanced Patterns

**Specific preposition patterns**

Find verbs that take "with" prepositional phrases like "provide with", "combine with", "fill with":

```bash
glazing search syntax "NP V PP[with]"
```

**Ditransitive verbs with location**

Matches patterns like "put the book on the shelf", "place the vase on the table":

```bash
glazing search syntax "NP V NP PP.location"
```

**Wildcard patterns**

Use `*` to match any trailing elements. This matches "give X Y Z" where Z can be any constituent:

```bash
glazing search syntax "NP V NP *"
```

**Optional elements**

Question marks indicate optional constituents. This matches both "eat" (NP V) and "eat food" (NP V NP):

```bash
glazing search syntax "NP V NP? PP?"
```

## Python API

### Basic Usage

```python
from glazing.search import UnifiedSearch

search = UnifiedSearch()
```

### Transitive Pattern Search

Returns all verb classes/frames matching subject-verb-object:

```python
results = search.search_by_syntax("NP V NP")
print(f"Found {len(results)} transitive verb patterns")
# Output: Found 4458 transitive verb patterns
```

### VerbNet Instrumental PPs

Thematic role matching is case-insensitive (instrument, Instrument, INSTRUMENT all work):

```python
results = search.search_by_syntax(
    "NP V PP.instrument",
    dataset="verbnet"
)
print(f"Found {len(results)} instrumental patterns")
# Output: Found 1 instrumental patterns
```

Alternatively, use `NP V PP[with]` to find patterns with "with" preposition.

### Complex Patterns

This matches progressive verbs with Agent/Theme roles and "with" PPs, such as "The chef is mixing the ingredients with a spoon":

```python
results = search.search_by_syntax("NP.Agent V[ING] NP.Theme PP[with]")
print(f"Complex pattern matches: {len(results)}")
# Output: Complex pattern matches: 2
```

## Pattern Examples

### Transitive Verbs

Pattern where subject acts on direct object:

```python
pattern = "NP V NP"
```

Matches VerbNet classes: give-13.1, get-13.5.1, bring-11.3

Example sentences:
- "John gave Mary a book"
- "She bought a car"
- "They made dinner"

### Motion Verbs

Pattern where subject moves to/from a location:

```python
pattern = "NP V PP.location"
```

Matches VerbNet classes: escape-51.1, meander-47.7, run-51.3.2

Example sentences:
- "She walked to the store"
- "The bird flew over the mountain"
- "They traveled across the country"

### Transfer Verbs

Pattern where agent transfers theme to recipient:

```python
pattern = "NP.Agent V NP.Theme PP.Recipient"
```

Matches VerbNet classes: send-11.1, give-13.1, contribute-13.2

Example sentences:
- "John sent the package to Mary"
- "She gave the book to her friend"
- "They delivered the message to the office"

### Causative Constructions

Pattern where subject causes object to do something:

```python
pattern = "NP V NP VP[to]"
```

Matches VerbNet classes: force-59.1, compel-59.1, order-60

Example sentences:
- "She forced him to leave"
- "They caused the machine to stop"
- "The teacher made the students to study"

## Matching Confidence

Confidence scores range from 0.0 to 1.0. Perfect matches score 1.0, good matches with minor differences score 0.8-0.9, partial matches score 0.6-0.7, and poor matches score below 0.6.

## Dataset-Specific Patterns

### VerbNet

Supports thematic roles and syntactic frames.

**Direct thematic role search**

Thematic role matching is case-insensitive:

```bash
glazing search syntax "Agent V Theme"  # or "agent v theme"
```

**Combined syntactic and thematic patterns**

Matches sentences like "The surgeon cut the patient with a scalpel":

```bash
glazing search syntax "NP V NP.Patient PP.Instrument"  # Any case works
```

### PropBank

Supports numbered arguments.

**Basic argument structure**

PropBank uses numbered arguments where ARG0=agent/causer, ARG1=patient/theme:

```bash
glazing search syntax "ARG0 V ARG1"
```

**Including ArgM modifiers**

ArgM modifiers represent adjuncts like location (ARGM-LOC). This matches sentences like "John[ARG0] ate[V] lunch[ARG1] in the cafeteria[ARGM-LOC]":

```bash
glazing search syntax "NP.ARG0 V NP.ARG1 PP.ARGM-LOC"
```

### FrameNet

Supports frame elements.

**Frame-specific element names**

Use FrameNet-specific frame element names. This matches the Giving frame as in "Mary gave the book to John":

```bash
glazing search syntax "Donor V Theme Recipient"
```

**Core vs non-core elements**

Core elements are required for the frame's meaning:

```bash
glazing search syntax "NP.Core[Agent] V NP.Core[Theme]"
```

## Search Tips

Start with general patterns (`PP`) before specific ones (`PP.location`). Mix specifications by combining roles, prepositions, and features in a single pattern. Use wildcards (`*`) to match any trailing elements. Higher confidence scores indicate better matches.
