"""Tests for FrameNet downloader functionality.

FrameNet-specific tests focusing on NLTK data repository download
with commit hash versioning and ZIP archive handling.
"""

from pathlib import Path

import pytest

from glazing.downloader import DownloadError, ExtractionError, FrameNetDownloader


class TestFrameNetDownloader:
    """Test FrameNet-specific downloader functionality."""

    def test_properties(self) -> None:
        """Test FrameNet downloader properties."""
        downloader = FrameNetDownloader()
        assert downloader.dataset_name == "framenet"
        assert downloader.version == "1.7"
        assert downloader.commit_hash == "427fc05d3a8cc1ca99e7ff93bdea937507cc9e7a"

    def test_commit_hash_format(self) -> None:
        """Test that commit hash is a valid format."""
        downloader = FrameNetDownloader()
        commit_hash = downloader.commit_hash

        # Should be 40 character hex string
        assert len(commit_hash) == 40
        assert all(c in "0123456789abcdef" for c in commit_hash.lower())

    def test_download_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful FrameNet download and extraction."""
        # Setup mocks
        extracted_dir = tmp_path / "framenet-1.7"
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

        # Verify the correct URL and archive path
        expected_url = "https://raw.githubusercontent.com/nltk/nltk_data/427fc05d3a8cc1ca99e7ff93bdea937507cc9e7a/packages/corpora/framenet_v17.zip"
        expected_archive = tmp_path / "framenet-1.7.zip"

        assert result == extracted_dir

    def test_download_url_format(self) -> None:
        """Test that download URL is correctly formatted for NLTK data repository."""
        downloader = FrameNetDownloader()

        # Test URL format for NLTK data repository
        expected_base = "https://raw.githubusercontent.com/nltk/nltk_data/"
        expected_file = "/packages/corpora/framenet_v17.zip"

        url = f"{expected_base}{downloader.commit_hash}{expected_file}"

        assert (
            url
            == "https://raw.githubusercontent.com/nltk/nltk_data/427fc05d3a8cc1ca99e7ff93bdea937507cc9e7a/packages/corpora/framenet_v17.zip"
        )

    def test_archive_filename_format(self) -> None:
        """Test that archive filename follows expected pattern."""
        downloader = FrameNetDownloader()

        # Archive name should be framenet-{version}.zip
        expected_name = f"framenet-{downloader.version}.zip"
        assert expected_name == "framenet-1.7.zip"

    def test_cleanup_behavior(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that archive cleanup works correctly."""
        # Create archive file
        archive_path = tmp_path / "framenet-1.7.zip"
        archive_path.write_bytes(b"fake archive")

        extracted_dir = tmp_path / "extracted"
        extracted_dir.mkdir()

        def mock_download_file(self: FrameNetDownloader, url: str, path: Path) -> None:
            # File already exists from setup
            pass

        def mock_extract_archive(
            self: FrameNetDownloader, archive_path: Path, output_dir: Path
        ) -> Path:
            return extracted_dir

        monkeypatch.setattr(FrameNetDownloader, "_download_file", mock_download_file)
        monkeypatch.setattr(FrameNetDownloader, "_extract_archive", mock_extract_archive)

        downloader = FrameNetDownloader()
        result = downloader.download(tmp_path)

        # Archive should be cleaned up
        assert not archive_path.exists()
        assert result == extracted_dir

    def test_extraction_failure_cleanup(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test cleanup when extraction fails."""
        # Create archive file
        archive_path = tmp_path / "framenet-1.7.zip"
        archive_path.write_bytes(b"bad archive")

        def mock_download_file(self: FrameNetDownloader, url: str, path: Path) -> None:
            pass

        def mock_extract_archive(
            self: FrameNetDownloader, archive_path: Path, output_dir: Path
        ) -> Path:
            raise ExtractionError("Bad archive")

        monkeypatch.setattr(FrameNetDownloader, "_download_file", mock_download_file)
        monkeypatch.setattr(FrameNetDownloader, "_extract_archive", mock_extract_archive)

        downloader = FrameNetDownloader()

        with pytest.raises(ExtractionError, match="Bad archive"):
            downloader.download(tmp_path)

        # Archive should still be cleaned up
        assert not archive_path.exists()

    def test_nltk_data_source(self) -> None:
        """Test that FrameNet uses NLTK data repository source."""
        downloader = FrameNetDownloader()

        # Should use NLTK data repository
        expected_domain = "raw.githubusercontent.com/nltk/nltk_data"
        url = f"https://raw.githubusercontent.com/nltk/nltk_data/{downloader.commit_hash}/packages/corpora/framenet_v17.zip"

        assert expected_domain in url
        assert "nltk" in url
        assert "framenet_v17.zip" in url

    def test_download_failure_handling(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test handling of download failures from NLTK data repository."""

        def mock_download_file(self: FrameNetDownloader, url: str, path: Path) -> None:
            raise DownloadError("NLTK repository unavailable")

        monkeypatch.setattr(FrameNetDownloader, "_download_file", mock_download_file)

        downloader = FrameNetDownloader()

        with pytest.raises(DownloadError, match="NLTK repository unavailable"):
            downloader.download(tmp_path)

        # No archive should remain
        archive_path = tmp_path / "framenet-1.7.zip"
        assert not archive_path.exists()
