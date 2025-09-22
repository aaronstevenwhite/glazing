"""Tests for CLI convert commands.

Comprehensive tests for the convert CLI functionality including
individual dataset conversions, bulk conversions, and error handling.
"""

import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from glazing.cli.convert import convert_dataset_cmd, dataset_info_cmd, list_datasets


class TestConvertDatasetCommand:
    """Test the dataset conversion command."""

    def test_convert_dataset_verbnet_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful VerbNet dataset conversion via CLI."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        def mock_convert_verbnet(in_dir: Path, out_dir: Path, verbose: bool = False) -> None:
            (out_dir / "verbnet.jsonl").touch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.convert"], "convert_verbnet", mock_convert_verbnet
        )

        runner = CliRunner()
        result = runner.invoke(
            convert_dataset_cmd,
            [
                "--dataset",
                "verbnet",
                "--input-dir",
                str(input_dir),
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0
        assert "Converting VerbNet" in result.output
        assert "Conversion complete!" in result.output

    def test_convert_dataset_propbank_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful PropBank dataset conversion via CLI."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        def mock_convert_propbank(in_dir: Path, out_dir: Path, verbose: bool = False) -> None:
            (out_dir / "propbank.jsonl").touch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.convert"], "convert_propbank", mock_convert_propbank
        )

        runner = CliRunner()
        result = runner.invoke(
            convert_dataset_cmd,
            [
                "--dataset",
                "propbank",
                "--input-dir",
                str(input_dir),
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0
        assert "Converting PropBank" in result.output
        assert "Conversion complete!" in result.output

    def test_convert_dataset_wordnet_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful WordNet dataset conversion via CLI."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        def mock_convert_wordnet(in_dir: Path, out_dir: Path, verbose: bool = False) -> None:
            (out_dir / "synsets_noun.jsonl").touch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.convert"], "convert_wordnet", mock_convert_wordnet
        )

        runner = CliRunner()
        result = runner.invoke(
            convert_dataset_cmd,
            [
                "--dataset",
                "wordnet",
                "--input-dir",
                str(input_dir),
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0
        assert "Converting WordNet" in result.output
        assert "Conversion complete!" in result.output

    def test_convert_dataset_framenet_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful FrameNet dataset conversion via CLI."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        def mock_convert_framenet(in_dir: Path, out_dir: Path, verbose: bool = False) -> None:
            (out_dir / "framenet.jsonl").touch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.convert"], "convert_framenet", mock_convert_framenet
        )

        runner = CliRunner()
        result = runner.invoke(
            convert_dataset_cmd,
            [
                "--dataset",
                "framenet",
                "--input-dir",
                str(input_dir),
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0
        assert "Converting FrameNet" in result.output
        assert "Conversion complete!" in result.output

    def test_convert_dataset_all_success(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful conversion of all datasets via CLI."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        def mock_convert_verbnet(in_dir: Path, out_dir: Path, verbose: bool = False) -> None:
            (out_dir / "verbnet.jsonl").touch()

        def mock_convert_propbank(in_dir: Path, out_dir: Path, verbose: bool = False) -> None:
            (out_dir / "propbank.jsonl").touch()

        def mock_convert_wordnet(in_dir: Path, out_dir: Path, verbose: bool = False) -> None:
            (out_dir / "synsets_noun.jsonl").touch()

        def mock_convert_framenet(in_dir: Path, out_dir: Path, verbose: bool = False) -> None:
            (out_dir / "framenet.jsonl").touch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.convert"], "convert_verbnet", mock_convert_verbnet
        )
        monkeypatch.setattr(
            sys.modules["glazing.cli.convert"], "convert_propbank", mock_convert_propbank
        )
        monkeypatch.setattr(
            sys.modules["glazing.cli.convert"], "convert_wordnet", mock_convert_wordnet
        )
        monkeypatch.setattr(
            sys.modules["glazing.cli.convert"], "convert_framenet", mock_convert_framenet
        )

        runner = CliRunner()
        result = runner.invoke(
            convert_dataset_cmd,
            ["--dataset", "all", "--input-dir", str(input_dir), "--output-dir", str(output_dir)],
        )

        assert result.exit_code == 0
        assert "Converting VerbNet" in result.output
        assert "Converting PropBank" in result.output
        assert "Converting WordNet" in result.output
        assert "Converting FrameNet" in result.output
        assert "Conversion complete!" in result.output

    def test_convert_dataset_nonexistent_input_dir(self, tmp_path: Path) -> None:
        """Test conversion with nonexistent input directory."""
        runner = CliRunner()
        output_dir = tmp_path / "output"
        result = runner.invoke(
            convert_dataset_cmd,
            [
                "--dataset",
                "verbnet",
                "--input-dir",
                "/nonexistent/path",
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 2
        assert "does not exist" in result.output

    def test_convert_dataset_invalid_dataset(self, tmp_path: Path) -> None:
        """Test conversion with invalid dataset name."""
        runner = CliRunner()
        result = runner.invoke(
            convert_dataset_cmd,
            [
                "--dataset",
                "invalid",
                "--input-dir",
                str(tmp_path),
                "--output-dir",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 2
        assert "Invalid value for '--dataset'" in result.output

    def test_convert_dataset_with_verbose_flag(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test conversion with verbose flag."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        verbose_called = False

        def mock_convert_verbnet(in_dir: Path, out_dir: Path, verbose: bool = False) -> None:
            nonlocal verbose_called
            verbose_called = verbose
            (out_dir / "verbnet.jsonl").touch()

        monkeypatch.setattr(
            sys.modules["glazing.cli.convert"], "convert_verbnet", mock_convert_verbnet
        )

        runner = CliRunner()
        result = runner.invoke(
            convert_dataset_cmd,
            [
                "--dataset",
                "verbnet",
                "--input-dir",
                str(input_dir),
                "--output-dir",
                str(output_dir),
                "--verbose",
            ],
        )

        assert result.exit_code == 0
        assert verbose_called is True

    def test_convert_dataset_permission_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test conversion with permission error."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()

        def mock_convert_verbnet(in_dir: Path, out_dir: Path, verbose: bool = False) -> None:
            raise PermissionError("Access denied")

        monkeypatch.setattr(
            sys.modules["glazing.cli.convert"], "convert_verbnet", mock_convert_verbnet
        )

        runner = CliRunner()
        result = runner.invoke(
            convert_dataset_cmd,
            [
                "--dataset",
                "verbnet",
                "--input-dir",
                str(input_dir),
                "--output-dir",
                str(output_dir),
            ],
        )

        assert result.exit_code == 1
        assert "Permission denied" in result.output


class TestListDatasetsCommand:
    """Test the list datasets command."""

    def test_list_datasets(self) -> None:
        """Test listing available datasets."""
        runner = CliRunner()
        result = runner.invoke(list_datasets)

        assert result.exit_code == 0
        assert "VerbNet" in result.output
        assert "PropBank" in result.output
        assert "WordNet" in result.output
        assert "FrameNet" in result.output
        assert "XML files" in result.output  # Check for format info


class TestDatasetInfoCommand:
    """Test the dataset info command."""

    def test_dataset_info_verbnet(self) -> None:
        """Test getting VerbNet dataset info."""
        runner = CliRunner()
        result = runner.invoke(dataset_info_cmd, ["--dataset", "verbnet"])

        assert result.exit_code == 0
        assert "VerbNet Conversion Information" in result.output
        assert "XML files" in result.output
        assert "verbnet.jsonl" in result.output
        assert "VerbNetConverter" in result.output

    def test_dataset_info_propbank(self) -> None:
        """Test getting PropBank dataset info."""
        runner = CliRunner()
        result = runner.invoke(dataset_info_cmd, ["--dataset", "propbank"])

        assert result.exit_code == 0
        assert "PropBank Conversion Information" in result.output
        assert "propbank.jsonl" in result.output

    def test_dataset_info_wordnet(self) -> None:
        """Test getting WordNet dataset info."""
        runner = CliRunner()
        result = runner.invoke(dataset_info_cmd, ["--dataset", "wordnet"])

        assert result.exit_code == 0
        assert "WordNet Conversion Information" in result.output
        assert "wordnet.jsonl" in result.output
        assert "Database files" in result.output

    def test_dataset_info_framenet(self) -> None:
        """Test getting FrameNet dataset info."""
        runner = CliRunner()
        result = runner.invoke(dataset_info_cmd, ["--dataset", "framenet"])

        assert result.exit_code == 0
        assert "FrameNet Conversion Information" in result.output
        assert "framenet.jsonl" in result.output

    def test_dataset_info_invalid(self) -> None:
        """Test getting info for invalid dataset."""
        runner = CliRunner()
        result = runner.invoke(dataset_info_cmd, ["--dataset", "invalid"])

        assert result.exit_code == 2
        assert "Invalid value for '--dataset'" in result.output
