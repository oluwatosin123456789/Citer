import threading
import time
import uuid

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.db.models import CodeChunk, Repo
from app.ingestion.chunker import Chunk, chunk_file
from app.ingestion.cloner import clone_repo
from app.ingestion.embedder import embed_texts
from app.ingestion.parser import list_source_files

_tasks: dict[str, dict] = {}
_tasks_lock = threading.Lock()


def create_task(repo_url: str) -> str:
    task_id = uuid.uuid4().hex[:12]
    with _tasks_lock:
        _tasks[task_id] = {
            "repo_url": repo_url,
            "status": "queued",
            "progress": 0.0,
            "message": "queued",
        }
    return task_id


def get_task(task_id: str) -> dict | None:
    with _tasks_lock:
        task = _tasks.get(task_id)
        return dict(task) if task else None


def _update_task(task_id: str, **fields) -> None:
    with _tasks_lock:
        if task_id in _tasks:
            _tasks[task_id].update(fields)


def _delete_task(task_id: str) -> None:
    with _tasks_lock:
        _tasks.pop(task_id, None)


def index_repo_async(db: Session, task_id: str, repo_url: str) -> None:
    try:
        index_repo(db, repo_url, task_id=task_id)
    except Exception as exc:
        _update_task(task_id, status="failed", message=str(exc))
        logger.exception("index failed for %s", repo_url)


def index_repo(db: Session, repo_url: str, task_id: str | None = None) -> Repo:
    if task_id is None:
        task_id = create_task(repo_url)
    _update_task(task_id, status="cloning", progress=0.0, message="cloning repository")

    existing = db.query(Repo).filter(Repo.url == repo_url).first()
    if existing:
        db.execute(delete(CodeChunk).where(CodeChunk.repo_id == existing.id))
        repo = existing
    else:
        repo = Repo(url=repo_url, name=repo_url.rsplit("/", 1)[-1], status="cloning")
        db.add(repo)
        db.commit()

    clone = clone_repo(repo_url)
    repo.name = clone.name
    repo.default_branch = clone.default_branch
    repo.commit_hash = clone.commit_hash
    repo.status = "parsing"
    db.commit()

    _update_task(task_id, status="parsing", progress=0.1, message="walking source files")
    sources = list_source_files(clone.repo_dir)
    logger.info("parsing %d files from %s", len(sources), repo_url)

    chunks: list[Chunk] = []
    for idx, source in enumerate(sources):
        try:
            chunks.extend(chunk_file(source))
        except Exception:
            logger.warning("chunking failed for %s", source.relative_path)
        if idx % 50 == 0 and sources:
            progress = 0.1 + 0.4 * (idx / len(sources))
            _update_task(task_id, progress=round(progress, 3), message=f"parsed {idx}/{len(sources)} files")

    if not chunks:
        _update_task(task_id, status="failed", message="no parseable source files found")
        raise RuntimeError(f"no parseable source files found in {repo_url}")

    _update_task(task_id, status="embedding", progress=0.5, message=f"embedding {len(chunks)} chunks")
    logger.info("embedding %d chunks", len(chunks))

    texts = [c.enriched_content() for c in chunks]
    embeddings = embed_texts(texts)

    repo.status = "embedding"
    db.commit()

    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        db.add(
            CodeChunk(
                repo_id=repo.id,
                file_path=chunk.file_path,
                symbol_name=chunk.symbol_name,
                symbol_type=chunk.symbol_type,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                language=chunk.language,
                content=chunk.content,
                embedding=emb,
                metadata_=chunk.metadata,
            )
        )
        if idx % 200 == 0:
            db.flush()

    db.commit()
    repo.status = "ready"
    db.commit()

    _update_task(task_id, status="done", progress=1.0, message=f"indexed {len(chunks)} chunks")
    logger.info("indexed %d chunks for %s", len(chunks), repo_url)
    return repo