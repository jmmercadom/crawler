"""
Command-line interface adapter.

This module provides the CLI adapter for the edition extraction application.
"""

import argparse
import json
import logging
import os
from typing import List, Optional

from opentelemetry import trace

from application.edition_extraction_service import EditionExtractionService
from domain.models import Edition

# Get logger for this module
logger = logging.getLogger(__name__)

# Get tracer for this module
tracer = trace.get_tracer(__name__)


def setup_argument_parser() -> argparse.ArgumentParser:
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


class EditionCLI:
    """Command-line interface for edition extraction."""

    def __init__(self) -> None:
        self.parser = setup_argument_parser()
        self.service = EditionExtractionService()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

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

        # Get the project root directory (parent of adapters)
        project_root = os.path.dirname(self.script_dir)
        output_dir = os.path.join(project_root, "output")

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        logger.debug("Created/verified output directory: %s", output_dir)

        output_path = os.path.join(output_dir, output_filename)
        logger.debug("Resolved output path: %s", output_path)
        return output_path

    def save_editions_to_json(self, editions: List[Edition], output_path: str) -> None:
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

    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run the CLI application.

        Args:
            args: Optional arguments list (defaults to sys.argv)

        Returns:
            Exit code (0 for success, 1 for error)
        """
        with tracer.start_as_current_span("cli.run") as span:
            parsed_args = self.parser.parse_args(args)

            logger.debug(
                "CLI arguments: input_file=%s, output_file=%s",
                parsed_args.input_file,
                parsed_args.output_file,
            )

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
                span.set_attribute(
                    "error.message", f"Input file '{parsed_args.input_file}' not found"
                )
                span.set_attribute("exit_code", 1)
                return 1
            except Exception as e:
                logger.error("Unexpected error: %s", str(e))
                span.set_attribute("success", False)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                span.set_attribute("exit_code", 1)
                return 1
