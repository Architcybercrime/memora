"""faster-whisper STT.

We load the model lazily and reuse the singleton — model load is expensive.
Transcription itself is CPU-bound, so we offload to a thread.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from functools import lru_cache
from pathlib import Path
from tempfile import NamedTemporaryFile

from faster_whisper import WhisperModel

from app.config import get_settings

log = logging.getLogger(__name__)


@lru_cache
def _model() -> WhisperModel:
    s = get_settings()
    log.info(
        "loading whisper model=%s device=%s compute_type=%s",
        s.whisper_model,
        s.whisper_device,
        s.whisper_compute_type,
    )
    return WhisperModel(
        s.whisper_model,
        device=s.whisper_device,
        compute_type=s.whisper_compute_type,
    )


def _transcribe_sync(path: str) -> str:
    segments, _info = _model().transcribe(path, beam_size=5, vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments).strip()


async def transcribe_bytes(audio: bytes, suffix: str = ".webm") -> str:
    """Write the upload to a tempfile and transcribe it off the event loop."""
    with NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(audio)
        tmp_path = f.name
    try:
        return await asyncio.to_thread(_transcribe_sync, tmp_path)
    finally:
        with contextlib.suppress(OSError):
            Path(tmp_path).unlink(missing_ok=True)


async def warmup() -> None:
    """Force model load at startup so the first request isn't slow."""
    await asyncio.to_thread(_model)
