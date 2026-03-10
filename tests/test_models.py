"""Tests for Pydantic data models."""

import pytest
from pydantic import ValidationError
from cv_builder.models import (
    PersonalInfo,
    Education,
    WorkExperience,
    Achievement,
    TechnicalSkill,
    Language,
    Certification,
    Skills,
    Project,
    AdditionalInfo,
    JobPreferences,
    UserProfile,
)


class TestPersonalInfo:
    def test_valid(self):
        pi = PersonalInfo(
            full_name="Jane Doe",
            email="jane@example.com",
            phone="+44 7700 900000",
            location="London, UK",
        )
        assert pi.full_name == "Jane Doe"
        assert pi.linkedin is None

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            PersonalInfo(
                full_name="Jane Doe",
                email="not-an-email",
                phone="0123456789",
                location="London, UK",
            )

    def test_optional_fields(self):
        pi = PersonalInfo(
            full_name="Bob Smith",
            email="bob@example.com",
            phone="0123456789",
            location="Remote",
            linkedin="https://linkedin.com/in/bob",
            portfolio="https://bob.dev",
            summary="Experienced engineer.",
        )
        assert pi.linkedin == "https://linkedin.com/in/bob"
        assert pi.summary == "Experienced engineer."


class TestEducation:
    def test_valid(self):
        edu = Education(
            degree="BSc",
            field_of_study="Computer Science",
            institution="MIT",
            start_date="09/2018",
            end_date="06/2022",
        )
        assert edu.degree == "BSc"
        assert edu.gpa is None


class TestWorkExperience:
    def test_valid_with_achievements(self):
        ach = Achievement(
            description="Led migration to microservices",
            quantified_impact="Reduced latency by 40%",
        )
        exp = WorkExperience(
            job_title="Senior Engineer",
            company="Acme Corp",
            location="London, UK",
            start_date="01/2020",
            end_date="Present",
            achievements=[ach],
        )
        assert exp.company == "Acme Corp"
        assert len(exp.achievements) == 1
        assert exp.achievements[0].quantified_impact == "Reduced latency by 40%"


class TestSkills:
    def test_default_empty(self):
        sk = Skills()
        assert sk.technical == []
        assert sk.soft == []
        assert sk.languages == []
        assert sk.certifications == []

    def test_technical_skills(self):
        sk = Skills(
            technical=[TechnicalSkill(name="Python", proficiency="Expert")],
            soft=["Communication"],
            languages=[Language(name="English", proficiency="Native")],
        )
        assert sk.technical[0].name == "Python"
        assert sk.languages[0].proficiency == "Native"


class TestProject:
    def test_valid(self):
        proj = Project(
            name="CV Builder",
            description="A CLI tool.",
            technologies="Python, Rich",
            role="Lead Developer",
            outcomes="Shipped to 100 users",
        )
        assert proj.link is None


class TestUserProfile:
    def test_default_empty(self):
        profile = UserProfile()
        assert profile.personal_info is None
        assert profile.education == []
        assert profile.work_experience == []

    def test_serialization_roundtrip(self):
        """Profile can be serialized to JSON and back."""
        profile = UserProfile(
            personal_info=PersonalInfo(
                full_name="Test User",
                email="test@example.com",
                phone="0123456789",
                location="Paris, France",
            )
        )
        json_str = profile.model_dump_json()
        restored = UserProfile.model_validate_json(json_str)
        assert restored.personal_info.full_name == "Test User"
