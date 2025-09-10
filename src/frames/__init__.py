"""Unified interface for FrameNet, PropBank, VerbNet, and WordNet linguistic resources.

This package provides type-safe data models and utilities for working with
four major linguistic resources. All models use Pydantic v2 for validation
and support JSON Lines serialization.

Modules
-------
framenet
    Models and utilities for FrameNet semantic frames.
propbank
    Models and utilities for PropBank rolesets.
verbnet
    Models and utilities for VerbNet verb classes.
wordnet
    Models and utilities for WordNet synsets and relations.
references
    Cross-reference resolution between datasets.
utils
    Shared utilities and helper functions.

Examples
--------
>>> from frames import FrameNet, PropBank, VerbNet, WordNet
>>> fn = FrameNet.load("data/framenet.jsonl")
>>> frames = fn.get_frames_by_lemma("give")
"""

from frames.__version__ import __version__, __version_info__

__all__ = [
    "__version__",
    "__version_info__",
]
