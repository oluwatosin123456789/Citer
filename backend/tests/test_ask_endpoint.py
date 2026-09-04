import json

from fastapi.testclient import TestClient

from app.api.routes import ask
from app.db.models import CodeChunk, Message, Repo, Session as SessionModel
from app.main import app
from app.retrieval import hybrid
from tests.conftest import fake_embed
from tests.fakes import FakeChatModel

REPO_URL = "https://github.com/test/demo"


def _seed(db):
    db.query(Message).delete()
    db.query(SessionModel).delete()
    db.query(CodeChunk).delete()
    db.query(Repo).delete()
    repo = Repo(url=REPO_URL, name="demo", status="ready")
    db.add(repo)
    db.flush()
    for path, sym, s, e, content in [
        ("src/auth/login.py", "login", 1, 10, "def login(username, password): validates credentials"),
        ("src/auth/middleware.py", "AuthMiddleware", 12, 40, "class AuthMiddleware: checks JWT token"),
    ]:
        db.add(CodeChunk(repo_id=repo.id, file_path=path, symbol_name=sym, start_line=s,
                         end_line=e, language="py", content=content, embedding=fake_embed(content)))
    db.commit()
    return repo.id


def _parse_sse(lines):
    events = []
    current = {}
    for line in lines:
        if line.startswith("event:"):
            current["event"] = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            current["data"] = json.loads(line.split(":", 1)[1].strip())
            events.append(current)
            current = {}
    return events


def test_ask_streams_answer(db_session, monkeypatch):
    _seed(db_session)
    monkeypatch.setattr(hybrid, "embed_text", fake_embed)
    monkeypatch.setattr(
        ask, "get_chat_model",
        lambda: FakeChatModel(
            default_response='{"action": "synthesize"}',
            stream_chunks=["Auth is in ", "[1]", "."],
        ),
    )

    client = TestClient(app)
    with client.stream(
        "POST",
        "/api/ask",
        json={"question": "Where is auth?", "repo_url": REPO_URL},
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        lines = [l for l in response.iter_lines() if l]

    events = _parse_sse(lines)
    nodes = [e["data"]["node"] for e in events if e["event"] == "node"]
    assert nodes == ["planner", "retrieve", "decide", "synthesize"]

    tokens = "".join(e["data"]["text"] for e in events if e["event"] == "token")
    assert tokens == "Auth is in [1]."

    cites = [e for e in events if e["event"] == "citations"]
    assert cites and isinstance(cites[0]["data"], list)

    done = [e for e in events if e["event"] == "done"]
    assert done and done[0]["data"]["session_id"]


def test_ask_saves_messages(db_session, monkeypatch):
    repo_id = _seed(db_session)
    monkeypatch.setattr(hybrid, "embed_text", fake_embed)
    monkeypatch.setattr(
        ask, "get_chat_model",
        lambda: FakeChatModel(
            default_response='{"action": "synthesize"}',
            stream_chunks=["answer text"],
        ),
    )

    client = TestClient(app)
    session_id = None
    with client.stream(
        "POST",
        "/api/ask",
        json={"question": "Where is auth?", "repo_url": REPO_URL},
    ) as response:
        for line in response.iter_lines():
            if line.startswith("event: done"):
                pass
            if line.startswith("data:") and '"session_id"' in line:
                session_id = json.loads(line.split(":", 1)[1].strip())["session_id"]

    assert session_id
    saved = db_session.query(Message).filter(Message.session_id == session_id).all()
    roles = [m.role for m in saved]
    assert roles == ["user", "assistant"]
    assert saved[-1].citations is not None
    assert repo_id  # repo exists