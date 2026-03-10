"""Input validation helpers for the CV Builder application."""

from __future__ import annotations

import re
from typing import Optional


def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def validate_url(url: str) -> bool:
    """Validate a URL (http/https)."""
    if not url:
        return True  # optional fields
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url.strip()))


def validate_date(date_str: str) -> bool:
    """Validate a date string in MM/YYYY or YYYY format, or 'Present'."""
    if date_str.strip().lower() == "present":
        return True
    # MM/YYYY
    if re.match(r"^\d{2}/\d{4}$", date_str.strip()):
        month, year = date_str.strip().split("/")
        return 1 <= int(month) <= 12 and 1900 <= int(year) <= 2100
    # YYYY
    if re.match(r"^\d{4}$", date_str.strip()):
        return 1900 <= int(date_str.strip()) <= 2100
    return False


def validate_phone(phone: str) -> bool:
    """Validate a phone number (digits, spaces, dashes, parentheses, plus)."""
    pattern = r"^[\+\d\s\-\(\)]{7,20}$"
    return bool(re.match(pattern, phone.strip()))


def validate_proficiency_level(level: str, allowed: list) -> bool:
    """Validate that a proficiency level is in the allowed list."""
    return level.strip().lower() in [a.lower() for a in allowed]


def normalize_date(date_str: str) -> str:
    """Normalize a date string to a consistent format."""
    stripped = date_str.strip()
    if stripped.lower() == "present":
        return "Present"
    return stripped
