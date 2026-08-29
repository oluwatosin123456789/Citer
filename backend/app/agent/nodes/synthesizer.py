from app.agent.state import AgentState


def synthesize_node(state: AgentState) -> dict:
    return {
        "answer": "",
        "citations": [],
    }