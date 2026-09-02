from app.agent import format


def _chunk(path, start, end, symbol=None, content="code"):
    return {
        "id": 1,
        "file_path": path,
        "symbol_name": symbol,
        "symbol_type": "function" if symbol else "module",
        "start_line": start,
        "end_line": end,
        "language": "py",
        "content": content,
    }


def test_format_context_numbers_chunks():
    chunks = [_chunk("a.py", 1, 2, "foo"), _chunk("b.py", 5, 6, "bar")]
    blocks = format.format_context(chunks)
    assert blocks[0].startswith("[1] a.py:1-2 (function foo)")
    assert blocks[1].startswith("[2] b.py:5-6 (function bar)")
    assert "code" in blocks[0]


def test_parse_citations_orders_by_first_use():
    chunks = [_chunk("a.py", 1, 2, "foo"), _chunk("b.py", 5, 6, "bar")]
    answer = "Look at [2] then [1] and again [2]."
    citations = format.parse_citations(answer, chunks)
    assert [c["file_path"] for c in citations] == ["b.py", "a.py"]


def test_parse_citations_ignores_out_of_range():
    chunks = [_chunk("a.py", 1, 2, "foo")]
    assert format.parse_citations("See [5]", chunks) == []


def test_parse_citations_snippet_truncated():
    chunks = [_chunk("a.py", 1, 2, "foo", content="x" * 1000)]
    citations = format.parse_citations("See [1]", chunks)
    assert len(citations[0]["snippet"]) == 500


def test_chunk_to_dict_round_trip():
    from app.db.models import CodeChunk

    chunk = CodeChunk(
        id=7, repo_id=1, file_path="x.py", symbol_name="f", start_line=1,
        end_line=3, language="py", content="def f(): pass",
    )
    data = format.chunk_to_dict(chunk)
    assert data["id"] == 7
    assert data["file_path"] == "x.py"