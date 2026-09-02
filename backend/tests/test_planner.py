import pytest

from app.agent.nodes.planner import PLANNER_SYSTEM, make_planner_node
from tests.fakes import FakeChatModel


def test_planner_uses_llm_query():
    model = FakeChatModel(default_response="authentication flow")
    node = make_planner_node(model)
    out = node({"question": "Where is auth handled?", "messages": []})
    assert out["search_query"] == "authentication flow"
    assert out["tool_calls"][0]["node"] == "planner"


def test_planner_falls_back_to_question_on_empty_response():
    model = FakeChatModel(default_response="  ")
    node = make_planner_node(model)
    out = node({"question": "Where is auth?", "messages": []})
    assert out["search_query"] == "Where is auth?"


def test_planner_includes_history():
    model = FakeChatModel(default_response="password reset flow")
    node = make_planner_node(model)
    history = [{"role": "user", "content": "What happens when a user forgets their password?"}]
    node({"question": "Trace the full flow", "messages": history})
    prompt = model.invocations[-1][1].content
    assert "forgets their password" in prompt
    assert "Trace the full flow" in prompt


def test_planner_appends_to_existing_tool_calls():
    model = FakeChatModel(default_response="x")
    node = make_planner_node(model)
    out = node({"question": "q", "messages": [], "tool_calls": [{"node": "prior"}]})
    assert [t["node"] for t in out["tool_calls"]] == ["prior", "planner"]


def test_planner_system_prompt_is_not_empty():
    assert "search query" in PLANNER_SYSTEM