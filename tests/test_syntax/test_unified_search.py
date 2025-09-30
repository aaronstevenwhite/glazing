"""Test unified syntax search integration."""

from glazing.framenet.search import FrameNetSearch
from glazing.propbank.search import PropBankSearch
from glazing.search import SearchResult, UnifiedSearch
from glazing.verbnet.search import VerbNetSearch
from glazing.wordnet.search import WordNetSearch


class TestUnifiedSyntaxSearch:
    """Test unified syntax search across all datasets."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create search instances (empty for testing)
        self.framenet = FrameNetSearch()
        self.propbank = PropBankSearch()
        self.wordnet = WordNetSearch()
        self.verbnet = VerbNetSearch()

        # Create unified search with all datasets
        self.unified = UnifiedSearch(
            framenet=self.framenet,
            propbank=self.propbank,
            wordnet=self.wordnet,
            verbnet=self.verbnet,
            auto_load=False,
        )

    def test_search_by_syntax_method_exists(self):
        """Test that search_by_syntax method exists and is callable."""
        assert hasattr(self.unified, "search_by_syntax")
        assert callable(self.unified.search_by_syntax)

    def test_search_by_syntax_empty_datasets(self):
        """Test syntax search with empty datasets."""
        results = self.unified.search_by_syntax("NP V NP")

        # Should return empty list for empty datasets
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_by_syntax_dataset_filter(self):
        """Test dataset filtering in syntax search."""
        # Test with specific dataset filters
        datasets = ["verbnet", "propbank", "framenet", "wordnet"]

        for dataset in datasets:
            results = self.unified.search_by_syntax("NP V NP", dataset=dataset)
            assert isinstance(results, list)
            assert len(results) == 0  # Empty datasets

    def test_search_by_syntax_confidence_filtering(self):
        """Test confidence score filtering."""
        # Test with different confidence thresholds
        for min_conf in [0.5, 0.7, 0.9]:
            results = self.unified.search_by_syntax("NP V NP", min_confidence=min_conf)
            assert isinstance(results, list)
            assert len(results) == 0  # Empty datasets

    def test_search_by_syntax_wildcard_option(self):
        """Test wildcard processing option."""
        # Test with wildcards enabled/disabled
        for allow_wildcards in [True, False]:
            results = self.unified.search_by_syntax("NP V NP *", allow_wildcards=allow_wildcards)
            assert isinstance(results, list)
            assert len(results) == 0  # Empty datasets

    def test_search_by_syntax_various_patterns(self):
        """Test syntax search with various pattern types."""
        patterns = [
            "NP V NP",  # Basic transitive
            "NP V PP",  # With PP
            "NP V PP.location",  # Specific PP role
            "NP V NP *",  # With wildcard
            "NP V",  # Intransitive
            "V NP",  # Imperative
        ]

        for pattern in patterns:
            results = self.unified.search_by_syntax(pattern)
            assert isinstance(results, list)
            assert len(results) == 0  # Empty datasets

    def test_search_by_syntax_returns_search_results(self):
        """Test that search returns SearchResult objects."""
        results = self.unified.search_by_syntax("NP V NP")

        # Even empty results should be a list of SearchResult objects
        assert isinstance(results, list)
        for result in results:
            assert isinstance(result, SearchResult)

    def test_search_by_syntax_result_sorting(self):
        """Test that results are sorted by confidence score."""
        # With empty datasets, this tests the sorting mechanism exists
        results = self.unified.search_by_syntax("NP V NP")

        # Check that results are sorted (even if empty)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_by_syntax_none_datasets(self):
        """Test syntax search with None datasets."""
        # Create unified search with None datasets
        unified_none = UnifiedSearch(
            framenet=None, propbank=None, wordnet=None, verbnet=None, auto_load=False
        )

        results = unified_none.search_by_syntax("NP V NP")
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_by_syntax_partial_datasets(self):
        """Test syntax search with some None datasets."""
        # Create unified search with partial datasets
        unified_partial = UnifiedSearch(
            framenet=self.framenet,
            propbank=None,
            wordnet=self.wordnet,
            verbnet=None,
            auto_load=False,
        )

        results = unified_partial.search_by_syntax("NP V NP")
        assert isinstance(results, list)
        assert len(results) == 0  # Still empty

    def test_search_by_syntax_invalid_patterns(self):
        """Test syntax search with invalid patterns."""
        invalid_patterns = [
            "",  # Empty pattern
            "   ",  # Whitespace only
            "INVALID",  # Invalid constituent
            "NP V V",  # Multiple verbs
        ]

        for pattern in invalid_patterns:
            # Should not raise an exception, might return empty or parse as best effort
            try:
                results = self.unified.search_by_syntax(pattern)
                assert isinstance(results, list)
            except (ValueError, AttributeError):
                # Some patterns might cause parsing exceptions, which is acceptable
                pass

    def test_search_by_syntax_parameter_validation(self):
        """Test parameter validation in syntax search."""
        # Test with edge case confidence scores (might not raise exceptions)
        # Just test they return valid results
        results1 = self.unified.search_by_syntax("NP V NP", min_confidence=-0.5)
        assert isinstance(results1, list)

        results2 = self.unified.search_by_syntax("NP V NP", min_confidence=1.5)
        assert isinstance(results2, list)

    def test_search_by_syntax_dataset_names(self):
        """Test valid and invalid dataset names."""
        valid_datasets = ["verbnet", "propbank", "framenet", "wordnet", None]
        invalid_datasets = ["invalid", "VerbNet", "PROPBANK", ""]

        # Valid dataset names should work
        for dataset in valid_datasets:
            results = self.unified.search_by_syntax("NP V NP", dataset=dataset)
            assert isinstance(results, list)

        # Invalid dataset names should still work (might be ignored)
        for dataset in invalid_datasets:
            results = self.unified.search_by_syntax("NP V NP", dataset=dataset)
            assert isinstance(results, list)
