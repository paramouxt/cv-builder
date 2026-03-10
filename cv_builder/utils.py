"""Utility functions for file I/O, formatting, and JSON persistence."""

from __future__ import annotations

import json
import os
from typing import Any

from cv_builder.models import UserProfile


PROGRESS_FILE = "cv_builder_progress.json"


def save_progress(profile: UserProfile, filepath: str = PROGRESS_FILE) -> None:
    """Save the current user profile to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write(profile.model_dump_json(indent=2))


def load_progress(filepath: str = PROGRESS_FILE) -> UserProfile | None:
    """Load a previously saved user profile from a JSON file."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return UserProfile.model_validate(data)
    except Exception:
        return None


def build_filename(full_name: str, extension: str = "pdf") -> str:
    """Build a safe filename from the user's full name."""
    safe = "_".join(full_name.strip().split())
    safe = "".join(c for c in safe if c.isalnum() or c == "_")
    return f"{safe}_CV.{extension}"


def format_date_range(start: str, end: str) -> str:
    """Format a start/end date range for display."""
    return f"{start} – {end}"


def list_to_bullet(items: list[str]) -> str:
    """Convert a list of strings to a bulleted text block."""
    return "\n".join(f"• {item}" for item in items)


def truncate(text: str, max_length: int = 100) -> str:
    """Truncate text to a maximum length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
