# glazing.framenet

FrameNet data models and utilities.

## Overview

The FrameNet module provides models for semantic frames, frame elements, lexical units, and their relationships. It supports the complete FrameNet annotation model including multi-layer annotations and valence patterns.

## Modules

- **[Models](models.md)** - Core data models (Frame, FrameElement, etc.)
- **[Loader](loader.md)** - Loading FrameNet data from JSON Lines
- **[Converter](converter.md)** - Converting from FrameNet XML format
- **[Search](search.md)** - Searching FrameNet data

## Quick Example

```python
from glazing.framenet.loader import FrameNetLoader
from pathlib import Path

loader = FrameNetLoader()
frames = loader.load_frames(Path("data/framenet.jsonl"))

# Find a specific frame
giving_frame = next(
    (f for f in frames if f.name == "Giving"),
    None
)
```

::: glazing.framenet
    options:
      show_source: false
      members: false
