from fastapi import APIRouter

router = APIRouter(tags=["eval"])


@router.post("/eval/run")
async def run_eval() -> dict:
    return {"status": "started", "run_id": ""}


@router.get("/eval/runs")
async def list_runs() -> list[dict]:
    return []