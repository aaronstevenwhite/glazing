"""Fuzzy string matching utilities.

This module provides functions for fuzzy string matching using Levenshtein
distance and other similarity metrics. It includes text normalization
and caching for performance.

Functions
---------
normalize_text
    Normalize text for fuzzy matching.
levenshtein_ratio
    Calculate Levenshtein ratio between strings.
fuzzy_match
    Find best fuzzy matches from candidates.
find_best_match
    Find the single best match from candidates.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import TypedDict

import Levenshtein


class FuzzyMatchResult(TypedDict):
    """Result of a fuzzy match operation.

    Attributes
    ----------
    match : str
        The matched string.
    score : float
        Similarity score (0.0 to 1.0).
    normalized_query : str
        Normalized form of the query.
    normalized_match : str
        Normalized form of the match.
    """

    match: str
    score: float
    normalized_query: str
    normalized_match: str


@lru_cache(maxsize=1024)
def normalize_text(text: str, preserve_case: bool = False) -> str:
    """Normalize text for fuzzy matching.

    Parameters
    ----------
    text : str
        Text to normalize.
    preserve_case : bool, default=False
        Whether to preserve letter case.

    Returns
    -------
    str
        Normalized text.

    Examples
    --------
    >>> normalize_text("Hello-World_123")
    'hello world 123'
    >>> normalize_text("café")
    'cafe'
    """
    # Remove accents
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")

    # Replace underscores and hyphens with spaces
    text = re.sub(r"[_\-]+", " ", text)

    # Remove non-alphanumeric characters except spaces
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)

    # Normalize whitespace
    text = " ".join(text.split())

    if not preserve_case:
        text = text.lower()

    return text


@lru_cache(maxsize=4096)
def levenshtein_ratio(s1: str, s2: str, normalize: bool = True) -> float:
    """Calculate Levenshtein ratio between two strings.

    The ratio is computed as:
    1 - (distance / max(len(s1), len(s2)))

    Parameters
    ----------
    s1 : str
        First string.
    s2 : str
        Second string.
    normalize : bool, default=True
        Whether to normalize strings before comparison.

    Returns
    -------
    float
        Similarity ratio between 0.0 and 1.0.

    Examples
    --------
    >>> levenshtein_ratio("hello", "helo")
    0.8
    >>> levenshtein_ratio("cat", "dog")
    0.0
    """
    if normalize:
        s1 = normalize_text(s1)
        s2 = normalize_text(s2)

    if not s1 or not s2:
        return 0.0

    if s1 == s2:
        return 1.0

    return Levenshtein.ratio(s1, s2)


def fuzzy_match(
    query: str,
    candidates: list[str],
    threshold: float = 0.8,
    max_results: int | None = None,
) -> list[FuzzyMatchResult]:
    """Find best fuzzy matches from candidates.

    Parameters
    ----------
    query : str
        Query string to match.
    candidates : list[str]
        List of candidate strings.
    threshold : float, default=0.8
        Minimum similarity score (0.0 to 1.0).
    max_results : int | None, default=None
        Maximum number of results to return.

    Returns
    -------
    list[FuzzyMatchResult]
        Sorted list of matches above threshold.

    Examples
    --------
    >>> candidates = ["instrument", "argument", "document"]
    >>> fuzzy_match("instsrument", candidates, threshold=0.7)
    [{'match': 'instrument', 'score': 0.9, ...}]
    """
    normalized_query = normalize_text(query)
    results: list[FuzzyMatchResult] = []

    for candidate in candidates:
        normalized_candidate = normalize_text(candidate)
        score = levenshtein_ratio(normalized_query, normalized_candidate, normalize=False)

        if score >= threshold:
            results.append(
                FuzzyMatchResult(
                    match=candidate,
                    score=score,
                    normalized_query=normalized_query,
                    normalized_match=normalized_candidate,
                )
            )

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)

    if max_results is not None:
        results = results[:max_results]

    return results


def find_best_match(query: str, candidates: list[str]) -> str | None:
    """Find the single best match from candidates.

    Parameters
    ----------
    query : str
        Query string to match.
    candidates : list[str]
        List of candidate strings.

    Returns
    -------
    str | None
        Best matching candidate or None if no good match.

    Examples
    --------
    >>> find_best_match("give", ["give", "take", "make"])
    'give'
    >>> find_best_match("giv", ["give", "take", "make"])
    'give'
    """
    # First try exact match
    if query in candidates:
        return query

    # Then try fuzzy match
    matches = fuzzy_match(query, candidates, threshold=0.6, max_results=1)
    return matches[0]["match"] if matches else None
