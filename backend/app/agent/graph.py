from langgraph.graph import END, START, StateGraph

from app.agent.nodes.planner import plan_node
from app.agent.nodes.router import should_continue
from app.agent.nodes.synthesizer import synthesize_node
from app.agent.state import AgentState


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("planner", plan_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("synthesize", synthesize_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "retrieve")
    graph.add_conditional_edges("retrieve", should_continue, {"synthesize": "synthesize", "retrieve": "retrieve"})
    graph.add_edge("synthesize", END)

    return graph.compile()


def retrieve_node(state: AgentState) -> dict:
    return state