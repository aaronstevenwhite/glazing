"""Tests for CLI structured search commands.

This module tests the CLI structured search functionality including
fuzzy search, xref commands, and structured role/arg filtering.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from glazing.cli.search import search_query
from glazing.cli.xref import clear_cache, extract_xref, resolve_xref


class TestFuzzySearchCLI:
    """Test fuzzy search CLI commands."""

    def test_search_query_with_fuzzy_flag(self, tmp_path: Path) -> None:
        """Test search query command with --fuzzy flag."""
        # Create mock data directory
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "verbnet.jsonl").touch()

        # Mock the search functionality
        with patch("glazing.cli.search.UnifiedSearch") as mock_unified_search:
            mock_search = MagicMock()
            mock_unified_search.return_value = mock_search

            # Mock search_with_fuzzy method
            mock_result = MagicMock()
            mock_result.dataset = "verbnet"
            mock_result.id = "give-13.1"
            mock_result.type = "verb_class"
            mock_result.name = "give"
            mock_result.description = "Transfer"
            mock_result.score = 0.9

            mock_search.search_with_fuzzy.return_value = [mock_result]

            runner = CliRunner()
            result = runner.invoke(
                search_query,
                ["giv", "--fuzzy", "--threshold", "0.8", "--data-dir", str(data_dir)],
            )

            assert result.exit_code == 0
            mock_search.search_with_fuzzy.assert_called_once_with("giv", 0.8)

    def test_search_query_fuzzy_with_json_output(self, tmp_path: Path) -> None:
        """Test fuzzy search with JSON output."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "verbnet.jsonl").touch()

        with patch("glazing.cli.search.UnifiedSearch") as mock_unified_search:
            mock_search = MagicMock()
            mock_unified_search.return_value = mock_search

            mock_result = MagicMock()
            mock_result.dataset = "verbnet"
            mock_result.id = "instrument-13.4.1"
            mock_result.type = "verb_class"
            mock_result.name = "instrument"
            mock_result.description = "Use instrument"
            mock_result.score = 0.85

            mock_search.search_with_fuzzy.return_value = [mock_result]

            runner = CliRunner()
            result = runner.invoke(
                search_query,
                ["instrment", "--fuzzy", "--json", "--data-dir", str(data_dir)],
            )

            assert result.exit_code == 0

            # Should output valid JSON
            output = json.loads(result.output)
            assert len(output) == 1
            assert output[0]["id"] == "instrument-13.4.1"
            assert output[0]["score"] == 0.85

    def test_search_query_without_fuzzy(self, tmp_path: Path) -> None:
        """Test that normal search works without --fuzzy flag."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "verbnet.jsonl").touch()

        with patch("glazing.cli.search.UnifiedSearch") as mock_unified_search:
            mock_search = MagicMock()
            mock_unified_search.return_value = mock_search

            mock_result = MagicMock()
            mock_result.dataset = "verbnet"
            mock_result.id = "give-13.1"
            mock_result.type = "verb_class"
            mock_result.name = "give"
            mock_result.description = "Transfer"
            mock_result.score = 1.0

            mock_search.search.return_value = [mock_result]

            runner = CliRunner()
            result = runner.invoke(
                search_query,
                ["give", "--data-dir", str(data_dir)],
            )

            assert result.exit_code == 0
            mock_search.search.assert_called_once_with("give")
            mock_search.search_with_fuzzy.assert_not_called()


class TestXrefCLI:
    """Test xref CLI commands."""

    def test_xref_resolve_command(self, tmp_path: Path) -> None:
        """Test xref resolve command."""
        with patch("glazing.cli.xref.CrossReferenceIndex") as mock_index_cls:
            mock_index = MagicMock()
            mock_index_cls.return_value = mock_index

            # Mock resolve result
            mock_index.resolve.return_value = {
                "source_dataset": "propbank",
                "source_id": "give.01",
                "verbnet_classes": ["give-13.1", "give-13.1-1"],
                "propbank_rolesets": [],
                "framenet_frames": ["Giving"],
                "wordnet_synsets": ["give%2:40:00::"],
                "confidence_scores": {
                    "verbnet:give-13.1": 0.95,
                    "verbnet:give-13.1-1": 0.90,
                    "framenet:Giving": 0.85,
                    "wordnet:give%2:40:00::": 0.80,
                },
            }

            runner = CliRunner()
            result = runner.invoke(
                resolve_xref,
                ["give.01", "--source", "propbank"],
            )

            assert result.exit_code == 0
            assert "give-13.1" in result.output
            assert "Giving" in result.output
            mock_index.resolve.assert_called_once_with(
                "give.01", "propbank", fuzzy=False, threshold=0.8
            )

    def test_xref_resolve_with_fuzzy(self, tmp_path: Path) -> None:
        """Test xref resolve with fuzzy matching."""
        with patch("glazing.cli.xref.CrossReferenceIndex") as mock_index_cls:
            mock_index = MagicMock()
            mock_index_cls.return_value = mock_index

            mock_index.resolve.return_value = {
                "source_dataset": "propbank",
                "source_id": "give.01",
                "verbnet_classes": ["give-13.1"],
                "propbank_rolesets": [],
                "framenet_frames": ["Giving"],
                "wordnet_synsets": [],
                "confidence_scores": {"verbnet:give-13.1": 0.95, "framenet:Giving": 0.85},
            }

            runner = CliRunner()
            result = runner.invoke(
                resolve_xref,
                ["giv.01", "--source", "propbank", "--fuzzy", "--threshold", "0.7"],
            )

            assert result.exit_code == 0
            mock_index.resolve.assert_called_once_with(
                "giv.01", "propbank", fuzzy=True, threshold=0.7
            )

    def test_xref_resolve_json_output(self, tmp_path: Path) -> None:
        """Test xref resolve with JSON output."""
        with patch("glazing.cli.xref.CrossReferenceIndex") as mock_index_cls:
            mock_index = MagicMock()
            mock_index_cls.return_value = mock_index

            mock_index.resolve.return_value = {
                "source_dataset": "verbnet",
                "source_id": "give-13.1",
                "verbnet_classes": [],
                "propbank_rolesets": ["give.01"],
                "framenet_frames": ["Giving"],
                "wordnet_synsets": [],
                "confidence_scores": {"propbank:give.01": 0.95, "framenet:Giving": 0.85},
            }

            runner = CliRunner()
            result = runner.invoke(
                resolve_xref,
                ["give-13.1", "--source", "verbnet", "--json"],
            )

            assert result.exit_code == 0

            # Should output valid JSON
            output = json.loads(result.output)
            assert output["source_id"] == "give-13.1"
            assert "give.01" in output["propbank_rolesets"]
            assert "Giving" in output["framenet_frames"]

    def test_xref_extract_command(self, tmp_path: Path) -> None:
        """Test xref extract command."""
        cache_dir = tmp_path / "cache"

        with patch("glazing.cli.xref.CrossReferenceIndex") as mock_index_cls:
            mock_index = MagicMock()
            mock_index_cls.return_value = mock_index

            runner = CliRunner()
            result = runner.invoke(
                extract_xref,
                ["--cache-dir", str(cache_dir), "--progress"],
            )

            assert result.exit_code == 0
            assert "Cross-references extracted successfully" in result.output
            mock_index.extract_all.assert_called_once()

    def test_xref_extract_with_force(self, tmp_path: Path) -> None:
        """Test xref extract with --force flag."""
        cache_dir = tmp_path / "cache"

        with patch("glazing.cli.xref.CrossReferenceIndex") as mock_index_cls:
            mock_index = MagicMock()
            mock_index_cls.return_value = mock_index

            runner = CliRunner()
            result = runner.invoke(
                extract_xref,
                ["--cache-dir", str(cache_dir), "--force"],
            )

            assert result.exit_code == 0
            mock_index.clear_cache.assert_called_once()
            mock_index.extract_all.assert_called_once()

    def test_xref_clear_cache_command(self, tmp_path: Path) -> None:
        """Test xref clear-cache command."""
        cache_dir = tmp_path / "cache"

        with patch("glazing.cli.xref.CrossReferenceIndex") as mock_index_cls:
            mock_index = MagicMock()
            mock_index_cls.return_value = mock_index

            runner = CliRunner()
            # Use --yes to skip confirmation
            result = runner.invoke(
                clear_cache,
                ["--cache-dir", str(cache_dir), "--yes"],
            )

            assert result.exit_code == 0
            assert "Cache cleared successfully" in result.output
            mock_index.clear_cache.assert_called_once()

    def test_xref_no_results_found(self, tmp_path: Path) -> None:
        """Test xref resolve when no results are found."""
        with patch("glazing.cli.xref.CrossReferenceIndex") as mock_index_cls:
            mock_index = MagicMock()
            mock_index_cls.return_value = mock_index

            mock_index.resolve.return_value = {
                "source_dataset": "verbnet",
                "source_id": "nonexistent-1.0",
                "verbnet_classes": [],
                "propbank_rolesets": [],
                "framenet_frames": [],
                "wordnet_synsets": [],
                "confidence_scores": {},
            }

            runner = CliRunner()
            result = runner.invoke(
                resolve_xref,
                ["nonexistent-1.0", "--source", "verbnet"],
            )

            assert result.exit_code == 0
            assert "No cross-references found" in result.output


class TestStructuredRoleSearch:
    """Test structured role/argument search via CLI."""

    def test_search_role_optional_verbnet(self, tmp_path: Path) -> None:
        """Test searching for optional VerbNet roles."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "verbnet.jsonl").touch()

        with patch("glazing.cli.search.load_search_index") as mock_load:
            mock_search = MagicMock()
            mock_load.return_value = mock_search

            # Mock search method
            mock_search.search.return_value = []

            runner = CliRunner()
            result = runner.invoke(
                search_query,
                ["--data-dir", str(data_dir), "--dataset", "verbnet", "?Agent"],
            )

            # This would require implementing the structured search in CLI
            # For now, just verify basic functionality works
            assert result.exit_code == 0

    def test_search_args_by_type_propbank(self, tmp_path: Path) -> None:
        """Test searching for PropBank arguments by type."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "propbank.jsonl").touch()

        with patch("glazing.cli.search.load_search_index") as mock_load:
            mock_search = MagicMock()
            mock_load.return_value = mock_search

            # Mock search method
            mock_search.search.return_value = []

            runner = CliRunner()
            result = runner.invoke(
                search_query,
                ["--data-dir", str(data_dir), "--dataset", "propbank", "ARGM-LOC"],
            )

            assert result.exit_code == 0


class TestProgressIndicators:
    """Test progress indicators in CLI commands."""

    def test_xref_extract_shows_progress(self, tmp_path: Path) -> None:
        """Test that xref extract shows progress indicators."""
        with patch("glazing.cli.xref.CrossReferenceIndex") as mock_index_cls:
            mock_index = MagicMock()
            mock_index_cls.return_value = mock_index

            # Verify that show_progress=True when --progress is used
            runner = CliRunner()
            result = runner.invoke(extract_xref, ["--progress"])

            assert result.exit_code == 0
            # Check that CrossReferenceIndex was called with show_progress=True
            mock_index_cls.assert_called_with(
                auto_extract=False,
                cache_dir=None,
                show_progress=True,
            )

    def test_xref_extract_no_progress(self, tmp_path: Path) -> None:
        """Test that xref extract can hide progress indicators."""
        with patch("glazing.cli.xref.CrossReferenceIndex") as mock_index_cls:
            mock_index = MagicMock()
            mock_index_cls.return_value = mock_index

            runner = CliRunner()
            result = runner.invoke(extract_xref, ["--no-progress"])

            assert result.exit_code == 0
            # Check that CrossReferenceIndex was called with show_progress=False
            mock_index_cls.assert_called_with(
                auto_extract=False,
                cache_dir=None,
                show_progress=False,
            )


class TestErrorHandling:
    """Test error handling in structured search CLI."""

    def test_invalid_source_dataset(self) -> None:
        """Test error handling for invalid source dataset."""
        runner = CliRunner()
        result = runner.invoke(
            resolve_xref,
            ["test.01", "--source", "invalid"],
        )

        assert result.exit_code != 0
        assert "Invalid value" in result.output

    def test_missing_required_source(self) -> None:
        """Test error when source is not provided."""
        runner = CliRunner()
        result = runner.invoke(resolve_xref, ["test.01"])

        assert result.exit_code != 0
        assert "Missing option" in result.output

    def test_invalid_threshold_value(self) -> None:
        """Test error for invalid threshold value."""
        runner = CliRunner()
        result = runner.invoke(
            resolve_xref,
            ["test.01", "--source", "verbnet", "--fuzzy", "--threshold", "1.5"],
        )

        # Click should reject values outside 0.0-1.0 range
        assert result.exit_code != 0  # Should fail with invalid threshold
        # Could check for error message about threshold range

    def test_cache_dir_permission_error(self, tmp_path: Path) -> None:
        """Test handling of cache directory permission errors."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        with patch("glazing.cli.xref.CrossReferenceIndex") as mock_index_cls:
            # PermissionError should be wrapped in RuntimeError by the index
            mock_index_cls.side_effect = RuntimeError(
                "Failed to create cache directory: Permission denied"
            )

            runner = CliRunner()
            result = runner.invoke(
                extract_xref,
                ["--cache-dir", str(cache_dir)],
            )

            # The CLI should catch RuntimeError and exit with code 1
            assert result.exit_code == 1
            assert "Extraction failed" in result.output or "Permission denied" in result.output
