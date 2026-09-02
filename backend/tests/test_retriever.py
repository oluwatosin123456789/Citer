from app.agent.nodes.retriever import make_retrieve_node
from app.db.models import CodeChunk, Message, Repo, Session as SessionModel
from app.retrieval import hybrid
from tests.conftest import fake_embed

REPO_URL = "https://github.com/test/demo"


def _seed(db):
    db.query(Message).delete()
    db.query(SessionModel).delete()
    db.query(CodeChunk).delete()
    db.query(Repo).delete()
    repo = Repo(url=REPO_URL, name="demo", status="ready")
    db.add(repo)
    db.flush()
    rows = [
        ("src/auth/login.py", "login", 1, 10, "def login(username, password): returns a session token"),
        ("src/auth/middleware.py", "AuthMiddleware", 12, 40, "class AuthMiddleware: validates JWT on requests"),
        ("src/payments/charge.py", "charge", 5, 8, "def charge(card, amount): runs a payment"),
    ]
    for path, sym, s, e, content in rows:
        db.add(CodeChunk(repo_id=repo.id, file_path=path, symbol_name=sym, start_line=s,
                         end_line=e, language="py", content=content, embedding=fake_embed(content)))
    db.commit()
    return repo.id


def test_retrieve_node_queries_db(db_session, monkeypatch):
    repo_id = _seed(db_session)
    monkeypatch.setattr(hybrid, "embed_text", fake_embed)

    node = make_retrieve_node(db_session)
    out = node({"question": "how does authentication work?", "repo_id": repo_id, "messages": []})

    assert out["iterations"] == 1
    assert len(out["retrieved_chunks"]) >= 2
    assert any(c["file_path"].startswith("src/auth") for c in out["retrieved_chunks"])
    assert out["context"][0].startswith("[1]")
    assert out["tool_calls"][-1]["node"] == "retrieve"


def test_retrieve_node_uses_search_query(db_session, monkeypatch):
    repo_id = _seed(db_session)
    monkeypatch.setattr(hybrid, "embed_text", fake_embed)

    node = make_retrieve_node(db_session)
    out = node({"question": "q", "search_query": "payment charge", "repo_id": repo_id, "messages": []})
    assert out["tool_calls"][-1]["query"] == "payment charge"