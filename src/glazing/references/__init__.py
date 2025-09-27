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
CrossReferenceIndex
    Automatic cross-reference extraction and resolution.
ReferenceExtractor
    Extract references from datasets.
ReferenceResolver
    Resolve cross-references between datasets.

Functions
---------
get_default_index
    Get or create the default global index.

Examples
--------
>>> from glazing.references.index import CrossReferenceIndex
>>> xref = CrossReferenceIndex()
>>> refs = xref.resolve("give.01", source="propbank")
>>> print(refs["verbnet_classes"])
['give-13.1']
"""

from glazing.references.models import CrossReference, MappingConfidence, MappingIndex

__all__ = [
    "CrossReference",
    "MappingConfidence",
    "MappingIndex",
]
