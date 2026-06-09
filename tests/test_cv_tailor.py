"""Tests for deterministic CV tailoring."""

from cv_builder.cv_tailor import MAX_BULLETS_PER_ROLE, MAX_PROJECTS, tailor
from cv_builder.jd_models import JobDescription, Requirement, RequirementKind
from cv_builder.models import (
    Achievement,
    PersonalInfo,
    Project,
    Skills,
    TechnicalSkill,
    UserProfile,
    WorkExperience,
)


def _profile() -> UserProfile:
    return UserProfile(
        personal_info=PersonalInfo(
            full_name="Test User",
            email="test@example.com",
            phone="0123456789",
            location="Oxford, UK",
        ),
        skills=Skills(
            technical=[
                TechnicalSkill(name="Excel", proficiency="Advanced"),
                TechnicalSkill(name="Python", proficiency="Advanced"),
                TechnicalSkill(name="PyTorch", proficiency="Intermediate"),
            ]
        ),
        work_experience=[
            WorkExperience(
                job_title="Analyst",
                company="Acme",
                location="London",
                start_date="01/2024",
                end_date="Present",
                achievements=[
                    Achievement(description="Managed stakeholder reporting"),
                    Achievement(description="Built PyTorch model in Python", tools_used="Python, PyTorch"),
                    Achievement(description="Created Excel tracker"),
                    Achievement(description="Wrote SQL checks", tools_used="SQL"),
                    Achievement(description="Coordinated team notes"),
                ],
            )
        ],
        projects=[
            Project(
                name="Admin Tool",
                description="Internal workflow app",
                technologies="Excel",
                role="Developer",
                outcomes="Shipped",
            ),
            Project(
                name="ML Risk Model",
                description="Machine learning model for risk",
                technologies="Python, PyTorch",
                role="Developer",
                outcomes="Validated model",
            ),
            Project(name="One", description="x", technologies="x", role="x", outcomes="x"),
            Project(name="Two", description="x", technologies="x", role="x", outcomes="x"),
            Project(name="Three", description="x", technologies="x", role="x", outcomes="x"),
        ],
    )


def _jd() -> JobDescription:
    return JobDescription(
        raw_text="",
        title="Machine Learning Engineer",
        requirements=[
            Requirement(keyword="python", kind=RequirementKind.MUST_HAVE),
            Requirement(keyword="pytorch", kind=RequirementKind.MUST_HAVE),
            Requirement(keyword="machine learning", kind=RequirementKind.PREFERRED),
            Requirement(keyword="sql", kind=RequirementKind.PREFERRED),
        ],
        keywords=["python", "pytorch", "machine learning", "sql"],
    )


def test_tailor_front_loads_relevant_skills_bullets_and_projects():
    result = tailor(_profile(), _jd())
    tailored = result.profile

    assert [s.name for s in tailored.skills.technical[:2]] == ["Python", "PyTorch"]
    assert len(tailored.work_experience[0].achievements) == MAX_BULLETS_PER_ROLE
    assert tailored.work_experience[0].achievements[0].description == "Built PyTorch model in Python"
    assert len(tailored.projects) == MAX_PROJECTS
    assert tailored.projects[0].name == "ML Risk Model"
    assert any("Reordered bullets" in change.change for change in result.changes)


def test_tailor_keeps_original_profile_unchanged():
    profile = _profile()

    tailor(profile, _jd())

    assert [s.name for s in profile.skills.technical] == ["Excel", "Python", "PyTorch"]
    assert len(profile.work_experience[0].achievements) == 5


def test_provider_rewrites_bullet_phrasing_when_lengths_match():
    class Provider:
        def rewrite_bullets(self, bullets, jd):
            return [f"Rewritten: {bullet}" for bullet in bullets]

    result = tailor(_profile(), _jd(), provider=Provider())

    assert result.profile.work_experience[0].achievements[0].description.startswith("Rewritten: ")
    assert any("Rewrote" in change.change for change in result.changes)
