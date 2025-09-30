"""VerbNet symbol parser using Pydantic v2 models.

This module provides parsing utilities for VerbNet verb class IDs and thematic
role symbols, with normalization and validation. Supports hierarchical
class IDs, optional roles, role indexing, and verb-specific roles. All parsing
functions use LRU caching for better performance.

Classes
-------
ParsedVerbClass
    Parsed VerbNet verb class ID with hierarchical structure.
ParsedThematicRole
    Parsed VerbNet thematic role with modifiers and indices.
ParsedFrameElement
    Parsed VerbNet frame syntax element.

Functions
---------
parse_verb_class
    Parse a VerbNet verb class ID (e.g., "give-13.1-1").
parse_thematic_role
    Parse a VerbNet thematic role (e.g., "?Theme_I").
parse_frame_element
    Parse a frame description element (e.g., "PP.location").
filter_roles_by_properties
    Filter thematic roles by optionality, indexing, and other properties.
extract_role_base
    Extract base role name without modifiers.
normalize_role_for_matching
    Normalize role names for fuzzy matching.
is_optional_role
    Check if role is optional (marked with ?).
is_indexed_role
    Check if role has index (e.g., _I, _J).
is_verb_specific_role
    Check if role is verb-specific.
is_pp_element
    Check if element is prepositional phrase.

Type Aliases
------------
RoleType
    Literal type for role types (thematic/pp/verb_specific).
RoleOptionalityType
    Literal type for role optionality (required/optional/implicit).
RoleIndexType
    Literal type for role indexing (indexed/coindexed/none).

Examples
--------
>>> from glazing.verbnet.symbol_parser import parse_verb_class
>>> parsed = parse_verb_class("give-13.1-1")
>>> parsed.base_name
'give'
>>> parsed.class_number
'13.1-1'

>>> from glazing.verbnet.symbol_parser import parse_thematic_role
>>> role = parse_thematic_role("?Theme_I")
>>> role.base_role
'Theme'
>>> role.is_optional
True
>>> role.index
'I'
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING, Literal

from pydantic import Field, field_validator

from glazing.symbols import BaseSymbol

if TYPE_CHECKING:
    from glazing.verbnet.models import ThematicRole

# Type aliases
type RoleOptionalityType = Literal["required", "optional", "implicit"]
type RoleIndexType = Literal["indexed", "coindexed", "none"]
type RoleType = Literal["thematic", "pp", "verb_specific"]

# Validation patterns
VERB_CLASS_PATTERN = re.compile(r"^[a-z][a-z0-9_]*-\d+(\.\d+)*(-\d+)?$")
THEMATIC_ROLE_PATTERN = re.compile(r"^\??[A-Z][a-zA-Z_]+(_[IJijk])?$")
FRAME_ELEMENT_PATTERN = re.compile(r"^(PP\.|NP\.)?[A-Za-z][a-zA-Z_]*$")


class ParsedVerbClass(BaseSymbol):
    """Parsed VerbNet verb class ID.

    Attributes
    ----------
    raw_string : str
        Original class ID string.
    normalized : str
        Normalized ID (lowercase, spaces to underscores).
    symbol_type : Literal["verb_class"]
        Always "verb_class".
    dataset : Literal["verbnet"]
        Always "verbnet".
    base_name : str
        Base class name without numbers.
    class_number : str
        Full class number (e.g., "13.1-1").
    parent_class : str | None
        Parent class ID if this is a subclass.
    """

    symbol_type: Literal["verb_class"] = "verb_class"
    dataset: Literal["verbnet"] = "verbnet"
    base_name: str = Field(..., min_length=1)
    class_number: str = Field(..., min_length=1)
    parent_class: str | None = None

    @field_validator("raw_string")
    @classmethod
    def validate_class_format(cls, v: str) -> str:
        """Validate verb class ID format."""
        if not VERB_CLASS_PATTERN.match(v.lower()):
            msg = f"Invalid verb class ID format: {v}"
            raise ValueError(msg)
        return v

    @classmethod
    def from_string(cls, class_id: str) -> ParsedVerbClass:
        """Create from verb class ID string.

        Parameters
        ----------
        class_id : str
            Verb class ID (e.g., "give-13.1-1").

        Returns
        -------
        ParsedVerbClass
            Parsed verb class ID.
        """
        # Normalize to lowercase
        class_lower = class_id.lower()

        # Split by dash to get base name and numbers
        parts = class_lower.split("-")
        if len(parts) < 2:
            msg = f"Invalid verb class ID format: {class_id}"
            raise ValueError(msg)

        base_name = parts[0]
        class_number = "-".join(parts[1:])

        # Determine parent class (everything except last dash-separated number)
        parent_class: str | None = None
        if len(parts) > 2:
            parent_class = f"{parts[0]}-{'-'.join(parts[1:-1])}"

        # Normalize base name (spaces to underscores)
        normalized_base = cls.normalize_string(base_name)
        normalized = f"{normalized_base}-{class_number}"

        return cls(
            raw_string=class_id,
            normalized=normalized,
            base_name=normalized_base,
            class_number=class_number,
            parent_class=parent_class,
        )


class ParsedThematicRole(BaseSymbol):
    """Parsed VerbNet thematic role.

    Attributes
    ----------
    raw_string : str
        Original role string.
    normalized : str
        Normalized role (lowercase, no prefix/suffix).
    symbol_type : Literal["thematic_role"]
        Always "thematic_role".
    dataset : Literal["verbnet"]
        Always "verbnet".
    base_role : str
        Base role name without modifiers.
    is_optional : bool
        Whether role is optional.
    index : str | None
        Index letter if present (I, J).
    is_verb_specific : bool
        Whether role is verb-specific.
    role_type : RoleType
        Type of role.
    """

    symbol_type: Literal["thematic_role"] = "thematic_role"
    dataset: Literal["verbnet"] = "verbnet"
    base_role: str = Field(..., min_length=0)  # Can be empty for edge cases
    is_optional: bool = False
    index: str | None = None
    is_verb_specific: bool = False
    role_type: RoleType = "thematic"

    @classmethod
    def from_string(cls, role: str) -> ParsedThematicRole:
        """Create from thematic role string.

        Parameters
        ----------
        role : str
            Thematic role (e.g., "Agent", "?Theme_I").

        Returns
        -------
        ParsedThematicRole
            Parsed thematic role.
        """
        original = role
        is_optional = False
        is_verb_specific = False
        index: str | None = None
        role_type: RoleType = "thematic"

        # Check for optional prefix
        if role.startswith("?"):
            is_optional = True
            role = role[1:]

        # Check for verb-specific prefix
        if role.startswith("V_"):
            is_verb_specific = True
            role_type = "verb_specific"
            role = role[2:]

        # Check for index suffix (both uppercase and lowercase)
        if role.endswith(("_I", "_J")):
            index = role[-1]
            role = role[:-2]
        elif role.endswith(("_i", "_j", "_k")):
            index = role[-1].upper()
            role = role[:-2]

        # Normalize to lowercase with underscores
        base_role = role
        if not base_role:
            msg = f"Empty base role after processing: {original}"
            raise ValueError(msg)
        normalized = cls.normalize_string(base_role)

        return cls(
            raw_string=original,
            normalized=normalized,
            base_role=base_role,
            is_optional=is_optional,
            index=index,
            is_verb_specific=is_verb_specific,
            role_type=role_type,
        )


class ParsedFrameElement(BaseSymbol):
    """Parsed VerbNet frame element.

    Attributes
    ----------
    raw_string : str
        Original element string.
    normalized : str
        Normalized element.
    symbol_type : Literal["frame_element"]
        Always "frame_element".
    dataset : Literal["verbnet"]
        Always "verbnet".
    base_role : str
        Base role name.
    pp_type : str | None
        PP type if PP element.
    role_type : RoleType
        Type of role.
    """

    symbol_type: Literal["frame_element"] = "frame_element"
    dataset: Literal["verbnet"] = "verbnet"
    base_role: str = Field(..., min_length=1)
    pp_type: str | None = None
    role_type: RoleType = "thematic"

    @classmethod
    def from_string(cls, element: str) -> ParsedFrameElement:
        """Create from frame element string.

        Parameters
        ----------
        element : str
            Frame element string.

        Returns
        -------
        ParsedFrameElement
            Parsed frame element.
        """
        base_role = element
        pp_type: str | None = None
        role_type: RoleType = "thematic"

        if element.startswith("PP."):
            pp_type = element[3:]
            base_role = element
            role_type = "pp"
        elif element.startswith("NP."):
            base_role = element[3:]

        normalized = cls.normalize_string(base_role)

        return cls(
            raw_string=element,
            normalized=normalized,
            base_role=base_role,
            pp_type=pp_type,
            role_type=role_type,
        )


@lru_cache(maxsize=512)
def parse_verb_class(class_id: str) -> ParsedVerbClass:
    """Parse a VerbNet verb class ID.

    Parameters
    ----------
    class_id : str
        Verb class ID to parse.

    Returns
    -------
    ParsedVerbClass
        Parsed verb class ID.
    """
    return ParsedVerbClass.from_string(class_id)


@lru_cache(maxsize=512)
def parse_thematic_role(role: str) -> ParsedThematicRole:
    """Parse a VerbNet thematic role.

    Parameters
    ----------
    role : str
        Thematic role to parse.

    Returns
    -------
    ParsedThematicRole
        Parsed thematic role.
    """
    return ParsedThematicRole.from_string(role)


@lru_cache(maxsize=512)
def parse_frame_element(element: str) -> ParsedFrameElement:
    """Parse a frame description element.

    Parameters
    ----------
    element : str
        Frame element string.

    Returns
    -------
    ParsedFrameElement
        Parsed element information.
    """
    return ParsedFrameElement.from_string(element)


@lru_cache(maxsize=1024)
def extract_role_base(role: str) -> str:
    """Extract base role name without modifiers.

    Parameters
    ----------
    role : str
        Thematic role string.

    Returns
    -------
    str
        Base role name.
    """
    # Remove optional prefix
    if role.startswith("?"):
        role = role[1:]

    # Remove verb-specific prefix
    if role.startswith("V_"):
        role = role[2:]

    # Remove index suffix
    if role.endswith(("_I", "_J", "_i", "_j", "_k")):
        role = role[:-2]

    return role


@lru_cache(maxsize=1024)
def normalize_role_for_matching(role: str) -> str:
    """Normalize a thematic role for fuzzy matching.

    Parameters
    ----------
    role : str
        Thematic role string.

    Returns
    -------
    str
        Normalized role.
    """
    base = extract_role_base(role)
    return BaseSymbol.normalize_string(base)


@lru_cache(maxsize=1024)
def is_optional_role(role: str) -> bool:
    """Check if role is optional.

    Parameters
    ----------
    role : str
        Thematic role string.

    Returns
    -------
    bool
        True if optional.
    """
    return role.startswith("?")


@lru_cache(maxsize=1024)
def is_indexed_role(role: str) -> bool:
    """Check if role is indexed.

    Parameters
    ----------
    role : str
        Thematic role string.

    Returns
    -------
    bool
        True if indexed.
    """
    # Check both uppercase and lowercase variants
    return role.endswith(("_I", "_J", "_i", "_j", "_k"))


@lru_cache(maxsize=1024)
def is_verb_specific_role(role: str) -> bool:
    """Check if role is verb-specific (starts with V_).

    Parameters
    ----------
    role : str
        Thematic role string.

    Returns
    -------
    bool
        True if verb-specific.
    """
    # Remove optional prefix first
    if role.startswith("?"):
        role = role[1:]
    return role.startswith("V_")


@lru_cache(maxsize=1024)
def is_pp_element(element: str) -> bool:
    """Check if element is a PP (prepositional phrase) element.

    Parameters
    ----------
    element : str
        Frame element string.

    Returns
    -------
    bool
        True if PP element.
    """
    return element.startswith("PP.")


def filter_roles_by_properties(
    roles: list[ThematicRole],
    optional: bool | None = None,
    indexed: bool | None = None,
    verb_specific: bool | None = None,
    base_role: str | None = None,
) -> list[ThematicRole]:
    """Filter thematic roles by their properties.

    Parameters
    ----------
    roles : list[ThematicRole]
        Roles to filter.
    optional : bool | None
        Filter for optional roles.
    indexed : bool | None
        Filter for indexed roles.
    verb_specific : bool | None
        Filter for verb-specific roles.
    base_role : str | None
        Filter for specific base role.

    Returns
    -------
    list[ThematicRole]
        Filtered roles.
    """
    filtered = roles

    if optional is not None:
        if optional:
            filtered = [r for r in filtered if is_optional_role(r.type)]
        else:
            filtered = [r for r in filtered if not is_optional_role(r.type)]

    if indexed is not None:
        if indexed:
            filtered = [r for r in filtered if is_indexed_role(r.type)]
        else:
            filtered = [r for r in filtered if not is_indexed_role(r.type)]

    if verb_specific is not None:
        if verb_specific:
            filtered = [r for r in filtered if is_verb_specific_role(r.type)]
        else:
            filtered = [r for r in filtered if not is_verb_specific_role(r.type)]

    if base_role is not None:
        normalized_base = BaseSymbol.normalize_string(base_role)
        filtered = [r for r in filtered if extract_role_base(r.type) == normalized_base]

    return filtered
