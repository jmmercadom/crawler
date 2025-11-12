import pytest
from unittest.mock import MagicMock
from datetime import datetime

from adapters.execution_cli import ExecutionCLI, setup_argument_parser
from domain.execution_models import ExecutionRecord, ExecutionStatus, ChangeType


class TestExecutionCLI:
    """End‑to‑end tests for the ExecutionCLI class."""

    def test_cli_initialization(self) -> None:
        """The CLI should be instantiated with a service."""
        cli = ExecutionCLI()
        assert cli.service is not None

    @pytest.mark.e2e
    def test_setup_argument_parser(self) -> None:
        """The argument parser must require a URL and accept optional flags."""
        parser = setup_argument_parser()

        # Missing required URL should cause SystemExit
        with pytest.raises(SystemExit):
            parser.parse_args([])

        # Provide only the required URL
        args = parser.parse_args(["https://example.com"])
        assert args.url == "https://example.com"
        # Optional flags default to False / None
        assert args.force is False
        assert args.save_content is False
        assert args.verbose is False
        assert args.no_etag_check is False
        assert args.no_hash_check is False
        assert args.output_dir == "executions"

    @pytest.mark.e2e
    def test_successful_execution(self) -> None:
        """Run the CLI with a mocked service and verify a successful exit code."""
        # Prepare a dummy execution record
        dummy_record = ExecutionRecord(
            url="https://example.com",
            execution_id="dummy-id",
            timestamp=datetime.now(),
            status=ExecutionStatus.COMPLETED,
            content_hash="abc123",
            normalized_hash="def456",
            etag="etag123",
            content_size=1024,
            download_duration_ms=100,
            change_detected=True,
            change_type=ChangeType.NEW_CONTENT,
        )
        # Mock the service method
        mock_service = MagicMock()
        mock_service.execute_url.return_value = dummy_record

        cli = ExecutionCLI(service=mock_service)
        # Run with only the required URL argument
        exit_code = cli.run(["https://example.com"])

        # The CLI should return 0 on success
        assert exit_code == 0
        # Ensure the service was called exactly once with the URL
        mock_service.execute_url.assert_called_once_with("https://example.com")
