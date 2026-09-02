import re

from app.db.models import CodeChunk

CITATION_RE = re.compile(r"\[(\d{1,3})\]")


def chunk_to_dict(chunk: CodeChunk) -> dict:
    return {
        "id": chunk.id,
        "file_path": chunk.file_path,
        "symbol_name": chunk.symbol_name,
        "symbol_type": chunk.symbol_type,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "language": chunk.language,
        "content": chunk.content,
    }


def dict_to_chunk(data: dict) -> CodeChunk:
    return CodeChunk(
        id=data.get("id"),
        repo_id=data.get("repo_id"),
        file_path=data.get("file_path", ""),
        symbol_name=data.get("symbol_name"),
        symbol_type=data.get("symbol_type"),
        start_line=data.get("start_line"),
        end_line=data.get("end_line"),
        language=data.get("language"),
        content=data.get("content", ""),
    )


def format_context(chunks: list[dict]) -> list[str]:
    """Turn chunks into numbered context blocks the LLM can cite: [1], [2], ..."""
    blocks = []
    for idx, chunk in enumerate(chunks, start=1):
        loc = f"{chunk['file_path']}:{chunk.get('start_line')}-{chunk.get('end_line')}"
        symbol = chunk.get("symbol_name") or "module"
        blocks.append(f"[{idx}] {loc} ({chunk.get('symbol_type') or 'def'} {symbol})\n{chunk.get('content', '')}")
    return blocks


def parse_citations(answer: str, chunks: list[dict]) -> list[dict]:
    """Map [N] markers in the answer to citation dicts, preserving first-use order."""
    ordered: list[int] = []
    seen: set[int] = set()
    for match in CITATION_RE.finditer(answer):
        num = int(match.group(1))
        if num in seen or num < 1 or num > len(chunks):
            continue
        seen.add(num)
        ordered.append(num)

    citations = []
    for num in ordered:
        chunk = chunks[num - 1]
        citations.append(
            {
                "file_path": chunk["file_path"],
                "start_line": chunk.get("start_line"),
                "end_line": chunk.get("end_line"),
                "snippet": (chunk.get("content") or "")[:500],
            }
        )
    return citations