import tempfile
from dataclasses import dataclass
from pathlib import Path

from git import Repo


@dataclass
class CloneResult:
    repo_dir: Path
    name: str
    default_branch: str
    commit_hash: str


def clone_repo(repo_url: str) -> CloneResult:
    tmp = Path(tempfile.mkdtemp(prefix="codeqa-"))
    repo = Repo.clone_from(repo_url, tmp, depth=1)
    name = repo_url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    return CloneResult(
        repo_dir=tmp,
        name=name,
        default_branch=str(repo.active_branch),
        commit_hash=str(repo.head.commit),
    )