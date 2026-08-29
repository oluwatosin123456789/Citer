from dataclasses import dataclass
from pathlib import Path

EXCLUDED_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".next"}
EXCLUDED_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf", ".zip",
    ".gz", ".tar", ".lock", ".woff", ".woff2", ".ttf", ".bin", ".min.js",
}
SOURCE_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb",
    ".php", ".c", ".cpp", ".h", ".hpp", ".cs", ".swift", ".kt", ".sql",
}


@dataclass
class SourceFile:
    path: Path
    relative_path: str
    language: str
    content: str


def list_source_files(repo_dir: Path) -> list[SourceFile]:
    files: list[SourceFile] = []
    for path in repo_dir.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.suffix in EXCLUDED_EXTS or path.suffix not in SOURCE_EXTS:
            continue
        language = path.suffix.lstrip(".")
        files.append(
            SourceFile(
                path=path,
                relative_path=str(path.relative_to(repo_dir)),
                language=language,
                content=path.read_text(encoding="utf-8", errors="ignore"),
            )
        )
    return files