"""Schema validation tests — pure, no external services."""

import pytest
from pydantic import ValidationError

from app.memory.schemas import ChatMessage, ChatRequest, MemoryIn


def test_memoryin_defaults():
    m = MemoryIn(content="user likes earl grey")
    assert m.category == "general"
    assert m.importance == 0.5
    assert m.context is None


def test_memoryin_importance_bounds():
    MemoryIn(content="x", importance=0.0)
    MemoryIn(content="x", importance=1.0)
    with pytest.raises(ValidationError):
        MemoryIn(content="x", importance=1.5)
    with pytest.raises(ValidationError):
        MemoryIn(content="x", importance=-0.1)


def test_chat_message_roles():
    for role in ("user", "assistant", "system", "tool"):
        ChatMessage(role=role, content="hi")
    with pytest.raises(ValidationError):
        ChatMessage(role="bogus", content="hi")  # type: ignore[arg-type]


def test_chat_request_defaults():
    r = ChatRequest(message="hello")
    assert r.user_id == "default"
    assert r.session_id == "default"
