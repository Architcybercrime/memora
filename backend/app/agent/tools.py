"""Tools exposed to the LLM.

We use ``@tool`` with a ``RunnableConfig`` so each invocation can read the
calling user from config metadata, rather than trusting the model to pass it.
"""

from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.memory import long_term
from app.memory.schemas import MemoryIn


def _user_id(config: RunnableConfig) -> str:
    md = (config or {}).get("configurable") or {}
    uid = md.get("user_id")
    if not uid:
        raise RuntimeError("user_id missing from runnable config")
    return uid


@tool
async def save_memory(
    content: str,
    context: str | None = None,
    category: str = "general",
    importance: float = 0.5,
    *,
    config: RunnableConfig,
) -> str:
    """Persist one atomic fact about the user for future sessions.

    Args:
        content: The fact / preference, phrased in the third person about the user.
        context: Why you're saving it (optional).
        category: One of preference | fact | project | todo | relationship | general.
        importance: 0.0 - 1.0 self-rated importance.
    """
    mem = await long_term.upsert(
        _user_id(config),
        MemoryIn(content=content, context=context, category=category, importance=importance),
    )
    return f"saved memory #{mem.id}: {mem.content}"


@tool
async def forget_memory(memory_id: int, *, config: RunnableConfig) -> str:
    """Delete a memory by id (use only when the user asks to forget something)."""
    ok = await long_term.delete(_user_id(config), memory_id)
    return f"deleted memory #{memory_id}" if ok else f"no memory #{memory_id} for this user"


TOOLS = [save_memory, forget_memory]
