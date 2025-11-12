from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from application.edition_extraction_service import EditionExtractionService
from domain.models import Edition


class TestEditionExtractionService:
    """Test the EditionExtractionService integration."""

    @pytest.mark.integration
    def test_service_initialization(self) -> None:
        """Test service initialization."""
        service = EditionExtractionService()
        assert service.extractor is not None

    @pytest.mark.integration
    def test_extract_from_html(self, sample_html_content: str) -> None:
        """Test extracting from HTML string."""
        service = EditionExtractionService()
        editions = service.extract_from_html(sample_html_content)

        assert len(editions) == 1
        assert isinstance(editions[0], Edition)
        assert editions[0].number == "1961NEC"

    @pytest.mark.integration
    def test_extract_from_file_success(
        self, tmp_path: Path, sample_html_content: str
    ) -> None:
        """Test successful file extraction."""
        # Create temporary HTML file
        html_file = tmp_path / "test.html"
        html_file.write_text(sample_html_content)

        service = EditionExtractionService()
        editions = service.extract_from_file(str(html_file))

        assert len(editions) == 1
        assert editions[0].number == "1961NEC"

    @pytest.mark.integration
    def test_extract_from_file_not_found(self) -> None:
        """Test file not found error handling."""
        service = EditionExtractionService()

        with pytest.raises(FileNotFoundError):
            service.extract_from_file("/nonexistent/file.html")

    @pytest.mark.integration
    def test_extract_from_file_io_error(self, tmp_path: Path) -> None:
        """Test IO error handling."""
        # Create a file and then remove read permissions
        html_file = tmp_path / "unreadable.html"
        html_file.write_text("<html></html>")
        html_file.chmod(0o000)  # Remove all permissions

        service = EditionExtractionService()

        try:
            with pytest.raises(IOError):
                service.extract_from_file(str(html_file))
        finally:
            # Restore permissions for cleanup
            html_file.chmod(0o644)

    @pytest.mark.integration
    @patch("builtins.open", new_callable=mock_open, read_data="<html></html>")
    def test_extract_from_file_empty_content(self, mock_file: MagicMock) -> None:
        """Test extraction from empty HTML content."""
        service = EditionExtractionService()
        editions = service.extract_from_file("dummy.html")

        assert len(editions) == 0

    @pytest.mark.integration
    def test_extract_from_html_with_tracing(self, sample_html_content: str) -> None:
        """Test that OpenTelemetry tracing is working."""
        service = EditionExtractionService()

        # This should not raise any exceptions
        editions = service.extract_from_html(sample_html_content)

        assert len(editions) == 1
        assert editions[0].number == "1961NEC"

    @pytest.mark.integration
    def test_multiple_extractions_consistency(self, sample_html_content: str) -> None:
        """Test that multiple extractions produce consistent results."""
        service = EditionExtractionService()

        # Extract multiple times
        editions1 = service.extract_from_html(sample_html_content)
        editions2 = service.extract_from_html(sample_html_content)

        # Should get same results
        assert len(editions1) == len(editions2)
        assert editions1[0].to_dict() == editions2[0].to_dict()
