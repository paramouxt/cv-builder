"""Tests for the optional LLM provider seam."""

import sys
import types

from cv_builder.llm.provider import ClaudeProvider, NullProvider, get_provider


def test_null_provider_is_noop():
    provider = NullProvider()

    assert provider.enrich_summary(None, None, None) is None
    assert provider.rewrite_bullets(["Built a model"], None) is None


def test_get_provider_returns_null_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    assert isinstance(get_provider(), NullProvider)


def test_claude_provider_parses_json_bullet_response(monkeypatch):
    class Messages:
        def create(self, **kwargs):
            block = types.SimpleNamespace(type="text", text='["Sharper bullet"]')
            return types.SimpleNamespace(content=[block])

    class Anthropic:
        def __init__(self, api_key=None):
            self.messages = Messages()

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=Anthropic))
    provider = ClaudeProvider(api_key="test-key")

    rewritten = provider.rewrite_bullets(["Original bullet"], types.SimpleNamespace(title="Role", keywords=[]))

    assert rewritten == ["Sharper bullet"]


def test_claude_provider_fails_safely_on_bad_json(monkeypatch):
    class Messages:
        def create(self, **kwargs):
            block = types.SimpleNamespace(type="text", text="not json")
            return types.SimpleNamespace(content=[block])

    class Anthropic:
        def __init__(self, api_key=None):
            self.messages = Messages()

    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=Anthropic))
    provider = ClaudeProvider(api_key="test-key")

    assert provider.rewrite_bullets(["Original bullet"], types.SimpleNamespace(title="Role", keywords=[])) is None
