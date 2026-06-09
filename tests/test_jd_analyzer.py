"""Tests for deterministic job-description parsing."""

from cv_builder.jd_analyzer import analyze_jd
from cv_builder.jd_models import RequirementKind


def test_analyze_jd_extracts_title_years_and_requirement_strengths():
    jd = analyze_jd(
        """
        Job Title: Graduate Machine Learning Engineer

        Essential requirements:
        - Python, PyTorch, and machine learning experience.
        - 2+ years of project or internship experience.

        Preferred:
        - SQL and financial markets knowledge.

        Bonus:
        - Docker or AWS exposure.
        """
    )

    assert jd.title == "Graduate Machine Learning Engineer"
    assert jd.years_required == 2
    assert "python" in jd.must_haves
    assert "pytorch" in jd.must_haves
    assert "sql" in jd.preferred
    assert "financial markets" in jd.preferred
    assert "docker" in jd.nice_to_have
    assert "aws" in jd.nice_to_have


def test_analyze_jd_matches_symbol_terms_next_to_punctuation():
    jd = analyze_jd("We use C++, C#, Node.js, CI/CD, and PyTorch.")

    assert {"c++", "c#", "node.js", "ci/cd", "pytorch"}.issubset(set(jd.keywords))
    assert all(req.kind == RequirementKind.MUST_HAVE for req in jd.requirements)
