import pytest

from app.agent.nodes.router import make_decide_node, parse_action
from tests.fakes import FakeChatModel


def _state(**over):
    base = {"question": "q", "context": ["[1] a.py"], "iterations": 1}
    base.update(over)
    return base


def test_parse_action_synthesize():
    assert parse_action('{"action": "synthesize"}')["action"] == "synthesize"


def test_parse_action_file_reader():
    d = parse_action('{"action": "file_reader", "file_path": "src/auth.py"}')
    assert d["action"] == "file_reader"
    assert d["args"]["file_path"] == "src/auth.py"


def test_parse_action_symbol_searcher():
    d = parse_action('{"action": "symbol_searcher", "symbol": "AuthService"}')
    assert d["action"] == "symbol_searcher"
    assert d["args"]["symbol"] == "AuthService"


def test_parse_action_garbage_falls_back():
    assert parse_action("not json at all")["action"] == "synthesize"


def test_parse_action_missing_args_forced_synthesize():
    d = parse_action('{"action": "file_reader"}')
    assert d["action"] == "synthesize"


def test_decide_routes_to_synthesize():
    model = FakeChatModel(default_response='{"action": "synthesize"}')
    node = make_decide_node(model)
    assert node(_state())["next_action"] == "synthesize"


def test_decide_routes_to_file_reader():
    model = FakeChatModel(default_response='{"action": "file_reader", "file_path": "a.py"}')
    node = make_decide_node(model)
    out = node(_state())
    assert out["next_action"] == "file_reader"
    assert out["tool_args"]["file_path"] == "a.py"


def test_decide_caps_iterations():
    model = FakeChatModel(default_response='{"action": "file_reader", "file_path": "a.py"}')
    node = make_decide_node(model, max_iterations=3)
    out = node(_state(iterations=3))
    assert out["next_action"] == "synthesize"
    assert "tool_args" not in out