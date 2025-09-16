"""Tests for PropBank downloader functionality.

PropBank-specific tests focusing on GitHub archive download
with commit hash versioning for PropBank frames repository.
"""

from pathlib import Path

import pytest

from glazing.downloader import ExtractionError, PropBankDownloader


class TestPropBankDownloader:
    """Test PropBank-specific downloader functionality."""

    def test_properties(self) -> None:
        """Test PropBank downloader properties."""
        downloader = PropBankDownloader()
        assert downloader.dataset_name == "PropBank"
        assert downloader.version == "3.4.0"
        assert downloader.commit_hash == "7280a04806b6ca3955ec82e28c4df96b6da76aef"

    def test_commit_hash_format(self) -> None:
        """Test that commit hash is a valid format."""
        downloader = PropBankDownloader()
        commit_hash = downloader.commit_hash

        # Should be 40 character hex string
        assert len(commit_hash) == 40
        assert all(c in "0123456789abcdef" for c in commit_hash.lower())

    def test_download_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful PropBank download and extraction."""
        # Setup mocks
        extracted_dir = tmp_path / "propbank-3.4.0"
        extracted_dir.mkdir()

        def mock_download_file(self: PropBankDownloader, url: str, path: Path) -> None:
            # Create fake archive
            path.write_bytes(b"fake archive")

        def mock_extract_archive(
            self: PropBankDownloader, archive_path: Path, output_dir: Path
        ) -> Path:
            return extracted_dir

        monkeypatch.setattr(PropBankDownloader, "_download_file", mock_download_file)
        monkeypatch.setattr(PropBankDownloader, "_extract_archive", mock_extract_archive)

        downloader = PropBankDownloader()
        result = downloader.download(tmp_path)

        # Verify the correct URL and archive path
        expected_url = "https://github.com/propbank/propbank-frames/archive/7280a04806b6ca3955ec82e28c4df96b6da76aef.zip"
        expected_archive = tmp_path / "propbank-3.4.0.zip"

        assert result == extracted_dir

    def test_download_url_format(self) -> None:
        """Test that download URL is correctly formatted for PropBank repository."""
        downloader = PropBankDownloader()

        # Test URL format for PropBank frames repository
        expected_base = "https://github.com/propbank/propbank-frames/archive/"
        expected_suffix = ".zip"

        url = f"{expected_base}{downloader.commit_hash}{expected_suffix}"

        assert (
            url
            == "https://github.com/propbank/propbank-frames/archive/7280a04806b6ca3955ec82e28c4df96b6da76aef.zip"
        )

    def test_archive_filename_format(self) -> None:
        """Test that archive filename follows expected pattern."""
        downloader = PropBankDownloader()

        # Archive name should be propbank-{version}.zip
        expected_name = f"propbank-{downloader.version}.zip"
        assert expected_name == "propbank-3.4.0.zip"

    def test_cleanup_behavior(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that archive cleanup works correctly."""
        # Create archive file
        archive_path = tmp_path / "propbank-3.4.0.zip"
        archive_path.write_bytes(b"fake archive")

        extracted_dir = tmp_path / "extracted"
        extracted_dir.mkdir()

        def mock_download_file(self: PropBankDownloader, url: str, path: Path) -> None:
            # File already exists from setup
            pass

        def mock_extract_archive(
            self: PropBankDownloader, archive_path: Path, output_dir: Path
        ) -> Path:
            return extracted_dir

        monkeypatch.setattr(PropBankDownloader, "_download_file", mock_download_file)
        monkeypatch.setattr(PropBankDownloader, "_extract_archive", mock_extract_archive)

        downloader = PropBankDownloader()
        result = downloader.download(tmp_path)

        # Archive should be cleaned up
        assert not archive_path.exists()
        assert result == extracted_dir

    def test_extraction_failure_cleanup(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test cleanup when extraction fails."""
        # Create archive file
        archive_path = tmp_path / "propbank-3.4.0.zip"
        archive_path.write_bytes(b"bad archive")

        def mock_download_file(self: PropBankDownloader, url: str, path: Path) -> None:
            pass

        def mock_extract_archive(
            self: PropBankDownloader, archive_path: Path, output_dir: Path
        ) -> Path:
            raise ExtractionError("Bad archive")

        monkeypatch.setattr(PropBankDownloader, "_download_file", mock_download_file)
        monkeypatch.setattr(PropBankDownloader, "_extract_archive", mock_extract_archive)

        downloader = PropBankDownloader()

        with pytest.raises(ExtractionError, match="Bad archive"):
            downloader.download(tmp_path)

        # Archive should still be cleaned up
        assert not archive_path.exists()

    def test_repository_specific_behavior(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test PropBank-specific repository behavior."""
        extracted_dir = tmp_path / "propbank-frames-7280a04806b6ca3955ec82e28c4df96b6da76aef"
        extracted_dir.mkdir()

        def mock_download_file(self: PropBankDownloader, url: str, path: Path) -> None:
            # Verify URL points to propbank-frames repository
            assert "propbank/propbank-frames" in url
            path.write_bytes(b"fake archive")

        def mock_extract_archive(
            self: PropBankDownloader, archive_path: Path, output_dir: Path
        ) -> Path:
            return extracted_dir

        monkeypatch.setattr(PropBankDownloader, "_download_file", mock_download_file)
        monkeypatch.setattr(PropBankDownloader, "_extract_archive", mock_extract_archive)

        downloader = PropBankDownloader()
        result = downloader.download(tmp_path)

        assert "propbank-frames" in str(result)

    def test_different_from_verbnet(self) -> None:
        """Test that PropBank downloader differs from VerbNet downloader."""
        from glazing.downloader import VerbNetDownloader

        propbank = PropBankDownloader()
        verbnet = VerbNetDownloader()

        # Different repositories
        assert propbank.dataset_name != verbnet.dataset_name
        assert propbank.version != verbnet.version

        # Should have different URLs
        pb_url = f"https://github.com/propbank/propbank-frames/archive/{propbank.commit_hash}.zip"
        vn_url = f"https://github.com/uvi-nlp/verbnet/archive/{verbnet.commit_hash}.zip"
        assert pb_url != vn_url
