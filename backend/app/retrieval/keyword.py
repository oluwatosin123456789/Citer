from sqlalchemy.orm import Session

from app.db.models import CodeChunk
from app.db.queries import keyword_search as _keyword_search


def keyword_search(
    db: Session,
    repo_id: int,
    query: str,
    top_k: int,
) -> list[tuple[CodeChunk, float]]:
    return _keyword_search(db, repo_id, query, top_k)