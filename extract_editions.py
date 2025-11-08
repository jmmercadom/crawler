#!/usr/bin/env python3
"""
CLI for extracting edition data from the Gaceta Oficial HTML index.

This module provides the command-line interface for the edition extraction service.
"""

import sys

from cli import EditionCLI
from setup_logger import setup_logger
from setup_telemetry import setup_opentelemetry


def main():
    """Main entry point for the CLI."""
    setup_logger()
    setup_opentelemetry()

    cli = EditionCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()
