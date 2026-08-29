from sqlalchemy.orm import Session

from app.db.models import CodeChunk
from app.ingestion.embedder import embed_text
from app.retrieval.keyword import keyword_search
from app.retrieval.rrf import rrf_merge
from app.retrieval.symbol import symbol_search
from app.retrieval.vector import vector_search


def hybrid_search(
    db: Session,
    repo_id: int,
    query: str,
    top_k: int = 20,
) -> list[CodeChunk]:
    embedding = embed_text(query)
    vector_hits = vector_search(db, repo_id, embedding, top_k)
    keyword_hits = keyword_search(db, repo_id, query, top_k)
    symbol_hits = symbol_search(db, repo_id, query)

    return rrf_merge(
        [vector_hits, keyword_hits, symbol_hits],
        k=60,
        final_k=top_k,
    )