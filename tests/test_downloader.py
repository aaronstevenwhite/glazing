"""Tests for the downloader module.

Comprehensive tests for the base downloader functionality and
dataset-specific downloaders including error handling and integration tests.
"""

import hashlib
import zipfile
from pathlib import Path

import pytest
import requests

from glazing.downloader import (
    BaseDownloader,
    DownloadError,
    ExtractionError,
    FrameNetDownloader,
    PropBankDownloader,
    VerbNetDownloader,
    WordNetDownloader,
    download_all,
    download_dataset,
    get_available_datasets,
    get_dataset_info,
    get_downloader,
)


class MockResponse:
    """Mock response for requests.get."""

    def __init__(self, headers: dict[str, str], content_chunks: list[bytes]) -> None:
        self.headers = headers
        self.content_chunks = content_chunks

    def raise_for_status(self) -> None:
        """Mock raise_for_status."""

    def iter_content(self, chunk_size: int = 8192) -> list[bytes]:
        """Mock iter_content."""
        return self.content_chunks


class TestBaseDownloader:
    """Test the abstract base downloader functionality."""

    def test_base_downloader_is_abstract(self) -> None:
        """Test that BaseDownloader cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseDownloader()  # type: ignore[abstract]

    def test_download_file_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful file download with progress tracking."""
        # Setup mock response
        mock_response = MockResponse(
            headers={"content-length": "12"}, content_chunks=[b"chunk1", b"chunk2"]
        )

        def mock_get(url: str, stream: bool = False, timeout: int = 30) -> MockResponse:
            return mock_response

        monkeypatch.setattr("glazing.downloader.requests.get", mock_get)

        # Create a concrete downloader for testing
        class TestDownloader(BaseDownloader):
            @property
            def dataset_name(self) -> str:
                return "Test"

            @property
            def version(self) -> str:
                return "1.0"

            def download(self, output_dir: Path) -> Path:
                return output_dir

        downloader = TestDownloader()
        test_file = tmp_path / "test.txt"

        # Test download
        downloader._download_file("http://example.com/file.txt", test_file)

        # Verify file was created and contains expected content
        assert test_file.exists()
        assert test_file.read_bytes() == b"chunk1chunk2"

    def test_download_file_request_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test download failure due to HTTP error."""

        def mock_get_error(url: str, stream: bool = False, timeout: int = 30) -> None:
            raise requests.RequestException("Network error")

        monkeypatch.setattr("glazing.downloader.requests.get", mock_get_error)

        class TestDownloader(BaseDownloader):
            @property
            def dataset_name(self) -> str:
                return "Test"

            @property
            def version(self) -> str:
                return "1.0"

            def download(self, output_dir: Path) -> Path:
                return output_dir

        downloader = TestDownloader()
        test_file = tmp_path / "test.txt"

        with pytest.raises(DownloadError, match="Failed to download"):
            downloader._download_file("http://example.com/file.txt", test_file)

    def test_download_file_size_mismatch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test download failure due to size mismatch."""
        mock_response = MockResponse(headers={"content-length": "500"}, content_chunks=[])

        def mock_get(url: str, stream: bool = False, timeout: int = 30) -> MockResponse:
            return mock_response

        monkeypatch.setattr("glazing.downloader.requests.get", mock_get)

        class TestDownloader(BaseDownloader):
            @property
            def dataset_name(self) -> str:
                return "Test"

            @property
            def version(self) -> str:
                return "1.0"

            def download(self, output_dir: Path) -> Path:
                return output_dir

        downloader = TestDownloader()
        test_file = tmp_path / "test.txt"

        with pytest.raises(DownloadError, match="Expected 1000 bytes, got 500"):
            downloader._download_file("http://example.com/file.txt", test_file, expected_size=1000)

    def test_extract_zip_archive(self, tmp_path: Path) -> None:
        """Test extracting ZIP archives."""

        class TestDownloader(BaseDownloader):
            @property
            def dataset_name(self) -> str:
                return "Test"

            @property
            def version(self) -> str:
                return "1.0"

            def download(self, output_dir: Path) -> Path:
                return output_dir

        downloader = TestDownloader()

        # Create a test ZIP file
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zip_file:
            zip_file.writestr("test_dir/file1.txt", "content1")
            zip_file.writestr("test_dir/file2.txt", "content2")

        # Extract the archive
        extracted_path = downloader._extract_archive(zip_path, tmp_path)

        # Verify extraction
        assert extracted_path.exists()
        assert extracted_path.is_dir()
        assert (extracted_path / "file1.txt").read_text() == "content1"
        assert (extracted_path / "file2.txt").read_text() == "content2"

    def test_extract_unsupported_format(self, tmp_path: Path) -> None:
        """Test extraction failure for unsupported format."""

        class TestDownloader(BaseDownloader):
            @property
            def dataset_name(self) -> str:
                return "Test"

            @property
            def version(self) -> str:
                return "1.0"

            def download(self, output_dir: Path) -> Path:
                return output_dir

        downloader = TestDownloader()
        bad_file = tmp_path / "test.txt"
        bad_file.write_text("not an archive")

        with pytest.raises(ExtractionError, match="Unsupported archive format"):
            downloader._extract_archive(bad_file, tmp_path)

    def test_verify_checksum_success(self, tmp_path: Path) -> None:
        """Test successful checksum verification."""

        class TestDownloader(BaseDownloader):
            @property
            def dataset_name(self) -> str:
                return "Test"

            @property
            def version(self) -> str:
                return "1.0"

            def download(self, output_dir: Path) -> Path:
                return output_dir

        downloader = TestDownloader()
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test content")

        # Calculate expected SHA-256 hash for "test content"
        expected_hash = hashlib.sha256(b"test content").hexdigest()

        # Should not raise any exception
        downloader._verify_checksum(test_file, expected_hash)

    def test_verify_checksum_failure(self, tmp_path: Path) -> None:
        """Test checksum verification failure."""

        class TestDownloader(BaseDownloader):
            @property
            def dataset_name(self) -> str:
                return "Test"

            @property
            def version(self) -> str:
                return "1.0"

            def download(self, output_dir: Path) -> Path:
                return output_dir

        downloader = TestDownloader()
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test content")

        wrong_hash = "0" * 64  # Wrong hash

        with pytest.raises(DownloadError, match="Checksum mismatch"):
            downloader._verify_checksum(test_file, wrong_hash)


class TestVerbNetDownloader:
    """Test VerbNet-specific downloader functionality."""

    def test_properties(self) -> None:
        """Test VerbNet downloader properties."""
        downloader = VerbNetDownloader()
        assert downloader.dataset_name == "verbnet"
        assert downloader.version == "3.4"

    def test_download_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful VerbNet download."""
        # Setup mocks
        extracted_dir = tmp_path / "verbnet-extracted"
        extracted_dir.mkdir()

        def mock_download_file(self: VerbNetDownloader, url: str, path: Path) -> None:
            # Create fake archive
            path.write_bytes(b"fake archive")

        def mock_extract_archive(
            self: VerbNetDownloader, archive_path: Path, output_dir: Path
        ) -> Path:
            return extracted_dir

        monkeypatch.setattr(VerbNetDownloader, "_download_file", mock_download_file)
        monkeypatch.setattr(VerbNetDownloader, "_extract_archive", mock_extract_archive)

        downloader = VerbNetDownloader()
        result = downloader.download(tmp_path)

        assert result == extracted_dir

    def test_download_extraction_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test VerbNet download with extraction failure."""

        def mock_download_file(self: VerbNetDownloader, url: str, path: Path) -> None:
            path.write_bytes(b"fake archive")

        def mock_extract_archive(
            self: VerbNetDownloader, archive_path: Path, output_dir: Path
        ) -> Path:
            raise ExtractionError("Extract failed")

        monkeypatch.setattr(VerbNetDownloader, "_download_file", mock_download_file)
        monkeypatch.setattr(VerbNetDownloader, "_extract_archive", mock_extract_archive)

        downloader = VerbNetDownloader()

        with pytest.raises(ExtractionError, match="Extract failed"):
            downloader.download(tmp_path)


class TestPropBankDownloader:
    """Test PropBank-specific downloader functionality."""

    def test_properties(self) -> None:
        """Test PropBank downloader properties."""
        downloader = PropBankDownloader()
        assert downloader.dataset_name == "propbank"
        assert downloader.version == "3.4.0"


class TestWordNetDownloader:
    """Test WordNet-specific downloader functionality."""

    def test_properties(self) -> None:
        """Test WordNet downloader properties."""
        downloader = WordNetDownloader()
        assert downloader.dataset_name == "wordnet"
        assert downloader.version == "3.1"


class TestFrameNetDownloader:
    """Test FrameNet-specific downloader functionality."""

    def test_properties(self) -> None:
        """Test FrameNet downloader properties."""
        downloader = FrameNetDownloader()
        assert downloader.dataset_name == "framenet"
        assert downloader.version == "1.7"

    def test_download_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful FrameNet download."""
        # Setup mocks
        extracted_dir = tmp_path / "framenet-extracted"
        extracted_dir.mkdir()

        def mock_download_file(self: FrameNetDownloader, url: str, path: Path) -> None:
            # Create fake archive
            path.write_bytes(b"fake archive")

        def mock_extract_archive(
            self: FrameNetDownloader, archive_path: Path, output_dir: Path
        ) -> Path:
            return extracted_dir

        monkeypatch.setattr(FrameNetDownloader, "_download_file", mock_download_file)
        monkeypatch.setattr(FrameNetDownloader, "_extract_archive", mock_extract_archive)

        downloader = FrameNetDownloader()
        result = downloader.download(tmp_path)

        assert result == extracted_dir


class TestUtilityFunctions:
    """Test module-level utility functions."""

    def test_get_downloader(self) -> None:
        """Test getting downloader instances."""
        # Test all supported datasets
        verbnet = get_downloader("verbnet")
        assert isinstance(verbnet, VerbNetDownloader)

        propbank = get_downloader("propbank")
        assert isinstance(propbank, PropBankDownloader)

        wordnet = get_downloader("wordnet")
        assert isinstance(wordnet, WordNetDownloader)

        framenet = get_downloader("framenet")
        assert isinstance(framenet, FrameNetDownloader)

    def test_get_downloader_invalid(self) -> None:
        """Test getting downloader for invalid dataset."""
        with pytest.raises(ValueError, match="Unsupported dataset: Invalid"):
            get_downloader("Invalid")  # type: ignore[arg-type]

    def test_download_dataset(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test downloading a dataset."""

        def mock_get_downloader(dataset: str) -> VerbNetDownloader:
            downloader = VerbNetDownloader()

            def mock_download(output_dir: Path) -> Path:
                return tmp_path / "result"

            monkeypatch.setattr(downloader, "download", mock_download)
            return downloader

        monkeypatch.setattr("glazing.downloader.get_downloader", mock_get_downloader)

        result = download_dataset("verbnet", tmp_path)
        assert result == tmp_path / "result"

    def test_get_available_datasets(self) -> None:
        """Test getting list of available datasets."""
        datasets = get_available_datasets()
        expected = ["verbnet", "propbank", "wordnet", "framenet"]
        assert datasets == expected

    def test_get_dataset_info(self) -> None:
        """Test getting dataset information."""
        info = get_dataset_info("verbnet")
        assert info["name"] == "verbnet"
        assert info["version"] == "3.4"
        assert info["class"] == "VerbNetDownloader"

    def test_download_all_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test downloading all datasets successfully."""

        def mock_download_dataset(dataset: str, output_dir: Path) -> Path:
            return output_dir / f"{dataset.lower()}-result"

        monkeypatch.setattr("glazing.downloader.download_dataset", mock_download_dataset)

        results = download_all(tmp_path, ["verbnet", "propbank"])

        # Verify all datasets were attempted
        assert len(results) == 2
        assert all(isinstance(path, Path) for path in results.values())
        assert results["verbnet"] == tmp_path / "verbnet-result"
        assert results["propbank"] == tmp_path / "propbank-result"

    def test_download_all_with_failures(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test downloading all datasets with some failures."""

        def mock_download_dataset(dataset: str, output_dir: Path) -> Path:
            if dataset == "verbnet":
                return output_dir / "verbnet-result"
            raise DownloadError("Download failed")

        monkeypatch.setattr("glazing.downloader.download_dataset", mock_download_dataset)

        results = download_all(tmp_path, ["verbnet", "propbank"])

        # Verify mixed results
        assert len(results) == 2
        assert isinstance(results["verbnet"], Path)
        assert isinstance(results["propbank"], DownloadError)

    def test_download_all_skip_manual(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test downloading all datasets while skipping manual ones."""

        def mock_download_dataset(dataset: str, output_dir: Path) -> Path:
            return output_dir / f"{dataset.lower()}-result"

        monkeypatch.setattr("glazing.downloader.download_dataset", mock_download_dataset)

        results = download_all(tmp_path)

        # All datasets should be included
        assert "framenet" in results
        assert len(results) == 4  # verbnet, propbank, wordnet, framenet
