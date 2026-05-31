"""CRUD endpoints for long-term memories."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.memory import long_term
from app.memory.schemas import Memory, MemoryIn

router = APIRouter(prefix="/memories", tags=["memories"])


@router.get("/{user_id}", response_model=list[Memory])
async def list_memories(user_id: str, limit: int = 100):
    return await long_term.list_for_user(user_id, limit=limit)


@router.post("/{user_id}", response_model=Memory)
async def create_memory(user_id: str, body: MemoryIn):
    return await long_term.upsert(user_id, body)


@router.get("/{user_id}/search", response_model=list[Memory])
async def search_memories(user_id: str, q: str, k: int = 8):
    if not q.strip():
        raise HTTPException(400, "query 'q' is required")
    return await long_term.search(user_id, q, top_k=k)


@router.delete("/{user_id}/{memory_id}")
async def delete_memory(user_id: str, memory_id: int):
    ok = await long_term.delete(user_id, memory_id)
    if not ok:
        raise HTTPException(404, "not found")
    return {"ok": True}


@router.delete("/{user_id}")
async def wipe_memories(user_id: str):
    n = await long_term.delete_all(user_id)
    return {"deleted": n}
