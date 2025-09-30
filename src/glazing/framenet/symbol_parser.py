"""FrameNet symbol parser using Pydantic v2 models.

This module provides parsing utilities for FrameNet frame and frame element
symbols, including normalization and fuzzy matching support. All parsing
functions use LRU caching for better performance on repeated operations.

Classes
-------
ParsedFrameName
    Parsed FrameNet frame name with normalization and metadata.
ParsedFrameElement
    Parsed FrameNet frame element with core type classification.

Functions
---------
parse_frame_name
    Parse a FrameNet frame name into structured components.
parse_frame_element
    Parse a frame element name with core type detection.
filter_elements_by_properties
    Filter frame elements by core type and other properties.
normalize_frame_name
    Normalize frame names for consistent matching.
normalize_element_for_matching
    Normalize element names for fuzzy matching.
extract_element_base
    Extract base element name without modifiers.
is_core_element
    Check if element is core type.
is_peripheral_element
    Check if element is peripheral type.
is_extra_thematic_element
    Check if element is extra-thematic type.

Type Aliases
------------
ElementCoreType
    Literal type for frame element core types.
FrameNameType
    Literal type for frame name categories.

Examples
--------
>>> from glazing.framenet.symbol_parser import parse_frame_name
>>> parsed = parse_frame_name("Motion_directional")
>>> parsed.normalized
'motion_directional'
>>> parsed.is_abbreviation
False

>>> from glazing.framenet.symbol_parser import parse_frame_element
>>> element = parse_frame_element("Theme")
>>> element.core_type
'core'
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING, Literal

from pydantic import field_validator

from glazing.symbols import BaseSymbol

if TYPE_CHECKING:
    from glazing.framenet.models import FrameElement

# Type aliases
type FrameNameType = Literal["frame", "frame_relation"]
type ElementCoreType = Literal["core", "peripheral", "extra_thematic"]


# Validation patterns
FRAME_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_\-\s]*$")
ELEMENT_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_\-\s\']*$")


class ParsedFrameName(BaseSymbol):
    """Parsed FrameNet frame name.

    Attributes
    ----------
    raw_string : str
        Original unparsed frame name.
    normalized : str
        Normalized name for matching.
    symbol_type : Literal["frame"]
        Always "frame" for frame names.
    dataset : Literal["framenet"]
        Always "framenet".
    name_type : FrameNameType
        Type of frame name.
    is_abbreviation : bool
        Whether the name appears to be an abbreviation.
    """

    symbol_type: Literal["frame"] = "frame"
    dataset: Literal["framenet"] = "framenet"
    name_type: FrameNameType = "frame"
    is_abbreviation: bool = False

    @field_validator("raw_string")
    @classmethod
    def validate_frame_name(cls, v: str) -> str:
        """Validate frame name format."""
        if not FRAME_NAME_PATTERN.match(v):
            msg = f"Invalid frame name format: {v}"
            raise ValueError(msg)
        return v

    @classmethod
    def from_string(cls, frame_name: str) -> ParsedFrameName:
        """Create from frame name string.

        Parameters
        ----------
        frame_name : str
            Frame name to parse.

        Returns
        -------
        ParsedFrameName
            Parsed frame name.
        """
        normalized = cls.normalize_string(frame_name)
        is_abbrev = len(frame_name) <= 3 and frame_name.isupper()

        return cls(
            raw_string=frame_name,
            normalized=normalized,
            is_abbreviation=is_abbrev,
        )


class ParsedFrameElement(BaseSymbol):
    """Parsed FrameNet frame element.

    Attributes
    ----------
    raw_string : str
        Original unparsed element name.
    normalized : str
        Normalized name for matching.
    symbol_type : Literal["frame_element"]
        Always "frame_element".
    dataset : Literal["framenet"]
        Always "framenet".
    core_type : ElementCoreType | None
        Core type classification.
    is_abbreviation : bool
        Whether the name appears to be an abbreviation.
    """

    symbol_type: Literal["frame_element"] = "frame_element"
    dataset: Literal["framenet"] = "framenet"
    core_type: ElementCoreType | None = None
    is_abbreviation: bool = False

    @field_validator("raw_string")
    @classmethod
    def validate_element_name(cls, v: str) -> str:
        """Validate element name format."""
        if not ELEMENT_NAME_PATTERN.match(v):
            msg = f"Invalid element name format: {v}"
            raise ValueError(msg)
        return v

    @classmethod
    def from_string(
        cls, element_name: str, core_type: ElementCoreType | None = None
    ) -> ParsedFrameElement:
        """Create from element name string.

        Parameters
        ----------
        element_name : str
            Element name to parse.
        core_type : ElementCoreType | None
            Core type if known.

        Returns
        -------
        ParsedFrameElement
            Parsed frame element.
        """
        normalized = cls.normalize_string(element_name)
        is_abbrev = len(element_name) <= 3 and element_name.isupper()

        return cls(
            raw_string=element_name,
            normalized=normalized,
            core_type=core_type,
            is_abbreviation=is_abbrev,
        )


@lru_cache(maxsize=512)
def parse_frame_name(frame_name: str) -> ParsedFrameName:
    """Parse a FrameNet frame name.

    Parameters
    ----------
    frame_name : str
        Frame name to parse.

    Returns
    -------
    ParsedFrameName
        Parsed frame name information.
    """
    return ParsedFrameName.from_string(frame_name)


@lru_cache(maxsize=512)
def parse_frame_element(element_name: str) -> ParsedFrameElement:
    """Parse a frame element name.

    Parameters
    ----------
    element_name : str
        Element name to parse.

    Returns
    -------
    ParsedFrameElement
        Parsed frame element information.
    """
    return ParsedFrameElement.from_string(element_name)


@lru_cache(maxsize=1024)
def normalize_frame_name(frame_name: str) -> str:
    """Normalize a frame name for matching.

    Parameters
    ----------
    frame_name : str
        Frame name to normalize.

    Returns
    -------
    str
        Normalized frame name.
    """
    return BaseSymbol.normalize_string(frame_name)


@lru_cache(maxsize=1024)
def normalize_element_for_matching(element_name: str) -> str:
    """Normalize a frame element name for matching.

    Parameters
    ----------
    element_name : str
        Element name to normalize.

    Returns
    -------
    str
        Normalized element name.
    """
    return BaseSymbol.normalize_string(element_name)


def extract_element_base(element_name: str) -> str:
    """Extract the base name from a frame element.

    Parameters
    ----------
    element_name : str
        Frame element name.

    Returns
    -------
    str
        Base element name without modifiers.
    """
    # For FrameNet, the base name is the element name itself
    # We don't strip underscores as they are part of the name
    return element_name


def is_core_element(element: FrameElement) -> bool:
    """Check if a frame element is core.

    Parameters
    ----------
    element : FrameElement
        Frame element to check.

    Returns
    -------
    bool
        True if element is core.
    """
    return element.core_type == "Core"


def is_peripheral_element(element: FrameElement) -> bool:
    """Check if a frame element is peripheral.

    Parameters
    ----------
    element : FrameElement
        Frame element to check.

    Returns
    -------
    bool
        True if element is peripheral.
    """
    return element.core_type == "Peripheral"


def is_extra_thematic_element(element: FrameElement) -> bool:
    """Check if a frame element is extra-thematic.

    Parameters
    ----------
    element : FrameElement
        Frame element to check.

    Returns
    -------
    bool
        True if element is extra-thematic.
    """
    return element.core_type == "Extra-Thematic"


def filter_elements_by_properties(
    elements: list[FrameElement],
    core_type: ElementCoreType | None = None,
    required: bool | None = None,
) -> list[FrameElement]:
    """Filter frame elements by their properties.

    Parameters
    ----------
    elements : list[FrameElement]
        Elements to filter.
    core_type : ElementCoreType | None
        Core type to filter by.
    required : bool | None
        Whether element is required.

    Returns
    -------
    list[FrameElement]
        Filtered elements.
    """
    filtered = elements

    # Map our normalized core types to FrameNet's original values
    core_type_map = {
        "core": "Core",
        "peripheral": "Peripheral",
        "extra_thematic": "Extra-Thematic",
    }

    if core_type is not None:
        original_type = core_type_map.get(core_type, core_type)
        filtered = [e for e in filtered if e.core_type == original_type]

    # Note: FrameNet doesn't have explicit "required" field,
    # but Core elements are typically required
    if required is not None:
        if required:
            filtered = [e for e in filtered if e.core_type == "Core"]
        else:
            filtered = [e for e in filtered if e.core_type != "Core"]

    return filtered
