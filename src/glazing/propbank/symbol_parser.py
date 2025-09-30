"""PropBank symbol parser using Pydantic v2 models.

This module provides parsing utilities for PropBank roleset IDs and argument
symbols, with normalization and validation. Supports core arguments, modifiers,
function tags, and continuation/reference prefixes. All parsing functions
use LRU caching for better performance.

Classes
-------
ParsedRolesetID
    Parsed PropBank roleset ID with lemma and sense number.
ParsedArgument
    Parsed PropBank argument with type classification and modifiers.

Functions
---------
parse_roleset_id
    Parse a PropBank roleset ID (e.g., "give.01").
parse_argument
    Parse a PropBank argument string (e.g., "ARG0-PPT").
filter_args_by_properties
    Filter arguments by type, modifiers, and other properties.
extract_arg_number
    Extract argument number from argument string.
extract_modifier_type
    Extract modifier type from modifier argument.
extract_function_tag
    Extract function tag from argument.
is_core_argument
    Check if argument is core (ARG0-ARG5, ARGA).
is_modifier
    Check if argument is modifier (ARGM-*).

Type Aliases
------------
ArgType
    Literal type for argument types (core/modifier).
ModifierType
    Literal type for modifier argument types.
PrefixType
    Literal type for continuation/reference prefixes.

Examples
--------
>>> from glazing.propbank.symbol_parser import parse_roleset_id
>>> parsed = parse_roleset_id("give.01")
>>> parsed.lemma
'give'
>>> parsed.sense_number
1

>>> from glazing.propbank.symbol_parser import parse_argument
>>> arg = parse_argument("ARG0-PPT")
>>> arg.arg_type
'core'
>>> arg.function_tag
'ppt'
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING, Literal

from pydantic import Field, field_validator

from glazing.symbols import BaseSymbol

if TYPE_CHECKING:
    from glazing.propbank.models import Role

# Type aliases
type ArgType = Literal["core", "modifier"]
type ModifierType = Literal[
    "loc",
    "tmp",
    "mnr",
    "cau",
    "prp",
    "dir",
    "dis",
    "adv",
    "mod",
    "neg",
    "pnc",
    "ext",
    "lvb",
    "rec",
    "gol",
    "prd",
    "com",
    "adj",
    "dsp",
    "prr",
    "prx",
    "cxn",
    "top",
]
type PrefixType = Literal["c", "r"]

# Validation patterns
ROLESET_PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.\d{2}$")
ARGUMENT_PATTERN = re.compile(r"^(C-|R-)?ARG(A|M|\d)(-[A-Z]+)?$", re.IGNORECASE)


class ParsedRolesetID(BaseSymbol):
    """Parsed PropBank roleset ID.

    Attributes
    ----------
    raw_string : str
        Original roleset ID string.
    normalized : str
        Normalized ID (lowercase lemma).
    symbol_type : Literal["roleset"]
        Always "roleset".
    dataset : Literal["propbank"]
        Always "propbank".
    lemma : str
        Verb lemma part.
    sense_number : int
        Sense number (00-99).
    """

    symbol_type: Literal["roleset"] = "roleset"
    dataset: Literal["propbank"] = "propbank"
    lemma: str = Field(..., min_length=1)
    sense_number: int = Field(..., ge=0, le=99)

    @field_validator("raw_string")
    @classmethod
    def validate_roleset_format(cls, v: str) -> str:
        """Validate roleset ID format."""
        if not ROLESET_PATTERN.match(v.lower()):
            msg = f"Invalid roleset ID format: {v}"
            raise ValueError(msg)
        return v

    @classmethod
    def from_string(cls, roleset_id: str) -> ParsedRolesetID:
        """Create from roleset ID string.

        Parameters
        ----------
        roleset_id : str
            Roleset ID (e.g., "give.01").

        Returns
        -------
        ParsedRolesetID
            Parsed roleset ID.
        """
        # Normalize to lowercase
        roleset_lower = roleset_id.lower()

        # Split into lemma and sense
        parts = roleset_lower.split(".")
        if len(parts) != 2:
            msg = f"Invalid roleset ID format: {roleset_id}"
            raise ValueError(msg)

        lemma = parts[0]
        try:
            sense_number = int(parts[1])
        except ValueError as e:
            msg = f"Invalid sense number in roleset ID: {parts[1]}"
            raise ValueError(msg) from e

        # Normalize lemma (spaces to underscores)
        normalized_lemma = cls.normalize_string(lemma)
        normalized = f"{normalized_lemma}.{sense_number:02d}"

        return cls(
            raw_string=roleset_id,
            normalized=normalized,
            lemma=normalized_lemma,
            sense_number=sense_number,
        )


class ParsedArgument(BaseSymbol):
    """Parsed PropBank argument.

    Attributes
    ----------
    raw_string : str
        Original argument string.
    normalized : str
        Normalized argument (lowercase, no prefix).
    symbol_type : Literal["argument"]
        Always "argument".
    dataset : Literal["propbank"]
        Always "propbank".
    arg_type : ArgType
        Type of argument (core, modifier, special).
    arg_number : str | None
        Argument number (0-5, "a", "m", or None for modifiers).
    modifier_type : ModifierType | None
        Modifier type if arg_type is "modifier".
    prefix : PrefixType | None
        Continuation/reference prefix if present.
    function_tag : str | None
        Function tag if present (e.g., "PPT", "PAG").
    """

    symbol_type: Literal["argument"] = "argument"
    dataset: Literal["propbank"] = "propbank"
    arg_type: ArgType
    arg_number: str | None = None
    modifier_type: ModifierType | None = None
    prefix: PrefixType | None = None
    function_tag: str | None = None

    @field_validator("raw_string")
    @classmethod
    def validate_argument_format(cls, v: str) -> str:
        """Validate argument format."""
        if not ARGUMENT_PATTERN.match(v):
            msg = f"Invalid argument format: {v}"
            raise ValueError(msg)
        return v

    @classmethod
    def from_string(cls, argument: str) -> ParsedArgument:  # noqa: C901, PLR0912
        """Create from argument string.

        Parameters
        ----------
        argument : str
            Argument string (e.g., "ARG0-PPT", "ARGM-LOC", "C-ARG1").

        Returns
        -------
        ParsedArgument
            Parsed argument.
        """
        # Parse with regex
        match = ARGUMENT_PATTERN.match(argument.upper())
        if not match:
            msg = f"Invalid argument format: {argument}"
            raise ValueError(msg)

        # Extract parts
        prefix_part = match.group(1)
        arg_char = match.group(2)
        tag_part = match.group(3)

        # Determine prefix
        prefix: PrefixType | None = None
        if prefix_part:
            prefix = prefix_part[0].lower()  # type: ignore[assignment]

        # Initialize variables
        modifier_type: ModifierType | None = None
        arg_number: str | None = None

        # Determine arg type and number
        if arg_char == "M":
            arg_type: ArgType = "modifier"
            # Extract modifier type from tag if present
            if tag_part:
                mod_str = tag_part.lstrip("-").lower()
                if mod_str in [
                    "loc",
                    "tmp",
                    "mnr",
                    "cau",
                    "prp",
                    "dir",
                    "dis",
                    "adv",
                    "mod",
                    "neg",
                    "pnc",
                    "ext",
                    "lvb",
                    "rec",
                    "gol",
                    "prd",
                    "com",
                    "adj",
                    "dsp",
                    "prr",
                    "prx",
                    "cxn",
                    "top",
                ]:
                    modifier_type = mod_str  # type: ignore[assignment]
        elif arg_char.isdigit():
            arg_type = "core"
            arg_number = arg_char
        elif arg_char == "A":
            # Special argument ARGA
            arg_type = "core"
            arg_number = arg_char.lower()  # Store as "a"
        else:
            msg = f"Invalid argument character: {arg_char}"
            raise ValueError(msg)

        # Extract function tag if present and not a modifier type
        function_tag: str | None = None
        if tag_part and arg_type != "modifier":
            function_tag = tag_part.lstrip("-").lower()

        # Create normalized form
        normalized_parts = []
        if arg_number:
            normalized_parts.append(arg_number)
        elif arg_type == "modifier":
            normalized_parts.append("m")

        if modifier_type:
            normalized_parts.append(modifier_type)
        elif function_tag:
            normalized_parts.append(function_tag.lower())

        normalized = "_".join(normalized_parts) if normalized_parts else "unknown"

        return cls(
            raw_string=argument,
            normalized=normalized,
            arg_type=arg_type,
            arg_number=arg_number,
            modifier_type=modifier_type,
            prefix=prefix,
            function_tag=function_tag,
        )


@lru_cache(maxsize=512)
def parse_roleset_id(roleset_id: str) -> ParsedRolesetID:
    """Parse a PropBank roleset ID.

    Parameters
    ----------
    roleset_id : str
        Roleset ID to parse.

    Returns
    -------
    ParsedRolesetID
        Parsed roleset ID.
    """
    return ParsedRolesetID.from_string(roleset_id)


@lru_cache(maxsize=512)
def parse_argument(argument: str) -> ParsedArgument:
    """Parse a PropBank argument.

    Parameters
    ----------
    argument : str
        Argument to parse.

    Returns
    -------
    ParsedArgument
        Parsed argument.
    """
    return ParsedArgument.from_string(argument)


@lru_cache(maxsize=1024)
def extract_arg_number(argument: str) -> str:
    """Extract argument number from argument string.

    Parameters
    ----------
    argument : str
        Argument string.

    Returns
    -------
    str
        Argument number.

    Raises
    ------
    ValueError
        If argument is invalid or has no number.
    """
    try:
        parsed = parse_argument(argument)
    except ValueError as e:
        msg = f"Cannot extract arg number from invalid argument: {argument}"
        raise ValueError(msg) from e
    else:
        if parsed.arg_number is None:
            msg = f"Argument has no number: {argument}"
            raise ValueError(msg)
        return parsed.arg_number


@lru_cache(maxsize=1024)
def extract_modifier_type(argument: str) -> str:
    """Extract modifier type from argument string.

    Parameters
    ----------
    argument : str
        Argument string.

    Returns
    -------
    str
        Modifier type.

    Raises
    ------
    ValueError
        If argument is invalid or not a modifier.
    """
    try:
        parsed = parse_argument(argument)
    except ValueError as e:
        msg = f"Cannot extract modifier type from invalid argument: {argument}"
        raise ValueError(msg) from e
    else:
        if parsed.modifier_type is None:
            msg = f"Argument is not a modifier: {argument}"
            raise ValueError(msg)
        return parsed.modifier_type


@lru_cache(maxsize=1024)
def extract_function_tag(argument: str) -> str:
    """Extract function tag from argument string.

    Parameters
    ----------
    argument : str
        Argument string.

    Returns
    -------
    str
        Function tag.

    Raises
    ------
    ValueError
        If argument is invalid or has no function tag.
    """
    try:
        parsed = parse_argument(argument)
    except ValueError as e:
        msg = f"Cannot extract function tag from invalid argument: {argument}"
        raise ValueError(msg) from e
    else:
        if parsed.function_tag is None:
            msg = f"Argument has no function tag: {argument}"
            raise ValueError(msg)
        return parsed.function_tag


@lru_cache(maxsize=1024)
def is_core_argument(argument: str) -> bool:
    """Check if argument is a core argument.

    Parameters
    ----------
    argument : str
        Argument string.

    Returns
    -------
    bool
        True if core argument.
    """
    try:
        parsed = parse_argument(argument)
    except ValueError:
        return False
    else:
        return parsed.arg_type == "core"


@lru_cache(maxsize=1024)
def is_modifier(argument: str) -> bool:
    """Check if argument is a modifier.

    Parameters
    ----------
    argument : str
        Argument string.

    Returns
    -------
    bool
        True if modifier.
    """
    try:
        parsed = parse_argument(argument)
    except ValueError:
        return False
    else:
        return parsed.arg_type == "modifier"


def filter_args_by_properties(  # noqa: C901, PLR0913
    args: list[Role],
    is_core: bool | None = None,
    is_modifier: bool | None = None,
    has_prefix: bool | None = None,
    modifier_type: ModifierType | None = None,
    arg_number: str | None = None,
) -> list[Role]:
    """Filter arguments by their properties.

    Parameters
    ----------
    args : list[Role]
        Arguments to filter.
    is_core : bool | None
        Filter for core arguments.
    is_modifier : bool | None
        Filter for modifiers.
    has_prefix : bool | None
        Filter for arguments with prefix.
    modifier_type : ModifierType | None
        Filter for specific modifier type.
    arg_number : str | None
        Filter for specific argument number (e.g., "0", "1", "2").

    Returns
    -------
    list[Role]
        Filtered arguments.
    """
    # Store function reference to avoid name collision with parameter
    is_modifier_func = globals()["is_modifier"]

    filtered = args

    # Helper to get argnum from Role
    def get_argnum(role: Role) -> str:
        """Reconstruct argnum from Role n and f fields."""
        if role.n in {"M", "m"}:
            # Modifier argument
            if role.f:
                return f"ARGM-{role.f}"
            return "ARGM"
        # Core or special argument
        return f"ARG{role.n}"

    if is_core is not None:
        if is_core:
            filtered = [a for a in filtered if is_core_argument(get_argnum(a))]
        else:
            filtered = [a for a in filtered if not is_core_argument(get_argnum(a))]

    if is_modifier is not None:
        if is_modifier:
            filtered = [a for a in filtered if is_modifier_func(get_argnum(a))]
        else:
            filtered = [a for a in filtered if not is_modifier_func(get_argnum(a))]

    if has_prefix is not None:
        # Prefix checking - reconstruct argnum to check
        if has_prefix:
            filtered = [a for a in filtered if get_argnum(a).startswith(("C-", "R-"))]
        else:
            filtered = [a for a in filtered if not get_argnum(a).startswith(("C-", "R-"))]

    if modifier_type is not None:
        # Only check modifier type for actual modifiers
        filtered = [
            a
            for a in filtered
            if is_modifier_func(get_argnum(a))
            and extract_modifier_type(get_argnum(a)) == modifier_type
        ]

    if arg_number is not None:
        # Filter by specific argument number
        filtered = [
            a
            for a in filtered
            if a.n == arg_number  # Use role.n field directly for argument number
        ]

    return filtered
