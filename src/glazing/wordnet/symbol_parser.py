"""WordNet symbol parser.

This module provides parsing utilities for WordNet synset IDs, sense keys,
and lemma keys.

Classes
-------
ParsedWordNetSymbol
    Parsed WordNet symbol information.

Functions
---------
parse_synset_id
    Parse a WordNet synset ID.
parse_sense_key
    Parse a WordNet sense key.
parse_lemma_key
    Parse a lemma key.
extract_pos_from_synset
    Extract POS from synset ID.
extract_sense_number
    Extract sense number from sense key.
normalize_lemma
    Normalize a lemma for matching.
filter_by_relation_type
    Filter pointers by relation type.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal, TypedDict, cast

from glazing.wordnet.types import Lemma, LemmaKey, Offset, SenseKey, SynsetID, WordNetPOS

if TYPE_CHECKING:
    from glazing.wordnet.models import Pointer


class ParsedWordNetSymbol(TypedDict):
    """Parsed WordNet symbol.

    Attributes
    ----------
    raw_string : str
        Original unparsed string.
    symbol_type : Literal["synset", "sense_key", "lemma"]
        Type of WordNet symbol.
    offset : str | None
        8-digit synset offset.
    pos : WordNetPOS | None
        Part of speech (n, v, a, r, s).
    lemma : str | None
        Word lemma.
    sense_number : int | None
        Sense number.
    lex_filenum : int | None
        Lexical file number.
    lex_id : int | None
        Lexical ID.
    head_word : str | None
        Head word for satellites.
    """

    raw_string: str
    symbol_type: Literal["synset", "sense_key", "lemma"]
    offset: str | None
    pos: WordNetPOS | None
    lemma: str | None
    sense_number: int | None
    lex_filenum: int | None
    lex_id: int | None
    head_word: str | None


# Patterns for parsing WordNet symbols
SYNSET_ID_PATTERN = re.compile(r"^(\d{8})-([nvasr])$")
SENSE_KEY_PATTERN = re.compile(r"^(.+)%(\d+):(\d+):(\d+)(?:::(.+))?$")
LEMMA_KEY_PATTERN = re.compile(r"^(.+)#([nvasr])#(\d+)$")

# Map between numeric POS and letter codes
POS_MAP = {
    "1": "n",  # noun
    "2": "v",  # verb
    "3": "a",  # adjective
    "4": "r",  # adverb
    "5": "s",  # satellite adjective
}

POS_REVERSE_MAP = {v: k for k, v in POS_MAP.items()}


def parse_synset_id(synset_id: SynsetID) -> ParsedWordNetSymbol:
    """Parse a WordNet synset ID.

    Parameters
    ----------
    synset_id : SynsetID
        Synset ID (e.g., "00001740-n", "00001740n").

    Returns
    -------
    ParsedWordNetSymbol
        Parsed synset information.

    Examples
    --------
    >>> parse_synset_id("00001740-n")
    {'raw_string': '00001740-n', 'offset': '00001740', 'pos': 'n', ...}
    >>> parse_synset_id("02084442v")
    {'raw_string': '02084442v', 'offset': '02084442', 'pos': 'v', ...}
    """
    result = ParsedWordNetSymbol(
        raw_string=synset_id,
        symbol_type="synset",
        offset=None,
        pos=None,
        lemma=None,
        sense_number=None,
        lex_filenum=None,
        lex_id=None,
        head_word=None,
    )

    # Try with hyphen
    if match := SYNSET_ID_PATTERN.match(synset_id):
        result["offset"] = match.group(1)
        result["pos"] = cast(WordNetPOS, match.group(2))
    # Try without hyphen
    elif len(synset_id) == 9 and synset_id[:8].isdigit() and synset_id[8] in "nvasr":
        result["offset"] = synset_id[:8]
        result["pos"] = cast(WordNetPOS, synset_id[8])

    return result


def parse_sense_key(sense_key: SenseKey) -> ParsedWordNetSymbol:
    """Parse a WordNet sense key.

    Parameters
    ----------
    sense_key : SenseKey
        Sense key (e.g., "dog%1:05:00::", "give%2:40:00::").

    Returns
    -------
    ParsedWordNetSymbol
        Parsed sense key information.

    Examples
    --------
    >>> parse_sense_key("dog%1:05:00::")
    {'raw_string': 'dog%1:05:00::', 'lemma': 'dog', 'pos': 'n', ...}
    >>> parse_sense_key("give%2:40:00::")
    {'raw_string': 'give%2:40:00::', 'lemma': 'give', 'pos': 'v', ...}
    """
    result = ParsedWordNetSymbol(
        raw_string=sense_key,
        symbol_type="sense_key",
        offset=None,
        pos=None,
        lemma=None,
        sense_number=None,
        lex_filenum=None,
        lex_id=None,
        head_word=None,
    )

    if match := SENSE_KEY_PATTERN.match(sense_key):
        result["lemma"] = match.group(1)

        # Convert numeric POS to letter
        pos_num = match.group(2)
        result["pos"] = cast(WordNetPOS | None, POS_MAP.get(pos_num))

        result["lex_filenum"] = int(match.group(3))
        result["lex_id"] = int(match.group(4))

        # Head word for satellites (if present)
        if match.group(5):
            result["head_word"] = match.group(5)

    return result


def parse_lemma_key(lemma_key: LemmaKey) -> ParsedWordNetSymbol:
    """Parse a lemma key.

    Parameters
    ----------
    lemma_key : LemmaKey
        Lemma key (e.g., "dog#n#1", "give#v#2").

    Returns
    -------
    ParsedWordNetSymbol
        Parsed lemma information.

    Examples
    --------
    >>> parse_lemma_key("dog#n#1")
    {'raw_string': 'dog#n#1', 'lemma': 'dog', 'pos': 'n', 'sense_number': 1, ...}
    """
    result = ParsedWordNetSymbol(
        raw_string=lemma_key,
        symbol_type="lemma",
        offset=None,
        pos=None,
        lemma=None,
        sense_number=None,
        lex_filenum=None,
        lex_id=None,
        head_word=None,
    )

    if match := LEMMA_KEY_PATTERN.match(lemma_key):
        result["lemma"] = match.group(1)
        result["pos"] = cast(WordNetPOS, match.group(2))
        result["sense_number"] = int(match.group(3))

    return result


def extract_pos_from_synset(synset_id: SynsetID) -> WordNetPOS | None:
    """Extract POS from synset ID.

    Parameters
    ----------
    synset_id : SynsetID
        Synset ID.

    Returns
    -------
    WordNetPOS | None
        POS letter (n, v, a, r, s) or None.

    Examples
    --------
    >>> extract_pos_from_synset("00001740-n")
    'n'
    >>> extract_pos_from_synset("02084442v")
    'v'
    """
    parsed = parse_synset_id(synset_id)
    return parsed["pos"]


def extract_sense_number(sense_key: SenseKey) -> int | None:
    """Extract sense number from sense key.

    The sense number is derived from the lex_id field.

    Parameters
    ----------
    sense_key : SenseKey
        WordNet sense key.

    Returns
    -------
    int | None
        Sense number or None.

    Examples
    --------
    >>> extract_sense_number("dog%1:05:00::")
    0
    >>> extract_sense_number("dog%1:05:01::")
    1
    """
    parsed = parse_sense_key(sense_key)
    return parsed["lex_id"]


def normalize_lemma(lemma: Lemma) -> str:
    """Normalize a lemma for matching.

    Parameters
    ----------
    lemma : Lemma
        Word lemma.

    Returns
    -------
    str
        Normalized lemma.

    Examples
    --------
    >>> normalize_lemma("dog")
    'dog'
    >>> normalize_lemma("give_up")
    'give up'
    >>> normalize_lemma("well-known")
    'well known'
    """
    # Replace underscores and hyphens with spaces
    normalized = lemma.replace("_", " ").replace("-", " ")

    # Remove apostrophes
    normalized = normalized.replace("'", "")

    # Lowercase and normalize whitespace
    return " ".join(normalized.split()).lower()


def is_satellite_adjective(pos: WordNetPOS) -> bool:
    """Check if POS is satellite adjective.

    Parameters
    ----------
    pos : WordNetPOS
        POS code.

    Returns
    -------
    bool
        True if satellite adjective (s).

    Examples
    --------
    >>> is_satellite_adjective("s")
    True
    >>> is_satellite_adjective("a")
    False
    """
    return pos == "s"


def synset_id_to_offset(synset_id: SynsetID) -> str | None:
    """Convert synset ID to offset.

    Parameters
    ----------
    synset_id : SynsetID
        Synset ID.

    Returns
    -------
    str | None
        8-digit offset or None.

    Examples
    --------
    >>> synset_id_to_offset("00001740-n")
    '00001740'
    >>> synset_id_to_offset("02084442v")
    '02084442'
    """
    parsed = parse_synset_id(synset_id)
    return parsed["offset"]


def build_synset_id(offset: Offset, pos: WordNetPOS) -> str:
    """Build a synset ID from offset and POS.

    Parameters
    ----------
    offset : Offset
        8-digit offset.
    pos : WordNetPOS
        POS letter.

    Returns
    -------
    str
        Synset ID.

    Examples
    --------
    >>> build_synset_id("00001740", "n")
    '00001740-n'
    """
    return f"{offset}-{pos}"


def filter_by_relation_type(
    pointers: list[Pointer],
    relation_type: str | None = None,
) -> list[Pointer]:
    """Filter pointers by relation type.

    Parameters
    ----------
    pointers : list[Pointer]
        List of pointers to filter.
    relation_type : str | None, optional
        Filter by relation type (e.g., "hypernym", "hyponym", "antonym").

    Returns
    -------
    list[Pointer]
        Filtered list of pointers.

    Examples
    --------
    >>> pointers = [ptr1, ptr2, ptr3]  # Where ptr1.symbol = "@"
    >>> filtered = filter_by_relation_type(pointers, relation_type="hypernym")
    >>> len(filtered)
    1
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
        "similar_to": "&",
        "attribute": "=",
        "also_see": "^",
        "entailment": "*",
        "cause": ">",
        "verb_group": "$",
        "derivation": "+",
        "pertainym": "\\",
        "participle": "<",
    }

    symbol = relation_map.get(relation_type.lower())
    if symbol is None:
        return []

    return [ptr for ptr in pointers if ptr.symbol == symbol]
