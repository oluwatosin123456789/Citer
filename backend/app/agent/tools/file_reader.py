from sqlalchemy.orm import Session

from app.db.queries import find_chunks_by_file


def build_file_view(file_path: str, chunks) -> str:
    """Reconstruct a readable view of a file from its stored chunks, line-ordered."""
    if not chunks:
        return f"{file_path}: (no indexed chunks for this file)"
    parts = []
    for c in chunks:
        loc = f"{c.start_line}-{c.end_line}"
        if c.symbol_name:
            loc += f" ({c.symbol_type or 'def'} {c.symbol_name})"
        parts.append(f"# {file_path}:{loc}\n{c.content}")
    return "\n\n".join(parts)


def make_file_reader_node(db_session: Session):
    def file_reader_node(state, config=None) -> dict:
        repo_id = state["repo_id"]
        file_path = (state.get("tool_args") or {}).get("file_path", "")

        chunks = find_chunks_by_file(db_session, repo_id, file_path)
        view = build_file_view(file_path, chunks)

        context = list(state.get("context", []))
        context.append(f"[FILE] {file_path}\n{view}")

        tool_calls = list(state.get("tool_calls", []))
        tool_calls.append({"node": "file_reader", "file_path": file_path, "lines": len(chunks)})

        return {"context": context, "tool_calls": tool_calls}

    return file_reader_node