from sqlalchemy.orm import Session

from app.agent.format import chunk_to_dict, format_context
from app.db.queries import find_chunks_by_symbol


def make_symbol_searcher_node(db_session: Session):
    def symbol_searcher_node(state, config=None) -> dict:
        repo_id = state["repo_id"]
        symbol = (state.get("tool_args") or {}).get("symbol", "")

        chunks = find_chunks_by_symbol(db_session, repo_id, symbol)
        chunk_dicts = [chunk_to_dict(c) for c in chunks]

        context = list(state.get("context", []))
        context.extend(format_context(chunk_dicts))

        tool_calls = list(state.get("tool_calls", []))
        tool_calls.append({"node": "symbol_searcher", "symbol": symbol, "hits": len(chunk_dicts)})

        return {"context": context, "tool_calls": tool_calls}

    return symbol_searcher_node