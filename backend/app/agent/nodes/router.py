import json
import re

from app.agent.llm import messages_from_text
from app.core.config import settings

VALID_ACTIONS = {"synthesize", "file_reader", "symbol_searcher"}

DECIDE_SYSTEM = (
    "You are the agent's decision checkpoint. Given the user's question and the context "
    "retrieved so far, choose the next step. Reply with ONLY valid JSON, one of:\n"
    '{"action": "synthesize"}\n'
    '{"action": "file_reader", "file_path": "<path>"}\n'
    '{"action": "symbol_searcher", "symbol": "<name>"}\n'
    "Rules:\n"
    "- synthesize if the context already answers the question.\n"
    "- file_reader if you need the full content of one specific file.\n"
    "- symbol_searcher if you need every chunk matching one function/class name."
)


def parse_action(raw: str) -> dict:
    """Robustly parse the LLM's JSON decision; fall back to 'synthesize' on failure."""
    if not raw:
        return {"action": "synthesize"}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}
        match = re.search(r'"(action)"\s*:\s*"(\w+)"', raw)
        if match:
            data["action"] = match.group(2)

    action = data.get("action", "synthesize")
    if action not in VALID_ACTIONS:
        action = "synthesize"

    args = {}
    if action == "file_reader":
        args["file_path"] = data.get("file_path") or data.get("args", {}).get("file_path")
    elif action == "symbol_searcher":
        args["symbol"] = data.get("symbol") or data.get("args", {}).get("symbol")

    if action == "file_reader" and not args.get("file_path"):
        action = "synthesize"
    elif action == "symbol_searcher" and not args.get("symbol"):
        action = "synthesize"

    return {"action": action, "args": args}


def make_decide_node(model, max_iterations: int | None = None):
    max_iter = max_iterations or settings.max_agent_iterations

    def decide_node(state, config=None) -> dict:
        if state.get("iterations", 0) >= max_iter:
            return {"next_action": "synthesize"}

        question = state["question"]
        context = "\n\n".join(state.get("context", []))[:8000]
        human = f"Question: {question}\n\nContext:\n{context}"

        response = model.invoke(messages_from_text(DECIDE_SYSTEM, human))
        decision = parse_action(response.content)

        out = {"next_action": decision["action"]}
        if decision["action"] in {"file_reader", "symbol_searcher"}:
            out["tool_args"] = decision["args"]
        return out

    return decide_node