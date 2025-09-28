"""VerbNet symbol parser.

This module provides parsing utilities for VerbNet thematic role symbols,
including optional roles, indexed roles, and PP roles.

Classes
-------
ParsedVerbNetRole
    Parsed VerbNet thematic role information.

Functions
---------
parse_thematic_role
    Parse a VerbNet thematic role value.
parse_frame_element
    Parse a VerbNet frame description element.
is_optional_role
    Check if a role is optional.
is_indexed_role
    Check if a role has an index.
is_pp_element
    Check if an element is a PP element.
extract_role_base
    Extract the base role name.
filter_roles_by_properties
    Filter roles by their properties.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal, TypedDict, cast

from glazing.verbnet.types import FrameDescriptionElement, ThematicRoleType, ThematicRoleValue

if TYPE_CHECKING:
    from glazing.verbnet.models import ThematicRole


class ParsedVerbNetRole(TypedDict):
    """Parsed VerbNet thematic role.

    Attributes
    ----------
    raw_string : str
        Original unparsed role string.
    base_role : str
        Base role name without modifiers.
    is_optional : bool
        Whether the role is optional (?-prefix).
    index : str | None
        Role index (I, J, etc.) if present.
    pp_type : str | None
        PP type (e.g., "location" for PP.location).
    is_verb_specific : bool
        Whether role is verb-specific (V_-prefix).
    role_type : Literal["thematic", "pp", "verb_specific"]
        Type of role.
    """

    raw_string: str
    base_role: str
    is_optional: bool
    index: str | None
    pp_type: str | None
    is_verb_specific: bool
    role_type: Literal["thematic", "pp", "verb_specific"]


# Patterns for parsing VerbNet roles
OPTIONAL_PATTERN = re.compile(r"^\?(.+)$")
INDEXED_PATTERN = re.compile(r"^(.+)_([IJ])$")
PP_PATTERN = re.compile(r"^PP\.(.+)$")
VERB_SPECIFIC_PATTERN = re.compile(r"^V_(.+)$")


def parse_thematic_role(role: ThematicRoleValue | ThematicRoleType) -> ParsedVerbNetRole:
    """Parse a VerbNet thematic role value.

    Parameters
    ----------
    role : ThematicRoleValue | ThematicRoleType
        VerbNet thematic role value (e.g., "?Agent", "Theme_I", "V_Final_State").

    Returns
    -------
    ParsedVerbNetRole
        Parsed role information.

    Examples
    --------
    >>> parse_thematic_role("?Agent")
    {'raw_string': '?Agent', 'base_role': 'Agent', 'is_optional': True, ...}
    >>> parse_thematic_role("Theme_I")
    {'raw_string': 'Theme_I', 'base_role': 'Theme', 'index': 'I', ...}
    """
    result = ParsedVerbNetRole(
        raw_string=role,
        base_role=role,
        is_optional=False,
        index=None,
        pp_type=None,
        is_verb_specific=False,
        role_type="thematic",
    )

    stripped_role: str = role  # Initialize to handle all cases

    # Check for optional prefix
    if match := OPTIONAL_PATTERN.match(role):
        result["is_optional"] = True
        stripped_role = match.group(1)
        result["base_role"] = stripped_role

    # Check for verb-specific prefix
    if match := VERB_SPECIFIC_PATTERN.match(stripped_role):
        result["is_verb_specific"] = True
        result["base_role"] = match.group(1)
        result["role_type"] = "verb_specific"
        return result

    # Check for indexed suffix
    if match := INDEXED_PATTERN.match(stripped_role):
        result["base_role"] = match.group(1)
        result["index"] = match.group(2)

    return result


def parse_frame_element(element: FrameDescriptionElement) -> ParsedVerbNetRole:
    """Parse a VerbNet frame description element.

    Parameters
    ----------
    element : FrameDescriptionElement
        Frame description element (e.g., "PP.location", "NP.agent").

    Returns
    -------
    ParsedVerbNetRole
        Parsed element information.

    Examples
    --------
    >>> parse_frame_element("PP.location")
    {'raw_string': 'PP.location', 'pp_type': 'location', 'role_type': 'pp', ...}
    >>> parse_frame_element("NP.agent")
    {'raw_string': 'NP.agent', 'base_role': 'agent', 'role_type': 'thematic', ...}
    """
    result = ParsedVerbNetRole(
        raw_string=element,
        base_role=element,
        is_optional=False,
        index=None,
        pp_type=None,
        is_verb_specific=False,
        role_type="thematic",
    )

    # Check for PP elements
    if match := PP_PATTERN.match(element):
        result["pp_type"] = match.group(1)
        result["base_role"] = f"PP.{match.group(1)}"
        result["role_type"] = "pp"
    # Check for NP elements with semantic roles
    elif element.startswith("NP."):
        result["base_role"] = element[3:]  # Remove "NP." prefix
        result["role_type"] = "thematic"

    return result


def is_optional_role(role: ThematicRoleValue | ThematicRoleType) -> bool:
    """Check if a role is optional.

    Parameters
    ----------
    role : ThematicRoleValue | ThematicRoleType
        VerbNet thematic role value.

    Returns
    -------
    bool
        True if role has optional prefix (?).

    Examples
    --------
    >>> is_optional_role("?Agent")
    True
    >>> is_optional_role("Agent")
    False
    """
    return role.startswith("?")


def is_indexed_role(role: ThematicRoleValue | ThematicRoleType) -> bool:
    """Check if a role has an index.

    Parameters
    ----------
    role : ThematicRoleValue | ThematicRoleType
        VerbNet thematic role value.

    Returns
    -------
    bool
        True if role has index suffix (_I, _J).

    Examples
    --------
    >>> is_indexed_role("Theme_I")
    True
    >>> is_indexed_role("Theme")
    False
    """
    return bool(INDEXED_PATTERN.match(role.lstrip("?")))


def is_pp_element(element: FrameDescriptionElement) -> bool:
    """Check if an element is a PP element.

    Parameters
    ----------
    element : FrameDescriptionElement
        Frame description element.

    Returns
    -------
    bool
        True if element is a PP element.

    Examples
    --------
    >>> is_pp_element("PP.location")
    True
    >>> is_pp_element("NP.agent")
    False
    """
    return element.startswith("PP.")


def is_verb_specific_role(role: ThematicRoleValue | ThematicRoleType) -> bool:
    """Check if a role is verb-specific.

    Parameters
    ----------
    role : ThematicRoleValue | ThematicRoleType
        VerbNet thematic role value.

    Returns
    -------
    bool
        True if role is verb-specific.

    Examples
    --------
    >>> is_verb_specific_role("V_Final_State")
    True
    >>> is_verb_specific_role("Agent")
    False
    """
    return role.lstrip("?").startswith("V_")


def extract_role_base(role: ThematicRoleValue | ThematicRoleType) -> str:
    """Extract the base role name without modifiers.

    Parameters
    ----------
    role : ThematicRoleValue | ThematicRoleType
        VerbNet thematic role value.

    Returns
    -------
    str
        Base role name.

    Examples
    --------
    >>> extract_role_base("?Agent")
    'Agent'
    >>> extract_role_base("Theme_I")
    'Theme'
    """
    parsed = parse_thematic_role(role)
    return parsed["base_role"]


def normalize_role_for_matching(role: ThematicRoleValue | ThematicRoleType) -> str:
    """Normalize a role for fuzzy matching.

    Parameters
    ----------
    role : ThematicRoleValue | ThematicRoleType
        VerbNet thematic role value.

    Returns
    -------
    str
        Normalized role string.

    Examples
    --------
    >>> normalize_role_for_matching("?Agent")
    'agent'
    >>> normalize_role_for_matching("Theme_I")
    'theme'
    """
    normalized_role = cast(str, role)

    # Remove optional prefix
    if normalized_role.startswith("?"):
        normalized_role = normalized_role[1:]

    # Remove index suffix
    if match := INDEXED_PATTERN.match(normalized_role):
        normalized_role = cast(str, match.group(1))

    # Remove V_ prefix for verb-specific roles
    if normalized_role.startswith("V_"):
        normalized_role = normalized_role[2:]

    # Keep PP roles as-is but lowercase
    return normalized_role.lower().replace("_", " ")


def filter_roles_by_properties(
    roles: list[ThematicRole],
    optional: bool | None = None,
    indexed: bool | None = None,
    verb_specific: bool | None = None,
    pp_type: str | None = None,
) -> list[ThematicRole]:
    """Filter thematic roles by their properties.

    Parameters
    ----------
    roles : list[ThematicRole]
        List of thematic roles to filter.
    optional : bool | None, optional
        Filter for optional roles (? prefix).
    indexed : bool | None, optional
        Filter for indexed roles (_I, _J suffix).
    verb_specific : bool | None, optional
        Filter for verb-specific roles (V_ prefix).
    pp_type : str | None, optional
        Filter for specific PP type (e.g., "location" for PP.location).

    Returns
    -------
    list[ThematicRole]
        Filtered list of roles.

    Examples
    --------
    >>> roles = [role1, role2, role3]  # Where role1.type = "?Agent"
    >>> filtered = filter_roles_by_properties(roles, optional=True)
    >>> len(filtered)
    1
    """
    filtered = []

    for role in roles:
        parsed = parse_thematic_role(role.type)

        # Apply filters
        if optional is not None and parsed["is_optional"] != optional:
            continue
        if indexed is not None and (parsed["index"] is not None) != indexed:
            continue
        if verb_specific is not None and parsed["is_verb_specific"] != verb_specific:
            continue
        if pp_type is not None and parsed["pp_type"] != pp_type:
            continue

        filtered.append(role)

    return filtered
