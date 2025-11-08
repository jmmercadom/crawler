import pytest
import re
from domain.extractors import EditionExtractor


class TestEditionExtractor:
    """Test the EditionExtractor HTML parser."""

    @pytest.mark.unit
    def test_extractor_initialization(self) -> None:
        """Test extractor initialization."""
        extractor = EditionExtractor()
        assert extractor.editions == []
        assert extractor.current_edition is None
        assert extractor.in_anuncio is False

    @pytest.mark.unit
    def test_single_edition_extraction(self, sample_html_content: str) -> None:
        """Test extracting a single edition."""
        extractor = EditionExtractor()
        extractor.feed(sample_html_content)
        editions = extractor.get_editions()

        assert len(editions) == 1
        edition = editions[0]
        assert edition.number == "1961NEC"
        assert edition.type == "Normal"
        assert edition.published_date == "2025-11-05"
        assert edition.administration == "LUIS ALBERTO ARCE CATACORA"

    @pytest.mark.unit
    def test_multiple_editions_extraction(self) -> None:
        """Test extracting multiple editions."""
        html_content = """
        <div class="anuncio">
            Nº de Edición : <strong>1961NEC</strong>
            <br />
            Tipo de Edición : <strong>Normal</strong>
            <br />
            Fecha de Publicación : <strong>05-11-2025</strong>
            <br />
            Gobierno : <a href="/edicions/view/1961NEC">LUIS ALBERTO ARCE CATACORA</a>
        </div>
        <div class="anuncio">
            Nº de Edición : <strong>1960NEC</strong>
            <br />
            Tipo de Edición : <strong>Normal</strong>
            <br />
            Fecha de Publicación : <strong>31-10-2025</strong>
            <br />
            Gobierno : <a href="/edicions/view/1960NEC">LUIS ALBERTO ARCE CATACORA</a>
        </div>
        """

        extractor = EditionExtractor()
        extractor.feed(html_content)
        editions = extractor.get_editions()

        assert len(editions) == 2
        assert editions[0].number == "1961NEC"
        assert editions[1].number == "1960NEC"

    @pytest.mark.unit
    def test_empty_html(self) -> None:
        """Test handling empty HTML."""
        extractor = EditionExtractor()
        extractor.feed("<html></html>")
        editions = extractor.get_editions()

        assert len(editions) == 0

    @pytest.mark.unit
    def test_html_without_anuncio_class(self) -> None:
        """Test HTML without anuncio divs."""
        html_content = """
        <div class="other-class">
            Nº de Edición : <strong>1961NEC</strong>
        </div>
        """

        extractor = EditionExtractor()
        extractor.feed(html_content)
        editions = extractor.get_editions()

        assert len(editions) == 0

    @pytest.mark.unit
    def test_edition_without_number(self) -> None:
        """Test handling edition without number."""
        html_content = """
        <div class="anuncio">
            Tipo de Edición : <strong>Normal</strong>
            <br />
            Fecha de Publicación : <strong>05-11-2025</strong>
            <br />
            Gobierno : <a href="/edicions/view/1961NEC">LUIS ALBERTO ARCE CATACORA</a>
        </div>
        """

        extractor = EditionExtractor()
        extractor.feed(html_content)
        editions = extractor.get_editions()

        # Should not add edition without number
        assert len(editions) == 0

    @pytest.mark.unit
    def test_date_format_conversion(self, sample_html_content: str) -> None:
        """Test date format conversion from DD-MM-YYYY to YYYY-MM-DD."""
        extractor = EditionExtractor()
        extractor.feed(sample_html_content)
        editions = extractor.get_editions()

        assert len(editions) == 1
        # Should convert "05-11-2025" to "2025-11-05"
        assert editions[0].published_date == "2025-11-05"

    @pytest.mark.unit
    def test_different_edition_types(self) -> None:
        """Test extraction of different edition types."""
        html_content = """
        <div class="anuncio">
            Nº de Edición : <strong>58PI</strong>
            <br />
            Tipo de Edición : <strong>Propiedad Intelectual</strong>
            <br />
            Fecha de Publicación : <strong>06-10-2025</strong>
            <br />
            Gobierno : <a href="/edicions/view/58PI">LUIS ALBERTO ARCE CATACORA</a>
        </div>
        """

        extractor = EditionExtractor()
        extractor.feed(html_content)
        editions = extractor.get_editions()

        assert len(editions) == 1
        assert editions[0].type == "Propiedad Intelectual"

    @pytest.mark.unit
    def test_regex_patterns(self) -> None:
        """Test individual regex patterns used in extraction."""
        # Note: These regex patterns work on text content after HTML parsing (tags stripped)
        text = """
        Nº de Edición : 1961NEC
        Tipo de Edición : Normal
        Fecha de Publicación : 05-11-2025
        Gobierno : LUIS ALBERTO ARCE CATACORA
        """

        # Test number extraction
        number_match = re.search(r"Nº de Edición\s*:\s*(\S+)", text)
        assert number_match is not None
        assert number_match.group(1) == "1961NEC"

        # Test type extraction
        type_match = re.search(
            r"Tipo de Edición\s*:\s*([^\n]+?)(?:\s*Fecha|\s*$)", text, re.DOTALL
        )
        assert type_match is not None
        assert type_match.group(1).strip() == "Normal"

        # Test date extraction
        date_match = re.search(r"Fecha de Publicación\s*:\s*(\d{2}-\d{2}-\d{4})", text)
        assert date_match is not None
        assert date_match.group(1) == "05-11-2025"

        # Test administration extraction
        admin_match = re.search(r"Gobierno\s*:\s*([^\n<]+)", text)
        assert admin_match is not None
        assert "LUIS ALBERTO ARCE CATACORA" in admin_match.group(1)
