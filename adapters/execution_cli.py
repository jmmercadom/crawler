import argparse
import logging
import os
from typing import List, Optional

from opentelemetry import trace

from adapters.http_client import HTTPClientAdapter
from adapters.storage_adapter import StorageAdapter
from application.url_execution_service import URLExecutionService
from domain.content_normalizer import ContentNormalizer

# Get logger for this module
logger = logging.getLogger(__name__)

# Get tracer for this module
tracer = trace.get_tracer(__name__)


def setup_argument_parser() -> argparse.ArgumentParser:
    """Configure CLI arguments."""
    parser = argparse.ArgumentParser(description="Execute URL and detect changes")
    parser.add_argument("url", help="URL to execute")
    parser.add_argument(
        "--output-dir",
        default="executions",
        help="Base directory for storage (default: executions)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force download even if ETag matches"
    )
    parser.add_argument(
        "--save-content",
        action="store_true",
        help="Save raw and normalized content to files",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Increase logging verbosity"
    )
    parser.add_argument(
        "--no-etag-check", action="store_true", help="Disable ETag verification"
    )
    parser.add_argument(
        "--no-hash-check", action="store_true", help="Disable hash verification"
    )
    return parser


class ExecutionCLI:
    """CLI for URL execution operations."""

    def __init__(self, service: Optional[URLExecutionService] = None) -> None:
        self.parser = setup_argument_parser()
        if service is None:
            self.service = URLExecutionService(
                http_client=HTTPClientAdapter(),
                storage=StorageAdapter(base_path="executions"),
                normalizer=ContentNormalizer(),
            )
        else:
            self.service = service

    def run(self, args: Optional[List[str]] = None) -> int:
        """Execute the CLI command."""
        with tracer.start_as_current_span("execution_cli.run") as span:
            parsed_args = self.parser.parse_args(args)

            logger.debug("Parsed CLI arguments: %s", parsed_args)
            span.set_attribute("cli.url", parsed_args.url)
            span.set_attribute("cli.output_dir", parsed_args.output_dir)
            span.set_attribute("cli.force", parsed_args.force)
            span.set_attribute("cli.save_content", parsed_args.save_content)
            span.set_attribute("cli.verbose", parsed_args.verbose)
            span.set_attribute("cli.no_etag_check", parsed_args.no_etag_check)
            span.set_attribute("cli.no_hash_check", parsed_args.no_hash_check)

        # Configure logging
        logging_level = logging.DEBUG if parsed_args.verbose else logging.INFO
        logging.basicConfig(
            level=logging_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

        try:
            # Set environment flags based on CLI options
            if parsed_args.no_etag_check:
                os.environ["ENABLE_ETAG_CHECK"] = "false"
            if parsed_args.no_hash_check:
                os.environ["ENABLE_CONTENT_HASH_CHECK"] = "false"
                os.environ["ENABLE_NORMALIZED_HASH_CHECK"] = "false"

            # Execute URL
            execution = self.service.execute_url(parsed_args.url)

            # Output results
            # Record execution details in span and logs
            span.set_attribute("execution.id", execution.execution_id)
            span.set_attribute("execution.status", execution.status.value)
            span.set_attribute("execution.change_detected", execution.change_detected)
            if execution.change_type:
                span.set_attribute("execution.change_type", execution.change_type.value)
            span.set_attribute("execution.content_size", execution.content_size)
            span.set_attribute(
                "execution.download_duration_ms",
                execution.download_duration_ms
                if execution.download_duration_ms is not None
                else 0,
            )

            logger.debug(
                "Execution result: id=%s, status=%s, change=%s, type=%s, size=%d, duration=%dms",
                execution.execution_id,
                execution.status.value,
                execution.change_detected,
                execution.change_type.value if execution.change_type else None,
                execution.content_size if execution.content_size else 0,
                execution.download_duration_ms if execution.download_duration_ms else 0,
            )

            logger.info(f"Execution ID: {execution.execution_id}")
            logger.info(f"Status: {execution.status.value}")
            logger.info(f"Change detected: {execution.change_detected}")
            if execution.change_type:
                logger.info(f"Change type: {execution.change_type.value}")
            logger.info(f"Content size: {execution.content_size} bytes")
            logger.info(f"Download duration: {execution.download_duration_ms} ms")

            return 0

        except Exception as e:
            logging.error(f"Execution failed: {str(e)}")
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e))
            span.set_attribute("success", False)
            span.set_attribute("exit_code", 1)
            return 1
