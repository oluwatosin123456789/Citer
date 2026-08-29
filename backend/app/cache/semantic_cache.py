import json
import redis

from app.core.config import settings
from app.ingestion.embedder import embed_text

_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
SIMILARITY_THRESHOLD = 0.95


def _embed_key(question: str) -> str:
    return f"cache:emb:{question}"


def _search_cached(question: str):
    emb = embed_text(question)
    for key in _client.scan_iter("cache:emb:*", count=100):
        cached = _client.get(key)
        if not cached:
            continue
        try:
            score = sum(a * b for a, b in zip(emb, json.loads(cached)))
        except (TypeError, ValueError):
            continue
        if score > SIMILARITY_THRESHOLD:
            original = key.removeprefix("cache:emb:")
            return _client.get(f"cache:ans:{original}")
    return None


def get_cached_answer(question: str) -> dict | None:
    cached = _search_cached(question)
    return json.loads(cached) if cached else None


def set_cached_answer(question: str, answer: str, citations: list) -> None:
    _client.setex(f"cache:emb:{question}", 3600, json.dumps(embed_text(question)))
    _client.setex(
        f"cache:ans:{question}",
        3600,
        json.dumps({"answer": answer, "citations": citations}),
    )