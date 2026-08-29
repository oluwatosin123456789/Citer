import threading

from fastapi import APIRouter, HTTPException

from app.db.session import SessionLocal
from app.ingestion.pipeline import create_task, get_task, index_repo_async
from app.schemas.index import IndexRequest, IndexResponse

router = APIRouter(tags=["index"])


def _validate_repo_url(repo_url: str) -> str:
    repo_url = repo_url.strip()
    if not (repo_url.startswith("https://github.com/") or repo_url.startswith("http://github.com/")):
        raise HTTPException(status_code=400, detail="must be a public GitHub repository URL")
    return repo_url


@router.post("/index", response_model=IndexResponse)
async def index_repo(req: IndexRequest) -> IndexResponse:
    repo_url = _validate_repo_url(req.repo_url)
    task_id = create_task(repo_url)

    def _run():
        db = SessionLocal()
        try:
            index_repo_async(db, task_id, repo_url)
        finally:
            db.close()

    threading.Thread(target=_run, daemon=True).start()
    return IndexResponse(task_id=task_id, status="queued", repo_id=None)


@router.get("/index/status/{task_id}")
async def index_status(task_id: str) -> dict:
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task