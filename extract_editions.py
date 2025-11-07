#!/usr/bin/env python3
"""
Extract edition data from the Gaceta Oficial HTML index.
"""

import argparse
import json
import os
import re
from html.parser import HTMLParser
from datetime import datetime


class EditionExtractor(HTMLParser):
    """Extract edition information from HTML."""

    def __init__(self):
        super().__init__()
        self.editions = []
        self.current_edition = None
        self.in_anuncio = False
        self.capture_text = False
        self.text_buffer = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # Look for the anuncio div that contains edition details
        if tag == "div" and attrs_dict.get("class") == "anuncio":
            self.in_anuncio = True
            self.current_edition = {
                "number": None,
                "type": None,
                "published_date": None,
                "administration": None,
            }
            self.text_buffer = []

    def handle_endtag(self, tag):
        if tag == "div" and self.in_anuncio:
            # Process the collected text
            text = "".join(self.text_buffer)
            self._parse_edition_text(text)

            # Only add if we have at least a number
            if self.current_edition and self.current_edition["number"]:
                self.editions.append(self.current_edition)

            self.in_anuncio = False
            self.current_edition = None
            self.text_buffer = []

    def handle_data(self, data):
        if self.in_anuncio:
            self.text_buffer.append(data)

    def _parse_edition_text(self, text):
        """Parse the edition text and extract fields."""
        if not self.current_edition:
            return

        # Extract edition number
        number_match = re.search(r"Nº de Edición\s*:\s*(\S+)", text)
        if number_match:
            self.current_edition["number"] = number_match.group(1).strip()

        # Extract edition type
        type_match = re.search(
            r"Tipo de Edición\s*:\s*([^\n]+?)(?:\s*Fecha|\s*$)", text, re.DOTALL
        )
        if type_match:
            self.current_edition["type"] = type_match.group(1).strip()

        # Extract publication date and convert to ISO 8601
        date_match = re.search(r"Fecha de Publicación\s*:\s*(\d{2}-\d{2}-\d{4})", text)
        if date_match:
            date_str = date_match.group(1).strip()
            try:
                # Convert from DD-MM-YYYY to YYYY-MM-DD
                date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                self.current_edition["published_date"] = date_obj.strftime("%Y-%m-%d")
            except ValueError:
                self.current_edition["published_date"] = None

        # Extract administration/government
        admin_match = re.search(r"Gobierno\s*:\s*([^\n<]+)", text)
        if admin_match:
            self.current_edition["administration"] = admin_match.group(1).strip()


def extract_editions(html_file_path, output_file_path):
    """Extract editions from HTML and save to JSON."""

    # Read the HTML file
    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Parse and extract
    parser = EditionExtractor()
    parser.feed(html_content)

    # Save to JSON
    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump(parser.editions, f, ensure_ascii=False, indent=2)

    return len(parser.editions)


if __name__ == "__main__":
    # Get the script's directory (project root)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Extract edition data from Gaceta Oficial HTML index."
    )
    parser.add_argument(
        "-in", "--input-file",
        dest="input_file",
        help="Path to the input HTML file, relative to the script's directory",
        required=True
    )
    parser.add_argument(
        "-out", "--output-file",
        dest="output_file",
        help="Path to the output JSON file (default: output/<input_filename>-editions.json)"
    )

    args = parser.parse_args()

    # Determine output file path
    if args.output_file:
        output_file = args.output_file
    else:
        # Create output filename from input filename
        input_basename = os.path.basename(args.input_file)
        input_name, _ = os.path.splitext(input_basename)
        output_filename = f"{input_name}-editions.json"
        output_dir = os.path.join(script_dir, "output")

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, output_filename)

    # Extract editions
    count = extract_editions(args.input_file, output_file)
    print(f"Extracted {count} editions to {output_file}")
