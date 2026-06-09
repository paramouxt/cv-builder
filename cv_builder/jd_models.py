"""Data models for job-description analysis, fit scoring, and CV tailoring.

These sit alongside the profile models in ``models.py``. They describe the
*target* of an application (a parsed job description) and the artifacts produced
when a :class:`~cv_builder.models.UserProfile` is measured and tailored against
that target.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from cv_builder.models import UserProfile


class RequirementKind(str, Enum):
    """How strongly a job description asks for something."""

    MUST_HAVE = "must_have"
    PREFERRED = "preferred"
    NICE_TO_HAVE = "nice_to_have"


class Requirement(BaseModel):
    """A single skill/keyword extracted from a job description."""

    keyword: str
    kind: RequirementKind = RequirementKind.PREFERRED


class JobDescription(BaseModel):
    """A job description parsed into structured, scoreable parts."""

    raw_text: str
    title: str | None = None
    company: str | None = None
    years_required: int | None = None
    requirements: list[Requirement] = []
    # Distinct, lowercased keywords worth matching against for ATS purposes.
    keywords: list[str] = []

    def keywords_by_kind(self, kind: RequirementKind) -> list[str]:
        return [r.keyword for r in self.requirements if r.kind == kind]

    @property
    def must_haves(self) -> list[str]:
        return self.keywords_by_kind(RequirementKind.MUST_HAVE)

    @property
    def preferred(self) -> list[str]:
        return self.keywords_by_kind(RequirementKind.PREFERRED)

    @property
    def nice_to_have(self) -> list[str]:
        return self.keywords_by_kind(RequirementKind.NICE_TO_HAVE)


class CategoryScore(BaseModel):
    """One weighted row of the fit-score breakdown."""

    name: str
    score: int       # points awarded
    max_score: int   # points available (the category weight)
    note: str = ""


class FitBand(str, Enum):
    """Coarse recommendation band derived from the overall score."""

    STRONG = "Strong"
    COMPETITIVE = "Competitive"
    STRETCH = "Stretch"
    POOR = "Poor"


class FitScore(BaseModel):
    """The result of scoring a profile against a job description."""

    overall: int
    band: FitBand
    categories: list[CategoryScore] = []
    matched_keywords: list[str] = []
    missing_keywords: list[str] = []
    summary: str = ""


class TailorChange(BaseModel):
    """One entry in the tailoring change-log: what changed and why."""

    change: str
    reason: str


class TailoredCV(BaseModel):
    """A profile reshaped for a specific job description, plus an audit trail."""

    profile: UserProfile
    target_title: str | None = None
    changes: list[TailorChange] = []
