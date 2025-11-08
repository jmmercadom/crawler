from typing import Dict, Optional

import pytest
from domain.models import Edition


class TestEditionModel:
    """Test the Edition domain model."""

    @pytest.mark.unit
    def test_edition_creation(self) -> None:
        """Test creating an Edition instance."""
        edition: Edition = Edition(
            number="1961NEC",
            type="Normal",
            published_date="2025-11-05",
            administration="LUIS ALBERTO ARCE CATACORA",
        )

        assert edition.number == "1961NEC"
        assert edition.type == "Normal"
        assert edition.published_date == "2025-11-05"
        assert edition.administration == "LUIS ALBERTO ARCE CATACORA"

    @pytest.mark.unit
    def test_edition_to_dict(self) -> None:
        """Test conversion to dictionary."""
        edition: Edition = Edition(
            number="1961NEC",
            type="Normal",
            published_date="2025-11-05",
            administration="LUIS ALBERTO ARCE CATACORA",
        )

        result: Dict[str, Optional[str]] = edition.to_dict()
        expected: Dict[str, Optional[str]] = {
            "number": "1961NEC",
            "type": "Normal",
            "published_date": "2025-11-05",
            "administration": "LUIS ALBERTO ARCE CATACORA",
        }

        assert result == expected

    @pytest.mark.unit
    def test_edition_with_none_values(self) -> None:
        """Test Edition with None values."""
        edition: Edition = Edition()
        result: Dict[str, Optional[str]] = edition.to_dict()

        assert result == {
            "number": None,
            "type": None,
            "published_date": None,
            "administration": None,
        }

    @pytest.mark.unit
    def test_edition_partial_data(self) -> None:
        """Test Edition with partial data."""
        edition: Edition = Edition(number="1961NEC")
        result: Dict[str, Optional[str]] = edition.to_dict()

        assert result["number"] == "1961NEC"
        assert result["type"] is None
        assert result["published_date"] is None
        assert result["administration"] is None
