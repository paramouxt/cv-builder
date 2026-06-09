"""Deterministic job-description analyzer.

Turns raw JD text into a structured :class:`~cv_builder.jd_models.JobDescription`
without any network calls or LLM. It extracts the role title, a rough
years-of-experience requirement, and a set of skill keywords classified as
must-have / preferred / nice-to-have based on the surrounding wording.

The skill vocabulary is seeded from the role catalogue in ``constants.py`` and
extended with a curated list of modern AI/ML, data, web, and finance terms so
that graduate and AI-focused job descriptions parse well.
"""

from __future__ import annotations

import re

from cv_builder.constants import INDUSTRY_SKILL_MAP, JOB_ROLE_SKILLS
from cv_builder.jd_models import JobDescription, Requirement, RequirementKind

# ─── Skill lexicon ───────────────────────────────────────────────────────────

# Curated additions the role catalogue doesn't already cover well — mostly
# modern AI/ML/LLM, data, and finance terminology relevant to graduate roles.
_EXTRA_SKILLS: set[str] = {
    # languages / core
    "python", "java", "c", "c++", "c#", "go", "rust", "javascript", "typescript",
    "sql", "bash", "scala", "r", "matlab", "kotlin", "swift",
    # ai / ml / nlp
    "machine learning", "deep learning", "nlp", "natural language processing",
    "llm", "llms", "large language models", "transformers", "bert", "finbert",
    "gpt", "hugging face", "huggingface", "pytorch", "tensorflow", "keras",
    "scikit-learn", "sklearn", "xgboost", "pandas", "numpy", "spacy", "nltk",
    "computer vision", "reinforcement learning", "mlops", "feature engineering",
    "model deployment", "prompt engineering", "rag", "embeddings", "fine-tuning",
    "anthropic", "claude", "openai", "langchain", "vector database",
    # data / cloud / tooling
    "data analysis", "data science", "etl", "data pipelines", "airflow", "spark",
    "kafka", "snowflake", "bigquery", "tableau", "power bi", "excel", "jupyter",
    "git", "github", "gitlab", "docker", "kubernetes", "aws", "gcp", "azure",
    "linux", "ci/cd", "rest api", "graphql", "fastapi", "flask", "django",
    # web
    "react", "node.js", "vue", "angular", "html", "css", "tailwind",
    # finance / quant
    "financial markets", "quantitative analysis", "trading", "equities",
    "risk management", "bloomberg", "time series", "statistics", "econometrics",
    "sentiment analysis", "alpha", "portfolio", "derivatives",
    # general engineering
    "algorithms", "data structures", "object-oriented programming", "oop",
    "agile", "scrum", "testing", "unit testing", "system design", "microservices",
}


def _build_lexicon() -> set[str]:
    lexicon: set[str] = set(_EXTRA_SKILLS)
    for role_data in JOB_ROLE_SKILLS.values():
        for skill in role_data.get("skills", []):
            lexicon.add(skill.lower())
    for skills in INDUSTRY_SKILL_MAP.values():
        for skill in skills:
            lexicon.add(skill.lower())
    return lexicon


SKILL_LEXICON: set[str] = _build_lexicon()


# ─── Section / strength cues ─────────────────────────────────────────────────

_MUST_CUES = (
    "must have", "must-have", "required", "requirement", "essential",
    "you have", "you will need", "what you'll need", "what we're looking for",
    "minimum qualifications", "minimum requirements", "we expect", "you bring",
)
_PREFERRED_CUES = ("preferred", "preferably", "ideally", "we'd love", "advantage")
_NICE_CUES = ("nice to have", "nice-to-have", "bonus", "plus", "desirable", "good to have")


def _line_kind(line_lower: str, current: RequirementKind) -> RequirementKind:
    """Decide the strength of requirements mentioned on a line."""
    if any(cue in line_lower for cue in _NICE_CUES):
        return RequirementKind.NICE_TO_HAVE
    if any(cue in line_lower for cue in _PREFERRED_CUES):
        return RequirementKind.PREFERRED
    if any(cue in line_lower for cue in _MUST_CUES):
        return RequirementKind.MUST_HAVE
    return current


_KIND_STRENGTH = {
    RequirementKind.MUST_HAVE: 3,
    RequirementKind.PREFERRED: 2,
    RequirementKind.NICE_TO_HAVE: 1,
}

_ROLE_NOUNS = (
    "engineer", "developer", "analyst", "scientist", "manager", "intern",
    "graduate", "consultant", "designer", "architect", "researcher",
    "specialist", "lead", "associate", "apprentice",
)


def _keyword_pattern(term: str) -> re.Pattern[str]:
    """Compile a boundary-aware pattern for a (possibly symbol-containing) term.

    Boundaries exclude only alphanumerics, so a term keeps matching when it sits
    next to punctuation (``PyTorch.``, ``Docker,``) while symbol-bearing terms
    like ``c++``, ``ci/cd`` and ``node.js`` still match as whole tokens.
    """
    escaped = re.escape(term)
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")


# Pre-compile patterns once.
_LEXICON_PATTERNS: dict[str, re.Pattern[str]] = {
    term: _keyword_pattern(term) for term in SKILL_LEXICON
}


def _extract_title(text: str) -> str | None:
    explicit = re.search(
        r"(?im)^\s*(?:job\s*title|role|position)\s*[:\-]\s*(.+)$", text
    )
    if explicit:
        return explicit.group(1).strip() or None

    for raw in text.splitlines():
        line = raw.strip(" \t-*•·")
        if not line or len(line) > 80:
            continue
        if any(noun in line.lower() for noun in _ROLE_NOUNS):
            return line

    for raw in text.splitlines():
        line = raw.strip()
        if line:
            return line[:80]
    return None


def _extract_years(text: str) -> int | None:
    matches = re.findall(
        r"(\d+)\s*\+?\s*(?:to|-|–)?\s*(?:\d+\s*)?years?", text.lower()
    )
    years = [int(m) for m in matches if m.isdigit()]
    return min(years) if years else None


def analyze_jd(text: str) -> JobDescription:
    """Parse raw job-description text into a structured :class:`JobDescription`."""
    text = (text or "").strip()
    lowered = text.lower()

    # Walk lines, tracking the current section strength, and collect the
    # strongest kind seen for each lexicon keyword that appears.
    found: dict[str, RequirementKind] = {}
    current = RequirementKind.MUST_HAVE  # body of a JD is requirement-ish by default
    for raw in text.splitlines():
        line_lower = raw.lower()
        if not line_lower.strip():
            continue
        kind = _line_kind(line_lower, current)
        # A short line that is purely a cue acts as a section header.
        if len(line_lower.strip()) <= 40 and any(
            cue in line_lower for cue in _MUST_CUES + _PREFERRED_CUES + _NICE_CUES
        ):
            current = kind
        for term, pattern in _LEXICON_PATTERNS.items():
            if pattern.search(line_lower):
                prev = found.get(term)
                if prev is None or _KIND_STRENGTH[kind] > _KIND_STRENGTH[prev]:
                    found[term] = kind

    # Any lexicon term present in the text but not tied to a line (rare) — catch
    # via a whole-text pass so nothing is missed.
    for term, pattern in _LEXICON_PATTERNS.items():
        if term not in found and pattern.search(lowered):
            found[term] = RequirementKind.PREFERRED

    requirements = [
        Requirement(keyword=term, kind=kind) for term, kind in sorted(found.items())
    ]
    keywords = sorted(found.keys())

    return JobDescription(
        raw_text=text,
        title=_extract_title(text),
        years_required=_extract_years(text),
        requirements=requirements,
        keywords=keywords,
    )
