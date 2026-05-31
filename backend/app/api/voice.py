"""Voice transcription endpoint."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.voice.whisper import transcribe_bytes

log = logging.getLogger(__name__)
router = APIRouter(prefix="/voice", tags=["voice"])

MAX_AUDIO_BYTES = 25 * 1024 * 1024  # 25 MB hard cap


@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    if audio.content_type and not audio.content_type.startswith("audio/"):
        raise HTTPException(415, f"unsupported content-type: {audio.content_type}")
    data = await audio.read()
    if not data:
        raise HTTPException(400, "empty audio upload")
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "audio too large (>25MB)")
    suffix = os.path.splitext(audio.filename or "")[1] or ".webm"
    try:
        text = await transcribe_bytes(data, suffix=suffix)
    except Exception as e:
        log.exception("transcription failed")
        raise HTTPException(500, f"transcription failed: {e}") from e
    return {"text": text}
