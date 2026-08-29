from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.models import CodeChunk


def find_chunks_by_symbol(db: Session, repo_id: int, symbol: str) -> list[CodeChunk]:
    stmt = (
        select(CodeChunk)
        .where(CodeChunk.repo_id == repo_id)
        .where(CodeChunk.symbol_name == symbol)
        .order_by(CodeChunk.start_line)
    )
    return list(db.execute(stmt).scalars())


def find_chunks_by_file(db: Session, repo_id: int, file_path: str) -> list[CodeChunk]:
    stmt = (
        select(CodeChunk)
        .where(CodeChunk.repo_id == repo_id)
        .where(CodeChunk.file_path == file_path)
        .order_by(CodeChunk.start_line)
    )
    return list(db.execute(stmt).scalars())


def vector_search(
    db: Session,
    repo_id: int,
    embedding: list[float],
    top_k: int,
) -> list[tuple[CodeChunk, float]]:
    stmt = text(
        """
        SELECT *, 1 - (embedding <=> :emb) AS score
        FROM code_chunks
        WHERE repo_id = :repo_id
        ORDER BY embedding <=> :emb
        LIMIT :top_k
        """
    )
    rows = db.execute(stmt, {"emb": embedding, "repo_id": repo_id, "top_k": top_k}).fetchall()
    return [(CodeChunk(**dict(r._mapping)), r.score) for r in rows]


def keyword_search(
    db: Session,
    repo_id: int,
    query: str,
    top_k: int,
) -> list[tuple[CodeChunk, float]]:
    stmt = text(
        """
        SELECT *, ts_rank(to_tsvector('english', content || ' ' || file_path), plainto_tsquery(:q)) AS score
        FROM code_chunks
        WHERE repo_id = :repo_id
          AND to_tsvector('english', content || ' ' || file_path) @@ plainto_tsquery(:q)
        ORDER BY score DESC
        LIMIT :top_k
        """
    )
    rows = db.execute(stmt, {"q": query, "repo_id": repo_id, "top_k": top_k}).fetchall()
    return [(CodeChunk(**dict(r._mapping)), r.score) for r in rows]