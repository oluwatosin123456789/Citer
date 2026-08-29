from app.agent.graph import build_graph
from app.agent.state import AgentState


def test_graph_builds():
    graph = build_graph()
    assert graph is not None


def test_planner_emits_retriever_call():
    from app.agent.nodes.planner import plan_node

    out = plan_node({"question": "Where is auth?", "messages": []})
    assert out["tool_calls"][0]["tool"] == "retriever"