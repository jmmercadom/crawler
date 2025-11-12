"""
Application services for edition extraction.

This module contains the application layer services that orchestrate domain logic.
"""

import logging
from typing import List

from opentelemetry import trace

from domain.models import Edition
from domain.extractors import EditionExtractor

# Get logger for this module
logger = logging.getLogger(__name__)

# Get tracer for this module
tracer = trace.get_tracer(__name__)


class EditionExtractionService:
    """Service for extracting editions from HTML content."""

    def __init__(self) -> None:
        self.extractor = EditionExtractor()

    def extract_from_html(self, html_content: str) -> List[Edition]:
        """
        Extract editions from HTML content.

        Args:
            html_content: The HTML content to parse

        Returns:
            List of extracted Edition objects
        """
        with tracer.start_as_current_span("extract_from_html") as span:
            span.set_attribute("html.content_length", len(html_content))
            logger.debug(
                "Starting HTML parsing (content length: %d chars)", len(html_content)
            )

            self.extractor.feed(html_content)
            editions = self.extractor.get_editions()

            span.set_attribute("editions.extracted", len(editions))
            logger.info("Extracted %d editions from HTML", len(editions))

            # Add event for extraction completion
            span.add_event("extraction_completed", {"editions_count": len(editions)})

            return editions

    def extract_from_file(self, file_path: str) -> List[Edition]:
        """
        Extract editions from an HTML file.

        Args:
            file_path: Path to the HTML file

        Returns:
            List of extracted Edition objects

        Raises:
            FileNotFoundError: If the file doesn't exist
            IOError: If there's an error reading the file
        """
        with tracer.start_as_current_span("read_html_file") as span:
            span.set_attribute("file.path", file_path)
            logger.debug("Reading HTML file: %s", file_path)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    html_content = f.read()

                span.set_attribute("file.size_bytes", len(html_content))
                logger.debug(
                    "Successfully read file (size: %d bytes)", len(html_content)
                )

                return self.extract_from_html(html_content)
            except FileNotFoundError:
                span.set_attribute("error", True)
                span.set_attribute("error.type", "FileNotFoundError")
                raise
            except IOError as e:
                span.set_attribute("error", True)
                span.set_attribute("error.type", "IOError")
                span.set_attribute("error.message", str(e))
                raise
