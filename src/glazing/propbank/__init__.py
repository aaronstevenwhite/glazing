"""PropBank data models and utilities.

This module provides models for PropBank framesets, rolesets, semantic roles,
and their mappings to other resources. It includes support for argument
structure and lexical links with confidence scores.

Classes
-------
Frameset
    Container for all senses of a predicate.
Roleset
    A single sense of a predicate with its semantic roles.
Role
    Semantic role definition with argument number and description.
RoleLink
    Link from a role to VerbNet or FrameNet.

Functions
---------
load
    Load PropBank data from JSON Lines.

Examples
--------
>>> from frames.propbank import load
>>> pb = load("data/propbank.jsonl")
>>> roleset = pb.get_roleset("give.01")
>>> print(roleset.roles)
"""

__all__: list[str] = []
