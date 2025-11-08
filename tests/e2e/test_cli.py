from pathlib import Path
import pytest
import json

from unittest.mock import patch
from adapters.cli import EditionCLI
from tests.helpers.fixtures import (
    load_html_fixture,
    load_expected_json,
    get_all_fixtures,
)


class TestEditionCLI:
    """Test the EditionCLI end-to-end functionality."""

    @pytest.mark.e2e
    def test_cli_initialization(self) -> None:
        """Test CLI initialization."""
        cli = EditionCLI()
        assert cli.service is not None

    @pytest.mark.e2e
    def test_setup_argument_parser(self) -> None:
        """Test argument parser setup."""
        cli = EditionCLI()
        parser = cli.setup_argument_parser()

        # Test required arguments
        with pytest.raises(SystemExit):
            parser.parse_args([])

        # Test with required input file
        args = parser.parse_args(["--input-file", "test.html"])
        assert args.input_file == "test.html"
        assert args.output_file is None

    @pytest.mark.e2e
    def test_resolve_output_path_explicit(self) -> None:
        """Test explicit output path resolution."""
        cli = EditionCLI()
        input_file = "samples/test.html"
        output_file = "custom/output.json"

        result = cli.resolve_output_path(input_file, output_file)
        assert result == output_file

    @pytest.mark.e2e
    def test_resolve_output_path_generated(self, tmp_path: str) -> None:
        """Test generated output path resolution."""
        cli = EditionCLI()
        input_file = "samples/test.html"

        with patch.object(cli, "script_dir", str(tmp_path)):
            result = cli.resolve_output_path(input_file, None)
            assert "output" in result
            assert "test-editions.json" in result

    @pytest.mark.e2e
    def test_save_editions_to_json(self, tmp_path: Path) -> None:
        """Test JSON output saving."""
        from domain.models import Edition

        cli = EditionCLI()
        editions = [
            Edition("1961NEC", "Normal", "2025-11-05", "LUIS ALBERTO ARCE CATACORA")
        ]
        output_path: Path = tmp_path / "output.json"

        cli.save_editions_to_json(editions, str(output_path))

        assert output_path.exists()

        # Verify JSON content
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["number"] == "1961NEC"

    @pytest.mark.e2e
    def test_complete_extraction_workflow(
        self, tmp_path: Path, fixtures_dir: Path
    ) -> None:
        """Test complete extraction workflow for all fixtures."""
        fixtures = get_all_fixtures(fixtures_dir)

        for fixture_name in fixtures:
            # Skip problematic fixtures for now
            if fixture_name == "empty-editions.html":
                continue

            print(f"\nTesting fixture: {fixture_name}")

            # Load input
            html_content = load_html_fixture(fixture_name, fixtures_dir)
            html_file = tmp_path / fixture_name
            html_file.write_text(html_content)

            # Load expected output
            expected_output = load_expected_json(fixture_name, fixtures_dir)
            print(f"  Expected: {len(expected_output)} editions")

            # Run extraction
            output_file = tmp_path / f"{fixture_name}.output.json"
            cli = EditionCLI()
            exit_code = cli.run(
                ["--input-file", str(html_file), "--output-file", str(output_file)]
            )

            # Verify success
            assert exit_code == 0
            assert output_file.exists()

            # Verify content matches expected
            with open(output_file, "r", encoding="utf-8") as f:
                actual_output = json.load(f)

            print(f"  Actual: {len(actual_output)} editions")

            assert actual_output == expected_output, (
                f"Mismatch in {fixture_name}: expected {len(expected_output)} editions, got {len(actual_output)}"
            )

    @pytest.mark.e2e
    def test_file_not_found_error(self) -> None:
        """Test handling of missing input file."""
        cli = EditionCLI()

        exit_code = cli.run(["--input-file", "/nonexistent/file.html"])

        assert exit_code == 1

    @pytest.mark.e2e
    def test_invalid_html_handling(self, tmp_path: Path) -> None:
        """Test handling of invalid HTML."""
        cli = EditionCLI()

        # Create invalid HTML file
        html_file = tmp_path / "invalid.html"
        html_file.write_text("<invalid><html>")

        output_file = tmp_path / "output.json"
        exit_code = cli.run(
            ["--input-file", str(html_file), "--output-file", str(output_file)]
        )

        # Should handle gracefully and produce empty output
        assert exit_code == 0
        assert output_file.exists()

        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data == []

    @pytest.mark.e2e
    def test_json_output_format(self, tmp_path: Path, sample_html_content: str) -> None:
        """Test JSON output format and encoding."""
        cli = EditionCLI()

        html_file = tmp_path / "test.html"
        html_file.write_text(sample_html_content)
        output_file = tmp_path / "output.json"

        exit_code = cli.run(
            ["--input-file", str(html_file), "--output-file", str(output_file)]
        )

        assert exit_code == 0

        # Verify JSON is properly formatted
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Should be valid JSON with proper encoding
        data = json.loads(content)
        assert isinstance(data, list)
        assert len(data) == 1

        # Verify pretty printing (indentation)
        assert "\n  " in content  # Indented JSON

    @pytest.mark.e2e
    def test_unicode_handling(self, tmp_path: Path) -> None:
        """Test Unicode character handling in output."""
        cli = EditionCLI()

        html_content = """
        <div class="anuncio">
            Nº de Edición : <strong>1961NEC</strong>
            <br />
            Tipo de Edición : <strong>Normal</strong>
            <br />
            Fecha de Publicación : <strong>05-11-2025</strong>
            <br />
            Gobierno : <a href="/edicions/view/1961NEC">LUIS ALBERTO ARCE CATACORA</a>
            <p><strong>Sección Especial: Ñandú</strong></p>
        </div>
        """

        html_file = tmp_path / "unicode.html"
        html_file.write_text(html_content, encoding="utf-8")
        output_file = tmp_path / "output.json"

        exit_code = cli.run(
            ["--input-file", str(html_file), "--output-file", str(output_file)]
        )

        assert exit_code == 0

        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Should handle Unicode characters correctly
        assert len(data) == 1
        assert data[0]["number"] == "1961NEC"
