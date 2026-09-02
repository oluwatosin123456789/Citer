import pytest

from app.agent.graph import build_graph
from app.db.models import CodeChunk, Message, Repo, Session as SessionModel
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
    rows = [
        ("src/auth/login.py", "login", 1, 10, "def login(username, password): validates credentials"),
        ("src/auth/middleware.py", "AuthMiddleware", 12, 40, "class AuthMiddleware: checks JWT token"),
        ("src/payments/charge.py", "charge", 5, 8, "def charge(card, amount): runs a payment"),
    ]
    for path, sym, s, e, content in rows:
        db.add(CodeChunk(repo_id=repo.id, file_path=path, symbol_name=sym, start_line=s,
                         end_line=e, language="py", content=content, embedding=fake_embed(content)))
    db.commit()
    return repo.id


def _initial_state(repo_id, question="Where is authentication handled?"):
    return {
        "question": question,
        "repo_id": repo_id,
        "messages": [],
        "context": [],
        "tool_calls": [],
        "iterations": 0,
        "session_id": "test-session",
    }


def test_graph_end_to_end_synthesizes(db_session, monkeypatch):
    repo_id = _seed(db_session)
    monkeypatch.setattr(hybrid, "embed_text", fake_embed)

    model = FakeChatModel(
        default_response='{"action": "synthesize"}',
        stream_chunks=["Auth is handled in ", "[1]", " and ", "[2]", "."],
    )
    graph = build_graph(db_session, model=model, max_iterations=3)
    result = graph.invoke(_initial_state(repo_id))

    assert result["answer"] == "Auth is handled in [1] and [2]."
    assert len(result["citations"]) == 2
    known = {"src/auth/login.py", "src/auth/middleware.py", "src/payments/charge.py"}
    assert all(c["file_path"] in known for c in result["citations"])
    assert any(c["file_path"].startswith("src/auth") for c in result["retrieved_chunks"])
    assert result["search_query"]


def test_graph_loop_uses_file_reader(db_session, monkeypatch):
    repo_id = _seed(db_session)
    monkeypatch.setattr(hybrid, "embed_text", fake_embed)

    model = FakeChatModel(
        invoke_responses=[
            "authentication flow",  # planner consumes this first
            '{"action": "file_reader", "file_path": "src/auth/login.py"}',
            '{"action": "synthesize"}',
        ],
        stream_chunks=["Answer with file context."],
    )
    graph = build_graph(db_session, model=model, max_iterations=3)
    result = graph.invoke(_initial_state(repo_id))

    nodes = [t["node"] for t in result["tool_calls"]]
    assert "file_reader" in nodes
    assert any("def login(username, password)" in c for c in result["context"])
    assert result["answer"]


def test_graph_iteration_cap_forces_answer(db_session, monkeypatch):
    repo_id = _seed(db_session)
    monkeypatch.setattr(hybrid, "embed_text", fake_embed)

    model = FakeChatModel(
        default_response='{"action": "file_reader", "file_path": "src/auth/login.py"}',
        stream_chunks=["Final answer."],
    )
    graph = build_graph(db_session, model=model, max_iterations=1)
    result = graph.invoke(_initial_state(repo_id))

    assert result["answer"] == "Final answer."
    assert result["tool_calls"][-1]["node"] == "synthesize"