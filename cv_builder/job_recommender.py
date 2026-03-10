"""Job/Role Recommendation Engine with skill gap analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cv_builder.constants import JOB_ROLE_SKILLS, INDUSTRY_SKILL_MAP, SKILL_GAPS
from cv_builder.models import UserProfile


@dataclass
class JobRecommendation:
    title: str
    match_score: int  # 0-100
    reasons: List[str] = field(default_factory=list)
    skill_gaps: List[str] = field(default_factory=list)
    industries: List[str] = field(default_factory=list)


def _extract_profile_keywords(profile: UserProfile) -> set[str]:
    """Extract all relevant keywords from the user profile as a lowercase set."""
    keywords: set[str] = set()

    # Technical skills
    for skill in profile.skills.technical:
        keywords.add(skill.name.lower())

    # Soft skills
    for skill in profile.skills.soft:
        keywords.add(skill.lower())

    # Job titles from work experience
    for exp in profile.work_experience:
        for word in exp.job_title.lower().split():
            keywords.add(word)
        for ach in exp.achievements:
            for word in ach.description.lower().split():
                keywords.add(word)
            if ach.tools_used:
                for tool in ach.tools_used.lower().split(","):
                    keywords.add(tool.strip())

    # Project technologies
    for proj in profile.projects:
        for tech in proj.technologies.lower().split(","):
            keywords.add(tech.strip())

    # Certifications
    for cert in profile.skills.certifications:
        for word in cert.name.lower().split():
            keywords.add(word)

    return keywords


def _score_role(keywords: set[str], role_data: dict) -> tuple[int, list[str]]:
    """Score a role based on keyword overlap. Returns (score, matched_skills)."""
    role_skills = [s.lower() for s in role_data.get("skills", [])]
    matched = [s for s in role_skills if s in keywords]

    if not role_skills:
        return 0, []

    raw_score = len(matched) / len(role_skills)

    # Bonus for experience keywords
    exp_keywords = [k.lower() for k in role_data.get("experience_keywords", [])]
    exp_match = sum(1 for k in exp_keywords if k in keywords)
    if exp_keywords:
        exp_bonus = (exp_match / len(exp_keywords)) * 0.2
    else:
        exp_bonus = 0.0

    score = min(100, int((raw_score * 0.8 + exp_bonus) * 100))
    return score, matched


def recommend_jobs(profile: UserProfile, top_n: int = 10) -> list[JobRecommendation]:
    """Analyze the user profile and return ranked job recommendations."""
    keywords = _extract_profile_keywords(profile)

    # Factor in desired roles from preferences (boost them)
    desired = [r.lower() for r in profile.job_preferences.desired_roles]

    recommendations: list[JobRecommendation] = []

    for role_title, role_data in JOB_ROLE_SKILLS.items():
        score, matched = _score_role(keywords, role_data)

        # Boost score if it matches a desired role
        if any(d in role_title.lower() or role_title.lower() in d for d in desired):
            score = min(100, score + 15)

        if score < 10:
            continue

        reasons = _build_reasons(role_title, matched, profile)
        gaps = SKILL_GAPS.get(role_title, [])[:3]
        industries = role_data.get("industries", [])

        recommendations.append(
            JobRecommendation(
                title=role_title,
                match_score=score,
                reasons=reasons,
                skill_gaps=gaps,
                industries=industries,
            )
        )

    # Sort by score descending
    recommendations.sort(key=lambda r: r.match_score, reverse=True)
    return recommendations[:top_n]


def _build_reasons(role_title: str, matched_skills: list[str], profile: UserProfile) -> list[str]:
    """Build human-readable reasons for why a role is recommended."""
    reasons: list[str] = []

    if matched_skills:
        skills_str = ", ".join(matched_skills[:5])
        reasons.append(f"Matching skills: {skills_str}")

    years = _estimate_years_experience(profile)
    if years > 0:
        reasons.append(f"~{years} year(s) of relevant experience")

    if profile.projects:
        reasons.append(f"{len(profile.projects)} project(s) demonstrating hands-on work")

    certs = profile.skills.certifications
    if certs:
        reasons.append(f"{len(certs)} certification(s) strengthening your profile")

    return reasons if reasons else ["Your profile shows relevant background for this role"]


def _estimate_years_experience(profile: UserProfile) -> int:
    """Roughly estimate total years of work experience."""
    import datetime

    total_months = 0
    current_year = datetime.datetime.now().year

    for exp in profile.work_experience:
        try:
            start_year = int(exp.start_date.split("/")[-1])
            if exp.end_date.lower() == "present":
                end_year = current_year
            else:
                end_year = int(exp.end_date.split("/")[-1])
            total_months += max(0, (end_year - start_year) * 12)
        except (ValueError, IndexError):
            pass

    return total_months // 12


def suggest_industries(profile: UserProfile) -> list[str]:
    """Suggest relevant industries based on the user's skill set."""
    keywords = _extract_profile_keywords(profile)
    industry_scores: dict[str, int] = {}

    for industry, skills in INDUSTRY_SKILL_MAP.items():
        matched = sum(1 for s in skills if s.lower() in keywords)
        if matched > 0:
            industry_scores[industry] = matched

    sorted_industries = sorted(industry_scores, key=lambda k: industry_scores[k], reverse=True)
    return sorted_industries[:5]
