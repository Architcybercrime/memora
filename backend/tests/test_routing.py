"""Graph routing tests — verify when the agent loops to tools vs. ends."""

from types import SimpleNamespace

from langgraph.graph import END

from app.agent.graph import route


def test_route_to_tools_when_tool_calls_present():
    state = {
        "messages": [SimpleNamespace(tool_calls=[{"name": "save_memory", "args": {}, "id": "1"}])]
    }
    assert route(state) == "tools"


def test_route_ends_when_no_tool_calls():
    state = {"messages": [SimpleNamespace(tool_calls=None, content="hello")]}
    assert route(state) == END


def test_route_ends_when_attribute_missing():
    state = {"messages": [SimpleNamespace(content="hi")]}
    assert route(state) == END
