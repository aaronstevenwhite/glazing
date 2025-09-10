"""Cross-reference models and resolution utilities.

This module provides models and utilities for managing cross-references
between FrameNet, PropBank, VerbNet, and WordNet. It includes confidence
scoring, transitive mapping resolution, and conflict detection.

Classes
-------
CrossReference
    A mapping between entities in different datasets.
MappingConfidence
    Confidence scoring for mappings.
UnifiedLemma
    A lemma with representations across all datasets.
MappingIndex
    Bidirectional index for fast mapping lookups.

Functions
---------
resolve_references
    Resolve cross-references between datasets.

Examples
--------
>>> from frames.references import CrossRef
>>> xref = CrossRef(fn, pb, vn, wn)
>>> mappings = xref.get_mappings("give", source="verbnet")
"""

__all__: list[str] = []
