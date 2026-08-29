import time

from openai import OpenAI
from openai import RateLimitError

from app.core.config import settings

_client = OpenAI(api_key=settings.openai_api_key)

BATCH_SIZE = 128
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2
MAX_CHARS_PER_TEXT = 24000


def _require_key() -> None:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set; add it to .env before embedding")


def embed_texts(texts: list[str]) -> list[list[float]]:
    results: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = [_truncate(t) for t in texts[i : i + BATCH_SIZE]]
        results.extend(_embed_batch_with_retry(batch))
    return results


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]


def _embed_batch_with_retry(texts: list[str]) -> list[list[float]]:
    _require_key()
    for attempt in range(MAX_RETRIES):
        try:
            resp = _client.embeddings.create(
                model=settings.openai_embedding_model,
                input=texts,
                dimensions=settings.embedding_dim,
            )
            return [item.embedding for item in resp.data]
        except RateLimitError:
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(RETRY_BACKOFF_SECONDS * (2**attempt))
    raise RuntimeError("embedding failed")


def _truncate(text: str) -> str:
    if len(text) <= MAX_CHARS_PER_TEXT:
        return text
    return text[:MAX_CHARS_PER_TEXT]