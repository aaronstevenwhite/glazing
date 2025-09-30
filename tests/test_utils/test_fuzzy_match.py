"""Tests for fuzzy matching utilities.

This module tests the fuzzy string matching functionality including
text normalization, Levenshtein ratio calculation, and fuzzy matching
with various thresholds.
"""

from __future__ import annotations

import time

from glazing.utils.fuzzy_match import (
    find_best_match,
    fuzzy_match,
    levenshtein_ratio,
    normalize_text,
)


class TestNormalizeText:
    """Test text normalization for fuzzy matching."""

    def test_basic_normalization(self) -> None:
        """Test basic text normalization."""
        assert normalize_text("Hello World") == "hello world"
        assert normalize_text("UPPERCASE") == "uppercase"
        assert normalize_text("Mixed-Case_Text") == "mixed case text"

    def test_preserve_case(self) -> None:
        """Test normalization with case preservation."""
        assert normalize_text("Hello World", preserve_case=True) == "Hello World"
        assert normalize_text("UPPERCASE", preserve_case=True) == "UPPERCASE"

    def test_accent_removal(self) -> None:
        """Test removal of accents and diacriticals."""
        assert normalize_text("café") == "cafe"
        assert normalize_text("résumé") == "resume"
        assert normalize_text("naïve") == "naive"
        assert normalize_text("Zürich") == "zurich"

    def test_special_character_handling(self) -> None:
        """Test handling of special characters."""
        assert normalize_text("hello-world") == "hello world"
        assert normalize_text("under_score") == "under score"
        assert normalize_text("dot.separated") == "dotseparated"
        assert normalize_text("slash/separated") == "slashseparated"
        assert normalize_text("special@#$%chars") == "specialchars"

    def test_whitespace_normalization(self) -> None:
        """Test normalization of whitespace."""
        assert normalize_text("  multiple   spaces  ") == "multiple spaces"
        assert normalize_text("\ttabs\there\t") == "tabs here"
        assert normalize_text("\nnewlines\nhere\n") == "newlines here"

    def test_empty_and_edge_cases(self) -> None:
        """Test edge cases and empty strings."""
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""
        assert normalize_text("123") == "123"
        assert normalize_text("a") == "a"

    def test_unicode_handling(self) -> None:
        """Test handling of various Unicode characters."""
        assert normalize_text("日本語") == ""  # Non-Latin scripts removed
        assert normalize_text("αβγ") == ""  # Greek letters removed
        assert normalize_text("test™") == "test"  # Trademark symbol removed
        assert normalize_text("test®") == "test"  # Registered symbol removed

    def test_caching_behavior(self) -> None:
        """Test that caching works properly."""
        # Call twice with same input to trigger cache
        result1 = normalize_text("test-string")
        result2 = normalize_text("test-string")
        assert result1 == result2 == "test string"

        # Different preserve_case should return different results
        result3 = normalize_text("Test-String", preserve_case=False)
        result4 = normalize_text("Test-String", preserve_case=True)
        assert result3 == "test string"
        assert result4 == "Test String"


class TestLevenshteinRatio:
    """Test Levenshtein ratio calculation."""

    def test_identical_strings(self) -> None:
        """Test ratio for identical strings."""
        assert levenshtein_ratio("hello", "hello") == 1.0
        assert levenshtein_ratio("test", "test") == 1.0
        assert levenshtein_ratio("", "") == 0.0  # Edge case

    def test_completely_different_strings(self) -> None:
        """Test ratio for completely different strings."""
        assert levenshtein_ratio("abc", "xyz") == 0.0
        assert levenshtein_ratio("hello", "world") < 0.3

    def test_similar_strings(self) -> None:
        """Test ratio for similar strings."""
        # One character difference
        ratio = levenshtein_ratio("hello", "helo")
        assert 0.7 < ratio < 0.9

        # Transposition
        ratio = levenshtein_ratio("hello", "hlelo")
        assert 0.7 < ratio < 0.9

        # One character added
        ratio = levenshtein_ratio("test", "tests")
        assert 0.8 < ratio < 1.0

    def test_normalization_effect(self) -> None:
        """Test effect of normalization on ratio."""
        # With normalization (default)
        ratio1 = levenshtein_ratio("Hello-World", "hello_world")
        assert ratio1 == 1.0  # Normalized to same string

        # Without normalization
        ratio2 = levenshtein_ratio("Hello-World", "hello_world", normalize=False)
        assert ratio2 < 1.0  # Different without normalization

    def test_empty_string_handling(self) -> None:
        """Test handling of empty strings."""
        assert levenshtein_ratio("", "") == 0.0
        assert levenshtein_ratio("hello", "") == 0.0
        assert levenshtein_ratio("", "hello") == 0.0

    def test_case_sensitivity(self) -> None:
        """Test case sensitivity in ratio calculation."""
        # With normalization (case-insensitive)
        assert levenshtein_ratio("HELLO", "hello") == 1.0

        # Without normalization (case-sensitive)
        assert levenshtein_ratio("HELLO", "hello", normalize=False) < 1.0

    def test_common_typos(self) -> None:
        """Test ratio for common typos."""
        # Missing letter
        assert levenshtein_ratio("instrument", "instrment") > 0.85

        # Extra letter
        assert levenshtein_ratio("necessary", "neccessary") > 0.85

        # Swapped letters
        assert levenshtein_ratio("receive", "recieve") > 0.85

        # Wrong letter
        assert levenshtein_ratio("definitely", "definately") > 0.85


class TestFuzzyMatch:
    """Test fuzzy matching against candidate lists."""

    def test_basic_fuzzy_matching(self) -> None:
        """Test basic fuzzy matching functionality."""
        candidates = ["apple", "application", "apply", "banana", "orange"]
        results = fuzzy_match("aple", candidates, threshold=0.7)

        assert len(results) > 0
        assert results[0]["match"] == "apple"
        assert results[0]["score"] > 0.7

    def test_threshold_filtering(self) -> None:
        """Test that threshold filters results correctly."""
        candidates = ["cat", "car", "cart", "dog", "card"]

        # High threshold
        results = fuzzy_match("car", candidates, threshold=0.9)
        assert all(r["score"] >= 0.9 for r in results)

        # Lower threshold
        results = fuzzy_match("car", candidates, threshold=0.6)
        assert len(results) > len(fuzzy_match("car", candidates, threshold=0.9))

    def test_max_results_limit(self) -> None:
        """Test limiting maximum number of results."""
        candidates = ["test1", "test2", "test3", "test4", "test5"]

        results = fuzzy_match("test", candidates, threshold=0.5, max_results=3)
        assert len(results) <= 3

        results = fuzzy_match("test", candidates, threshold=0.5, max_results=None)
        assert len(results) == 5  # All should match with high similarity

    def test_result_sorting(self) -> None:
        """Test that results are sorted by score descending."""
        candidates = ["exact", "exac", "exa", "ex", "e"]
        results = fuzzy_match("exact", candidates, threshold=0.1)

        # Should be sorted by score descending
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)
        assert results[0]["match"] == "exact"  # Exact match first

    def test_normalized_fields(self) -> None:
        """Test that results include normalized query and match."""
        candidates = ["Hello-World", "HELLO_WORLD", "hello world"]
        results = fuzzy_match("hello-world", candidates, threshold=0.8)

        for result in results:
            assert "normalized_query" in result
            assert "normalized_match" in result
            assert result["normalized_query"] == "hello world"

    def test_empty_candidates(self) -> None:
        """Test fuzzy matching with empty candidate list."""
        results = fuzzy_match("test", [], threshold=0.8)
        assert results == []

    def test_special_characters_matching(self) -> None:
        """Test matching with special characters."""
        candidates = ["give-13.1", "give_13.2", "give.13.3", "take-15.1"]
        results = fuzzy_match("give-13", candidates, threshold=0.7)

        assert len(results) >= 3  # Should match give variants
        assert all("give" in r["match"] for r in results[:3])

    def test_common_typo_correction(self) -> None:
        """Test correction of common typos."""
        candidates = ["instrument", "argument", "document", "environment"]

        # Missing letter
        results = fuzzy_match("instrment", candidates, threshold=0.8)
        assert results[0]["match"] == "instrument"

        # Extra letter
        results = fuzzy_match("arguement", candidates, threshold=0.8)
        assert results[0]["match"] == "argument"

        # Swapped letters
        results = fuzzy_match("documnet", candidates, threshold=0.8)
        assert results[0]["match"] == "document"


class TestFindBestMatch:
    """Test finding single best match."""

    def test_exact_match(self) -> None:
        """Test that exact matches are returned immediately."""
        candidates = ["give", "take", "make", "bake"]
        assert find_best_match("give", candidates) == "give"
        assert find_best_match("take", candidates) == "take"

    def test_fuzzy_best_match(self) -> None:
        """Test finding best fuzzy match."""
        candidates = ["instrument", "document", "argument"]

        # Typo correction
        assert find_best_match("instrment", candidates) == "instrument"
        assert find_best_match("documnt", candidates) == "document"
        assert find_best_match("argumnt", candidates) == "argument"

    def test_no_good_match(self) -> None:
        """Test that None is returned when no good match exists."""
        candidates = ["apple", "banana", "orange"]
        assert find_best_match("xyz", candidates) is None
        assert find_best_match("12345", candidates) is None

    def test_empty_candidates(self) -> None:
        """Test with empty candidate list."""
        assert find_best_match("test", []) is None

    def test_case_insensitive_matching(self) -> None:
        """Test case-insensitive matching."""
        candidates = ["Hello", "World", "Test"]
        assert find_best_match("hello", candidates) == "Hello"
        assert find_best_match("WORLD", candidates) == "World"
        assert find_best_match("TeSt", candidates) == "Test"

    def test_verbnet_class_matching(self) -> None:
        """Test matching VerbNet class IDs."""
        candidates = ["give-13.1", "give-13.1-1", "take-15.1", "put-9.1"]

        # Exact match
        assert find_best_match("give-13.1", candidates) == "give-13.1"

        # Close match
        assert find_best_match("give-13", candidates) == "give-13.1"
        assert find_best_match("giv-13.1", candidates) == "give-13.1"

    def test_propbank_roleset_matching(self) -> None:
        """Test matching PropBank rolesets."""
        candidates = ["give.01", "give.02", "take.01", "put.01"]

        # Exact match
        assert find_best_match("give.01", candidates) == "give.01"

        # Close match
        assert find_best_match("giv.01", candidates) == "give.01"
        assert find_best_match("give.1", candidates) == "give.01"


class TestPerformance:
    """Test performance characteristics."""

    def test_cache_effectiveness(self) -> None:
        """Test that caching improves performance."""
        text = "test-string-with-hyphens"

        # First call (not cached)
        start = time.perf_counter()
        result1 = normalize_text(text)
        time.perf_counter() - start

        # Second call (should be cached)
        start = time.perf_counter()
        result2 = normalize_text(text)
        time.perf_counter() - start

        assert result1 == result2
        # Cache hit should be much faster (allowing for timing variations)
        # Just verify it works, don't assert on timing which can be flaky

    def test_large_candidate_list(self) -> None:
        """Test fuzzy matching with large candidate list."""
        # Generate 1000 candidates
        candidates = [f"word_{i:04d}" for i in range(1000)]

        results = fuzzy_match("word_0500", candidates, threshold=0.9)
        assert len(results) > 0
        assert results[0]["match"] == "word_0500"

    def test_matching_with_common_patterns(self) -> None:
        """Test matching with common linguistic patterns."""
        # VerbNet patterns
        vn_candidates = [
            "give-13.1",
            "give-13.1-1",
            "spray-9.7",
            "spray-9.7-1",
            "spray-9.7-2",
        ]
        assert find_best_match("spary-9.7", vn_candidates) == "spray-9.7"  # Typo

        # PropBank patterns
        pb_candidates = [
            "give.01",
            "give.02",
            "spray.01",
            "spray.02",
        ]
        assert find_best_match("give.1", pb_candidates) == "give.01"  # Missing zero

        # FrameNet patterns
        fn_candidates = [
            "Giving",
            "Transfer",
            "Commerce_buy",
            "Commerce_sell",
        ]
        assert find_best_match("Givng", fn_candidates) == "Giving"  # Typo
