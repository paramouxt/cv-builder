"""Deterministic fit scoring of a profile against a job description.

Produces a 0-100 score with the four-category breakdown used by the
job-application pipeline:

    Skills match      40%  - does the profile hold the skills the JD asks for?
    Experience        30%  - do past roles/projects map to what the job needs?
    ATS keywords      20%  - do JD keywords appear anywhere in the profile?
    Structural fit    10%  - education, and years-of-experience vs. requirement.

Everything here is deterministic and offline. If an optional LLM provider is
passed, it is given the chance to rewrite the prose summary — but never the
numbers.
"""

from __future__ import annotations

import re

from cv_builder.jd_models import (
    CategoryScore,
    FitBand,
    FitScore,
    JobDescription,
    RequirementKind,
)
from cv_builder.job_recommender import _estimate_years_experience
from cv_builder.models import UserProfile

_KIND_WEIGHT = {
    RequirementKind.MUST_HAVE: 3,
    RequirementKind.PREFERRED: 2,
    RequirementKind.NICE_TO_HAVE: 1,
}


def _pattern(term: str) -> re.Pattern[str]:
    # Boundaries exclude only alphanumerics, so terms match next to punctuation
    # (e.g. "PyTorch.") while c++, ci/cd, node.js still match as whole tokens.
    escaped = re.escape(term)
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")


def _matches(term: str, text: str) -> bool:
    return _pattern(term).search(text.lower()) is not None


# ─── Profile text surfaces ───────────────────────────────────────────────────

def _skills_text(profile: UserProfile) -> str:
    parts: list[str] = []
    parts += [s.name for s in profile.skills.technical]
    parts += [c.name for c in profile.skills.certifications]
    for proj in profile.projects:
        parts.append(proj.technologies)
    for exp in profile.work_experience:
        for ach in exp.achievements:
            if ach.tools_used:
                parts.append(ach.tools_used)
    return " ; ".join(parts).lower()


def _experience_text(profile: UserProfile) -> str:
    parts: list[str] = []
    for exp in profile.work_experience:
        parts.append(exp.job_title)
        for ach in exp.achievements:
            parts.append(ach.description)
            if ach.outcome:
                parts.append(ach.outcome)
            if ach.quantified_impact:
                parts.append(ach.quantified_impact)
            if ach.tools_used:
                parts.append(ach.tools_used)
    for proj in profile.projects:
        parts += [proj.name, proj.role, proj.description, proj.outcomes, proj.technologies]
        if proj.problem_solved:
            parts.append(proj.problem_solved)
    return " ; ".join(parts).lower()


def _full_text(profile: UserProfile) -> str:
    parts: list[str] = [_skills_text(profile), _experience_text(profile)]
    pi = profile.personal_info
    if pi and pi.summary:
        parts.append(pi.summary)
    for edu in profile.education:
        parts += [edu.degree, edu.field_of_study, edu.institution]
        if edu.notable_coursework:
            parts.append(edu.notable_coursework)
    parts += profile.skills.soft
    return " ; ".join(parts).lower()


# ─── Category scorers ────────────────────────────────────────────────────────

def _score_skills(jd: JobDescription, skills_text: str, full_text: str) -> CategoryScore:
    reqs = jd.requirements
    if not reqs:
        return CategoryScore(
            name="Skills match", score=20, max_score=40,
            note="No specific skills could be extracted from the JD.",
        )
    total = sum(_KIND_WEIGHT[r.kind] for r in reqs)
    matched_weight = 0
    matched: list[str] = []
    for r in reqs:
        if _matches(r.keyword, skills_text) or _matches(r.keyword, full_text):
            matched_weight += _KIND_WEIGHT[r.kind]
            matched.append(r.keyword)
    score = round(matched_weight / total * 40) if total else 0
    note = (
        f"{len(matched)}/{len(reqs)} listed skills present"
        + (f" ({', '.join(matched[:4])}...)" if matched else "")
    )
    return CategoryScore(name="Skills match", score=score, max_score=40, note=note)


def _score_experience(
    jd: JobDescription, profile: UserProfile, experience_text: str
) -> CategoryScore:
    keywords = jd.keywords
    if keywords:
        present = [k for k in keywords if _matches(k, experience_text)]
        overlap = len(present) / len(keywords)
    else:
        overlap, present = 0.0, []
    overlap_pts = round(overlap * 18)  # up to 18 of 30

    years = _estimate_years_experience(profile)
    if jd.years_required:
        if years >= jd.years_required:
            years_pts = 12
        elif jd.years_required - years <= 1:
            years_pts = 8
        else:
            years_pts = max(0, round(12 * years / jd.years_required))
        years_note = f"~{years}y vs {jd.years_required}y asked"
    else:
        years_pts = 9  # neutral when the JD states no requirement
        years_note = "no explicit years requirement"

    score = min(30, overlap_pts + years_pts)
    note = f"{len(present)} JD terms evidenced in experience; {years_note}"
    return CategoryScore(name="Experience relevance", score=score, max_score=30, note=note)


def _score_ats(jd: JobDescription, full_text: str) -> tuple[CategoryScore, list[str], list[str]]:
    keywords = jd.keywords
    if not keywords:
        cat = CategoryScore(
            name="ATS keywords", score=10, max_score=20,
            note="No keywords extracted from the JD.",
        )
        return cat, [], []
    matched = [k for k in keywords if _matches(k, full_text)]
    missing = [k for k in keywords if k not in matched]
    score = round(len(matched) / len(keywords) * 20)
    note = f"{len(matched)}/{len(keywords)} JD keywords found in the profile"
    return CategoryScore(name="ATS keywords", score=score, max_score=20, note=note), matched, missing


def _score_structural(jd: JobDescription, profile: UserProfile) -> CategoryScore:
    score = 0
    notes: list[str] = []
    if profile.education:
        score += 4
        notes.append("education present")
    if profile.work_experience or profile.projects:
        score += 3
        notes.append("relevant experience/projects")
    years = _estimate_years_experience(profile)
    if jd.years_required:
        if years >= jd.years_required:
            score += 3
            notes.append("meets years requirement")
        else:
            notes.append("below stated years requirement")
    else:
        score += 3
    return CategoryScore(
        name="Structural fit", score=min(10, score), max_score=10,
        note="; ".join(notes) or "limited structural signal",
    )


def _band(overall: int) -> FitBand:
    if overall >= 80:
        return FitBand.STRONG
    if overall >= 65:
        return FitBand.COMPETITIVE
    if overall >= 50:
        return FitBand.STRETCH
    return FitBand.POOR


def _default_summary(
    fit_overall: int, band: FitBand, jd: JobDescription,
    matched: list[str], missing_must: list[str],
) -> str:
    role = jd.title or "this role"
    lead = {
        FitBand.STRONG: f"Strong fit for {role} — worth a tailored application.",
        FitBand.COMPETITIVE: f"Competitive for {role} if the CV is well tailored.",
        FitBand.STRETCH: f"A stretch for {role}; apply if it's a priority target.",
        FitBand.POOR: f"Weak fit for {role} as things stand.",
    }[band]
    bits = [lead]
    if matched:
        bits.append(f"Clear overlap on {', '.join(matched[:4])}.")
    if missing_must:
        bits.append(f"Main gaps: {', '.join(missing_must[:4])}.")
    return " ".join(bits)


def score_fit(
    profile: UserProfile, jd: JobDescription, provider=None
) -> FitScore:
    """Score ``profile`` against ``jd`` and return a :class:`FitScore`."""
    skills_text = _skills_text(profile)
    experience_text = _experience_text(profile)
    full_text = _full_text(profile)

    skills_cat = _score_skills(jd, skills_text, full_text)
    exp_cat = _score_experience(jd, profile, experience_text)
    ats_cat, matched, missing = _score_ats(jd, full_text)
    struct_cat = _score_structural(jd, profile)

    categories = [skills_cat, exp_cat, ats_cat, struct_cat]
    overall = min(100, sum(c.score for c in categories))
    band = _band(overall)

    missing_must = [k for k in jd.must_haves if k in missing]
    summary = _default_summary(overall, band, jd, matched, missing_must)

    fit = FitScore(
        overall=overall,
        band=band,
        categories=categories,
        matched_keywords=matched,
        missing_keywords=missing,
        summary=summary,
    )

    if provider is not None:
        try:
            enriched = provider.enrich_summary(fit, jd, profile)
            if enriched:
                fit.summary = enriched.strip()
        except Exception:
            pass  # never let the optional path break scoring
    return fit
