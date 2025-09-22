"""Tests for CLI search commands.

Tests for the search CLI functionality including query, entity,
role, and cross-reference search commands.
"""

import json
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from glazing.cli.search import find_cross_ref, get_entity, search_query, search_role
from glazing.verbnet.models import VerbClass


class TestSearchQueryCommand:
    """Test the search query command."""

    def test_search_query_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful search query."""
        # Create mock data files
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "verbnet_classes.jsonl").touch()

        # Mock the search functionality
        class MockSearchResult:
            def __init__(self):
                self.dataset = "verbnet"
                self.id = "give-13.1"
                self.type = "verb_class"
                self.name = "give"
                self.description = "Transfer of possession"
                self.score = 0.95

        def mock_load_search_index(data_dir: Path, datasets: list[str] | None = None):
            class MockSearch:
                def search(self, query: str):
                    return [MockSearchResult()]

            return MockSearch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.search"], "load_search_index", mock_load_search_index
        )

        runner = CliRunner()
        result = runner.invoke(search_query, ["give", "--data-dir", str(data_dir)])

        assert result.exit_code == 0
        assert "give" in result.output
        assert "verbnet" in result.output.lower()

    def test_search_query_no_results(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test search query with no results."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        def mock_load_search_index(data_dir: Path, datasets: list[str] | None = None):
            class MockSearch:
                def search(self, query: str):
                    return []

            return MockSearch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.search"], "load_search_index", mock_load_search_index
        )

        runner = CliRunner()
        result = runner.invoke(search_query, ["nonexistent", "--data-dir", str(data_dir)])

        assert result.exit_code == 0
        assert "No results found" in result.output

    def test_search_query_json_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test search query with JSON output."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        class MockSearchResult:
            def __init__(self):
                self.dataset = "verbnet"
                self.id = "give-13.1"
                self.type = "verb_class"
                self.name = "give"
                self.description = "Transfer"
                self.score = 0.95

        def mock_load_search_index(data_dir: Path, datasets: list[str] | None = None):
            class MockSearch:
                def search(self, query: str):
                    return [MockSearchResult()]

            return MockSearch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.search"], "load_search_index", mock_load_search_index
        )

        runner = CliRunner()
        result = runner.invoke(search_query, ["give", "--data-dir", str(data_dir), "--json"])

        assert result.exit_code == 0
        # Check if output is valid JSON
        output_json = json.loads(result.output)
        assert isinstance(output_json, list)
        assert len(output_json) == 1
        assert output_json[0]["id"] == "give-13.1"

    def test_search_query_with_limit(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test search query with result limit."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        class MockSearchResult:
            def __init__(self, idx: int):
                self.dataset = "verbnet"
                self.id = f"class-{idx}"
                self.type = "verb_class"
                self.name = f"verb{idx}"
                self.description = f"Description {idx}"
                self.score = 0.9 - idx * 0.1

        def mock_load_search_index(data_dir: Path, datasets: list[str] | None = None):
            class MockSearch:
                def search(self, query: str):
                    return [MockSearchResult(i) for i in range(20)]

            return MockSearch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.search"], "load_search_index", mock_load_search_index
        )

        runner = CliRunner()
        result = runner.invoke(search_query, ["test", "--data-dir", str(data_dir), "--limit", "5"])

        assert result.exit_code == 0
        assert "Showing 5 of 20 results" in result.output

    def test_search_query_specific_dataset(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test search query for specific dataset."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        datasets_loaded = []

        def mock_load_search_index(data_dir: Path, datasets: list[str] | None = None):
            nonlocal datasets_loaded
            datasets_loaded = datasets

            class MockSearch:
                def search(self, query: str):
                    return []

            return MockSearch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.search"], "load_search_index", mock_load_search_index
        )

        runner = CliRunner()
        result = runner.invoke(
            search_query, ["test", "--data-dir", str(data_dir), "--dataset", "verbnet"]
        )

        assert result.exit_code == 0
        assert datasets_loaded == ["verbnet"]


class TestGetEntityCommand:
    """Test the get entity command."""

    def test_get_entity_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful entity retrieval."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        class MockEntity:
            def __init__(self):
                self.id = "give-13.1"
                self.members = [1, 2, 3]
                self.themroles = [type("Role", (), {"type": "Agent"})]
                self.frames = [1, 2]

            def model_dump_json(self, indent: int = 2):
                return json.dumps({"id": self.id, "members": 3}, indent=indent)

        def mock_load_search_index(data_dir: Path, datasets: list[str] | None = None):
            class MockSearch:
                def get_entity(self, entity_id: str, dataset: str):
                    return MockEntity()

            return MockSearch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.search"], "load_search_index", mock_load_search_index
        )

        # Patch isinstance to recognize MockEntity as VerbClass
        original_isinstance = isinstance

        def mock_isinstance(obj, classinfo):
            if classinfo == VerbClass and hasattr(obj, "members"):
                return True
            return original_isinstance(obj, classinfo)

        monkeypatch.setattr("builtins.isinstance", mock_isinstance)

        runner = CliRunner()
        result = runner.invoke(
            get_entity, ["give-13.1", "--dataset", "verbnet", "--data-dir", str(data_dir)]
        )

        assert result.exit_code == 0
        assert "give-13.1" in result.output
        assert "Members: 3" in result.output

    def test_get_entity_not_found(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test entity not found."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        def mock_load_search_index(data_dir: Path, datasets: list[str] | None = None):
            class MockSearch:
                def get_entity(self, entity_id: str, dataset: str):
                    return None

            return MockSearch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.search"], "load_search_index", mock_load_search_index
        )

        runner = CliRunner()
        result = runner.invoke(
            get_entity, ["nonexistent", "--dataset", "verbnet", "--data-dir", str(data_dir)]
        )

        assert result.exit_code == 0
        assert "not found" in result.output


class TestSearchRoleCommand:
    """Test the search role command."""

    def test_search_role_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful role search."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        class MockResult:
            def __init__(self, dataset: str, idx: int):
                self.dataset = dataset
                self.id = f"{dataset}-{idx}"
                self.description = f"Role in {dataset}"

        def mock_load_search_index(data_dir: Path, datasets: list[str] | None = None):
            class MockSearch:
                def search_semantic_roles(self, role_name: str):
                    return [MockResult("verbnet", 1), MockResult("framenet", 2)]

            return MockSearch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.search"], "load_search_index", mock_load_search_index
        )

        runner = CliRunner()
        result = runner.invoke(search_role, ["Agent", "--data-dir", str(data_dir)])

        assert result.exit_code == 0
        assert "VERBNET" in result.output
        assert "FRAMENET" in result.output

    def test_search_role_no_results(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test role search with no results."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        def mock_load_search_index(data_dir: Path, datasets: list[str] | None = None):
            class MockSearch:
                def search_semantic_roles(self, role_name: str):
                    return []

            return MockSearch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.search"], "load_search_index", mock_load_search_index
        )

        runner = CliRunner()
        result = runner.invoke(search_role, ["NonexistentRole", "--data-dir", str(data_dir)])

        assert result.exit_code == 0
        assert "No roles matching" in result.output


class TestFindCrossRefCommand:
    """Test the find cross-reference command."""

    def test_find_cross_ref_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful cross-reference search."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        class MockRef:
            def __init__(self):
                self.target_id = "abandon.01"
                self.mapping_type = "exact"
                self.confidence = 0.95

            def __getitem__(self, key):
                return getattr(self, key)

            def get(self, key, default=None):
                return getattr(self, key, default)

        def mock_load_search_index(data_dir: Path, datasets: list[str] | None = None):
            class MockSearch:
                def find_cross_references(self, entity_id: str, source: str, target: str):
                    return [MockRef()]

            return MockSearch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.search"], "load_search_index", mock_load_search_index
        )

        runner = CliRunner()
        result = runner.invoke(
            find_cross_ref,
            [
                "--source",
                "verbnet",
                "--target",
                "propbank",
                "--id",
                "give-13.1",
                "--data-dir",
                str(data_dir),
            ],
        )

        assert result.exit_code == 0
        assert "abandon.01" in result.output
        assert "0.95" in result.output

    def test_find_cross_ref_no_results(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test cross-reference search with no results."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        def mock_load_search_index(data_dir: Path, datasets: list[str] | None = None):
            class MockSearch:
                def find_cross_references(self, entity_id: str, source: str, target: str):
                    return []

            return MockSearch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.search"], "load_search_index", mock_load_search_index
        )

        runner = CliRunner()
        result = runner.invoke(
            find_cross_ref,
            [
                "--source",
                "verbnet",
                "--target",
                "propbank",
                "--id",
                "nonexistent",
                "--data-dir",
                str(data_dir),
            ],
        )

        assert result.exit_code == 0
        assert "No propbank references found" in result.output
