"""Tests for input validators."""

import pytest
from cv_builder.validators import (
    validate_email,
    validate_url,
    validate_date,
    validate_phone,
    validate_proficiency_level,
    normalize_date,
)


class TestValidateEmail:
    def test_valid_simple(self):
        assert validate_email("user@example.com") is True

    def test_valid_subdomain(self):
        assert validate_email("user@mail.example.co.uk") is True

    def test_valid_plus_addressing(self):
        assert validate_email("user+tag@example.org") is True

    def test_invalid_missing_at(self):
        assert validate_email("userexample.com") is False

    def test_invalid_missing_tld(self):
        assert validate_email("user@example") is False

    def test_invalid_empty(self):
        assert validate_email("") is False


class TestValidateUrl:
    def test_valid_https(self):
        assert validate_url("https://github.com/user") is True

    def test_valid_http(self):
        assert validate_url("http://example.com") is True

    def test_empty_is_valid(self):
        # Optional fields pass empty string
        assert validate_url("") is True

    def test_invalid_no_scheme(self):
        assert validate_url("github.com/user") is False

    def test_invalid_ftp(self):
        assert validate_url("ftp://example.com") is False


class TestValidateDate:
    def test_mm_yyyy_valid(self):
        assert validate_date("01/2023") is True

    def test_mm_yyyy_invalid_month(self):
        assert validate_date("13/2023") is False

    def test_yyyy_valid(self):
        assert validate_date("2023") is True

    def test_present(self):
        assert validate_date("Present") is True
        assert validate_date("present") is True

    def test_invalid_format(self):
        assert validate_date("March 2023") is False

    def test_out_of_range_year(self):
        assert validate_date("01/1800") is False


class TestValidatePhone:
    def test_valid_international(self):
        assert validate_phone("+1 234 567 8900") is True

    def test_valid_digits_only(self):
        assert validate_phone("01234567890") is True

    def test_valid_dashes(self):
        assert validate_phone("0123-456-789") is True

    def test_too_short(self):
        assert validate_phone("123") is False

    def test_letters_invalid(self):
        assert validate_phone("abc-defg-hij") is False


class TestValidateProficiencyLevel:
    def test_valid_case_insensitive(self):
        levels = ["Beginner", "Intermediate", "Advanced", "Expert"]
        assert validate_proficiency_level("intermediate", levels) is True
        assert validate_proficiency_level("EXPERT", levels) is True

    def test_invalid_level(self):
        levels = ["Beginner", "Intermediate"]
        assert validate_proficiency_level("Master", levels) is False


class TestNormalizeDate:
    def test_strips_whitespace(self):
        assert normalize_date("  2023  ") == "2023"

    def test_present_capitalized(self):
        assert normalize_date("present") == "Present"
        assert normalize_date("PRESENT") == "Present"

    def test_mm_yyyy_unchanged(self):
        assert normalize_date("01/2023") == "01/2023"
