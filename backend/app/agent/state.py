from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    question: str
    messages: Annotated[list, add_messages]
    retrieved_chunks: list
    tool_calls: list
    answer: str
    citations: list
    session_id: str