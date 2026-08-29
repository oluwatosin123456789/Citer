from fastapi import APIRouter

from app.schemas.ask import AskRequest, AskResponse

router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest) -> AskResponse:
    return AskResponse(session_id=req.session_id or "", answer="", citations=[])