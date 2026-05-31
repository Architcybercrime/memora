"""Pydantic schemas for memories and chat."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MemoryIn(BaseModel):
    content: str = Field(..., description="The fact / preference to remember.")
    context: str | None = Field(None, description="Why / when it was learned.")
    category: str = Field("general", description="Category, e.g. preference, fact, todo.")
    importance: float = Field(0.5, ge=0.0, le=1.0)


class Memory(MemoryIn):
    id: int
    user_id: str
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    last_used_at: datetime | None = None
    score: float | None = None  # similarity score when returned from search


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str


class ChatRequest(BaseModel):
    user_id: str = "default"
    session_id: str = "default"
    message: str
