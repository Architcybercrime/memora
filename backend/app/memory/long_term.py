"""Long-term semantic memory in Postgres + pgvector.

All embeddings are produced via the configured OpenAI embedding model.
Search uses cosine distance against an HNSW index.
"""

from __future__ import annotations

import logging
from typing import Sequence

from langchain_openai import OpenAIEmbeddings
from sqlalchemy import text

from app.config import get_settings
from app.db.postgres import session
from app.memory.schemas import Memory, MemoryIn

log = logging.getLogger(__name__)

_embedder: OpenAIEmbeddings | None = None


def _embeddings() -> OpenAIEmbeddings:
    global _embedder
    if _embedder is None:
        s = get_settings()
        _embedder = OpenAIEmbeddings(
            model=s.embedding_model,
            api_key=s.openai_api_key,
            dimensions=s.embedding_dim,
        )
    return _embedder


def _to_pgvector(vec: Sequence[float]) -> str:
    """pgvector accepts a string literal of the form '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{x:.7f}" for x in vec) + "]"


async def upsert(user_id: str, mem: MemoryIn) -> Memory:
    """Insert a new memory (we treat memories as append-only by design)."""
    embedding = (await _embeddings().aembed_documents([mem.content]))[0]
    async with session() as s:
        row = (
            await s.execute(
                text(
                    """
                    INSERT INTO memories
                        (user_id, content, context, category, importance, embedding)
                    VALUES
                        (:user_id, :content, :context, :category, :importance, CAST(:embedding AS vector))
                    RETURNING id, user_id, content, context, category, importance,
                              created_at, updated_at, access_count, last_used_at
                    """
                ),
                {
                    "user_id": user_id,
                    "content": mem.content,
                    "context": mem.context,
                    "category": mem.category,
                    "importance": mem.importance,
                    "embedding": _to_pgvector(embedding),
                },
            )
        ).mappings().one()
        await s.commit()
    return Memory(**dict(row))


async def search(user_id: str, query: str, top_k: int | None = None) -> list[Memory]:
    settings = get_settings()
    k = top_k or settings.long_term_top_k
    embedding = (await _embeddings().aembed_query(query))
    async with session() as s:
        rows = (
            await s.execute(
                text(
                    """
                    SELECT id, user_id, content, context, category, importance,
                           created_at, updated_at, access_count, last_used_at,
                           1 - (embedding <=> CAST(:embedding AS vector)) AS score
                    FROM memories
                    WHERE user_id = :user_id
                    ORDER BY embedding <=> CAST(:embedding AS vector)
                    LIMIT :k
                    """
                ),
                {
                    "user_id": user_id,
                    "embedding": _to_pgvector(embedding),
                    "k": k,
                },
            )
        ).mappings().all()
        ids = [r["id"] for r in rows]
        if ids:
            await s.execute(
                text(
                    """
                    UPDATE memories
                       SET access_count = access_count + 1,
                           last_used_at = NOW()
                     WHERE id = ANY(:ids)
                    """
                ),
                {"ids": ids},
            )
            await s.commit()
    return [Memory(**dict(r)) for r in rows]


async def list_for_user(user_id: str, limit: int = 100) -> list[Memory]:
    async with session() as s:
        rows = (
            await s.execute(
                text(
                    """
                    SELECT id, user_id, content, context, category, importance,
                           created_at, updated_at, access_count, last_used_at
                    FROM memories
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT :limit
                    """
                ),
                {"user_id": user_id, "limit": limit},
            )
        ).mappings().all()
    return [Memory(**dict(r)) for r in rows]


async def delete(user_id: str, memory_id: int) -> bool:
    async with session() as s:
        result = await s.execute(
            text("DELETE FROM memories WHERE id = :id AND user_id = :user_id"),
            {"id": memory_id, "user_id": user_id},
        )
        await s.commit()
    return (result.rowcount or 0) > 0


async def delete_all(user_id: str) -> int:
    async with session() as s:
        result = await s.execute(
            text("DELETE FROM memories WHERE user_id = :user_id"),
            {"user_id": user_id},
        )
        await s.commit()
    return result.rowcount or 0
