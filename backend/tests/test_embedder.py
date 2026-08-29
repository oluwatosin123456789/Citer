from types import SimpleNamespace

import pytest

from app.ingestion import embedder


class FakeEmbeddingResponse:
    def __init__(self, dim: int, count: int):
        self.data = [
            SimpleNamespace(embedding=[float(i) / 10.0] * dim) for i in range(count)
        ]


@pytest.fixture(autouse=True)
def fake_client(monkeypatch):
    calls = []

    def fake_create(model, input, dimensions):
        calls.append({"model": model, "input": input, "dimensions": dimensions})
        return FakeEmbeddingResponse(dimensions, len(input))

    fake = SimpleNamespace(embeddings=SimpleNamespace(create=fake_create))
    monkeypatch.setattr(embedder, "_client", fake)
    monkeypatch.setattr(embedder.settings, "openai_api_key", "test-key")
    return calls


def test_embed_text_returns_single_vector(fake_client):
    vec = embedder.embed_text("hello")
    assert len(vec) == embedder.settings.embedding_dim
    assert fake_client[0]["dimensions"] == embedder.settings.embedding_dim


def test_batch_splits_large_inputs(fake_client):
    texts = [f"text {i}" for i in range(embedder.BATCH_SIZE + 5)]
    vecs = embedder.embed_texts(texts)
    assert len(vecs) == len(texts)
    assert len(fake_client) == 2


def test_long_text_is_truncated(fake_client):
    long_text = "x" * (embedder.MAX_CHARS_PER_TEXT + 100)
    embedder.embed_text(long_text)
    sent = fake_client[0]["input"][0]
    assert len(sent) == embedder.MAX_CHARS_PER_TEXT


def test_missing_key_raises(monkeypatch):
    monkeypatch.setattr(embedder.settings, "openai_api_key", "")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        embedder.embed_text("hello")