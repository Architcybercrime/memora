"""FastAPI entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import chat, memories, voice
from app.config import get_settings
from app.db.postgres import close_engine, init_engine
from app.memory.short_term import close_redis, init_redis
from app.voice.whisper import warmup as warmup_whisper

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")
structlog.configure(processors=[structlog.processors.JSONRenderer()])
log = logging.getLogger("memora")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("starting memora backend v%s", __version__)
    await init_engine()
    await init_redis()
    # Warm whisper in the background so first /voice request isn't a cold load.
    import asyncio

    asyncio.create_task(warmup_whisper())
    try:
        yield
    finally:
        await close_redis()
        await close_engine()
        log.info("shutdown complete")


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title="Memora",
        version=__version__,
        description="Personal AI agent with layered long-term memory.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(chat.router)
    app.include_router(voice.router)
    app.include_router(memories.router)

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": __version__}

    return app


app = create_app()
