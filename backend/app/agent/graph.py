"""LangGraph wiring.

Flow:
    start -> recall (semantic search) -> model -> [tools -> model]* -> end
"""

from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent.llm import get_llm
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.state import AgentState
from app.agent.tools import TOOLS
from app.memory import long_term


def _format_memories(memories) -> str:
    if not memories:
        return "(none yet)"
    lines = []
    for m in memories:
        score = f"{m.score:.2f}" if m.score is not None else "-"
        lines.append(f"- [{m.id}] ({m.category}, sim={score}) {m.content}")
    return "\n".join(lines)


async def recall_node(state: AgentState) -> dict:
    """Semantic-search long-term memory using the latest user message as the query."""
    user_id = state["user_id"]
    last = next(
        (m for m in reversed(state["messages"]) if getattr(m, "type", None) == "human"),
        None,
    )
    query = getattr(last, "content", "") if last else ""
    memories = await long_term.search(user_id, query) if query else []
    return {
        "system_prompt": SYSTEM_PROMPT.format(
            time=datetime.now().isoformat(timespec="seconds"),
            memories=_format_memories(memories),
        )
    }


async def model_node(state: AgentState) -> dict:
    """Call the LLM with [SystemMessage] + history. System is never persisted to state."""
    llm = get_llm().bind_tools(TOOLS)
    system = SystemMessage(content=state.get("system_prompt", ""))
    msg = await llm.ainvoke([system, *state["messages"]])
    return {"messages": [msg]}


def route(state: AgentState) -> str:
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return END


@lru_cache
def build_graph():
    g = StateGraph(AgentState)
    g.add_node("recall", recall_node)
    g.add_node("model", model_node)
    g.add_node("tools", ToolNode(TOOLS))
    g.add_edge(START, "recall")
    g.add_edge("recall", "model")
    g.add_conditional_edges("model", route, {"tools": "tools", END: END})
    g.add_edge("tools", "model")
    return g.compile()
