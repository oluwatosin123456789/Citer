from pydantic import BaseModel


class IndexRequest(BaseModel):
    repo_url: str


class IndexResponse(BaseModel):
    task_id: str
    status: str
    repo_id: int | None = None