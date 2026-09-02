import pytest
from sqlalchemy import text

from app.db.session import SessionLocal

DB_REACHABLE = True
try:
    db = SessionLocal()
    db.execute(text("SELECT 1"))
    db.close()
except Exception:
    DB_REACHABLE = False


@pytest.fixture()
def db_session():
    """Real database session. Skips tests that need it if Postgres is down."""
    if not DB_REACHABLE:
        pytest.skip("Postgres not reachable - run `docker compose up -d postgres redis`")
    session = SessionLocal()
    yield session
    session.close()


def fake_embed(text: str, dim: int = 1536) -> list[float]:
    """Deterministic pseudo-embedding so tests can insert vectors without an API key."""
    vec = [0.0] * dim
    grams = {t.lower()[i : i + 3] for t in text.split() for i in range(max(len(t) - 2, 0))}
    for g in grams:
        vec[hash(g) % dim] += 1.0
    norm = sum(v * v for v in vec) ** 0.5
    return [v / norm if norm else 0.0 for v in vec]