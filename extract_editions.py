#!/usr/bin/env python3
"""
CLI for extracting edition data from the Gaceta Oficial HTML index.

This module provides the command-line interface for the edition extraction service.
"""

import argparse
import json
import os
import sys
from typing import Optional

from edition_core import EditionExtractionService


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
            return output_file

        # Create output filename from input filename
        input_basename = os.path.basename(input_file)
        input_name, _ = os.path.splitext(input_basename)
        output_filename = f"{input_name}-editions.json"
        output_dir = os.path.join(self.script_dir, "output")

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        return os.path.join(output_dir, output_filename)

    def save_editions_to_json(self, editions, output_path: str) -> None:
        """
        Save editions to a JSON file.

        Args:
            editions: List of Edition objects
            output_path: Path to save the JSON file
        """
        editions_data = [edition.to_dict() for edition in editions]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(editions_data, f, ensure_ascii=False, indent=2)

    def run(self, args=None) -> int:
        """
        Run the CLI application.

        Args:
            args: Optional arguments list (defaults to sys.argv)

        Returns:
            Exit code (0 for success, 1 for error)
        """
        parser = self.setup_argument_parser()
        parsed_args = parser.parse_args(args)

        try:
            # Extract editions using the service
            editions = self.service.extract_from_file(parsed_args.input_file)

            # Resolve output path
            output_path = self.resolve_output_path(
                parsed_args.input_file, parsed_args.output_file
            )

            # Save to JSON
            self.save_editions_to_json(editions, output_path)

            # Report success
            print(f"Extracted {len(editions)} editions to {output_path}")
            return 0

        except FileNotFoundError:
            print(f"Error: Input file '{parsed_args.input_file}' not found", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
            return 1


def main():
    """Main entry point for the CLI."""
    cli = EditionCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
