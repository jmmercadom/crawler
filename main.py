#!/usr/bin/env python3
"""
Main entry point for the Gaceta Oficial edition extraction service.

This module serves as the composition root where all dependencies are wired together.
"""

import sys

from adapters.cli import EditionCLI
from infrastructure.logging import setup_logger
from infrastructure.telemetry import setup_opentelemetry


def main():
    """Main entry point for the CLI."""
    # Setup infrastructure
    setup_logger()
    setup_opentelemetry()

    # Run the CLI adapter
    cli = EditionCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()

