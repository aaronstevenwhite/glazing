"""WordNet symbol parser using Pydantic v2 models.

This module provides parsing utilities for WordNet synset IDs, sense keys,
and lemma keys using Pydantic v2 models for validation. Supports offset
extraction, POS detection, and relation filtering. All parsing functions
use LRU caching for better performance.

Classes
-------
ParsedSynsetID
    Parsed WordNet synset ID with offset and POS.
ParsedSenseKey
    Parsed WordNet sense key with full lexical information.
ParsedLemmaKey
    Parsed WordNet lemma key with sense number.

Functions
---------
parse_synset_id
    Parse a WordNet synset ID (e.g., "00001740-n").
parse_sense_key
    Parse a WordNet sense key (e.g., "dog%1:05:00::").
parse_lemma_key
    Parse a WordNet lemma key (e.g., "dog#n#1").
extract_pos_from_synset
    Extract part of speech from synset ID.
extract_pos_from_sense
    Extract part of speech from sense key.
extract_lemma_from_key
    Extract lemma from lemma key.
extract_synset_offset
    Extract 8-digit offset from synset ID.
extract_sense_number
    Extract sense number from sense key.
filter_synsets_by_pos
    Filter synsets by part of speech.
filter_by_relation_type
    Filter pointers by relation type.
normalize_lemma
    Normalize lemma for matching.
normalize_synset_for_matching
    Normalize synset ID for fuzzy matching.
synset_id_to_offset
    Convert synset ID to offset string.
build_synset_id
    Build synset ID from offset and POS.
is_satellite_adjective
    Check if POS is satellite adjective.
is_valid_synset_id
    Validate synset ID format.
is_valid_sense_key
    Validate sense key format.
is_valid_lemma_key
    Validate lemma key format.

Type Aliases
------------
POSType
    Literal type for WordNet parts of speech.
SynsetType
    Literal type for WordNet identifier types.

Examples
--------
>>> from glazing.wordnet.symbol_parser import parse_synset_id
>>> parsed = parse_synset_id("00001740-n")
>>> parsed.offset
'00001740'
>>> parsed.pos
'n'

>>> from glazing.wordnet.symbol_parser import parse_sense_key
>>> sense = parse_sense_key("dog%1:05:00::")
>>> sense.lemma
'dog'
>>> sense.ss_type
1
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import TYPE_CHECKING, Literal

from pydantic import Field, field_validator

from glazing.symbols import BaseSymbol
from glazing.wordnet.types import WordNetPOS

if TYPE_CHECKING:
    from glazing.wordnet.models import Pointer, Synset

# Type aliases
type POSType = Literal["n", "v", "a", "r", "s"]
type SynsetType = Literal["synset", "sense", "lemma"]

# Validation patterns
SYNSET_ID_PATTERN = re.compile(r"^(\d{8})-([nvasr])$")
SENSE_KEY_PATTERN = re.compile(r"^(.+)%(\d+):(\d{2}):(\d{2}):(.*)$")
LEMMA_KEY_PATTERN = re.compile(r"^(.+)#([nvasr])#(\d+)$")

# POS number mapping
POS_MAP = {
    "1": "n",  # noun
    "2": "v",  # verb
    "3": "a",  # adjective
    "4": "r",  # adverb
    "5": "s",  # satellite adjective
}

POS_REVERSE_MAP = {v: k for k, v in POS_MAP.items()}


class ParsedSynsetID(BaseSymbol):
    """Parsed WordNet synset ID.

    Attributes
    ----------
    raw_string : str
        Original synset ID string.
    normalized : str
        Normalized synset ID.
    symbol_type : Literal["synset"]
        Always "synset".
    dataset : Literal["wordnet"]
        Always "wordnet".
    offset : str
        8-digit synset offset.
    pos : POSType
        Part of speech.
    numeric_offset : int
        Numeric value of the offset.
    """

    symbol_type: Literal["synset"] = "synset"
    dataset: Literal["wordnet"] = "wordnet"
    offset: str = Field(..., pattern=r"^\d{8}$")
    pos: POSType
    numeric_offset: int = Field(..., ge=0)

    @field_validator("raw_string")
    @classmethod
    def validate_synset_format(cls, v: str) -> str:
        """Validate synset ID format."""
        # Try with hyphen
        if SYNSET_ID_PATTERN.match(v):
            return v
        # Try without hyphen (e.g., "00001740n")
        if len(v) == 9 and v[:8].isdigit() and v[8] in "nvasr":
            return v
        msg = f"Invalid synset ID format: {v}"
        raise ValueError(msg)

    @classmethod
    def from_string(cls, synset_id: str) -> ParsedSynsetID:
        """Create from synset ID string.

        Parameters
        ----------
        synset_id : str
            Synset ID (e.g., "00001740-n", "00001740n").

        Returns
        -------
        ParsedSynsetID
            Parsed synset ID.
        """
        # Try with hyphen
        match = SYNSET_ID_PATTERN.match(synset_id)
        if match:
            offset = match.group(1)
            pos: POSType = match.group(2)  # type: ignore[assignment]
            normalized = f"{offset}-{pos}"
        # Try without hyphen
        elif len(synset_id) == 9 and synset_id[:8].isdigit() and synset_id[8] in "nvasr":
            offset = synset_id[:8]
            pos = synset_id[8]  # type: ignore[assignment]
            normalized = f"{offset}-{pos}"
        else:
            msg = f"Invalid synset ID format: {synset_id}"
            raise ValueError(msg)

        return cls(
            raw_string=synset_id,
            normalized=normalized,
            offset=offset,
            pos=pos,
            numeric_offset=int(offset),
        )


class ParsedSenseKey(BaseSymbol):
    """Parsed WordNet sense key.

    Attributes
    ----------
    raw_string : str
        Original sense key string.
    normalized : str
        Normalized lemma.
    symbol_type : Literal["sense_key"]
        Always "sense_key".
    dataset : Literal["wordnet"]
        Always "wordnet".
    lemma : str
        Word lemma.
    ss_type : int
        Synset type (POS number).
    pos : POSType
        Part of speech.
    lex_filenum : int
        Lexical file number.
    lex_id : int
        Lexical ID.
    head : str
        Head word for satellites (empty string if none).
    """

    symbol_type: Literal["sense_key"] = "sense_key"
    dataset: Literal["wordnet"] = "wordnet"
    lemma: str = Field(..., min_length=1)
    ss_type: int = Field(..., ge=1, le=5)
    pos: POSType
    lex_filenum: int = Field(..., ge=0, le=99)
    lex_id: int = Field(..., ge=0, le=99)
    head: str = ""

    @field_validator("raw_string")
    @classmethod
    def validate_sense_key_format(cls, v: str) -> str:
        """Validate sense key format."""
        if not SENSE_KEY_PATTERN.match(v):
            msg = f"Invalid sense key format: {v}"
            raise ValueError(msg)
        return v

    @classmethod
    def from_string(cls, sense_key: str) -> ParsedSenseKey:
        """Create from sense key string.

        Parameters
        ----------
        sense_key : str
            Sense key (e.g., "dog%1:05:00::").

        Returns
        -------
        ParsedSenseKey
            Parsed sense key.
        """
        match = SENSE_KEY_PATTERN.match(sense_key)
        if not match:
            msg = f"Invalid sense key format: {sense_key}"
            raise ValueError(msg)

        lemma = match.group(1)
        pos_num = match.group(2)
        lex_filenum = int(match.group(3))
        lex_id = int(match.group(4))
        raw_head = match.group(5) if match.group(5) else ""
        # Handle double colon case where raw_head is just ":"
        head = "" if raw_head == ":" else raw_head

        # Convert POS number to letter
        ss_type = int(pos_num)
        pos = POS_MAP.get(pos_num)
        if not pos:
            msg = f"Invalid ss_type in sense key: {pos_num}"
            raise ValueError(msg)

        # Normalize lemma (spaces to underscores)
        normalized_lemma = cls.normalize_string(lemma)

        return cls(
            raw_string=sense_key,
            normalized=normalized_lemma,
            lemma=lemma,
            ss_type=ss_type,
            pos=pos,  # type: ignore[arg-type]
            lex_filenum=lex_filenum,
            lex_id=lex_id,
            head=head,
        )


class ParsedLemmaKey(BaseSymbol):
    """Parsed WordNet lemma key.

    Attributes
    ----------
    raw_string : str
        Original lemma key string.
    normalized : str
        Normalized lemma.
    symbol_type : Literal["lemma_key"]
        Always "lemma_key".
    dataset : Literal["wordnet"]
        Always "wordnet".
    lemma : str
        Word lemma.
    pos : POSType
        Part of speech.
    sense_number : int
        Sense number.
    """

    symbol_type: Literal["lemma_key"] = "lemma_key"
    dataset: Literal["wordnet"] = "wordnet"
    lemma: str = Field(..., min_length=1)
    pos: POSType
    sense_number: int = Field(..., ge=0)

    @field_validator("raw_string")
    @classmethod
    def validate_lemma_key_format(cls, v: str) -> str:
        """Validate lemma key format."""
        if not LEMMA_KEY_PATTERN.match(v):
            msg = f"Invalid lemma key format: {v}"
            raise ValueError(msg)
        return v

    @classmethod
    def from_string(cls, lemma_key: str) -> ParsedLemmaKey:
        """Create from lemma key string.

        Parameters
        ----------
        lemma_key : str
            Lemma key (e.g., "dog#n#1").

        Returns
        -------
        ParsedLemmaKey
            Parsed lemma key.
        """
        match = LEMMA_KEY_PATTERN.match(lemma_key)
        if not match:
            msg = f"Invalid lemma key format: {lemma_key}"
            raise ValueError(msg)

        lemma = match.group(1)
        pos: POSType = match.group(2)  # type: ignore[assignment]
        sense_number = int(match.group(3))

        # Normalize lemma (spaces to underscores)
        normalized_lemma = cls.normalize_string(lemma)

        return cls(
            raw_string=lemma_key,
            normalized=normalized_lemma,
            lemma=lemma,
            pos=pos,
            sense_number=sense_number,
        )


@lru_cache(maxsize=512)
def parse_synset_id(synset_id: str) -> ParsedSynsetID:
    """Parse a WordNet synset ID.

    Parameters
    ----------
    synset_id : str
        Synset ID to parse.

    Returns
    -------
    ParsedSynsetID
        Parsed synset ID.
    """
    return ParsedSynsetID.from_string(synset_id)


@lru_cache(maxsize=512)
def parse_sense_key(sense_key: str) -> ParsedSenseKey:
    """Parse a WordNet sense key.

    Parameters
    ----------
    sense_key : str
        Sense key to parse.

    Returns
    -------
    ParsedSenseKey
        Parsed sense key.
    """
    return ParsedSenseKey.from_string(sense_key)


@lru_cache(maxsize=512)
def parse_lemma_key(lemma_key: str) -> ParsedLemmaKey:
    """Parse a WordNet lemma key.

    Parameters
    ----------
    lemma_key : str
        Lemma key to parse.

    Returns
    -------
    ParsedLemmaKey
        Parsed lemma key.
    """
    return ParsedLemmaKey.from_string(lemma_key)


def extract_pos_from_synset(synset_id: str) -> WordNetPOS:
    """Extract POS from synset ID.

    Parameters
    ----------
    synset_id : str
        Synset ID.

    Returns
    -------
    WordNetPOS
        Part of speech.

    Raises
    ------
    ValueError
        If synset_id is invalid.
    """
    try:
        parsed = parse_synset_id(synset_id)
    except ValueError as e:
        msg = f"Cannot extract POS from invalid synset ID: {synset_id}"
        raise ValueError(msg) from e
    else:
        return parsed.pos


def extract_pos_from_sense(sense_key: str) -> WordNetPOS:
    """Extract POS from a sense key.

    Parameters
    ----------
    sense_key : str
        Sense key.

    Returns
    -------
    WordNetPOS
        The POS.

    Raises
    ------
    ValueError
        If sense_key is invalid.
    """
    try:
        parsed = parse_sense_key(sense_key)
    except ValueError as e:
        msg = f"Cannot extract POS from invalid sense key: {sense_key}"
        raise ValueError(msg) from e
    else:
        return parsed.pos


def extract_lemma_from_key(lemma_key: str) -> str:
    """Extract lemma from a lemma key or sense key.

    Parameters
    ----------
    lemma_key : str
        Lemma key or sense key.

    Returns
    -------
    str
        The lemma.

    Raises
    ------
    ValueError
        If key is neither a valid lemma key nor sense key.
    """
    # Try as lemma key first
    try:
        parsed_lemma = parse_lemma_key(lemma_key)
    except ValueError:
        pass
    else:
        return parsed_lemma.lemma

    # Try as sense key
    try:
        parsed_sense = parse_sense_key(lemma_key)
    except ValueError as e:
        msg = f"Cannot extract lemma from invalid key: {lemma_key}"
        raise ValueError(msg) from e
    else:
        return parsed_sense.lemma


def extract_synset_offset(synset_id: str) -> str:
    """Extract offset from synset ID.

    Parameters
    ----------
    synset_id : str
        Synset ID.

    Returns
    -------
    str
        The 8-digit offset.

    Raises
    ------
    ValueError
        If synset_id is invalid.
    """
    try:
        parsed = parse_synset_id(synset_id)
    except ValueError as e:
        msg = f"Cannot extract offset from invalid synset ID: {synset_id}"
        raise ValueError(msg) from e
    else:
        return parsed.offset


def extract_sense_number(sense_key: str) -> int:
    """Extract sense number (lex_id) from a sense key.

    Parameters
    ----------
    sense_key : str
        Sense key.

    Returns
    -------
    int
        Sense number (lex_id).

    Raises
    ------
    ValueError
        If sense_key is invalid.
    """
    try:
        parsed = parse_sense_key(sense_key)
    except ValueError as e:
        msg = f"Cannot extract sense number from invalid sense key: {sense_key}"
        raise ValueError(msg) from e
    else:
        return parsed.lex_id


@lru_cache(maxsize=1024)
def normalize_lemma(lemma: str) -> str:
    """Normalize a lemma for matching.

    Parameters
    ----------
    lemma : str
        Lemma to normalize.

    Returns
    -------
    str
        Normalized lemma.
    """
    return BaseSymbol.normalize_string(lemma)


@lru_cache(maxsize=1024)
def normalize_synset_for_matching(synset_id: str) -> str:
    """Normalize a synset ID for matching.

    Parameters
    ----------
    synset_id : str
        Synset ID to normalize.

    Returns
    -------
    str
        Normalized synset ID.

    Raises
    ------
    ValueError
        If synset_id is invalid.
    """
    try:
        parsed = parse_synset_id(synset_id)
    except ValueError as e:
        msg = f"Cannot normalize invalid synset ID: {synset_id}"
        raise ValueError(msg) from e
    else:
        return parsed.normalized


def is_satellite_adjective(pos: WordNetPOS) -> bool:
    """Check if POS is satellite adjective.

    Parameters
    ----------
    pos : WordNetPOS
        Part of speech.

    Returns
    -------
    bool
        True if satellite adjective.
    """
    return pos == "s"


def is_valid_synset_id(synset_id: str) -> bool:
    """Check if a string is a valid synset ID.

    Parameters
    ----------
    synset_id : str
        String to check.

    Returns
    -------
    bool
        True if valid synset ID.
    """
    try:
        parse_synset_id(synset_id)
    except ValueError:
        return False
    else:
        return True


def is_valid_sense_key(sense_key: str) -> bool:
    """Check if a string is a valid sense key.

    Parameters
    ----------
    sense_key : str
        String to check.

    Returns
    -------
    bool
        True if valid sense key.
    """
    try:
        parse_sense_key(sense_key)
    except ValueError:
        return False
    else:
        return True


def is_valid_lemma_key(lemma_key: str) -> bool:
    """Check if a string is a valid lemma key.

    Parameters
    ----------
    lemma_key : str
        String to check.

    Returns
    -------
    bool
        True if valid lemma key.
    """
    try:
        parse_lemma_key(lemma_key)
    except ValueError:
        return False
    else:
        return True


def synset_id_to_offset(synset_id: str) -> str:
    """Convert synset ID to offset.

    Parameters
    ----------
    synset_id : str
        Synset ID.

    Returns
    -------
    str
        8-digit offset.

    Raises
    ------
    ValueError
        If synset_id is invalid.
    """
    try:
        parsed = parse_synset_id(synset_id)
    except ValueError as e:
        msg = f"Cannot convert invalid synset ID to offset: {synset_id}"
        raise ValueError(msg) from e
    else:
        return parsed.offset


def build_synset_id(offset: str, pos: WordNetPOS) -> str:
    """Build a synset ID from offset and POS.

    Parameters
    ----------
    offset : str
        8-digit offset.
    pos : WordNetPOS
        Part of speech.

    Returns
    -------
    str
        Synset ID.
    """
    return f"{offset}-{pos}"


def filter_synsets_by_pos(
    synsets: list[Synset],
    pos: WordNetPOS | None = None,
) -> list[Synset]:
    """Filter synsets by part of speech.

    Parameters
    ----------
    synsets : list[Synset]
        List of synsets.
    pos : WordNetPOS | None
        POS to filter by (n, v, a, r, s).

    Returns
    -------
    list[Synset]
        Filtered synsets.
    """
    if pos is None:
        return synsets

    # Simply filter by matching POS
    return [s for s in synsets if s.ss_type == pos]


def filter_by_relation_type(
    pointers: list[Pointer],
    relation_type: str | None = None,
) -> list[Pointer]:
    """Filter pointers by relation type.

    Parameters
    ----------
    pointers : list[Pointer]
        List of pointers to filter.
    relation_type : str | None
        Filter by relation type (e.g., "hypernym", "hyponym", "antonym").

    Returns
    -------
    list[Pointer]
        Filtered list of pointers.
    """
    if relation_type is None:
        return pointers

    # Map relation types to pointer symbols
    relation_map = {
        "hypernym": "@",
        "hyponym": "~",
        "instance_hypernym": "@i",
        "instance_hyponym": "~i",
        "member_holonym": "#m",
        "part_holonym": "#p",
        "substance_holonym": "#s",
        "member_meronym": "%m",
        "part_meronym": "%p",
        "substance_meronym": "%s",
        "antonym": "!",
        "derivation": "+",
        "pertainym": "\\",
        "attribute": "=",
        "cause": ">",
        "entailment": "*",
        "similar_to": "&",
        "also": "^",
        "domain_topic": ";c",
        "domain_region": ";r",
        "domain_usage": ";u",
        "participle": "<",
        "verb_group": "$",
    }

    symbol = relation_map.get(relation_type)
    if not symbol:
        return pointers

    return [p for p in pointers if p.symbol == symbol]
