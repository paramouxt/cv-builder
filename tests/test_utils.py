"""Tests for utility functions."""

import json
import os
import tempfile

import pytest
from cv_builder.models import PersonalInfo, UserProfile
from cv_builder.utils import (
    build_filename,
    format_date_range,
    list_to_bullet,
    load_progress,
    save_progress,
    truncate,
)


class TestBuildFilename:
    def test_basic(self):
        assert build_filename("John Doe") == "John_Doe_CV.pdf"

    def test_custom_extension(self):
        assert build_filename("Jane Smith", "txt") == "Jane_Smith_CV.txt"

    def test_special_chars_stripped(self):
        # Only alphanumeric and _ are kept
        name = "O'Brien"
        filename = build_filename(name)
        assert "'" not in filename
        assert filename.endswith("_CV.pdf")

    def test_multiple_spaces(self):
        assert build_filename("  John   Doe  ") == "John_Doe_CV.pdf"


class TestFormatDateRange:
    def test_standard(self):
        result = format_date_range("01/2020", "Present")
        assert result == "01/2020 - Present"

    def test_both_dates(self):
        result = format_date_range("2018", "2022")
        assert result == "2018 - 2022"


class TestListToBullet:
    def test_empty(self):
        assert list_to_bullet([]) == ""

    def test_single_item(self):
        assert list_to_bullet(["Python"]) == "• Python"

    def test_multiple_items(self):
        result = list_to_bullet(["Python", "Go"])
        assert result == "• Python\n• Go"


class TestTruncate:
    def test_no_truncation_needed(self):
        assert truncate("Hello", 100) == "Hello"

    def test_truncation(self):
        result = truncate("A" * 200, 100)
        assert len(result) == 100
        assert result.endswith("...")

    def test_exact_length(self):
        assert truncate("A" * 100, 100) == "A" * 100


class TestSaveLoadProgress:
    def test_roundtrip(self, tmp_path):
        profile = UserProfile(
            personal_info=PersonalInfo(
                full_name="Save Test",
                email="save@example.com",
                phone="0123456789",
                location="Nowhere",
            )
        )
        filepath = str(tmp_path / "progress.json")
        save_progress(profile, filepath)

        loaded = load_progress(filepath)
        assert loaded is not None
        assert loaded.personal_info.full_name == "Save Test"

    def test_load_nonexistent(self, tmp_path):
        result = load_progress(str(tmp_path / "missing.json"))
        assert result is None

    def test_load_invalid_json(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json at all", encoding="utf-8")
        result = load_progress(str(bad_file))
        assert result is None
