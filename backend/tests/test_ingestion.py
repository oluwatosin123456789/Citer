from app.ingestion.parser import list_source_files


def test_list_source_files_excludes_venv(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "venv").mkdir()
    (tmp_path / "main.py").write_text("def main(): pass")
    (tmp_path / "node_modules").mkdir()

    files = list_source_files(tmp_path)
    assert [f.relative_path for f in files] == ["main.py"]