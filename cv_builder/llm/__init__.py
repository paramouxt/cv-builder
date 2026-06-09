"""Optional LLM enrichment layer.

The whole application runs deterministically with no LLM. This package adds an
*optional* upgrade: when the ``anthropic`` package is installed and an
``ANTHROPIC_API_KEY`` is set, :func:`get_provider` returns a provider that uses
the Claude API to sharpen the fit summary and rewrite CV bullets. Otherwise it
returns a :class:`NullProvider` that changes nothing.
"""

from cv_builder.llm.provider import (
    ClaudeProvider,
    LLMProvider,
    NullProvider,
    get_provider,
)

__all__ = ["LLMProvider", "NullProvider", "ClaudeProvider", "get_provider"]
