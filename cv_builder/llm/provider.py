"""LLM provider seam: a deterministic default and an optional Claude provider.

Scoring and tailoring accept an optional ``provider`` argument. The contract is
deliberately tiny — two methods, both allowed to return ``None`` to mean "no
enrichment". This keeps the optional path strictly additive: nothing downstream
depends on it succeeding.
"""

from __future__ import annotations

import json
import os
from typing import Protocol, runtime_checkable

# Default to a small, fast, inexpensive model for enrichment. Override with the
# CV_BUILDER_CLAUDE_MODEL environment variable.
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


@runtime_checkable
class LLMProvider(Protocol):
    """Optional enrichment hooks. Any method may return ``None``."""

    def enrich_summary(self, fit, jd, profile) -> str | None:
        """Return a sharper prose fit-summary, or ``None`` to keep the default."""
        ...

    def rewrite_bullets(self, bullets: list[str], jd) -> list[str] | None:
        """Return rewritten bullets (same length/order), or ``None`` to keep them."""
        ...


class NullProvider:
    """The default. Deterministic — enriches nothing."""

    def enrich_summary(self, fit, jd, profile) -> str | None:
        return None

    def rewrite_bullets(self, bullets: list[str], jd) -> list[str] | None:
        return None


class ClaudeProvider:
    """Uses the Claude API to enrich scoring/tailoring output.

    Created only when ``anthropic`` is importable and an API key is available.
    All network calls are wrapped so a failure degrades silently to the
    deterministic result.
    """

    def __init__(self, model: str | None = None, api_key: str | None = None):
        import anthropic  # imported lazily; only needed on this path

        self.model = model or os.environ.get("CV_BUILDER_CLAUDE_MODEL", DEFAULT_MODEL)
        self._client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    def _complete(self, prompt: str, max_tokens: int = 600) -> str | None:
        try:
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(
                block.text for block in resp.content if getattr(block, "type", "") == "text"
            ).strip()
        except Exception:
            return None

    def enrich_summary(self, fit, jd, profile) -> str | None:
        prompt = (
            "You are an honest HR screener. Write a 2-3 sentence fit summary for a "
            "candidate applying to this role. Be direct, no fluff, no fabrication. "
            "Use British spelling.\n\n"
            f"Role: {jd.title or 'unspecified'}\n"
            f"Overall fit: {fit.overall}/100 ({fit.band.value})\n"
            f"Matched strengths: {', '.join(fit.matched_keywords[:8]) or 'none detected'}\n"
            f"Gaps: {', '.join(fit.missing_keywords[:8]) or 'none detected'}\n\n"
            "Return only the summary text."
        )
        return self._complete(prompt, max_tokens=300)

    def rewrite_bullets(self, bullets: list[str], jd) -> list[str] | None:
        if not bullets:
            return None
        numbered = "\n".join(f"{i + 1}. {b}" for i, b in enumerate(bullets))
        keywords = ", ".join(jd.keywords[:15])
        prompt = (
            "Rewrite each CV bullet to be sharper and aligned to the job below, using "
            "the XYZ formula (accomplished X measured by Y by doing Z) where a metric "
            "exists. Do NOT invent metrics, tools, or claims not already present. Keep "
            "British spelling. Avoid words like 'leveraged', 'spearheaded', 'robust'.\n\n"
            f"Target role: {jd.title or 'unspecified'}\n"
            f"Relevant keywords: {keywords}\n\n"
            f"Bullets:\n{numbered}\n\n"
            'Return ONLY a JSON array of strings, same count and order, e.g. ["...", "..."].'
        )
        raw = self._complete(prompt, max_tokens=1500)
        if not raw:
            return None
        try:
            start, end = raw.index("["), raw.rindex("]") + 1
            parsed = json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            return None
        if isinstance(parsed, list) and len(parsed) == len(bullets):
            return [str(x) for x in parsed]
        return None


def get_provider() -> LLMProvider:
    """Return a Claude provider if available, else the deterministic NullProvider."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return NullProvider()
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return NullProvider()
    try:
        return ClaudeProvider()
    except Exception:
        return NullProvider()
