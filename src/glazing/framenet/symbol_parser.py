"""FrameNet symbol parser.

This module provides parsing utilities for FrameNet frame and frame element
symbols, including normalization and fuzzy matching support.

Classes
-------
ParsedFrameNetSymbol
    Parsed FrameNet frame or element information.

Functions
---------
parse_frame_name
    Parse and normalize a FrameNet frame name.
parse_frame_element
    Parse a frame element name.
is_core_element
    Check if a frame element is core.
normalize_frame_name
    Normalize a frame name for matching.
normalize_element_name
    Normalize an element name for matching.
filter_elements_by_properties
    Filter frame elements by their properties.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal, TypedDict

from glazing.framenet.types import CoreType, FEAbbrev, FEName, FrameName, LexicalUnitName

if TYPE_CHECKING:
    from glazing.framenet.models import FrameElement


class ParsedFrameNetSymbol(TypedDict):
    """Parsed FrameNet symbol.

    Attributes
    ----------
    raw_string : str
        Original unparsed string.
    normalized_name : str
        Normalized name for matching.
    symbol_type : Literal["frame", "frame_element", "lexical_unit"]
        Type of FrameNet symbol.
    core_type : CoreType | None
        Core type for frame elements ("Core", "Non-Core", "Extra-Thematic").
    is_abbreviation : bool
        Whether the symbol appears to be an abbreviation.
    """

    raw_string: str
    normalized_name: str
    symbol_type: Literal["frame", "frame_element", "lexical_unit"]
    core_type: CoreType | None
    is_abbreviation: bool


# Common frame name variations
FRAME_NAME_VARIATIONS = {
    "cause_motion": ["Cause_motion", "CauseMotion", "cause motion"],
    "commerce_buy": ["Commerce_buy", "CommerceBuy", "commerce buy"],
    "giving": ["Giving", "giving"],
    "transfer": ["Transfer", "transfer"],
}

# Common frame element abbreviations
FE_ABBREVIATIONS = {
    "AGT": "Agent",
    "PAT": "Patient",
    "THM": "Theme",
    "SRC": "Source",
    "GOAL": "Goal",
    "LOC": "Location",
    "INST": "Instrument",
    "BEN": "Beneficiary",
    "MANN": "Manner",
    "PURP": "Purpose",
    "TIME": "Time",
    "CAUS": "Cause",
}


def parse_frame_name(frame_name: FrameName) -> ParsedFrameNetSymbol:
    """Parse and normalize a FrameNet frame name.

    Parameters
    ----------
    frame_name : FrameName
        FrameNet frame name (e.g., "Cause_motion", "Commerce_buy").

    Returns
    -------
    ParsedFrameNetSymbol
        Parsed frame information.

    Examples
    --------
    >>> parse_frame_name("Cause_motion")
    {'raw_string': 'Cause_motion', 'normalized_name': 'cause motion', ...}
    >>> parse_frame_name("Commerce_buy")
    {'raw_string': 'Commerce_buy', 'normalized_name': 'commerce buy', ...}
    """
    return ParsedFrameNetSymbol(
        raw_string=frame_name,
        normalized_name=normalize_frame_name(frame_name),
        symbol_type="frame",
        core_type=None,
        is_abbreviation=False,
    )


def parse_frame_element(
    element_name: FEName, core_type: CoreType | None = None
) -> ParsedFrameNetSymbol:
    """Parse a frame element name.

    Parameters
    ----------
    element_name : FEName
        Frame element name (e.g., "Agent", "Theme").
    core_type : CoreType | None
        Core type ("Core", "Non-Core", "Extra-Thematic").

    Returns
    -------
    ParsedFrameNetSymbol
        Parsed element information.

    Examples
    --------
    >>> parse_frame_element("Agent", "Core")
    {'raw_string': 'Agent', 'core_type': 'Core', ...}
    >>> parse_frame_element("Time", "Non-Core")
    {'raw_string': 'Time', 'core_type': 'Non-Core', ...}
    """
    # Check if it's an abbreviation
    is_abbrev = element_name.upper() in FE_ABBREVIATIONS

    # If it's an abbreviation, get the full name
    if is_abbrev and element_name.upper() in FE_ABBREVIATIONS:
        normalized = FE_ABBREVIATIONS[element_name.upper()].lower()
    else:
        normalized = normalize_element_name(element_name)

    return ParsedFrameNetSymbol(
        raw_string=element_name,
        normalized_name=normalized,
        symbol_type="frame_element",
        core_type=core_type,
        is_abbreviation=is_abbrev,
    )


def parse_lexical_unit(lu_name: LexicalUnitName) -> ParsedFrameNetSymbol:
    """Parse a lexical unit name.

    Parameters
    ----------
    lu_name : LexicalUnitName
        Lexical unit name (e.g., "give.v", "gift.n").

    Returns
    -------
    ParsedFrameNetSymbol
        Parsed lexical unit information.

    Examples
    --------
    >>> parse_lexical_unit("give.v")
    {'raw_string': 'give.v', 'normalized_name': 'give', ...}
    """
    # Remove POS suffix for normalization
    normalized = lu_name.rsplit(".", 1)[0] if "." in lu_name else lu_name

    return ParsedFrameNetSymbol(
        raw_string=lu_name,
        normalized_name=normalized.lower(),
        symbol_type="lexical_unit",
        core_type=None,
        is_abbreviation=False,
    )


def is_core_element(element_name: FEName, core_type: CoreType | None) -> bool:
    """Check if a frame element is core.

    Parameters
    ----------
    element_name : FEName
        Frame element name.
    core_type : CoreType | None
        Core type string.

    Returns
    -------
    bool
        True if element is core.

    Examples
    --------
    >>> is_core_element("Agent", "Core")
    True
    >>> is_core_element("Time", "Non-Core")
    False
    """
    _ = element_name  # Currently unused, kept for future use
    return core_type == "Core"


def normalize_frame_name(frame_name: FrameName) -> str:
    """Normalize a frame name for matching.

    Handles various conventions:
    - Underscore separation (Cause_motion)
    - CamelCase (CauseMotion)
    - Space separation (Cause motion)

    Parameters
    ----------
    frame_name : FrameName
        FrameNet frame name.

    Returns
    -------
    str
        Normalized frame name.

    Examples
    --------
    >>> normalize_frame_name("Cause_motion")
    'cause motion'
    >>> normalize_frame_name("CauseMotion")
    'cause motion'
    >>> normalize_frame_name("cause motion")
    'cause motion'
    """
    # Replace underscores with spaces
    normalized = frame_name.replace("_", " ")

    # Handle CamelCase by inserting spaces
    normalized = re.sub(r"([a-z])([A-Z])", r"\1 \2", normalized)
    normalized = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", normalized)

    # Normalize whitespace and lowercase
    return " ".join(normalized.split()).lower()


def normalize_element_name(element_name: FEName) -> str:
    """Normalize an element name for matching.

    Parameters
    ----------
    element_name : FEName
        Frame element name.

    Returns
    -------
    str
        Normalized element name.

    Examples
    --------
    >>> normalize_element_name("Agent")
    'agent'
    >>> normalize_element_name("Goal_location")
    'goal location'
    """
    # Handle abbreviations
    if element_name.upper() in FE_ABBREVIATIONS:
        return FE_ABBREVIATIONS[element_name.upper()].lower()

    # Replace underscores and normalize
    return element_name.replace("_", " ").lower()


def expand_abbreviation(abbrev: FEAbbrev) -> str | None:
    """Expand a frame element abbreviation.

    Parameters
    ----------
    abbrev : FEAbbrev
        Abbreviation to expand.

    Returns
    -------
    str | None
        Expanded form or None if not recognized.

    Examples
    --------
    >>> expand_abbreviation("AGT")
    'Agent'
    >>> expand_abbreviation("THM")
    'Theme'
    """
    return FE_ABBREVIATIONS.get(abbrev.upper())


def find_frame_variations(frame_name: FrameName) -> list[str]:
    """Find known variations of a frame name.

    Parameters
    ----------
    frame_name : FrameName
        Frame name to find variations for.

    Returns
    -------
    list[str]
        List of known variations.

    Examples
    --------
    >>> find_frame_variations("cause_motion")
    ['Cause_motion', 'CauseMotion', 'cause motion']
    """
    normalized = normalize_frame_name(frame_name)

    # Check if we have known variations
    for key, variations in FRAME_NAME_VARIATIONS.items():
        if normalize_frame_name(key) == normalized:
            return variations

    # Return the original if no variations found
    return [frame_name]


def filter_elements_by_properties(
    elements: list[FrameElement],
    core_type: CoreType | None = None,
    semantic_type: str | None = None,
) -> list[FrameElement]:
    """Filter frame elements by their properties.

    Parameters
    ----------
    elements : list[FrameElement]
        List of frame elements to filter.
    core_type : CoreType | None, optional
        Filter by core type ("Core", "Non-Core", "Extra-Thematic").
    semantic_type : str | None, optional
        Filter by semantic type.

    Returns
    -------
    list[FrameElement]
        Filtered list of frame elements.

    Examples
    --------
    >>> elements = [elem1, elem2, elem3]  # Where elem1.core_type = "Core"
    >>> filtered = filter_elements_by_properties(elements, core_type="Core")
    >>> len(filtered)
    1
    """
    filtered = []

    for element in elements:
        # Apply filters
        if core_type is not None and element.core_type != core_type:
            continue
        if semantic_type is not None and getattr(element, "semantic_type", None) != semantic_type:
            continue

        filtered.append(element)

    return filtered
