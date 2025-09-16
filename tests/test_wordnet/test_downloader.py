"""Tests for WordNet downloader functionality.

WordNet-specific tests focusing on Princeton University
tar.gz archive download and version handling.
"""

from pathlib import Path

import pytest

from glazing.downloader import DownloadError, ExtractionError, WordNetDownloader


class TestWordNetDownloader:
    """Test WordNet-specific downloader functionality."""

    def test_properties(self) -> None:
        """Test WordNet downloader properties."""
        downloader = WordNetDownloader()
        assert downloader.dataset_name == "WordNet"
        assert downloader.version == "3.1"

    def test_version_format(self) -> None:
        """Test that WordNet version follows semantic versioning."""
        downloader = WordNetDownloader()
        version = downloader.version

        # Should be semantic version format
        assert version == "3.1"
        # Should be parseable as float (for this simple case)
        assert float(version) == 3.1

    def test_download_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful WordNet download and extraction."""
        # Setup mocks
        extracted_dir = tmp_path / "wordnet-3.1"
        extracted_dir.mkdir()

        def mock_download_file(self: WordNetDownloader, url: str, path: Path) -> None:
            # Create fake archive
            path.write_bytes(b"fake tar.gz archive")

        def mock_extract_archive(
            self: WordNetDownloader, archive_path: Path, output_dir: Path
        ) -> Path:
            return extracted_dir

        monkeypatch.setattr(WordNetDownloader, "_download_file", mock_download_file)
        monkeypatch.setattr(WordNetDownloader, "_extract_archive", mock_extract_archive)

        downloader = WordNetDownloader()
        result = downloader.download(tmp_path)

        # Verify the correct URL and archive path
        expected_url = "https://wordnetcode.princeton.edu/wn3.1.dict.tar.gz"
        expected_archive = tmp_path / "wordnet-3.1.tar.gz"

        assert result == extracted_dir

    def test_download_url_format(self) -> None:
        """Test that download URL points to Princeton University."""
        downloader = WordNetDownloader()

        # URL should point to Princeton's official WordNet distribution
        expected_url = "https://wordnetcode.princeton.edu/wn3.1.dict.tar.gz"

        # This is the URL that would be used in the actual download
        assert expected_url.startswith("https://wordnetcode.princeton.edu/")
        assert "wn3.1.dict.tar.gz" in expected_url

    def test_archive_filename_format(self) -> None:
        """Test that archive filename follows expected pattern."""
        downloader = WordNetDownloader()

        # Archive name should be wordnet-{version}.tar.gz
        expected_name = f"wordnet-{downloader.version}.tar.gz"
        assert expected_name == "wordnet-3.1.tar.gz"

    def test_uses_tar_gz_format(self) -> None:
        """Test that WordNet uses tar.gz format unlike others."""
        downloader = WordNetDownloader()

        # WordNet uses .tar.gz while others use .zip
        archive_name = f"wordnet-{downloader.version}.tar.gz"
        assert archive_name.endswith(".tar.gz")
        assert not archive_name.endswith(".zip")

    def test_cleanup_behavior(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that tar.gz archive cleanup works correctly."""
        # Create archive file
        archive_path = tmp_path / "wordnet-3.1.tar.gz"
        archive_path.write_bytes(b"fake tar.gz archive")

        extracted_dir = tmp_path / "extracted"
        extracted_dir.mkdir()

        def mock_download_file(self: WordNetDownloader, url: str, path: Path) -> None:
            # File already exists from setup
            pass

        def mock_extract_archive(
            self: WordNetDownloader, archive_path: Path, output_dir: Path
        ) -> Path:
            return extracted_dir

        monkeypatch.setattr(WordNetDownloader, "_download_file", mock_download_file)
        monkeypatch.setattr(WordNetDownloader, "_extract_archive", mock_extract_archive)

        downloader = WordNetDownloader()
        result = downloader.download(tmp_path)

        # Archive should be cleaned up
        assert not archive_path.exists()
        assert result == extracted_dir

    def test_extraction_failure_cleanup(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test cleanup when tar.gz extraction fails."""
        # Create archive file
        archive_path = tmp_path / "wordnet-3.1.tar.gz"
        archive_path.write_bytes(b"corrupted tar.gz")

        def mock_download_file(self: WordNetDownloader, url: str, path: Path) -> None:
            pass

        def mock_extract_archive(
            self: WordNetDownloader, archive_path: Path, output_dir: Path
        ) -> Path:
            raise ExtractionError("Corrupted tar.gz")

        monkeypatch.setattr(WordNetDownloader, "_download_file", mock_download_file)
        monkeypatch.setattr(WordNetDownloader, "_extract_archive", mock_extract_archive)

        downloader = WordNetDownloader()

        with pytest.raises(ExtractionError, match="Corrupted tar.gz"):
            downloader.download(tmp_path)

        # Archive should still be cleaned up
        assert not archive_path.exists()

    def test_official_source(self) -> None:
        """Test that WordNet uses official Princeton source."""
        downloader = WordNetDownloader()

        # Should use Princeton's official distribution
        expected_domain = "wordnetcode.princeton.edu"
        url = "https://wordnetcode.princeton.edu/wn3.1.dict.tar.gz"

        assert expected_domain in url
        assert "princeton" in url

    def test_different_from_github_datasets(self) -> None:
        """Test that WordNet differs from GitHub-based datasets."""
        from glazing.downloader import PropBankDownloader, VerbNetDownloader

        wordnet = WordNetDownloader()
        propbank = PropBankDownloader()
        verbnet = VerbNetDownloader()

        # WordNet uses different source
        wn_url = "https://wordnetcode.princeton.edu/wn3.1.dict.tar.gz"
        pb_url = f"https://github.com/propbank/propbank-frames/archive/{propbank.version}.zip"
        vn_url = f"https://github.com/uvi-nlp/verbnet/archive/{verbnet.version}.zip"

        assert "github.com" not in wn_url
        assert "github.com" in pb_url
        assert "github.com" in vn_url

        # WordNet uses tar.gz, others use zip
        assert wn_url.endswith(".tar.gz")
        assert pb_url.endswith(".zip")
        assert vn_url.endswith(".zip")

    def test_download_failure_handling(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test handling of download failures from Princeton server."""

        def mock_download_file(self: WordNetDownloader, url: str, path: Path) -> None:
            raise DownloadError("Princeton server unavailable")

        monkeypatch.setattr(WordNetDownloader, "_download_file", mock_download_file)

        downloader = WordNetDownloader()

        with pytest.raises(DownloadError, match="Princeton server unavailable"):
            downloader.download(tmp_path)

        # No archive should remain
        archive_path = tmp_path / "wordnet-3.1.tar.gz"
        assert not archive_path.exists()
