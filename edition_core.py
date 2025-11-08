"""
Core domain logic for extracting edition data from HTML.

This module contains the business logic for parsing and extracting
edition information from Gaceta Oficial HTML files.
"""

import re
import logging
from html.parser import HTMLParser
from datetime import datetime
from typing import List, Dict, Optional

from opentelemetry import trace

# Get logger for this module
logger = logging.getLogger(__name__)

# Get tracer for this module
tracer = trace.get_tracer(__name__)


class Edition:
    """Domain model representing a Gaceta Oficial edition."""

    def __init__(
        self,
        number: Optional[str] = None,
        type: Optional[str] = None,
        published_date: Optional[str] = None,
        administration: Optional[str] = None,
    ):
        self.number = number
        self.type = type
        self.published_date = published_date
        self.administration = administration

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert to dictionary representation."""
        return {
            "number": self.number,
            "type": self.type,
            "published_date": self.published_date,
            "administration": self.administration,
        }

    def __repr__(self) -> str:
        return f"Edition(number={self.number}, type={self.type}, date={self.published_date})"


class EditionExtractor(HTMLParser):
    """Extract edition information from HTML."""

    def __init__(self):
        super().__init__()
        self.editions: List[Edition] = []
        self.current_edition: Optional[Edition] = None
        self.in_anuncio = False
        self.text_buffer: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        attrs_dict = dict(attrs)

        # Look for the anuncio div that contains edition details
        if tag == "div" and attrs_dict.get("class") == "anuncio":
            # Start processing the edition
            logger.debug("Found anuncio div, starting new edition extraction")
            self.in_anuncio = True
            self.current_edition = Edition()
            self.text_buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "div" and self.in_anuncio:
            # Process the collected text
            text = "".join(self.text_buffer)
            logger.debug("Processing edition text block (length: %d chars)", len(text))
            self._parse_edition_text(text)

            # Only add if we have at least a number
            if self.current_edition and self.current_edition.number:
                logger.debug("Successfully extracted edition: %s", self.current_edition)
                self.editions.append(self.current_edition)
            else:
                logger.warning("No edition number found in text")

            # Reset the parser state
            self.in_anuncio = False
            self.current_edition = None
            self.text_buffer = []

    def handle_data(self, data: str) -> None:
        if self.in_anuncio:
            self.text_buffer.append(data)

    def _parse_edition_text(self, text: str) -> None:
        """Parse the edition text and extract fields."""
        if not self.current_edition:
            return

        with tracer.start_as_current_span("parse_edition_text") as span:
            span.set_attribute("text.length", len(text))
            logger.debug("Parsing edition text with regex patterns")

            # Extract edition number
            number_match = re.search(r"Nº de Edición\s*:\s*(\S+)", text)
            if number_match:
                self.current_edition.number = number_match.group(1).strip()
                span.set_attribute("edition.number", self.current_edition.number)
                logger.debug("Extracted edition number: %s", self.current_edition.number)
            else:
                logger.warning("No edition number found in text")

            # Extract edition type
            type_match = re.search(
                r"Tipo de Edición\s*:\s*([^\n]+?)(?:\s*Fecha|\s*$)", text, re.DOTALL
            )
            if type_match:
                self.current_edition.type = type_match.group(1).strip()
                span.set_attribute("edition.type", self.current_edition.type)
                logger.debug("Extracted edition type: %s", self.current_edition.type)
            else:
                logger.warning("No edition type found in text")

            # Extract publication date and convert to ISO 8601
            date_match = re.search(r"Fecha de Publicación\s*:\s*(\d{2}-\d{2}-\d{4})", text)
            if date_match:
                date_str = date_match.group(1).strip()
                logger.debug("Found publication date: %s", date_str)
                try:
                    # Convert from DD-MM-YYYY to YYYY-MM-DD
                    date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                    self.current_edition.published_date = date_obj.strftime("%Y-%m-%d")
                    span.set_attribute("edition.published_date", self.current_edition.published_date)
                    logger.debug("Converted to ISO 8601: %s", self.current_edition.published_date)
                except ValueError:
                    logger.warning("Invalid publication date format: %s", date_str)
                    self.current_edition.published_date = None
            else:
                logger.warning("No publication date found in text")

            # Extract administration/government
            admin_match = re.search(r"Gobierno\s*:\s*([^\n<]+)", text)
            if admin_match:
                self.current_edition.administration = admin_match.group(1).strip()
                span.set_attribute("edition.administration", self.current_edition.administration)
                logger.debug("Extracted administration: %s", self.current_edition.administration)
            else:
                logger.warning("No administration/government found in text")

    def get_editions(self) -> List[Edition]:
        """Get the list of extracted editions."""
        return self.editions


class EditionExtractionService:
    """Service for extracting editions from HTML content."""

    def __init__(self):
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
            logger.debug("Starting HTML parsing (content length: %d chars)", len(html_content))

            self.extractor.feed(html_content)
            editions = self.extractor.get_editions()

            span.set_attribute("editions.extracted", len(editions))
            logger.info("Extracted %d editions from HTML", len(editions))

            # Add event for extraction completion
            span.add_event("extraction_completed", {
                "editions_count": len(editions)
            })

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
                logger.debug("Successfully read file (size: %d bytes)", len(html_content))

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

