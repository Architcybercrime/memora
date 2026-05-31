"""Chat endpoint with SSE streaming."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from langchain_core.messages import AIMessageChunk
from sse_starlette.sse import EventSourceResponse

from app.agent import build_graph
from app.memory import short_term
from app.memory.schemas import ChatMessage, ChatRequest

log = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(req: ChatRequest):
    """Stream tokens for one turn over SSE."""
    graph = build_graph()

    # Build full message list: persisted short-term history + this turn.
    history = await short_term.history(req.user_id, req.session_id)
    msgs = [{"role": m.role, "content": m.content} for m in history]
    msgs.append({"role": "user", "content": req.message})

    config = {"configurable": {"user_id": req.user_id, "session_id": req.session_id}}

    async def event_stream():
        full = []
        try:
            async for ev, chunk in graph.astream(
                {"messages": msgs, "user_id": req.user_id, "session_id": req.session_id},
                config=config,
                stream_mode=["messages"],
            ):
                if ev != "messages":
                    continue
                message, meta = chunk
                # Only stream the model's final answer; ignore tool / system / recall.
                if meta.get("langgraph_node") != "model":
                    continue
                if isinstance(message, AIMessageChunk) and message.content:
                    full.append(message.content)
                    yield {"event": "token", "data": json.dumps({"text": message.content})}
        except Exception as e:
            log.exception("chat stream failed")
            yield {"event": "error", "data": json.dumps({"message": str(e)})}
            return

        final = "".join(full).strip()
        # Persist both turns to short-term history.
        await short_term.append(
            req.user_id, req.session_id, ChatMessage(role="user", content=req.message)
        )
        if final:
            await short_term.append(
                req.user_id, req.session_id, ChatMessage(role="assistant", content=final)
            )
        yield {"event": "done", "data": json.dumps({"final": final})}

    return EventSourceResponse(event_stream())


@router.delete("/{user_id}/{session_id}")
async def clear_session(user_id: str, session_id: str):
    await short_term.clear(user_id, session_id)
    return {"ok": True}
