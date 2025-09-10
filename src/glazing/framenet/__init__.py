"""FrameNet data models and utilities.

This module provides models for FrameNet semantic frames, frame elements,
lexical units, and their relationships. It supports the complete FrameNet
annotation model including multi-layer annotations and valence patterns.

Classes
-------
Frame
    A semantic frame representing a schematic situation.
FrameElement
    A participant or prop in a frame.
LexicalUnit
    A word or phrase that evokes a frame.
FrameRelation
    Relationships between frames.

Functions
---------
load
    Load FrameNet data from JSON Lines.

Examples
--------
>>> from frames.framenet import load
>>> fn = load("data/framenet.jsonl")
>>> frame = fn.get_frame("Giving")
>>> print(frame.definition)
"""

__all__: list[str] = []
