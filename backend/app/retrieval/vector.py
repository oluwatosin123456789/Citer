from sqlalchemy.orm import Session

from app.db.models import CodeChunk
from app.db.queries import vector_search as _vector_search


def vector_search(
    db: Session,
    repo_id: int,
    embedding: list[float],
    top_k: int,
) -> list[tuple[CodeChunk, float]]:
    return _vector_search(db, repo_id, embedding, top_k)