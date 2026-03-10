"""Tests for CV generation (PDF and plain text)."""

import os
import tempfile

import pytest
from cv_builder.cv_generator import CVGenerator, _build_text_cv
from cv_builder.models import (
    Achievement,
    AdditionalInfo,
    Certification,
    Education,
    Language,
    PersonalInfo,
    Project,
    Skills,
    TechnicalSkill,
    UserProfile,
    WorkExperience,
)


def _full_profile() -> UserProfile:
    """Return a fully populated UserProfile for generation tests."""
    return UserProfile(
        personal_info=PersonalInfo(
            full_name="Jane Doe",
            email="jane@example.com",
            phone="+44 7700 900001",
            location="London, UK",
            linkedin="https://linkedin.com/in/janedoe",
            summary="Experienced software engineer.",
        ),
        education=[
            Education(
                degree="BSc",
                field_of_study="Computer Science",
                institution="University of London",
                start_date="09/2015",
                end_date="06/2019",
                gpa="3.9",
                honors="First Class",
            )
        ],
        work_experience=[
            WorkExperience(
                job_title="Software Engineer",
                company="Acme Corp",
                location="London, UK",
                start_date="07/2019",
                end_date="Present",
                achievements=[
                    Achievement(
                        description="Built internal tooling",
                        quantified_impact="Saved 10 hours/week",
                        tools_used="Python, FastAPI",
                    )
                ],
            )
        ],
        skills=Skills(
            technical=[TechnicalSkill(name="Python", proficiency="Expert")],
            soft=["Teamwork"],
            languages=[Language(name="English", proficiency="Native")],
            certifications=[
                Certification(name="AWS SAA", issuing_org="Amazon", date="01/2022")
            ],
        ),
        projects=[
            Project(
                name="CV Builder",
                description="A Python CLI tool.",
                technologies="Python, Rich, fpdf2",
                role="Lead Developer",
                outcomes="Used by 100 people",
                problem_solved="Manual CV creation is tedious",
            )
        ],
        additional_info=AdditionalInfo(
            volunteer_work="Code Club mentor",
            interests="Open source",
        ),
    )


class TestCVGeneratorTextOutput:
    def test_text_cv_contains_name(self, tmp_path):
        profile = _full_profile()
        gen = CVGenerator(profile)
        path = gen.generate_text(str(tmp_path))
        assert os.path.exists(path)
        content = open(path, encoding="utf-8").read()
        assert "Jane Doe" in content

    def test_text_cv_contains_education(self, tmp_path):
        profile = _full_profile()
        content = _build_text_cv(profile)
        assert "Computer Science" in content
        assert "University of London" in content

    def test_text_cv_contains_experience(self, tmp_path):
        profile = _full_profile()
        content = _build_text_cv(profile)
        assert "Acme Corp" in content
        assert "Built internal tooling" in content

    def test_text_cv_contains_skills(self):
        profile = _full_profile()
        content = _build_text_cv(profile)
        assert "Python" in content
        assert "Teamwork" in content

    def test_text_cv_contains_certifications(self):
        profile = _full_profile()
        content = _build_text_cv(profile)
        assert "AWS SAA" in content

    def test_text_cv_contains_additional_info(self):
        profile = _full_profile()
        content = _build_text_cv(profile)
        assert "Open source" in content

    def test_text_cv_filename(self, tmp_path):
        profile = _full_profile()
        gen = CVGenerator(profile)
        path = gen.generate_text(str(tmp_path))
        assert "Jane_Doe_CV.txt" in path

    def test_text_cv_requires_personal_info(self, tmp_path):
        profile = UserProfile()
        gen = CVGenerator(profile)
        with pytest.raises(ValueError, match="Personal information is required"):
            gen.generate_text(str(tmp_path))


class TestCVGeneratorPDFOutput:
    def test_pdf_creates_file(self, tmp_path):
        profile = _full_profile()
        gen = CVGenerator(profile)
        path = gen.generate_pdf(str(tmp_path))
        assert os.path.exists(path)
        assert path.endswith(".pdf")
        # PDF should have some non-trivial size (> 1 KB)
        assert os.path.getsize(path) > 1024

    def test_pdf_filename(self, tmp_path):
        profile = _full_profile()
        gen = CVGenerator(profile)
        path = gen.generate_pdf(str(tmp_path))
        assert "Jane_Doe_CV.pdf" in path

    def test_pdf_requires_personal_info(self, tmp_path):
        profile = UserProfile()
        gen = CVGenerator(profile)
        with pytest.raises(ValueError, match="Personal information is required"):
            gen.generate_pdf(str(tmp_path))

    def test_pdf_starts_with_pdf_magic(self, tmp_path):
        """Verify the file is a valid PDF by checking its magic bytes."""
        profile = _full_profile()
        gen = CVGenerator(profile)
        path = gen.generate_pdf(str(tmp_path))
        with open(path, "rb") as f:
            header = f.read(4)
        assert header == b"%PDF"
