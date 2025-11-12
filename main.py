#!/usr/bin/env python3
"""
Main entry point for the Gaceta Oficial edition extraction service.

This module serves as the composition root where all dependencies are wired together.
"""

import sys

from adapters.main_cli import main as unified_main


def main() -> None:
    """Main entry point for the CLI."""

    # Run the CLI adapter
    sys.exit(unified_main())


if __name__ == "__main__":
    main()
