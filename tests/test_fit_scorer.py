"""Tests for deterministic JD fit scoring."""

from pathlib import Path

from cv_builder.fit_scorer import _matches, score_fit
from cv_builder.jd_analyzer import analyze_jd
from cv_builder.jd_models import FitBand
from cv_builder.models import UserProfile

ROOT = Path(__file__).resolve().parents[1]


def _sample_profile() -> UserProfile:
    return UserProfile.model_validate_json(
        (ROOT / "cv_builder" / "sample_data" / "sample_profile.json").read_text(encoding="utf-8")
    )


def _sample_jd():
    return analyze_jd(
        (ROOT / "cv_builder" / "sample_data" / "sample_jd.txt").read_text(encoding="utf-8")
    )


def test_score_fit_matches_sample_demo_score():
    fit = score_fit(_sample_profile(), _sample_jd())

    assert fit.overall == 60
    assert fit.band == FitBand.STRETCH
    assert [(c.name, c.score, c.max_score) for c in fit.categories] == [
        ("Skills match", 25, 40),
        ("Experience relevance", 15, 30),
        ("ATS keywords", 10, 20),
        ("Structural fit", 10, 10),
    ]
    assert "python" in fit.matched_keywords
    assert "docker" in fit.missing_keywords


def test_optional_provider_can_only_rewrite_summary():
    class Provider:
        def enrich_summary(self, fit, jd, profile):
            return "Custom summary."

    fit = score_fit(_sample_profile(), _sample_jd(), provider=Provider())

    assert fit.overall == 60
    assert fit.summary == "Custom summary."


def test_match_boundaries_allow_punctuation_but_not_substrings():
    assert _matches("pytorch", "Built models with PyTorch.")
    assert _matches("c++", "Production C++, Python")
    assert not _matches("r", "risk management")
