"""Tests for ATS-friendly DOCX generation."""

from pathlib import Path

from docx import Document

from cv_builder.docx_generator import DocxGenerator
from cv_builder.models import UserProfile

ROOT = Path(__file__).resolve().parents[1]


def test_docx_generator_writes_readable_document(tmp_path):
    profile = UserProfile.model_validate_json(
        (ROOT / "cv_builder" / "sample_data" / "sample_profile.json").read_text(encoding="utf-8")
    )

    path = DocxGenerator(profile).generate(str(tmp_path))

    assert path.endswith("_CV.docx")
    assert Path(path).exists()
    text = "\n".join(p.text for p in Document(path).paragraphs)
    assert "Piyush Jain Sanjay" in text
    assert "PROFESSIONAL SUMMARY" in text
    assert "WORK EXPERIENCE" in text
    assert "SKILLS" in text


def test_docx_generator_requires_personal_info(tmp_path):
    profile = UserProfile()

    try:
        DocxGenerator(profile).generate(str(tmp_path))
    except ValueError as exc:
        assert "Personal information is required" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
