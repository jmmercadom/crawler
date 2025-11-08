"""
Logging infrastructure setup.

This module provides logging configuration for the application.
"""

import logging
import os

# Get logger for this module
logger = logging.getLogger(__name__)


def get_log_level() -> int:
    """
    Get the logging level from the LOG_LEVEL environment variable.

    Returns:
        The logging level (defaults to logging.INFO if not set or invalid)
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_name, logging.INFO)


def setup_logger() -> None:
    """Configure and initialize the application logger."""
    # Get log level from environment variable
    log_level = get_log_level()

    # Setup colored logging
    try:
        import coloredlogs  # type: ignore

        coloredlogs.install(
            level=log_level,
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            level_styles={
                "debug": {"color": "cyan"},
                "info": {"color": "green"},
                "warning": {"color": "yellow"},
                "error": {"color": "red"},
                "critical": {"color": "red", "bold": True},
            },
        )
    except ImportError:
        # Fallback to basic logging if coloredlogs not installed
        logging.basicConfig(
            level=log_level, format="%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        logger.warning("coloredlogs not installed, using basic logging")

    logger.info("log level: %s", log_level)
