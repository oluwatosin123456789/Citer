from app.agent.llm import format_history, messages_from_text

PLANNER_SYSTEM = (
    "You turn the user's question about a codebase into ONE focused search query "
    "that a code search engine can use. Use conversation history to resolve pronouns "
    "like 'it' or 'that file'. Reply with only the search query text."
)


def make_planner_node(model):
    def plan_node(state, config=None) -> dict:
        question = state["question"]
        history = state.get("messages", [])
        human = question
        if history:
            human = f"Conversation history:\n{format_history(history)}\n\nCurrent question: {question}"

        response = model.invoke(messages_from_text(PLANNER_SYSTEM, human))
        search_query = (response.content or "").strip() or question

        tool_calls = list(state.get("tool_calls", []))
        tool_calls.append({"node": "planner", "query": search_query})
        return {"search_query": search_query, "tool_calls": tool_calls}

    return plan_node