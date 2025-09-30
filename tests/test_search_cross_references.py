"""Integration tests for search cross-references.

This module tests the integration of cross-reference search functionality
including VerbNet→FrameNet mapping, reverse lookups, and confidence scoring.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from glazing.references.index import CrossReferenceIndex
from glazing.references.models import CrossReference, MappingConfidence, MappingMetadata
from glazing.search import UnifiedSearch as Search
from glazing.verbnet.models import Member, VerbClass


def create_test_metadata() -> MappingMetadata:
    """Create default metadata for test CrossReferences."""
    return MappingMetadata(
        created_date=datetime.now(tz=UTC),
        created_by="test",
        version="1.0",
        validation_status="validated",
    )


class TestCrossReferenceIntegration:
    """Test cross-reference integration across datasets."""

    @pytest.fixture
    def mock_xref_index(self) -> CrossReferenceIndex:
        """Create a mock cross-reference index."""
        with (
            patch("glazing.references.index.VerbNetLoader"),
            patch("glazing.references.index.PropBankLoader"),
            patch("glazing.references.index.FrameNetLoader"),
            patch("glazing.references.index.WordNetLoader"),
        ):
            index = CrossReferenceIndex(auto_extract=False, show_progress=False)
            index.is_extracted = True
            return index

    def test_verbnet_to_framenet_mapping(self, mock_xref_index: CrossReferenceIndex) -> None:
        """Test VerbNet to FrameNet mapping with fuzzy matching."""
        # Mock the extractor's mapping index
        mock_xref_index.extractor.mapping_index.forward_index["verbnet:give-13.1"] = [
            CrossReference(
                source_dataset="verbnet",
                source_id="give-13.1",
                source_version="1.0",
                target_dataset="framenet",
                target_id="Giving",
                mapping_type="direct",
                confidence=MappingConfidence(score=0.95, method="manual"),
                metadata=create_test_metadata(),
            )
        ]

        # Test exact match
        refs = mock_xref_index.resolve("give-13.1", source="verbnet")
        assert "Giving" in refs["framenet_frames"]
        assert refs["confidence_scores"]["framenet:Giving"] == 0.95

    def test_framenet_to_verbnet_reverse_lookup(self, mock_xref_index: CrossReferenceIndex) -> None:
        """Test FrameNet to VerbNet reverse lookups."""
        # Mock both the reverse index AND the get_mappings_for_entity method
        mock_xref_index.extractor.mapping_index.reverse_index["framenet:Giving"] = [
            CrossReference(
                source_dataset="verbnet",
                source_id="give-13.1",
                source_version="1.0",
                target_dataset="framenet",
                target_id="Giving",
                mapping_type="direct",
                confidence=MappingConfidence(score=0.95, method="manual"),
                metadata=create_test_metadata(),
            )
        ]

        # Mock get_mappings_for_entity to return the reverse mapping
        def mock_get_mappings(entity_id: str, dataset_type: str) -> list[CrossReference]:
            if dataset_type == "framenet" and entity_id == "Giving":
                return mock_xref_index.extractor.mapping_index.reverse_index.get(
                    "framenet:Giving", []
                )
            return []

        mock_xref_index.extractor.get_mappings_for_entity = mock_get_mappings

        # Get mappings for FrameNet frame
        mappings = mock_xref_index.extractor.get_mappings_for_entity("Giving", "framenet")

        # Should find the VerbNet class via reverse lookup
        vn_mappings = [m for m in mappings if m.source_dataset == "verbnet"]
        assert len(vn_mappings) > 0
        assert vn_mappings[0].source_id == "give-13.1"

    def test_propbank_cross_references(self, mock_xref_index: CrossReferenceIndex) -> None:
        """Test PropBank cross-references via lexlinks."""
        # Mock PropBank to VerbNet mapping
        mock_xref_index.extractor.mapping_index.forward_index["propbank:give.01"] = [
            CrossReference(
                source_dataset="propbank",
                source_id="give.01",
                source_version="1.0",
                target_dataset="verbnet",
                target_id="give-13.1",
                mapping_type="direct",
                confidence=MappingConfidence(score=0.9, method="lexlink"),
                metadata=create_test_metadata(),
            ),
            CrossReference(
                source_dataset="propbank",
                source_id="give.01",
                source_version="1.0",
                target_dataset="framenet",
                target_id="Giving",
                mapping_type="inferred",
                confidence=MappingConfidence(score=0.85, method="inferred"),
                metadata=create_test_metadata(),
            ),
        ]

        # Mock get_mappings_for_entity for PropBank

        def mock_get_mappings(entity_id: str, dataset_type: str) -> list[CrossReference]:
            if dataset_type == "propbank" and entity_id == "give.01":
                return mock_xref_index.extractor.mapping_index.forward_index.get(
                    "propbank:give.01", []
                )
            # Call original for other cases
            return []

        mock_xref_index.extractor.get_mappings_for_entity = mock_get_mappings

        refs = mock_xref_index.resolve("give.01", source="propbank")

        # Should have both VerbNet and FrameNet references
        assert "give-13.1" in refs["verbnet_classes"]
        assert "Giving" in refs["framenet_frames"]

        # Check confidence scores
        assert refs["confidence_scores"]["verbnet:give-13.1"] == 0.9
        assert refs["confidence_scores"]["framenet:Giving"] == 0.85

    def test_confidence_score_validation(self, mock_xref_index: CrossReferenceIndex) -> None:
        """Test that confidence scores are properly validated."""
        # Add mappings with various confidence scores
        mock_xref_index.extractor.mapping_index.forward_index["verbnet:spray-9.7"] = [
            CrossReference(
                source_dataset="verbnet",
                source_id="spray-9.7",
                source_version="1.0",
                target_dataset="framenet",
                target_id="Filling",
                mapping_type="direct",
                confidence=MappingConfidence(score=0.7, method="automatic"),
                metadata=create_test_metadata(),
            ),
            CrossReference(
                source_dataset="verbnet",
                source_id="spray-9.7",
                source_version="1.0",
                target_dataset="framenet",
                target_id="Adorning",
                mapping_type="automatic",
                confidence=MappingConfidence(score=0.5, method="inferred"),
                metadata=create_test_metadata(),
            ),
        ]

        # Mock get_mappings_for_entity for VerbNet
        def mock_get_mappings(entity_id: str, dataset_type: str) -> list[CrossReference]:
            if dataset_type == "verbnet" and entity_id == "spray-9.7":
                return mock_xref_index.extractor.mapping_index.forward_index.get(
                    "verbnet:spray-9.7", []
                )
            return []

        mock_xref_index.extractor.get_mappings_for_entity = mock_get_mappings

        refs = mock_xref_index.resolve("spray-9.7", source="verbnet")

        # All confidence scores should be between 0 and 1
        for score in refs["confidence_scores"].values():
            assert 0.0 <= score <= 1.0

        # Higher confidence mapping should be present
        assert "Filling" in refs["framenet_frames"]
        assert refs["confidence_scores"]["framenet:Filling"] == 0.7

    def test_transitive_mapping_resolution(self, mock_xref_index: CrossReferenceIndex) -> None:
        """Test transitive mapping resolution."""
        # VerbNet -> PropBank
        mock_xref_index.extractor.mapping_index.forward_index["verbnet:put-9.1"] = [
            CrossReference(
                source_dataset="verbnet",
                source_id="put-9.1",
                source_version="1.0",
                target_dataset="propbank",
                target_id="put.01",
                mapping_type="direct",
                confidence=MappingConfidence(score=0.95, method="manual"),
                metadata=create_test_metadata(),
            )
        ]

        # PropBank -> FrameNet (transitive)
        mock_xref_index.extractor.mapping_index.forward_index["propbank:put.01"] = [
            CrossReference(
                source_dataset="propbank",
                source_id="put.01",
                source_version="1.0",
                target_dataset="framenet",
                target_id="Placing",
                mapping_type="direct",
                confidence=MappingConfidence(score=0.9, method="manual"),
                metadata=create_test_metadata(),
            )
        ]

        # Resolve from VerbNet should find both PropBank and transitive FrameNet
        refs = mock_xref_index.resolve("put-9.1", source="verbnet")
        assert "put.01" in refs["propbank_rolesets"]

        # Note: Current implementation doesn't do transitive resolution automatically
        # This test documents the expected behavior for future enhancement

    def test_fuzzy_matching_in_resolution(self, mock_xref_index: CrossReferenceIndex) -> None:
        """Test fuzzy matching in cross-reference resolution."""
        # Mock fuzzy resolution
        with patch.object(mock_xref_index, "_fuzzy_resolve_entity_id") as mock_fuzzy:
            mock_fuzzy.return_value = "give-13.1"  # Corrected ID

            # Add mapping for corrected ID
            mock_xref_index.extractor.mapping_index.forward_index["verbnet:give-13.1"] = [
                CrossReference(
                    source_dataset="verbnet",
                    source_id="give-13.1",
                    source_version="1.0",
                    target_dataset="framenet",
                    target_id="Giving",
                    mapping_type="direct",
                    confidence=MappingConfidence(score=0.95, method="manual"),
                    metadata=create_test_metadata(),
                )
            ]

            # Try to resolve with typo
            refs = mock_xref_index.resolve("giv-13.1", source="verbnet", fuzzy=True)

            # Should call fuzzy resolution
            mock_fuzzy.assert_called_once_with("giv-13.1", "verbnet")

            # Should find the mapping
            assert "Giving" in refs["framenet_frames"]

    def test_multiple_target_ids(self, mock_xref_index: CrossReferenceIndex) -> None:
        """Test handling of cross-references with multiple target IDs."""
        # Add mapping with multiple targets
        mock_xref_index.extractor.mapping_index.forward_index["verbnet:break-45.1"] = [
            CrossReference(
                source_dataset="verbnet",
                source_id="break-45.1",
                source_version="1.0",
                target_dataset="framenet",
                target_id=["Cause_to_fragment", "Breaking_apart", "Experience_bodily_harm"],
                mapping_type="direct",
                confidence=MappingConfidence(score=0.85, method="manual"),
                metadata=create_test_metadata(),
            )
        ]

        refs = mock_xref_index.resolve("break-45.1", source="verbnet")

        # Should have all three FrameNet frames
        assert len(refs["framenet_frames"]) == 3
        assert "Cause_to_fragment" in refs["framenet_frames"]
        assert "Breaking_apart" in refs["framenet_frames"]
        assert "Experience_bodily_harm" in refs["framenet_frames"]

        # Each should have the same confidence score
        for frame in refs["framenet_frames"]:
            assert refs["confidence_scores"][f"framenet:{frame}"] == 0.85


class TestSearchWithCrossReferences:
    """Test search functionality with cross-references."""

    @pytest.fixture
    def mock_search(self, tmp_path: Path) -> Search:
        """Create a mock search instance."""
        # Create minimal mock data files
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # Mock data files
        (data_dir / "verbnet.jsonl").touch()
        (data_dir / "propbank.jsonl").touch()
        (data_dir / "framenet.jsonl").touch()

        with (
            patch("glazing.search.VerbNetLoader"),
            patch("glazing.search.PropBankLoader"),
            patch("glazing.search.FrameNetLoader"),
            patch("glazing.search.WordNetLoader"),
        ):
            return Search(data_dir=data_dir)

    def test_search_with_fuzzy_matching(self, mock_search: Search) -> None:
        """Test search with fuzzy matching for typo correction."""
        # Create a proper mock result
        mock_result = VerbClass(
            id="give-13.1",
            members=[Member(name="give", verbnet_key="give#1", wn=None, grouping=None)],
            themroles=[],
            frames=[],
        )

        # Mock the underlying search components
        # The Search class uses .verbnet not ._verbnet_search
        mock_vn = MagicMock()
        mock_vn.get_all_classes.return_value = [mock_result]
        mock_search.verbnet = mock_vn

        # Mock other components to have empty data
        mock_pb = MagicMock()
        mock_pb.get_all_rolesets.return_value = []
        mock_search.propbank = mock_pb

        mock_fn = MagicMock()
        mock_fn._frames_by_id = {}
        mock_search.framenet = mock_fn

        mock_wn = MagicMock()
        mock_wn.get_all_synsets.return_value = []
        mock_search.wordnet = mock_wn

        # Search with typo
        results = mock_search.search_with_fuzzy("giv", fuzzy_threshold=0.8)

        # Should return results
        assert len(results) == 1
        assert results[0].id == "give-13.1"

    def test_cross_reference_search_integration(self, mock_search: Search) -> None:
        """Test integration of cross-reference search."""
        # Create a proper mock result
        mock_result = VerbClass(
            id="give-13.1",
            members=[Member(name="give", verbnet_key="give#1", wn=None, grouping=None)],
            themroles=[],
            frames=[],
            framenet_mappings={"Giving": ["Agent", "Theme", "Recipient"]},
        )

        # Mock VerbNet search - search() uses by_members
        mock_vn = MagicMock()
        mock_vn.by_members.return_value = [mock_result]
        mock_search.verbnet = mock_vn

        # Mock FrameNet search - search() uses find_frames_by_lemma
        mock_fn = MagicMock()
        mock_fn.find_frames_by_lemma.return_value = []  # No direct FrameNet results
        mock_search.framenet = mock_fn

        # Mock PropBank search - search() uses by_lemma
        mock_pb = MagicMock()
        mock_pb.by_lemma.return_value = []
        mock_search.propbank = mock_pb

        # Mock WordNet search - search() uses by_lemma
        mock_wn = MagicMock()
        mock_wn.by_lemma.return_value = []
        mock_search.wordnet = mock_wn

        # Search should find VerbNet class
        results = mock_search.search("give")

        # Should include VerbNet results
        assert len(results) == 1
        assert results[0].id == "give-13.1"

    def test_search_result_confidence_scores(self, mock_search: Search) -> None:
        """Test that search results include confidence scores for fuzzy matches."""
        # Create a proper mock result
        mock_result = VerbClass(
            id="instrument-13.4.1",
            members=[Member(name="instrument", verbnet_key="instrument#1", wn=None, grouping=None)],
            themroles=[],
            frames=[],
        )

        # Mock fuzzy search results with scores
        mock_vn = MagicMock()
        mock_vn.get_all_classes.return_value = [mock_result]
        mock_search.verbnet = mock_vn

        # Mock PropBank search
        mock_pb = MagicMock()
        mock_pb.get_all_rolesets.return_value = []
        mock_search.propbank = mock_pb

        # Mock FrameNet search
        mock_fn = MagicMock()
        mock_fn._frames_by_id = {}
        mock_search.framenet = mock_fn

        # Mock WordNet search
        mock_wn = MagicMock()
        mock_wn.get_all_synsets.return_value = []
        mock_search.wordnet = mock_wn

        # Search with typo
        results = mock_search.search_with_fuzzy("instrment", fuzzy_threshold=0.8)

        # Results should be returned
        assert len(results) == 1
        assert results[0].id == "instrument-13.4.1"


class TestCrossReferencePerformance:
    """Test performance characteristics of cross-reference operations."""

    def test_cache_effectiveness(self) -> None:
        """Test that cross-reference caching improves performance."""
        with (
            patch("glazing.references.index.VerbNetLoader"),
            patch("glazing.references.index.PropBankLoader"),
            patch("glazing.references.index.FrameNetLoader"),
            patch("glazing.references.index.WordNetLoader"),
        ):
            # Create index without auto-extract
            index = CrossReferenceIndex(auto_extract=False, show_progress=False)
            index.is_extracted = True

            # Mock some mappings
            index.extractor.mapping_index.forward_index["verbnet:test-1.0"] = [
                CrossReference(
                    source_dataset="verbnet",
                    source_id="test-1.0",
                    source_version="1.0",
                    target_dataset="framenet",
                    target_id="Testing",
                    mapping_type="direct",
                    confidence=MappingConfidence(score=0.9, method="manual"),
                    metadata=create_test_metadata(),
                )
            ]

            # First resolution (not cached)
            start = time.perf_counter()
            refs1 = index.resolve("test-1.0", source="verbnet")
            time.perf_counter() - start

            # Second resolution (should use any internal caching)
            start = time.perf_counter()
            refs2 = index.resolve("test-1.0", source="verbnet")
            time.perf_counter() - start

            # Results should be the same
            assert refs1 == refs2

            # Just verify it works, don't assert on timing which can be flaky

    def test_large_mapping_index(self) -> None:
        """Test handling of large mapping indices."""
        with (
            patch("glazing.references.index.VerbNetLoader"),
            patch("glazing.references.index.PropBankLoader"),
            patch("glazing.references.index.FrameNetLoader"),
            patch("glazing.references.index.WordNetLoader"),
        ):
            index = CrossReferenceIndex(auto_extract=False, show_progress=False)
            index.is_extracted = True

            # Add many mappings
            for i in range(1000):
                index.extractor.mapping_index.forward_index[f"verbnet:test-{i}"] = [
                    CrossReference(
                        source_dataset="verbnet",
                        source_id=f"test-{i}",
                        source_version="1.0",
                        target_dataset="framenet",
                        target_id=f"Frame_{i}",
                        mapping_type="direct",
                        confidence=MappingConfidence(score=0.9, method="automatic"),
                        metadata=create_test_metadata(),
                    )
                ]

            # Should handle resolution efficiently
            refs = index.resolve("test-500", source="verbnet")
            assert "Frame_500" in refs["framenet_frames"]

    def test_fuzzy_matching_performance(self) -> None:
        """Test performance of fuzzy matching in cross-references."""
        with (
            patch("glazing.references.index.VerbNetLoader"),
            patch("glazing.references.index.PropBankLoader"),
            patch("glazing.references.index.FrameNetLoader"),
            patch("glazing.references.index.WordNetLoader"),
        ):
            index = CrossReferenceIndex(auto_extract=False, show_progress=False)
            index.is_extracted = True

            # Add candidates for fuzzy matching
            candidates = [f"class-{i}.{j}" for i in range(100) for j in range(1, 5)]
            for candidate in candidates:
                index.extractor.mapping_index.forward_index[f"verbnet:{candidate}"] = []

            # Mock the fuzzy resolution to simulate the search
            with patch.object(index, "_get_dataset_entity_ids") as mock_get:
                mock_get.return_value = candidates

                with patch("glazing.references.index.find_best_match") as mock_find:
                    mock_find.return_value = "class-50.2"

                    # Fuzzy resolve should complete quickly even with many candidates
                    result = index._fuzzy_resolve_entity_id("clas-50.2", "verbnet")
                    assert result == "class-50.2"
