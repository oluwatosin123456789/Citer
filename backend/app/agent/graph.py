from langgraph.graph import END, START, StateGraph

from app.agent.nodes.planner import make_planner_node
from app.agent.nodes.retriever import make_retrieve_node
from app.agent.nodes.router import make_decide_node
from app.agent.nodes.synthesizer import make_synthesize_node
from app.agent.state import AgentState
from app.agent.tools.file_reader import make_file_reader_node
from app.agent.tools.symbol_searcher import make_symbol_searcher_node


def build_graph(db_session, model=None, max_iterations: int | None = None):
    """Assemble the LangGraph agent.

    - db_session: open SQLAlchemy session for retrieval/tools.
    - model: chat model; defaults to the configured OpenAI model.
    - max_iterations: loop cap; defaults to settings.max_agent_iterations.
    """
    if model is None:
        from app.agent.llm import get_chat_model

        model = get_chat_model()

    graph = StateGraph(AgentState)
    graph.add_node("planner", make_planner_node(model))
    graph.add_node("retrieve", make_retrieve_node(db_session))
    graph.add_node("decide", make_decide_node(model, max_iterations=max_iterations))
    graph.add_node("file_reader", make_file_reader_node(db_session))
    graph.add_node("symbol_searcher", make_symbol_searcher_node(db_session))
    graph.add_node("synthesize", make_synthesize_node(model))

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "retrieve")
    graph.add_edge("retrieve", "decide")

    graph.add_conditional_edges(
        "decide",
        _route,
        {
            "file_reader": "file_reader",
            "symbol_searcher": "symbol_searcher",
            "synthesize": "synthesize",
        },
    )
    graph.add_edge("file_reader", "decide")
    graph.add_edge("symbol_searcher", "decide")
    graph.add_edge("synthesize", END)

    return graph.compile()


def _route(state: dict) -> str:
    return state.get("next_action", "synthesize")