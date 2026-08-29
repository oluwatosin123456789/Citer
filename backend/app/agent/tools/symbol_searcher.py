from langchain_core.tools import tool


@tool
def symbol_searcher(symbol: str) -> str:
    """Find all chunks matching a symbol (function/class) name."""
    return ""