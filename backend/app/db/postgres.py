"""Postgres + pgvector connection pool and schema bootstrap."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

log = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_engine() -> AsyncEngine:
    """Create the async engine and ensure schema exists."""
    global _engine, _session_factory
    settings = get_settings()
    if _engine is None:
        _engine = create_async_engine(
            settings.postgres_dsn,
            pool_size=10,
            max_overflow=5,
            pool_pre_ping=True,
        )
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
        await _bootstrap_schema(_engine, settings.embedding_dim)
        log.info("Postgres engine ready")
    return _engine


async def close_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


@asynccontextmanager
async def session() -> AsyncIterator[AsyncSession]:
    if _session_factory is None:
        await init_engine()
    assert _session_factory is not None
    async with _session_factory() as s:
        yield s


async def _bootstrap_schema(engine: AsyncEngine, embedding_dim: int) -> None:
    """Idempotently create pgvector extension + memories table + index."""
    ddl = [
        "CREATE EXTENSION IF NOT EXISTS vector",
        f"""
        CREATE TABLE IF NOT EXISTS memories (
            id           BIGSERIAL PRIMARY KEY,
            user_id      TEXT NOT NULL,
            content      TEXT NOT NULL,
            context      TEXT,
            category     TEXT DEFAULT 'general',
            importance   REAL DEFAULT 0.5,
            embedding    VECTOR({embedding_dim}) NOT NULL,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            access_count INTEGER NOT NULL DEFAULT 0,
            last_used_at TIMESTAMPTZ
        )
        """,
        "CREATE INDEX IF NOT EXISTS memories_user_idx ON memories (user_id)",
        "CREATE INDEX IF NOT EXISTS memories_category_idx ON memories (user_id, category)",
        # HNSW for production-grade ANN; cosine distance.
        """
        CREATE INDEX IF NOT EXISTS memories_embedding_hnsw_idx
            ON memories USING hnsw (embedding vector_cosine_ops)
        """,
    ]
    async with engine.begin() as conn:
        for stmt in ddl:
            await conn.execute(text(stmt))
