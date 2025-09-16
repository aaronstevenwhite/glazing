"""Tests for CLI download commands.

Comprehensive tests for the download CLI functionality including
individual dataset downloads, bulk downloads, and error handling.
"""

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from glazing.cli.download import dataset_info, download_dataset_cmd, list_datasets
from glazing.downloader import DownloadError, ExtractionError


class TestDownloadDatasetCommand:
    """Test the dataset download command."""

    def test_dataset_command_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful dataset download via CLI."""

        def mock_download_dataset(dataset_name: str, output_dir: Path) -> Path:
            return output_dir / f"{dataset_name.lower()}-result"

        monkeypatch.setattr(
            sys.modules["glazing.cli.download"], "download_dataset", mock_download_dataset
        )

        runner = CliRunner()
        result = runner.invoke(
            download_dataset_cmd, ["--dataset", "verbnet", "--output-dir", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "✓ VerbNet: Downloaded to" in result.output
        assert str(tmp_path / "verbnet-result") in result.output

    def test_dataset_command_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test dataset download failure via CLI."""

        def mock_download_dataset(dataset_name: str, output_dir: Path) -> Path:
            raise DownloadError("Network error")

        monkeypatch.setattr(
            sys.modules["glazing.cli.download"], "download_dataset", mock_download_dataset
        )

        runner = CliRunner()
        result = runner.invoke(
            download_dataset_cmd, ["--dataset", "verbnet", "--output-dir", str(tmp_path)]
        )

        assert result.exit_code == 1
        assert "✗ Failed to download VerbNet:" in result.output
        assert "Network error" in result.output

    def test_dataset_command_extraction_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test dataset extraction failure via CLI."""

        def mock_download_dataset(dataset_name: str, output_dir: Path) -> Path:
            raise ExtractionError("Corrupted archive")

        monkeypatch.setattr(
            sys.modules["glazing.cli.download"], "download_dataset", mock_download_dataset
        )

        runner = CliRunner()
        result = runner.invoke(
            download_dataset_cmd, ["--dataset", "wordnet", "--output-dir", str(tmp_path)]
        )

        assert result.exit_code == 1
        assert "✗ Failed to download WordNet:" in result.output
        assert "Corrupted archive" in result.output

    def test_dataset_command_invalid_dataset(self, tmp_path: Path) -> None:
        """Test invalid dataset name via CLI."""
        runner = CliRunner()
        result = runner.invoke(
            download_dataset_cmd, ["--dataset", "invaliddata", "--output-dir", str(tmp_path)]
        )

        assert result.exit_code == 2
        assert "Invalid value for '--dataset'" in result.output

    def test_dataset_command_nonexistent_directory(self) -> None:
        """Test download to nonexistent directory."""
        runner = CliRunner()
        result = runner.invoke(
            download_dataset_cmd, ["--dataset", "verbnet", "--output-dir", "/nonexistent/path"]
        )

        assert result.exit_code == 1
        assert "✗ Failed to create output directory:" in result.output

    def test_dataset_command_with_verbose_output(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test dataset download with verbose output."""

        def mock_download_dataset(dataset_name: str, output_dir: Path) -> Path:
            print(f"Downloading {dataset_name}...")
            print("Extracting archive...")
            return output_dir / f"{dataset_name.lower()}-result"

        monkeypatch.setattr(
            sys.modules["glazing.cli.download"], "download_dataset", mock_download_dataset
        )

        runner = CliRunner()
        result = runner.invoke(
            download_dataset_cmd, ["--dataset", "propbank", "--output-dir", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "✓ PropBank: Downloaded to" in result.output


class TestListDatasetsCommand:
    """Test the list datasets command."""

    def test_list_datasets_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test listing available datasets."""

        def mock_get_available_datasets() -> list[str]:
            return ["VerbNet", "PropBank", "WordNet", "FrameNet"]

        def mock_get_dataset_info(dataset_name: str) -> dict[str, str]:
            versions = {"VerbNet": "3.4", "PropBank": "3.4.0", "WordNet": "3.1", "FrameNet": "1.7"}
            return {
                "name": dataset_name,
                "version": versions[dataset_name],
                "class": f"{dataset_name}Downloader",
            }

        monkeypatch.setattr(
            sys.modules["glazing.cli.download"],
            "get_available_datasets",
            mock_get_available_datasets,
        )
        monkeypatch.setattr(
            sys.modules["glazing.cli.download"], "get_dataset_info", mock_get_dataset_info
        )

        runner = CliRunner()
        result = runner.invoke(list_datasets)

        assert result.exit_code == 0
        assert "Available datasets:" in result.output
        assert "VerbNet" in result.output
        assert "PropBank" in result.output
        assert "WordNet" in result.output
        assert "FrameNet" in result.output

    def test_list_datasets_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test listing when no datasets are available."""

        def mock_get_available_datasets() -> list[str]:
            return []

        def mock_get_dataset_info(dataset_name: str) -> dict[str, str]:
            return {"name": dataset_name, "version": "1.0", "class": "TestDownloader"}

        monkeypatch.setattr(
            sys.modules["glazing.cli.download"],
            "get_available_datasets",
            mock_get_available_datasets,
        )
        monkeypatch.setattr(
            sys.modules["glazing.cli.download"], "get_dataset_info", mock_get_dataset_info
        )

        runner = CliRunner()
        result = runner.invoke(list_datasets)

        assert result.exit_code == 0
        assert "Available datasets:" in result.output


class TestInfoCommand:
    """Test the dataset info command."""

    def test_info_command_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting dataset information."""

        def mock_get_dataset_info(dataset_name: str) -> dict[str, str]:
            return {"name": "VerbNet", "version": "3.4", "class": "VerbNetDownloader"}

        monkeypatch.setattr(
            sys.modules["glazing.cli.download"], "get_dataset_info", mock_get_dataset_info
        )

        runner = CliRunner()
        result = runner.invoke(dataset_info, ["verbnet"])

        assert result.exit_code == 0
        assert "Dataset: VerbNet" in result.output
        assert "Version: 3.4" in result.output
        assert "Downloader: VerbNetDownloader" in result.output

    def test_info_command_invalid_dataset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting info for invalid dataset."""

        def mock_get_dataset_info(dataset_name: str) -> dict[str, str]:
            raise ValueError("Unsupported dataset: InvalidDataset")

        monkeypatch.setattr(
            sys.modules["glazing.cli.download"], "get_dataset_info", mock_get_dataset_info
        )

        runner = CliRunner()
        result = runner.invoke(dataset_info, ["invaliddata"])

        assert result.exit_code == 2
        assert "Invalid value for" in result.output

    def test_info_command_multiple_datasets(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting info for multiple datasets."""

        def mock_get_dataset_info(dataset_name: str) -> dict[str, str]:
            if dataset_name == "VerbNet":
                return {"name": "VerbNet", "version": "3.4", "class": "VerbNetDownloader"}
            if dataset_name == "WordNet":
                return {"name": "WordNet", "version": "3.1", "class": "WordNetDownloader"}
            raise ValueError(f"Unsupported dataset: {dataset_name}")

        monkeypatch.setattr(
            sys.modules["glazing.cli.download"], "get_dataset_info", mock_get_dataset_info
        )

        runner = CliRunner()
        result = runner.invoke(dataset_info, ["verbnet", "wordnet"])

        assert result.exit_code == 2
        assert "Usage:" in result.output

    def test_info_command_mixed_success_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting info where some datasets succeed and others fail."""

        def mock_get_dataset_info(dataset_name: str) -> dict[str, str]:
            if dataset_name == "VerbNet":
                return {"name": "VerbNet", "version": "3.4", "class": "VerbNetDownloader"}
            raise ValueError(f"Unsupported dataset: {dataset_name}")

        monkeypatch.setattr(
            sys.modules["glazing.cli.download"], "get_dataset_info", mock_get_dataset_info
        )

        runner = CliRunner()
        result = runner.invoke(dataset_info, ["verbnet", "invaliddata"])

        assert result.exit_code == 2  # Should fail due to invalid usage
        assert "Usage:" in result.output


class TestCLIIntegration:
    """Test CLI integration scenarios."""

    def test_cli_error_handling_formatting(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that CLI error messages are properly formatted."""

        def mock_download_dataset(dataset_name: str, output_dir: Path) -> Path:
            raise DownloadError("Connection timeout after 30 seconds")

        monkeypatch.setattr(
            sys.modules["glazing.cli.download"], "download_dataset", mock_download_dataset
        )

        runner = CliRunner()
        result = runner.invoke(
            download_dataset_cmd, ["--dataset", "framenet", "--output-dir", str(tmp_path)]
        )

        assert result.exit_code == 1
        assert "✗ Failed to download FrameNet:" in result.output
        assert "Connection timeout after 30 seconds" in result.output

    def test_cli_success_message_formatting(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that CLI success messages are properly formatted."""
        result_path = tmp_path / "framenet-1.7"

        def mock_download_dataset(dataset_name: str, output_dir: Path) -> Path:
            return result_path

        monkeypatch.setattr(
            sys.modules["glazing.cli.download"], "download_dataset", mock_download_dataset
        )

        runner = CliRunner()
        result = runner.invoke(
            download_dataset_cmd, ["--dataset", "framenet", "--output-dir", str(tmp_path)]
        )

        assert result.exit_code == 0
        assert "✓ FrameNet: Downloaded to" in result.output
        assert str(result_path) in result.output

    def test_cli_path_resolution(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that CLI properly resolves relative paths."""

        def mock_download_dataset(dataset_name: str, output_dir: Path) -> Path:
            assert output_dir.is_absolute()
            return output_dir / f"{dataset_name.lower()}-result"

        monkeypatch.setattr(
            sys.modules["glazing.cli.download"], "download_dataset", mock_download_dataset
        )

        runner = CliRunner()
        # Use relative path
        with runner.isolated_filesystem():
            result = runner.invoke(
                download_dataset_cmd, ["--dataset", "verbnet", "--output-dir", "."]
            )
            assert result.exit_code == 0
