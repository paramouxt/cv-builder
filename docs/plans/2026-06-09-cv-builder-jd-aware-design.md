# Design: JD-aware CV assistant for cv-builder

**Date:** 2026-06-09
**Status:** Approved
**Author:** Piyush Jain Sanjay (with Claude)

## Goal

Make `cv-builder` impressive to recruiters by adding two capabilities adapted from the
`job-application-pipeline` skill, then ship it as a polished, public GitHub repo:

1. **JD fit scoring** — paste a job description, get a 0–100 fit score with a category
   breakdown and an honest summary.
2. **CV tailoring to a JD** — reorder/trim/surface CV content to target a specific JD and
   emit a tailored `.docx`.

Constraints from the brainstorm:

- **Deterministic by default.** All scoring/tailoring runs in pure Python — free, offline,
  no API key required.
- **Optional Claude hook.** A clean provider seam lets the user plug in the Claude API later
  for richer feedback. The base install has zero AI dependencies.
- **Primary output is `.docx`** (best for ATS, matches the pipeline). Existing PDF/text
  generators are kept as secondary options, not deleted.
- **Excellent, published repo.** README, tests, CI, license, demo command.
- Website wiring is **out of scope** for this round (the user builds that separately).

## Chosen approach: additive JD-targeting layer (Approach A)

New modules consume the existing `UserProfile`. The current catalog recommender
("which roles suit me?") is left untouched; the new flow answers a different question
("how do I fit *this* job, and tailor my CV to it?"). Lowest risk, clean separation, one
obvious place to inject the optional LLM.

Rejected: (B) merging the catalog recommender and JD scorer into one engine — more churn,
no demo benefit now; (C) treating a JD as a synthetic catalog role — conflates two different
problems and yields a weaker breakdown.

## Architecture

```
raw JD text ──► jd_analyzer ──► JobDescription ┐
                                               ├─► fit_scorer ─► FitScore
UserProfile ───────────────────────────────────┘
                                               └─► cv_tailor ─► TailoredCV ─► DocxGenerator ─► .docx
        (optional) LLMProvider enriches both steps when ANTHROPIC_API_KEY is set
```

### New modules (in `cv_builder/`)

- **`jd_analyzer.py`** — `analyze_jd(text: str) -> JobDescription`. Deterministic extraction:
  - title (heuristic: first strong line / "role:"/"position:" patterns)
  - required vs. preferred vs. nice-to-have, by section/keyword cues
    ("required", "must have", "you have" vs. "preferred", "nice to have", "bonus")
  - skills/keywords matched against a skill lexicon (seeded from `constants.py` +
    a curated additions list, e.g. ML/LLM/NLP terms)
  - years-of-experience via regex
  - retains the raw text for ATS keyword matching

- **`fit_scorer.py`** — `score_fit(profile, jd, provider=None) -> FitScore`. The pipeline's
  four weighted categories: **Skills 40 / Experience 30 / ATS keywords 20 / Structural 10**.
  Reuses `job_recommender._extract_profile_keywords`. Produces per-category sub-scores, a
  threshold band (Strong 80+ / Competitive 65–79 / Stretch 50–64 / Poor <50), and an honest
  summary. `provider` (if present) rewrites the summary into sharper prose.

- **`cv_tailor.py`** — `tailor(profile, jd, provider=None) -> TailoredCV`. Deterministic:
  - reorder sections + bullets so the most JD-relevant content is front-loaded
  - select the top-N most relevant bullets per role (trim noise)
  - surface matching skills using the JD's exact terminology
  - returns a tailored `UserProfile` (flows into the generators) **plus a change-log**
    (list of `(change, why)`) — a strong demo artifact
  - `provider` (if present) rewrites bullet phrasing (XYZ/CAR frameworks); deterministic
    mode reorders/selects only, never fabricates

- **`docx_generator.py`** — `DocxGenerator(profile).generate(path)` using `python-docx`.
  Single-column, standard headings, no tables/text-boxes (ATS-safe), 11pt Calibri/Arial.
  Primary output for tailored CVs.

- **`llm/` package**
  - `provider.py` — `LLMProvider` protocol (`enrich_summary`, `rewrite_bullets`);
    `NullProvider` (deterministic no-op, default); `ClaudeProvider` (uses the `anthropic`
    SDK only if installed *and* `ANTHROPIC_API_KEY` set).
  - `get_provider()` factory: returns `ClaudeProvider` when available, else `NullProvider`.

### New data models (`cv_builder/jd_models.py`)

`JobDescription`, `Requirement`, `CategoryScore`, `FitScore`, `TailoredCV` — all pydantic,
consistent with the existing models.

### CLI + scripting

Add an `argparse` layer (entry point stays `cv_builder.main:main`):

- `cv-builder` — interactive flow (unchanged), with two new menu items:
  "Score against a job description" and "Tailor my CV to a job".
- `cv-builder demo` — loads bundled sample profile + sample JD, runs scoring + tailoring
  non-interactively, writes a tailored `.docx`. The "show a recruiter in 5 seconds" path.
- `cv-builder score --profile p.json --jd jd.txt`
- `cv-builder tailor --profile p.json --jd jd.txt -o out/`

Add JSON **save/load** for `UserProfile` (`utils.save_profile` / `load_profile`), needed by
the demo and the scripted subcommands.

### Demo assets (`examples/`)

- `sample_profile.json` — Piyush's **real professional story** (name, Oxford Brookes BSc AI
  2023–2027 predicted First, Curriculum Consultant / Treasurer / Student Ambassador roles,
  Python/Java/C/C++ skills, projects, languages). **Privacy:** city + country + LinkedIn
  only — no home address, phone, or personal email in the public repo.
- `sample_jd.txt` — a realistic graduate ML/AI engineer JD.

## Repo polish

- **README** rewrite: features, the deterministic-with-optional-LLM design as a selling
  point, quickstart, `cv-builder demo`, example output, architecture diagram.
- **Tests**: `test_jd_analyzer.py`, `test_fit_scorer.py`, `test_cv_tailor.py`,
  `test_docx_generator.py`, `test_llm_provider.py` (NullProvider + mocked ClaudeProvider).
  Deterministic engine ⇒ no network/key needed in CI.
- **CI**: GitHub Actions running `pytest` + `ruff` on push/PR.
- **Packaging**: `pyproject.toml` version bump (→ 2.0.0), optional `[ai]` extra for
  `anthropic`, `python-docx` dependency, ruff config, project URLs; add `LICENSE` (MIT) if
  absent.

## Error handling

- Empty/garbage JD → analyzer returns a low-confidence `JobDescription`; scorer reports a
  low score with a "couldn't extract requirements" note rather than crashing.
- Missing `python-docx` → clear install hint.
- `ClaudeProvider` errors (no key, network, rate limit) → silently fall back to deterministic
  output; never block the core flow.

## Out of scope (YAGNI)

Company research / web fetch, cover-letter generation, Cowork auto-fill block, the website
integration, and multi-page CV layout. Can be added later behind the same seams.
