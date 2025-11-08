import json
import logging
from pathlib import Path
from typing import Any, Dict, List, cast

logger = logging.getLogger(__name__)


def load_html_fixture(fixture_name: str, fixtures_dir: Path) -> str:
    """
    Load HTML fixture content from the fixtures directory.

    Args:
        fixture_name: Name of the HTML fixture file
        fixtures_dir: Path to the fixtures directory

    Returns:
        HTML content as string

    Raises:
        FileNotFoundError: If fixture doesn't exist
    """
    fixture_path = fixtures_dir / "html" / fixture_name
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")
    return fixture_path.read_text(encoding="utf-8")


def load_expected_json(fixture_name: str, fixtures_dir: Path) -> List[Dict[str, Any]]:
    """
    Load expected JSON output for a fixture.

    Args:
        fixture_name: Name of the HTML fixture file
        fixtures_dir: Path to the fixtures directory

    Returns:
        List of edition dictionaries

    Raises:
        FileNotFoundError: If expected output doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    json_name = fixture_name.replace(".html", ".json")
    expected_path = fixtures_dir / "expected" / json_name
    if not expected_path.exists():
        raise FileNotFoundError(f"Expected output not found: {expected_path}")

    # Read and parse JSON content
    json_content = expected_path.read_text(encoding="utf-8")
    logger.debug(f"Loading JSON from {expected_path}")

    # Parse JSON and cast to the expected type to satisfy mypy
    parsed_data = json.loads(json_content)
    logger.debug(f"Parsed data type: {type(parsed_data)}")

    # Cast to the expected return type to satisfy mypy's strict type checking
    return cast(List[Dict[str, Any]], parsed_data)


def get_all_fixtures(fixtures_dir: Path) -> List[str]:
    """
    Get list of all HTML fixture files.

    Args:
        fixtures_dir: Path to the fixtures directory

    Returns:
        List of fixture filenames
    """
    html_dir = fixtures_dir / "html"
    return [f.name for f in html_dir.glob("*.html") if f.is_file()]
