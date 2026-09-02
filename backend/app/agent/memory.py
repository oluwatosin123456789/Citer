import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Message, Session as SessionModel


def get_or_create_session(db: Session, session_id: str | None, repo_id: int) -> str:
    if session_id:
        return session_id
    session = SessionModel(id=uuid.uuid4().hex, repo_id=repo_id)
    db.add(session)
    db.commit()
    return session.id


def load_history(db: Session, session_id: str, limit: int = 20) -> list[dict]:
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.id)
        .limit(limit)
    )
    return [
        {"role": m.role, "content": m.content}
        for m in db.execute(stmt).scalars()
    ]


def save_message(
    db: Session,
    session_id: str,
    role: str,
    content: str,
    citations: list[dict] | None = None,
) -> None:
    db.add(
        Message(
            session_id=session_id,
            role=role,
            content=content,
            citations=citations,
        )
    )
    db.commit()