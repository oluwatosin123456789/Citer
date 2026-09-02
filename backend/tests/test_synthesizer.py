import queue

from app.agent.nodes.synthesizer import make_synthesize_node
from tests.fakes import FakeChatModel

CHUNKS = [
    {
        "id": 1, "file_path": "src/auth/login.py", "symbol_name": "login",
        "symbol_type": "function", "start_line": 1, "end_line": 10,
        "language": "py", "content": "def login(): return token",
    },
    {
        "id": 2, "file_path": "src/auth/middleware.py", "symbol_name": "AuthMiddleware",
        "symbol_type": "class", "start_line": 12, "end_line": 40,
        "language": "py", "content": "class AuthMiddleware: pass",
    },
]


def _state(**over):
    base = {
        "question": "Where is auth?",
        "messages": [],
        "context": ["[1] src/auth/login.py:1-10\nbody", "[2] src/auth/middleware.py:12-40\nbody"],
        "retrieved_chunks": CHUNKS,
    }
    base.update(over)
    return base


def test_synthesize_concatenates_stream_chunks():
    model = FakeChatModel(stream_chunks=["Auth is in ", "[1]", " and ", "[2]", "."])
    node = make_synthesize_node(model)
    out = node(_state())
    assert out["answer"] == "Auth is in [1] and [2]."


def test_synthesize_parses_citations_in_first_use_order():
    model = FakeChatModel(stream_chunks=["See [2] then [1]."])
    node = make_synthesize_node(model)
    out = node(_state())
    assert [c["file_path"] for c in out["citations"]] == [
        "src/auth/middleware.py",
        "src/auth/login.py",
    ]
    assert out["citations"][0]["start_line"] == 12


def test_synthesize_streams_tokens_to_queue():
    mailbox = queue.Queue()
    model = FakeChatModel(stream_chunks=["hello ", "world"])
    node = make_synthesize_node(model)
    node(_state(), config={"configurable": {"token_queue": mailbox}})
    tokens = []
    while not mailbox.empty():
        tokens.append(mailbox.get())
    assert tokens == [("token", "hello "), ("token", "world")]


def test_synthesize_no_context_says_so():
    model = FakeChatModel(stream_chunks=["Nothing found."])
    node = make_synthesize_node(model)
    out = node(_state(context=[]))
    prompt = model.invocations[0][1].content
    assert "No relevant code was retrieved" in prompt


def test_synthesize_includes_history_in_prompt():
    model = FakeChatModel(stream_chunks=["answer"])
    node = make_synthesize_node(model)
    history = [{"role": "user", "content": "What about login?"}]
    node(_state(messages=history))
    prompt = model.invocations[0][1].content
    assert "What about login?" in prompt