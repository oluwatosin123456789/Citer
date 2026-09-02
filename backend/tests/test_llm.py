import pytest

from app.agent import llm


def test_format_history_limits_to_recent_messages():
    history = [{"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"} for i in range(20)]
    out = llm.format_history(history)
    assert "msg 0" not in out
    assert "msg 19" in out
    assert "User: msg 18" in out


def test_format_history_handles_empty():
    assert llm.format_history([]) == ""


def test_get_chat_model_requires_key(monkeypatch):
    monkeypatch.setattr(llm.settings, "openai_api_key", "")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        llm.get_chat_model()


def test_get_chat_model_returns_model(monkeypatch):
    monkeypatch.setattr(llm.settings, "openai_api_key", "test-key")
    model = llm.get_chat_model()
    assert model.model_name == "gpt-4o"


def test_messages_from_text_builds_system_and_human():
    msgs = llm.messages_from_text("be helpful", "hello")
    assert msgs[0].content == "be helpful"
    assert msgs[1].content == "hello"