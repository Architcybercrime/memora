"""Agent graph state."""

from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """State carried through the graph.

    ``messages`` uses LangGraph's ``add_messages`` reducer so each node can
    return only the new messages it produced and they're appended.
    ``system_prompt`` is rebuilt every turn by ``recall_node`` and consumed
    (not stored as a message) by ``model_node`` so it never pollutes history.
    """

    messages: Annotated[list, add_messages]
    user_id: str
    session_id: str
    system_prompt: str
