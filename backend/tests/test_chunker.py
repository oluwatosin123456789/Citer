import importlib.util
from pathlib import Path

import pytest

from app.ingestion.chunker import (
    Chunk,
    chunk_file,
)
from app.ingestion.parser import SourceFile

HAS_TREE_SITTER = importlib.util.find_spec("tree_sitter_language_pack") is not None or importlib.util.find_spec(
    "tree_sitter_languages"
) is not None


def _source(language: str, content: str, path: str = "test.py") -> SourceFile:
    return SourceFile(
        path=Path(path),
        relative_path=path,
        language=language,
        content=content,
    )


def test_whole_file_chunk_for_unknown_language():
    source = _source("sql", "SELECT 1;\nSELECT 2;")
    chunks = chunk_file(source)
    assert len(chunks) == 1
    assert chunks[0].symbol_type == "module"
    assert chunks[0].content == "SELECT 1;\nSELECT 2;"


def test_enriched_content_includes_header():
    chunk = Chunk(
        file_path="src/auth.py",
        language="py",
        content="def login(): pass",
        symbol_name="login",
        symbol_type="function",
        start_line=1,
        end_line=1,
    )
    text = chunk.enriched_content()
    assert "File: src/auth.py" in text
    assert "Symbol: login (function)" in text
    assert "def login(): pass" in text


PY_FILE = '''
import os
import jwt

CONSTANT = 42


def helper(x):
    return x + 1


class UserService:
    def __init__(self, db):
        self.db = db

    def get_user(self, user_id):
        return self.db.get(user_id)


def main():
    print("hi")
'''


@pytest.mark.skipif(
    not HAS_TREE_SITTER,
    reason="tree_sitter_languages not installed",
)
def test_python_chunking_splits_definitions():
    chunks = chunk_file(_source("py", PY_FILE))
    symbols = [(c.symbol_name, c.symbol_type) for c in chunks]
    assert ("helper", "function") in symbols
    assert ("UserService", "class") in symbols
    assert ("main", "function") in symbols


@pytest.mark.skipif(
    not HAS_TREE_SITTER,
    reason="tree_sitter_languages not installed",
)
def test_python_chunks_have_correct_line_numbers():
    chunks = chunk_file(_source("py", PY_FILE))
    helper = next(c for c in chunks if c.symbol_name == "helper")
    assert helper.start_line == 8
    assert helper.end_line == 9
    assert helper.content.strip() == "def helper(x):\n    return x + 1"


@pytest.mark.skipif(
    not HAS_TREE_SITTER,
    reason="tree_sitter_languages not installed",
)
def test_module_top_level_code_captured():
    chunks = chunk_file(_source("py", PY_FILE))
    module = next(c for c in chunks if c.symbol_type == "module")
    assert "CONSTANT = 42" in module.content
    assert "import os" in module.content
