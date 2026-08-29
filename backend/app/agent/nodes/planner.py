from app.agent.state import AgentState


def plan_node(state: AgentState) -> dict:
    question = state["question"]
    return {"tool_calls": [{"tool": "retriever", "query": question}]}