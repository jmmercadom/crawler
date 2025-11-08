#!/usr/bin/env python3
"""
CLI for extracting edition data from the Gaceta Oficial HTML index.

This module provides the command-line interface for the edition extraction service.
"""

import argparse
import json
import os
import sys
import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.instrumentation.logging import LoggingInstrumentor

from edition_core import EditionExtractionService

# Get logger for this module
logger = logging.getLogger(__name__)

# Get tracer for this module
tracer = trace.get_tracer(__name__)


class EditionCLI:
    """Command-line interface for edition extraction."""

    def __init__(self):
        self.service = EditionExtractionService()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

    def setup_argument_parser(self) -> argparse.ArgumentParser:
        """Configure and return the argument parser."""
        parser = argparse.ArgumentParser(
            description="Extract edition data from Gaceta Oficial HTML index."
        )
        parser.add_argument(
            "-in",
            "--input-file",
            dest="input_file",
            help="Path to the input HTML file, relative to the script's directory",
            required=True,
        )
        parser.add_argument(
            "-out",
            "--output-file",
            dest="output_file",
            help="Path to the output JSON file (default: output/<input_filename>-editions.json)",
        )
        return parser

    def resolve_output_path(self, input_file: str, output_file: Optional[str]) -> str:
        """
        Determine the output file path.

        Args:
            input_file: The input file path
            output_file: Optional explicit output file path

        Returns:
            The resolved output file path
        """
        if output_file:
            logger.debug("Using explicit output file: %s", output_file)
            return output_file

        # Create output filename from input filename
        input_basename = os.path.basename(input_file)
        input_name, _ = os.path.splitext(input_basename)
        output_filename = f"{input_name}-editions.json"
        output_dir = os.path.join(self.script_dir, "output")

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        logger.debug("Created/verified output directory: %s", output_dir)

        output_path = os.path.join(output_dir, output_filename)
        logger.debug("Resolved output path: %s", output_path)
        return output_path

    def save_editions_to_json(self, editions, output_path: str) -> None:
        """
        Save editions to a JSON file.

        Args:
            editions: List of Edition objects
            output_path: Path to save the JSON file
        """
        logger.debug("Converting %d editions to JSON format", len(editions))
        editions_data = [edition.to_dict() for edition in editions]
        logger.debug("Writing JSON to file: %s", output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(editions_data, f, ensure_ascii=False, indent=2)
        logger.debug("Successfully wrote JSON file")

    def run(self, args=None) -> int:
        """
        Run the CLI application.

        Args:
            args: Optional arguments list (defaults to sys.argv)

        Returns:
            Exit code (0 for success, 1 for error)
        """
        with tracer.start_as_current_span("extract_editions.run") as span:
            parser = self.setup_argument_parser()
            parsed_args = parser.parse_args(args)

            logger.debug("CLI arguments: input_file=%s, output_file=%s",
                        parsed_args.input_file, parsed_args.output_file)

            # Add input file as span attribute
            span.set_attribute("input.file", parsed_args.input_file)
            if parsed_args.output_file:
                span.set_attribute("output.file", parsed_args.output_file)

            try:
                # Extract editions using the service
                with tracer.start_as_current_span("extract_from_file") as extract_span:
                    extract_span.set_attribute("file.path", parsed_args.input_file)
                    editions = self.service.extract_from_file(parsed_args.input_file)
                    extract_span.set_attribute("editions.count", len(editions))

                # Resolve output path
                output_path = self.resolve_output_path(
                    parsed_args.input_file, parsed_args.output_file
                )
                span.set_attribute("output.resolved_path", output_path)

                # Save to JSON
                with tracer.start_as_current_span("save_to_json") as save_span:
                    save_span.set_attribute("output.path", output_path)
                    save_span.set_attribute("editions.count", len(editions))
                    self.save_editions_to_json(editions, output_path)

                # Report success
                logger.info("Extracted %d editions to %s", len(editions), output_path)
                span.set_attribute("success", True)
                span.set_attribute("exit_code", 0)
                return 0

            except FileNotFoundError:
                logger.error("Input file '%s' not found", parsed_args.input_file)
                span.set_attribute("success", False)
                span.set_attribute("error.type", "FileNotFoundError")
                span.set_attribute("error.message", f"Input file '{parsed_args.input_file}' not found")
                span.set_attribute("exit_code", 1)
                return 1
            except Exception as e:
                logger.error("Unexpected error: %s", str(e))
                span.set_attribute("success", False)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                span.set_attribute("exit_code", 1)
                return 1


def get_log_level() -> int:
    """
    Get the logging level from the LOG_LEVEL environment variable.

    Returns:
        The logging level (defaults to logging.INFO if not set or invalid)
    """
    level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    return level_map.get(level_name, logging.INFO)


def setup_opentelemetry() -> None:
    """
    Initialize OpenTelemetry tracing.

    Configuration is controlled by environment variables:
    - OTEL_SERVICE_NAME: Service name (default: gaceta-crawler)
    - OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (default: http://localhost:4318)
    - OTEL_TRACES_ENABLED: Enable/disable tracing (default: true)
    """
    # Check if tracing is enabled
    traces_enabled = os.getenv('OTEL_TRACES_ENABLED', 'true').lower() in ('true', '1', 'yes')
    if not traces_enabled:
        logger.info("OpenTelemetry tracing is disabled")
        return

    # Get service name from environment or use default
    service_name = os.getenv('OTEL_SERVICE_NAME', 'gaceta-crawler')

    # Create resource with service name
    resource = Resource(attributes={
        SERVICE_NAME: service_name
    })

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Get OTLP endpoint from environment or use default
    otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318')

    try:
        # Create OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")

        # Add batch span processor
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # Set the tracer provider
        trace.set_tracer_provider(provider)

        # Instrument logging to correlate logs with traces
        LoggingInstrumentor().instrument(set_logging_format=False)

        logger.info("OpenTelemetry initialized: service=%s, endpoint=%s", service_name, otlp_endpoint)
    except Exception as e:
        logger.warning("Failed to initialize OpenTelemetry: %s", str(e))


def main():
    """Main entry point for the CLI."""
    # Get log level from environment variable
    log_level = get_log_level()

    # Setup colored logging
    try:
        import coloredlogs
        coloredlogs.install(
            level=log_level,
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
            level_styles={
                'debug': {'color': 'cyan'},
                'info': {'color': 'green'},
                'warning': {'color': 'yellow'},
                'error': {'color': 'red'},
                'critical': {'color': 'red', 'bold': True},
            }
        )
    except ImportError:
        # Fallback to basic logging if coloredlogs not installed
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s %(name)s %(levelname)s %(message)s'
        )
        logger.warning("coloredlogs not installed, using basic logging")

    logger.info("log level: %s", log_level)

    setup_opentelemetry()

    cli = EditionCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
