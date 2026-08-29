from langchain_core.tools import tool


@tool
def file_reader(file_path: str, start_line: int = 1, end_line: int | None = None) -> str:
    """Read raw content of a file (optionally a line range) for full context."""
    return ""