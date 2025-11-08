"""
Domain logic for extracting edition data from HTML.

This module contains the core business logic for parsing HTML and extracting
edition information.
"""

import re
import logging
from html.parser import HTMLParser
from datetime import datetime
from typing import List, Optional

from opentelemetry import trace

from domain.models import Edition

# Get logger for this module
logger = logging.getLogger(__name__)

# Get tracer for this module
tracer = trace.get_tracer(__name__)


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

