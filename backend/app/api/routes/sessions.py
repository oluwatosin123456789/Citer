from fastapi import APIRouter

router = APIRouter(tags=["sessions"])


@router.get("/sessions")
async def list_sessions() -> list[dict]:
    return []


@router.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict:
    return {"session_id": session_id, "messages": []}