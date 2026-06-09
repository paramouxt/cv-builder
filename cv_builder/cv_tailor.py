"""Deterministic CV tailoring against a job description.

Reshapes a :class:`~cv_builder.models.UserProfile` so the content most relevant
to a specific JD is front-loaded, trimmed to what fits a focused one-page CV, and
ordered for a recruiter's 6-second scan. It never invents skills or metrics — it
only reorders, trims, and surfaces what is already there.

If an optional LLM provider is supplied it may rewrite bullet *phrasing*; the
deterministic path leaves wording untouched.
"""

from __future__ import annotations

from cv_builder.fit_scorer import _matches
from cv_builder.jd_models import JobDescription, TailorChange, TailoredCV
from cv_builder.models import UserProfile

MAX_BULLETS_PER_ROLE = 4
MAX_PROJECTS = 4


def _relevance(text: str, keywords: list[str]) -> int:
    """How many JD keywords appear in ``text`` (boundary-aware)."""
    low = text.lower()
    return sum(1 for k in keywords if _matches(k, low))


def _skill_is_relevant(name: str, keywords: list[str]) -> bool:
    low = name.lower()
    return low in keywords or any(_matches(k, low) for k in keywords)


def tailor(profile: UserProfile, jd: JobDescription, provider=None) -> TailoredCV:
    """Return a JD-tailored copy of ``profile`` plus a change-log."""
    tp = profile.model_copy(deep=True)
    changes: list[TailorChange] = []
    kws = jd.keywords
    role = jd.title or "the target role"

    # 1. Lead the skills list with JD-relevant skills (stable order otherwise).
    if tp.skills.technical and kws:
        relevant = [s for s in tp.skills.technical if _skill_is_relevant(s.name, kws)]
        rest = [s for s in tp.skills.technical if not _skill_is_relevant(s.name, kws)]
        if relevant and rest:
            tp.skills.technical = relevant + rest
            changes.append(
                TailorChange(
                    change=f"Moved {', '.join(s.name for s in relevant[:5])} to the front of Skills",
                    reason=f"These are named or implied in the JD for {role}; lead with the match.",
                )
            )

    # 2. Within each role, order bullets by JD relevance and trim to fit one page.
    for exp in tp.work_experience:
        if not exp.achievements:
            continue
        original = list(exp.achievements)
        ranked = sorted(
            original,
            key=lambda a: _relevance(_achievement_text(a), kws),
            reverse=True,
        )
        trimmed = ranked[:MAX_BULLETS_PER_ROLE]
        if ranked != original:
            changes.append(
                TailorChange(
                    change=f"Reordered bullets under {exp.job_title} @ {exp.company} by JD relevance",
                    reason="Recruiters scan top-down; the most relevant evidence should come first.",
                )
            )
        if len(original) > MAX_BULLETS_PER_ROLE:
            changes.append(
                TailorChange(
                    change=f"Trimmed {exp.job_title} from {len(original)} to {MAX_BULLETS_PER_ROLE} bullets",
                    reason="A focused one-page CV has room for only the strongest, most relevant lines.",
                )
            )
        exp.achievements = trimmed

    # 3. Order projects by relevance; keep the most relevant few.
    if tp.projects and kws:
        original = list(tp.projects)
        ranked = sorted(
            original,
            key=lambda p: _relevance(_project_text(p), kws),
            reverse=True,
        )
        kept = ranked[:MAX_PROJECTS]
        if ranked != original:
            changes.append(
                TailorChange(
                    change="Reordered projects to lead with the most JD-relevant work",
                    reason=f"Projects that demonstrate what {role} needs earn their place at the top.",
                )
            )
        if len(original) > MAX_PROJECTS:
            changes.append(
                TailorChange(
                    change=f"Kept the top {MAX_PROJECTS} of {len(original)} projects",
                    reason="Only projects that fill a gap the JD cares about make the cut.",
                )
            )
        tp.projects = kept

    # 4. Optional LLM bullet rewriting (phrasing only; never invents content).
    if provider is not None:
        _apply_provider_rewrite(tp, jd, provider, changes)

    if not changes:
        changes.append(
            TailorChange(
                change="No structural changes needed",
                reason="The profile already leads with the content most relevant to this JD.",
            )
        )

    return TailoredCV(profile=tp, target_title=jd.title, changes=changes)


def _achievement_text(achievement) -> str:
    parts = [achievement.description]
    if achievement.outcome:
        parts.append(achievement.outcome)
    if achievement.quantified_impact:
        parts.append(achievement.quantified_impact)
    if achievement.tools_used:
        parts.append(achievement.tools_used)
    return " ".join(parts)


def _project_text(project) -> str:
    parts = [project.name, project.role, project.description, project.technologies, project.outcomes]
    if project.problem_solved:
        parts.append(project.problem_solved)
    return " ".join(parts)


def _apply_provider_rewrite(tp: UserProfile, jd: JobDescription, provider, changes) -> None:
    bullets: list[str] = []
    index: list[tuple[int, int]] = []  # (exp_idx, ach_idx)
    for ei, exp in enumerate(tp.work_experience):
        for ai, ach in enumerate(exp.achievements):
            bullets.append(ach.description)
            index.append((ei, ai))
    if not bullets:
        return
    try:
        rewritten = provider.rewrite_bullets(bullets, jd)
    except Exception:
        return
    if not rewritten or len(rewritten) != len(bullets):
        return
    for (ei, ai), text in zip(index, rewritten, strict=True):
        if text and text.strip():
            tp.work_experience[ei].achievements[ai].description = text.strip()
    changes.append(
        TailorChange(
            change=f"Rewrote {len(bullets)} bullets with the Claude API for sharper, JD-aligned phrasing",
            reason="An API key was configured, so the optional LLM pass refined wording (content unchanged).",
        )
    )
