from typing import TypedDict


class AgentState(TypedDict, total=False):
    """Shared memory bag passed between graph nodes.

    total=False means nodes may only set the fields they care about;
    LangGraph merges the returned partial updates into the running state.
    """

    question: str
    repo_id: int
    session_id: str
    messages: list[dict]      # prior conversation turns (role/content)
    search_query: str         # planner output
    retrieved_chunks: list[dict]
    context: list[str]        # numbered context blocks for the LLM
    tool_calls: list[dict]    # trace of agent actions
    next_action: str          # decide output: synthesize | file_reader | symbol_searcher
    tool_args: dict           # arguments for the chosen tool
    iterations: int           # loop counter (capped)
    answer: str
    citations: list[dict]