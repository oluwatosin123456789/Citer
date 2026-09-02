from sqlalchemy.orm import Session

from app.agent.format import chunk_to_dict, format_context
from app.core.config import settings
from app.retrieval.hybrid import hybrid_search


def make_retrieve_node(db_session: Session):
    def retrieve_node(state, config=None) -> dict:
        query = state.get("search_query") or state["question"]
        repo_id = state["repo_id"]

        chunks = hybrid_search(db_session, repo_id, query, top_k=settings.top_k_retrieval)
        chunk_dicts = [chunk_to_dict(c) for c in chunks]

        tool_calls = list(state.get("tool_calls", []))
        tool_calls.append(
            {"node": "retrieve", "query": query, "hits": len(chunk_dicts)}
        )

        return {
            "retrieved_chunks": chunk_dicts,
            "context": format_context(chunk_dicts),
            "tool_calls": tool_calls,
            "iterations": state.get("iterations", 0) + 1,
        }

    return retrieve_node