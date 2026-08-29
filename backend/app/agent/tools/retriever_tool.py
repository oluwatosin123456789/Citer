from langchain_core.tools import tool


@tool
def retriever(query: str) -> str:
    """Hybrid search over the indexed repo. Returns ranked code chunks with file paths and lines."""
    return query