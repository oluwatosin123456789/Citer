from sqlalchemy.orm import Session

from app.db.models import CodeChunk
from app.db.queries import find_chunks_by_symbol


def extract_symbols(query: str) -> list[str]:
    import re

    candidates = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", query)
    return [c for c in candidates if len(c) >= 3 and c.lower() not in {
        "where", "what", "which", "how", "does", "is", "the", "and", "for",
        "file", "files", "function", "class", "code", "this", "that", "with",
    }]


def symbol_search(
    db: Session,
    repo_id: int,
    query: str,
) -> list[tuple[CodeChunk, float]]:
    hits: dict[int, tuple[CodeChunk, float]] = {}
    for symbol in extract_symbols(query):
        for chunk in find_chunks_by_symbol(db, repo_id, symbol):
            hits.setdefault(chunk.id, (chunk, 1.0))
    return list(hits.values())