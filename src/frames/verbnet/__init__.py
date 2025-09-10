"""VerbNet data models and utilities.

This module provides models for VerbNet verb classes, thematic roles,
syntactic frames, and semantic predicates. It includes support for the
complete role inheritance hierarchy and optional Generative Lexicon features.

Classes
-------
VerbClass
    A verb class with members, roles, and frames.
Member
    Individual verb with cross-references.
ThematicRole
    Semantic role with selectional restrictions.
VNFrame
    Syntactic-semantic frame pattern.

Functions
---------
load
    Load VerbNet data from JSON Lines.

Examples
--------
>>> from frames.verbnet import load
>>> vn = load("data/verbnet.json")
>>> verb_class = vn.get_class("give-13.1")
>>> print(verb_class.themroles)
"""

__all__: list[str] = []
