"""
Domain models for edition extraction.

This module contains the core domain entities.
"""

from typing import Dict, Optional


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

