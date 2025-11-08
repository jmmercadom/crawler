import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def fixtures_dir(project_root: Path) -> Path:
    """Return the fixtures directory path."""
    return project_root / "tests" / "fixtures"


@pytest.fixture
def sample_html_content() -> str:
    """Sample HTML content for unit tests."""
    return """
    <div class="anuncio">
        Nº de Edición : <strong>1961NEC</strong>
        <br />
        Tipo de Edición : <strong>Normal</strong>
        <br />
        Fecha de Publicación : <strong>05-11-2025</strong>
        <br />
        Gobierno : <a href="/edicions/view/1961NEC">LUIS ALBERTO ARCE CATACORA</a>
    </div>
    """
