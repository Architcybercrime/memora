"""Prompt formatting + memory formatter tests."""

from types import SimpleNamespace

from app.agent.graph import _format_memories
from app.agent.prompts import SYSTEM_PROMPT


def test_format_memories_empty():
    assert _format_memories([]) == "(none yet)"


def test_format_memories_rendering():
    fake = [
        SimpleNamespace(id=1, content="likes earl grey", category="preference", score=0.87),
        SimpleNamespace(id=2, content="lives in Berlin", category="fact", score=None),
    ]
    out = _format_memories(fake)
    assert "[1]" in out and "earl grey" in out and "0.87" in out
    assert "[2]" in out and "Berlin" in out and "sim=-" in out


def test_system_prompt_placeholders():
    rendered = SYSTEM_PROMPT.format(time="2026-01-01T00:00:00", memories="(none yet)")
    assert "2026-01-01" in rendered
    assert "save_memory" in rendered and "forget_memory" in rendered
