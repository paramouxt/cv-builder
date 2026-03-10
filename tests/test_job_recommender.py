"""Tests for the job recommender engine."""

import pytest
from cv_builder.job_recommender import (
    recommend_jobs,
    suggest_industries,
    _extract_profile_keywords,
)
from cv_builder.models import (
    Achievement,
    Certification,
    JobPreferences,
    Language,
    PersonalInfo,
    Project,
    Skills,
    TechnicalSkill,
    UserProfile,
    WorkExperience,
)


def _make_profile(**kwargs) -> UserProfile:
    """Helper to build a UserProfile with sane defaults."""
    defaults = dict(
        personal_info=PersonalInfo(
            full_name="Test User",
            email="test@example.com",
            phone="0123456789",
            location="London, UK",
        ),
        skills=Skills(
            technical=[
                TechnicalSkill(name="Python", proficiency="Advanced"),
                TechnicalSkill(name="SQL", proficiency="Intermediate"),
            ],
            soft=["Communication"],
        ),
    )
    defaults.update(kwargs)
    return UserProfile(**defaults)


class TestExtractProfileKeywords:
    def test_includes_technical_skills(self):
        profile = _make_profile()
        kws = _extract_profile_keywords(profile)
        assert "python" in kws
        assert "sql" in kws

    def test_includes_soft_skills(self):
        profile = _make_profile()
        kws = _extract_profile_keywords(profile)
        assert "communication" in kws

    def test_includes_project_technologies(self):
        profile = _make_profile(
            projects=[
                Project(
                    name="Demo",
                    description="A demo project",
                    technologies="Docker, Kubernetes",
                    role="Dev",
                    outcomes="Done",
                )
            ]
        )
        kws = _extract_profile_keywords(profile)
        assert "docker" in kws
        assert "kubernetes" in kws

    def test_includes_work_experience_tools(self):
        profile = _make_profile(
            work_experience=[
                WorkExperience(
                    job_title="Engineer",
                    company="Acme",
                    location="London",
                    start_date="2020",
                    end_date="Present",
                    achievements=[
                        Achievement(
                            description="Built APIs",
                            tools_used="FastAPI, Redis",
                        )
                    ],
                )
            ]
        )
        kws = _extract_profile_keywords(profile)
        assert "fastapi" in kws
        assert "redis" in kws


class TestRecommendJobs:
    def test_returns_list(self):
        profile = _make_profile()
        recs = recommend_jobs(profile)
        assert isinstance(recs, list)

    def test_sorted_by_score_desc(self):
        profile = _make_profile()
        recs = recommend_jobs(profile)
        scores = [r.match_score for r in recs]
        assert scores == sorted(scores, reverse=True)

    def test_top_n_limit(self):
        profile = _make_profile()
        recs = recommend_jobs(profile, top_n=3)
        assert len(recs) <= 3

    def test_scores_within_range(self):
        profile = _make_profile()
        for rec in recommend_jobs(profile):
            assert 0 <= rec.match_score <= 100

    def test_desired_role_boosts_score(self):
        """A profile that explicitly targets a role should score at least as well."""
        base_profile = _make_profile()
        base_recs = {r.title: r.match_score for r in recommend_jobs(base_profile)}

        targeted_profile = _make_profile(
            job_preferences=JobPreferences(desired_roles=["Data Scientist"])
        )
        targeted_recs = {r.title: r.match_score for r in recommend_jobs(targeted_profile)}

        # Data Scientist score should not decrease when targeting it
        if "Data Scientist" in base_recs and "Data Scientist" in targeted_recs:
            assert targeted_recs["Data Scientist"] >= base_recs["Data Scientist"]

    def test_low_relevance_profile_may_return_empty(self):
        """A profile with zero skills still returns a list (possibly empty)."""
        empty_profile = UserProfile()
        recs = recommend_jobs(empty_profile)
        assert isinstance(recs, list)


class TestSuggestIndustries:
    def test_returns_list(self):
        profile = _make_profile()
        industries = suggest_industries(profile)
        assert isinstance(industries, list)

    def test_max_five(self):
        profile = _make_profile()
        assert len(suggest_industries(profile)) <= 5

    def test_technology_for_python_dev(self):
        profile = _make_profile(
            skills=Skills(
                technical=[
                    TechnicalSkill(name="Python", proficiency="Expert"),
                    TechnicalSkill(name="AWS", proficiency="Intermediate"),
                    TechnicalSkill(name="Docker", proficiency="Intermediate"),
                    TechnicalSkill(name="SQL", proficiency="Advanced"),
                    TechnicalSkill(name="Git", proficiency="Advanced"),
                ]
            )
        )
        industries = suggest_industries(profile)
        assert "Technology" in industries
