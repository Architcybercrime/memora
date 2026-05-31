"""Short-term memory: rolling conversation buffer kept in Redis.

Keyed by ``(user_id, session_id)``. Only the last N messages are retained
to control prompt size; older messages are expected to be promoted into
long-term memory by the agent's memory tool when worth keeping.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import get_settings
from app.memory.schemas import ChatMessage

log = logging.getLogger(__name__)

_client: redis.Redis | None = None


async def init_redis() -> redis.Redis:
    global _client
    if _client is None:
        settings = get_settings()
        _client = redis.from_url(settings.redis_url, decode_responses=True)
        await _client.ping()
        log.info("Redis connected")
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _key(user_id: str, session_id: str) -> str:
    return f"memora:hist:{user_id}:{session_id}"


async def append(user_id: str, session_id: str, message: ChatMessage) -> None:
    settings = get_settings()
    r = await init_redis()
    key = _key(user_id, session_id)
    pipe = r.pipeline()
    pipe.rpush(key, message.model_dump_json())
    pipe.ltrim(key, -settings.short_term_window * 2, -1)
    # Sessions expire after 7 days of inactivity.
    pipe.expire(key, 60 * 60 * 24 * 7)
    await pipe.execute()


async def history(user_id: str, session_id: str) -> list[ChatMessage]:
    r = await init_redis()
    raw: list[Any] = await r.lrange(_key(user_id, session_id), 0, -1)
    out: list[ChatMessage] = []
    for item in raw:
        try:
            out.append(ChatMessage(**json.loads(item)))
        except Exception:
            log.warning("dropping malformed history entry")
    return out


async def clear(user_id: str, session_id: str) -> None:
    r = await init_redis()
    await r.delete(_key(user_id, session_id))
