"""Search result ranking utilities.

This module provides functions for ranking and scoring search results
based on multiple criteria including match type, field specificity,
and contextual relevance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from glazing.search import SearchResult


class MatchType(IntEnum):
    """Type of match with priority weights."""

    EXACT = 100
    PREFIX = 80
    SUFFIX = 70
    CONTAINS = 60
    FUZZY = 40


class FieldWeight(IntEnum):
    """Field-specific weights for ranking."""

    ID = 100
    NAME = 90
    DEFINITION = 70
    DESCRIPTION = 60
    EXAMPLE = 40
    NOTE = 30


@dataclass
class RankingScore:
    """Detailed ranking score breakdown.

    Attributes
    ----------
    match_type_score : float
        Score based on match type.
    field_weight_score : float
        Score based on field importance.
    fuzzy_score : float
        Fuzzy match similarity score.
    total_score : float
        Combined total score.
    """

    match_type_score: float
    field_weight_score: float
    fuzzy_score: float
    total_score: float

    def __lt__(self, other: RankingScore) -> bool:
        """Compare by total score for sorting."""
        return self.total_score < other.total_score


class RankedResult(TypedDict):
    """Search result with ranking score.

    Attributes
    ----------
    result : SearchResult
        Original search result.
    ranking : RankingScore
        Detailed ranking scores.
    """

    result: SearchResult
    ranking: RankingScore


def get_match_type(query: str, text: str) -> MatchType:
    """Determine the type of match between query and text.

    Parameters
    ----------
    query : str
        Search query.
    text : str
        Text to match against.

    Returns
    -------
    MatchType
        Type of match found.
    """
    query_lower = query.lower()
    text_lower = text.lower()

    if query_lower == text_lower:
        return MatchType.EXACT
    if text_lower.startswith(query_lower):
        return MatchType.PREFIX
    if text_lower.endswith(query_lower):
        return MatchType.SUFFIX
    if query_lower in text_lower:
        return MatchType.CONTAINS
    return MatchType.FUZZY


def calculate_ranking_score(
    query: str,
    matched_text: str,
    field_type: str = "description",
    fuzzy_similarity: float = 0.0,
) -> RankingScore:
    """Calculate ranking score for a search result.

    Parameters
    ----------
    query : str
        Search query.
    matched_text : str
        Text that matched.
    field_type : str
        Type of field matched.
    fuzzy_similarity : float
        Fuzzy match similarity (0.0 to 1.0).

    Returns
    -------
    RankingScore
        Detailed ranking scores.
    """
    # Get match type score
    match_type = get_match_type(query, matched_text)
    match_type_score = float(match_type.value)

    # Get field weight score
    field_weight_map = {
        "id": FieldWeight.ID,
        "name": FieldWeight.NAME,
        "definition": FieldWeight.DEFINITION,
        "description": FieldWeight.DESCRIPTION,
        "example": FieldWeight.EXAMPLE,
        "note": FieldWeight.NOTE,
    }
    field_weight = field_weight_map.get(field_type.lower(), FieldWeight.DESCRIPTION)
    field_weight_score = float(field_weight.value)

    # Calculate fuzzy score component
    fuzzy_score = fuzzy_similarity * 100.0

    # Calculate total score with weights
    total_score = match_type_score * 0.4 + field_weight_score * 0.3 + fuzzy_score * 0.3

    return RankingScore(
        match_type_score=match_type_score,
        field_weight_score=field_weight_score,
        fuzzy_score=fuzzy_score,
        total_score=total_score,
    )


def rank_search_results(
    results: list[SearchResult], query: str, top_k: int | None = None
) -> list[RankedResult]:
    """Rank search results by relevance.

    Parameters
    ----------
    results : list[SearchResult]
        Search results to rank.
    query : str
        Original search query.
    top_k : int | None
        Return only top K results.

    Returns
    -------
    list[RankedResult]
        Ranked results sorted by score.
    """
    ranked_results: list[RankedResult] = []

    for result in results:
        # Calculate ranking based on name match
        name_score = calculate_ranking_score(
            query=query,
            matched_text=result.name,
            field_type="name",
            fuzzy_similarity=result.score,
        )

        # Calculate ranking based on description match
        desc_score = calculate_ranking_score(
            query=query,
            matched_text=result.description,
            field_type="description",
            fuzzy_similarity=result.score,
        )

        # Use the better score
        best_score = name_score if name_score.total_score > desc_score.total_score else desc_score

        ranked_results.append(
            RankedResult(
                result=result,
                ranking=best_score,
            )
        )

    # Sort by total score descending
    ranked_results.sort(key=lambda x: x["ranking"].total_score, reverse=True)

    if top_k is not None:
        ranked_results = ranked_results[:top_k]

    return ranked_results


def merge_and_rank_results(
    result_sets: list[list[SearchResult]], query: str, top_k: int | None = None
) -> list[RankedResult]:
    """Merge multiple result sets and rank them.

    Parameters
    ----------
    result_sets : list[list[SearchResult]]
        Multiple sets of search results.
    query : str
        Original search query.
    top_k : int | None
        Return only top K results.

    Returns
    -------
    list[RankedResult]
        Merged and ranked results.
    """
    # Flatten all results
    all_results: list[SearchResult] = []
    for result_set in result_sets:
        all_results.extend(result_set)

    # Rank the merged results
    return rank_search_results(all_results, query, top_k)
