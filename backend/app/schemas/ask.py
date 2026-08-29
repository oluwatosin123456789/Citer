from pydantic import BaseModel

from app.schemas.index import IndexRequest


class AskRequest(BaseModel):
    question: str
    repo_url: str | None = None
    session_id: str | None = None


class Citation(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    snippet: str


class AskResponse(BaseModel):
    session_id: str
    answer: str
    citations: list[Citation]