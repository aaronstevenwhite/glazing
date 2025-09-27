"""PropBank symbol parser.

This module provides parsing utilities for PropBank argument symbols,
including core arguments, modifier arguments, and special prefixes.

Classes
-------
ParsedPropBankArg
    Parsed PropBank argument information.

Functions
---------
parse_core_arg
    Parse a PropBank core argument.
parse_modifier_arg
    Parse a PropBank modifier argument.
parse_continuation_arg
    Parse a PropBank continuation argument.
parse_reference_arg
    Parse a PropBank reference argument.
is_core_arg
    Check if an argument is a core argument.
is_modifier_arg
    Check if an argument is a modifier argument.
is_continuation_arg
    Check if an argument is a continuation.
is_reference_arg
    Check if an argument is a reference.
extract_arg_number
    Extract the argument number from ARG notation.
extract_modifier_type
    Extract the modifier type from ARGM notation.
"""

from __future__ import annotations

import re
from typing import Literal, TypedDict, cast

from glazing.propbank.types import (
    ContinuationArgumentType,
    CoreArgumentType,
    ModifierArgumentType,
    PropBankArgumentType,
    ReferenceArgumentType,
)


class ParsedPropBankArg(TypedDict):
    """Parsed PropBank argument.

    Attributes
    ----------
    raw_string : str
        Original unparsed argument string.
    base_arg : str
        Base argument name without prefixes.
    arg_number : int | None
        Argument number for ARG0-7, ARGA.
    modifier_type : str | None
        Modifier type for ARGM arguments.
    prefix : Literal["C", "R"] | None
        Continuation or reference prefix.
    is_core : bool
        Whether this is a core argument.
    is_modifier : bool
        Whether this is a modifier argument.
    arg_type : Literal["core", "modifier", "special"]
        Type of argument.
    """

    raw_string: str
    base_arg: str
    arg_number: int | None
    modifier_type: str | None
    prefix: Literal["C", "R"] | None
    is_core: bool
    is_modifier: bool
    arg_type: Literal["core", "modifier", "special"]


# Patterns for parsing PropBank arguments
CORE_ARG_PATTERN = re.compile(r"^(C-|R-)?(ARG)([0-7]|A)$")
MODIFIER_ARG_PATTERN = re.compile(r"^(C-|R-)?(ARGM)-(.+)$")
SPECIAL_ARG_PATTERN = re.compile(r"^(ARGA|ARGM-TOP)$")


def parse_propbank_arg(arg: PropBankArgumentType) -> ParsedPropBankArg:
    """Parse a PropBank argument symbol.

    Parameters
    ----------
    arg : PropBankArgumentType
        PropBank argument string (e.g., "ARG0", "ARGM-LOC", "C-ARG1").

    Returns
    -------
    ParsedPropBankArg
        Parsed argument information.

    Examples
    --------
    >>> parse_propbank_arg("ARG0")
    {'raw_string': 'ARG0', 'arg_number': 0, 'is_core': True, ...}
    >>> parse_propbank_arg("ARGM-LOC")
    {'raw_string': 'ARGM-LOC', 'modifier_type': 'LOC', 'is_modifier': True, ...}
    >>> parse_propbank_arg("C-ARG1")
    {'raw_string': 'C-ARG1', 'prefix': 'C', 'arg_number': 1, ...}
    """
    result = ParsedPropBankArg(
        raw_string=arg,
        base_arg=arg,
        arg_number=None,
        modifier_type=None,
        prefix=None,
        is_core=False,
        is_modifier=False,
        arg_type="special",
    )

    # Check for core arguments
    if match := CORE_ARG_PATTERN.match(arg):
        prefix = match.group(1)
        if prefix:
            result["prefix"] = prefix.rstrip("-")  # type: ignore[typeddict-item]

        arg_char = match.group(3)
        if arg_char == "A":
            result["arg_number"] = -1  # Special value for ARGA
        else:
            result["arg_number"] = int(arg_char)

        result["base_arg"] = f"ARG{arg_char}"
        result["is_core"] = True
        result["arg_type"] = "core"
        return result

    # Check for modifier arguments
    if match := MODIFIER_ARG_PATTERN.match(arg):
        prefix = match.group(1)
        if prefix:
            result["prefix"] = prefix.rstrip("-")  # type: ignore[typeddict-item]

        result["modifier_type"] = match.group(3)
        result["base_arg"] = f"ARGM-{match.group(3)}"
        result["is_modifier"] = True
        result["arg_type"] = "modifier"
        return result

    # Check for special arguments
    if SPECIAL_ARG_PATTERN.match(arg):
        if arg == "ARGA":
            result["arg_number"] = -1
            result["is_core"] = True
            result["arg_type"] = "core"
        else:  # ARGM-TOP
            result["modifier_type"] = "TOP"
            result["is_modifier"] = True
            result["arg_type"] = "modifier"

    return result


def parse_core_arg(arg: CoreArgumentType) -> ParsedPropBankArg:
    """Parse a PropBank core argument.

    Parameters
    ----------
    arg : CoreArgumentType
        Core argument string (e.g., "ARG0", "ARG1", "ARGA").

    Returns
    -------
    ParsedPropBankArg
        Parsed argument information.

    Examples
    --------
    >>> parse_core_arg("ARG0")
    {'raw_string': 'ARG0', 'arg_number': 0, 'is_core': True, ...}
    >>> parse_core_arg("ARGA")
    {'raw_string': 'ARGA', 'arg_number': -1, 'is_core': True, ...}
    """
    result = ParsedPropBankArg(
        raw_string=arg,
        base_arg=arg,
        arg_number=None,
        modifier_type=None,
        prefix=None,
        is_core=True,
        is_modifier=False,
        arg_type="core",
    )

    if arg == "ARGA":
        result["arg_number"] = -1
    else:
        # Extract number from ARG0-7
        result["arg_number"] = int(arg[3])  # Extract digit after "ARG"

    return result


def parse_modifier_arg(arg: ModifierArgumentType) -> ParsedPropBankArg:
    """Parse a PropBank modifier argument.

    Parameters
    ----------
    arg : ModifierArgumentType
        Modifier argument string (e.g., "ARGM-LOC", "ARGM-TMP").

    Returns
    -------
    ParsedPropBankArg
        Parsed argument information.

    Examples
    --------
    >>> parse_modifier_arg("ARGM-LOC")
    {'raw_string': 'ARGM-LOC', 'modifier_type': 'LOC', 'is_modifier': True, ...}
    >>> parse_modifier_arg("ARGM-TMP")
    {'raw_string': 'ARGM-TMP', 'modifier_type': 'TMP', 'is_modifier': True, ...}
    """
    result = ParsedPropBankArg(
        raw_string=arg,
        base_arg=arg,
        arg_number=None,
        modifier_type=None,
        prefix=None,
        is_core=False,
        is_modifier=True,
        arg_type="modifier",
    )

    # Extract modifier type after "ARGM-"
    result["modifier_type"] = arg[5:]  # Remove "ARGM-" prefix

    return result


def parse_continuation_arg(arg: ContinuationArgumentType) -> ParsedPropBankArg:
    """Parse a PropBank continuation argument.

    Parameters
    ----------
    arg : ContinuationArgumentType
        Continuation argument string (e.g., "C-ARG0", "C-ARGM-LOC").

    Returns
    -------
    ParsedPropBankArg
        Parsed argument information.

    Examples
    --------
    >>> parse_continuation_arg("C-ARG0")
    {'raw_string': 'C-ARG0', 'prefix': 'C', 'arg_number': 0, ...}
    >>> parse_continuation_arg("C-ARGM-LOC")
    {'raw_string': 'C-ARGM-LOC', 'prefix': 'C', 'modifier_type': 'LOC', ...}
    """
    result = ParsedPropBankArg(
        raw_string=arg,
        base_arg=arg[2:],  # Remove "C-" prefix
        arg_number=None,
        modifier_type=None,
        prefix="C",
        is_core=False,
        is_modifier=False,
        arg_type="special",
    )

    base_arg = arg[2:]  # Remove "C-" prefix
    if base_arg.startswith("ARG") and base_arg[3:].isdigit():
        # Core continuation argument
        result["arg_number"] = int(base_arg[3])
        result["is_core"] = True
        result["arg_type"] = "core"
    elif base_arg.startswith("ARGM-"):
        # Modifier continuation argument
        result["modifier_type"] = base_arg[5:]  # Remove "ARGM-" prefix
        result["is_modifier"] = True
        result["arg_type"] = "modifier"

    return result


def parse_reference_arg(arg: ReferenceArgumentType) -> ParsedPropBankArg:
    """Parse a PropBank reference argument.

    Parameters
    ----------
    arg : ReferenceArgumentType
        Reference argument string (e.g., "R-ARG0", "R-ARGM-LOC").

    Returns
    -------
    ParsedPropBankArg
        Parsed argument information.

    Examples
    --------
    >>> parse_reference_arg("R-ARG0")
    {'raw_string': 'R-ARG0', 'prefix': 'R', 'arg_number': 0, ...}
    >>> parse_reference_arg("R-ARGM-LOC")
    {'raw_string': 'R-ARGM-LOC', 'prefix': 'R', 'modifier_type': 'LOC', ...}
    """
    result = ParsedPropBankArg(
        raw_string=arg,
        base_arg=arg[2:],  # Remove "R-" prefix
        arg_number=None,
        modifier_type=None,
        prefix="R",
        is_core=False,
        is_modifier=False,
        arg_type="special",
    )

    base_arg = arg[2:]  # Remove "R-" prefix
    if base_arg.startswith("ARG") and base_arg[3:].isdigit():
        # Core reference argument
        result["arg_number"] = int(base_arg[3])
        result["is_core"] = True
        result["arg_type"] = "core"
    elif base_arg.startswith("ARGM-"):
        # Modifier reference argument
        result["modifier_type"] = base_arg[5:]  # Remove "ARGM-" prefix
        result["is_modifier"] = True
        result["arg_type"] = "modifier"

    return result


def is_core_arg(arg: PropBankArgumentType) -> bool:
    """Check if an argument is a core argument.

    Parameters
    ----------
    arg : PropBankArgumentType
        PropBank argument string.

    Returns
    -------
    bool
        True if argument is ARG0-7 or ARGA.

    Examples
    --------
    >>> is_core_arg("ARG0")
    True
    >>> is_core_arg("ARGM-LOC")
    False
    """
    return bool(CORE_ARG_PATTERN.match(arg))


def is_modifier_arg(arg: PropBankArgumentType) -> bool:
    """Check if an argument is a modifier argument.

    Parameters
    ----------
    arg : PropBankArgumentType
        PropBank argument string.

    Returns
    -------
    bool
        True if argument is ARGM-*.

    Examples
    --------
    >>> is_modifier_arg("ARGM-LOC")
    True
    >>> is_modifier_arg("ARG0")
    False
    """
    return bool(MODIFIER_ARG_PATTERN.match(arg))


def is_continuation_arg(arg: PropBankArgumentType) -> bool:
    """Check if an argument is a continuation.

    Parameters
    ----------
    arg : PropBankArgumentType
        PropBank argument string.

    Returns
    -------
    bool
        True if argument has C- prefix.

    Examples
    --------
    >>> is_continuation_arg("C-ARG1")
    True
    >>> is_continuation_arg("ARG1")
    False
    """
    return arg.startswith("C-")


def is_reference_arg(arg: PropBankArgumentType) -> bool:
    """Check if an argument is a reference.

    Parameters
    ----------
    arg : PropBankArgumentType
        PropBank argument string.

    Returns
    -------
    bool
        True if argument has R- prefix.

    Examples
    --------
    >>> is_reference_arg("R-ARG0")
    True
    >>> is_reference_arg("ARG0")
    False
    """
    return arg.startswith("R-")


def extract_arg_number(
    arg: CoreArgumentType | ContinuationArgumentType | ReferenceArgumentType,
) -> int | None:
    """Extract the argument number from ARG notation.

    Parameters
    ----------
    arg : CoreArgumentType | ContinuationArgumentType | ReferenceArgumentType
        PropBank argument string.

    Returns
    -------
    int | None
        Argument number (0-7) or -1 for ARGA, None if not a numbered arg.

    Examples
    --------
    >>> extract_arg_number("ARG0")
    0
    >>> extract_arg_number("C-ARG1")
    1
    >>> extract_arg_number("ARGA")
    -1
    """
    if arg.startswith("C-"):
        parsed = parse_continuation_arg(arg)  # type: ignore[arg-type]
    elif arg.startswith("R-"):
        parsed = parse_reference_arg(arg)  # type: ignore[arg-type]
    else:
        parsed = parse_core_arg(arg)  # type: ignore[arg-type]
    return parsed["arg_number"]


def extract_modifier_type(
    arg: ModifierArgumentType | ContinuationArgumentType | ReferenceArgumentType,
) -> str | None:
    """Extract the modifier type from ARGM notation.

    Parameters
    ----------
    arg : ModifierArgumentType | ContinuationArgumentType | ReferenceArgumentType
        PropBank argument string.

    Returns
    -------
    str | None
        Modifier type (e.g., "LOC", "TMP") or None if not a modifier.

    Examples
    --------
    >>> extract_modifier_type("ARGM-LOC")
    'LOC'
    >>> extract_modifier_type("C-ARGM-TMP")
    'TMP'
    """
    if arg.startswith("C-"):
        parsed = parse_continuation_arg(arg)  # type: ignore[arg-type]
    elif arg.startswith("R-"):
        parsed = parse_reference_arg(arg)  # type: ignore[arg-type]
    else:
        parsed = parse_modifier_arg(arg)  # type: ignore[arg-type]
    return parsed["modifier_type"]


def normalize_arg_for_matching(
    arg: CoreArgumentType | ModifierArgumentType | ContinuationArgumentType | ReferenceArgumentType,
) -> str:
    """Normalize an argument for fuzzy matching.

    Parameters
    ----------
    arg : CoreArgumentType | ModifierArgumentType | ContinuationArgumentType | ReferenceArgumentType
        PropBank argument string.

    Returns
    -------
    str
        Normalized argument string.

    Examples
    --------
    >>> normalize_arg_for_matching("C-ARG0")
    'arg0'
    >>> normalize_arg_for_matching("ARGM-LOC")
    'argm loc'
    """
    # Remove prefixes
    normalized_arg = cast(str, arg)
    if normalized_arg.startswith(("C-", "R-")):
        normalized_arg = normalized_arg[2:]

    # Normalize and lowercase
    return normalized_arg.lower().replace("-", " ")
