"""VerbNet data models and utilities.

This module provides models for VerbNet verb classes, thematic roles,
syntactic frames, semantic predicates, and Generative Lexicon extensions.
It includes support for the complete role inheritance hierarchy.

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

from glazing.verbnet.gl_models import (
    Event,
    EventStructure,
    GLFrame,
    GLVerbClass,
    Opposition,
    Qualia,
    State,
    Subcategorization,
    SubcatMember,
    Subevent,
)
from glazing.verbnet.models import (
    Example,
    FrameDescription,
    Member,
    Predicate,
    PredicateArgument,
    SelectionalRestriction,
    SelectionalRestrictions,
    Semantics,
    SyntacticRestriction,
    Syntax,
    SyntaxElement,
    ThematicRole,
    VerbClass,
    VNFrame,
    WordNetCrossRef,
)

__all__ = [
    "Event",
    "EventStructure",
    "Example",
    "FrameDescription",
    "GLFrame",
    "GLVerbClass",
    "Member",
    "Opposition",
    "Predicate",
    "PredicateArgument",
    "Qualia",
    "SelectionalRestriction",
    "SelectionalRestrictions",
    "Semantics",
    "State",
    "SubcatMember",
    "Subcategorization",
    "Subevent",
    "SyntacticRestriction",
    "Syntax",
    "SyntaxElement",
    "ThematicRole",
    "VNFrame",
    "VerbClass",
    "WordNetCrossRef",
]
