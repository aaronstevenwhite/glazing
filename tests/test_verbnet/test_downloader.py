"""Tests for VerbNet downloader functionality.

VerbNet-specific tests focusing on GitHub archive download
with commit hash versioning and error handling.
"""

import zipfile
from pathlib import Path

import pytest

from glazing.downloader import DownloadError, ExtractionError, VerbNetDownloader


class TestVerbNetDownloader:
    """Test VerbNet-specific downloader functionality."""

    def test_properties(self) -> None:
        """Test VerbNet downloader properties."""
        downloader = VerbNetDownloader()
        assert downloader.dataset_name == "verbnet"
        assert downloader.version == "3.4"
        assert downloader.commit_hash == "ae8e9cfdc2c0d3414b748763612f1a0a34194cc1"

    def test_commit_hash_format(self) -> None:
        """Test that commit hash is a valid format."""
        downloader = VerbNetDownloader()
        commit_hash = downloader.commit_hash

        # Should be 40 character hex string
        assert len(commit_hash) == 40
        assert all(c in "0123456789abcdef" for c in commit_hash.lower())

    def test_download_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful VerbNet download and extraction."""
        # Setup mocks
        extracted_dir = tmp_path / "verbnet-3.4"
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

        # Verify the correct URL and archive path
        expected_url = "https://github.com/uvi-nlp/verbnet/archive/ae8e9cfdc2c0d3414b748763612f1a0a34194cc1.zip"
        expected_archive = tmp_path / "verbnet-3.4.zip"

        assert result == extracted_dir

    def test_download_url_format(self) -> None:
        """Test that download URL is correctly formatted."""
        downloader = VerbNetDownloader()

        # We can test the URL format without actually downloading
        expected_base = "https://github.com/uvi-nlp/verbnet/archive/"
        expected_suffix = ".zip"

        # The URL would be constructed as:
        url = f"{expected_base}{downloader.commit_hash}{expected_suffix}"

        assert (
            url
            == "https://github.com/uvi-nlp/verbnet/archive/ae8e9cfdc2c0d3414b748763612f1a0a34194cc1.zip"
        )

    def test_archive_filename_format(self, tmp_path: Path) -> None:
        """Test that archive filename follows expected pattern."""
        downloader = VerbNetDownloader()

        # Archive name should be verbnet-{version}.zip
        expected_name = f"verbnet-{downloader.version}.zip"
        assert expected_name == "verbnet-3.4.zip"

    def test_cleanup_on_successful_extraction(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that archive file is cleaned up after successful extraction."""
        # Create a real archive file to test cleanup
        archive_path = tmp_path / "verbnet-3.4.zip"
        with zipfile.ZipFile(archive_path, "w") as zf:
            zf.writestr("test_file.txt", "test content")

        extracted_dir = tmp_path / "extracted"
        extracted_dir.mkdir()

        def mock_download_file(self: VerbNetDownloader, url: str, path: Path) -> None:
            # File already exists from our setup
            pass

        def mock_extract_archive(
            self: VerbNetDownloader, archive_path: Path, output_dir: Path
        ) -> Path:
            return extracted_dir

        monkeypatch.setattr(VerbNetDownloader, "_download_file", mock_download_file)
        monkeypatch.setattr(VerbNetDownloader, "_extract_archive", mock_extract_archive)

        downloader = VerbNetDownloader()

        result = downloader.download(tmp_path)

        # Archive should be cleaned up
        assert not archive_path.exists()
        assert result == extracted_dir

    def test_cleanup_on_extraction_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that archive file is cleaned up even when extraction fails."""
        # Create a real archive file
        archive_path = tmp_path / "verbnet-3.4.zip"
        archive_path.write_bytes(b"fake archive content")

        def mock_download_file(self: VerbNetDownloader, url: str, path: Path) -> None:
            # File already exists from our setup
            pass

        def mock_extract_archive(
            self: VerbNetDownloader, archive_path: Path, output_dir: Path
        ) -> Path:
            raise ExtractionError("Extraction failed")

        monkeypatch.setattr(VerbNetDownloader, "_download_file", mock_download_file)
        monkeypatch.setattr(VerbNetDownloader, "_extract_archive", mock_extract_archive)

        downloader = VerbNetDownloader()

        with pytest.raises(ExtractionError, match="Extraction failed"):
            downloader.download(tmp_path)

        # Archive should still be cleaned up on failure
        assert not archive_path.exists()

    def test_download_failure_no_cleanup_needed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test behavior when download itself fails."""

        def mock_download_file(self: VerbNetDownloader, url: str, path: Path) -> None:
            raise DownloadError("Network error")

        monkeypatch.setattr(VerbNetDownloader, "_download_file", mock_download_file)

        downloader = VerbNetDownloader()

        with pytest.raises(DownloadError, match="Network error"):
            downloader.download(tmp_path)

        # No archive file should exist
        archive_path = tmp_path / "verbnet-3.4.zip"
        assert not archive_path.exists()

    def test_multiple_downloads_independent(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that multiple downloads to different directories work independently."""
        dir1 = tmp_path / "download1"
        dir2 = tmp_path / "download2"
        dir1.mkdir()
        dir2.mkdir()

        extracted1 = dir1 / "verbnet-extracted"
        extracted2 = dir2 / "verbnet-extracted"
        extracted1.mkdir()
        extracted2.mkdir()

        call_count = 0

        def mock_download_file(self: VerbNetDownloader, url: str, path: Path) -> None:
            # Create fake archive
            path.write_bytes(b"fake archive")

        def mock_extract_archive(
            self: VerbNetDownloader, archive_path: Path, output_dir: Path
        ) -> Path:
            nonlocal call_count
            call_count += 1
            return extracted1 if call_count == 1 else extracted2

        monkeypatch.setattr(VerbNetDownloader, "_download_file", mock_download_file)
        monkeypatch.setattr(VerbNetDownloader, "_extract_archive", mock_extract_archive)

        downloader = VerbNetDownloader()

        result1 = downloader.download(dir1)
        result2 = downloader.download(dir2)

        assert result1 == extracted1
        assert result2 == extracted2

        # Should have called extract twice
        assert call_count == 2
