from app.agent.state import AgentState


def should_continue(state: AgentState) -> str:
    return "synthesize"