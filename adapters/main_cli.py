import argparse
import sys

from infrastructure.logging import setup_logger
from infrastructure.telemetry import setup_opentelemetry

from adapters.edition_cli import EditionCLI
from adapters.execution_cli import ExecutionCLI


def main() -> int:
    """
    Unified entry point for the `gaceta` command.

    Subcommands:
        extract   – Run the edition extraction CLI.
        execute   – Run the URL execution CLI.
    """
    # Setup shared infrastructure
    setup_logger()
    setup_opentelemetry()

    # Top‑level parser only defines subcommands; each subcommand parses its own arguments.
    parser = argparse.ArgumentParser(
        prog="gaceta", description="Gaceta Oficial CLI with multiple subcommands"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand placeholders – the actual argument definitions live in the respective CLI classes.
    subparsers.add_parser("extract", help="Extract edition data from an HTML file")
    subparsers.add_parser("execute", help="Execute a URL and detect changes")

    # Parse only the subcommand name; the remaining args are passed through.
    # If no args provided, it will raise a system exit
    args, remaining = parser.parse_known_args()

    if args.command == "extract":
        return EditionCLI().run(remaining)
    elif args.command == "execute":
        return ExecutionCLI().run(remaining)
    else:
        parser.error(f"Unknown subcommand: {args.command}")


if __name__ == "__main__":
    sys.exit(main())
