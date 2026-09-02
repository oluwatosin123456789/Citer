from app.agent.tools.file_reader import build_file_view, make_file_reader_node
from app.agent.tools.symbol_searcher import make_symbol_searcher_node
from app.db.models import CodeChunk, Message, Repo, Session as SessionModel
from tests.conftest import fake_embed


def _seed(db):
    db.query(Message).delete()
    db.query(SessionModel).delete()
    db.query(CodeChunk).delete()
    db.query(Repo).delete()
    repo = Repo(url="https://github.com/test/demo", name="demo", status="ready")
    db.add(repo)
    db.flush()
    rows = [
        ("src/auth/login.py", "login", 1, 10, "def login(username, password):\n    pass"),
        ("src/auth/middleware.py", "AuthMiddleware", 12, 40, "class AuthMiddleware:\n    pass"),
        ("src/auth/token.py", "make_token", 3, 9, "def make_token(user):\n    return 'tok'"),
    ]
    for path, sym, s, e, content in rows:
        db.add(CodeChunk(repo_id=repo.id, file_path=path, symbol_name=sym, start_line=s,
                         end_line=e, language="py", content=content, embedding=fake_embed(content)))
    db.commit()
    return repo.id


def test_file_reader_node_returns_file_view(db_session):
    repo_id = _seed(db_session)
    node = make_file_reader_node(db_session)
    out = node({"repo_id": repo_id, "tool_args": {"file_path": "src/auth/login.py"},
                "context": [], "tool_calls": []})
    assert "def login(username, password):" in out["context"][-1]
    assert out["context"][-1].startswith("[FILE] src/auth/login.py")
    assert out["tool_calls"][-1]["node"] == "file_reader"


def test_file_reader_unknown_file(db_session):
    repo_id = _seed(db_session)
    node = make_file_reader_node(db_session)
    out = node({"repo_id": repo_id, "tool_args": {"file_path": "nope.py"}, "context": [], "tool_calls": []})
    assert "no indexed chunks" in out["context"][-1]


def test_build_file_view_formats_with_symbol():
    class Fake:
        file_path = "x.py"
        start_line = 1
        end_line = 5
        symbol_name = "f"
        symbol_type = "function"
        content = "body"

    view = build_file_view("x.py", [Fake()])
    assert "# x.py:1-5 (function f)" in view


def test_symbol_searcher_node_finds_symbol(db_session):
    repo_id = _seed(db_session)
    node = make_symbol_searcher_node(db_session)
    out = node({"repo_id": repo_id, "tool_args": {"symbol": "make_token"}, "context": [], "tool_calls": []})
    assert any("make_token" in c for c in out["context"])
    assert out["tool_calls"][-1]["hits"] == 1


def test_symbol_searcher_unknown_symbol(db_session):
    repo_id = _seed(db_session)
    node = make_symbol_searcher_node(db_session)
    out = node({"repo_id": repo_id, "tool_args": {"symbol": "nope"}, "context": [], "tool_calls": []})
    assert out["context"] == []
    assert out["tool_calls"][-1]["hits"] == 0