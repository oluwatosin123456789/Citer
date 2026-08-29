from pydantic import BaseModel


class SessionSummary(BaseModel):
    id: str
    repo_url: str | None = None
    created_at: str
    message_count: int


class MessageOut(BaseModel):
    role: str
    content: str
    citations: list[dict] = []