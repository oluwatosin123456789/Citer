import json
import queue
import threading
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.graph import build_graph
from app.agent.llm import get_chat_model
from app.agent.memory import (
    get_or_create_session,
    load_history,
    save_message,
)
from app.core.logger import logger
from app.db.models import Repo, Session as SessionModel
from app.db.session import SessionLocal
from app.schemas.ask import AskRequest

router = APIRouter(tags=["ask"])


def resolve_repo(db: Session, repo_url: str | None, session_id: str | None) -> Repo:
    if repo_url:
        repo = db.execute(
            select(Repo).where(Repo.url == repo_url.strip())
        ).scalar_one_or_none()
        if repo is None:
            raise HTTPException(status_code=400, detail="repo not indexed yet - call /api/index first")
        return repo
    if session_id:
        session = db.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        ).scalar_one_or_none()
        if session and session.repo_id:
            return db.get(Repo, session.repo_id)
    repo = db.execute(
        select(Repo).where(Repo.status == "ready").order_by(Repo.id.desc())
    ).scalars().first()
    if repo is None:
        raise HTTPException(status_code=400, detail="no indexed repo found")
    return repo


def _run_agent(
    session_id: str,
    question: str,
    repo_id: int,
    history: list[dict],
    mailbox: queue.Queue,
) -> None:
    db = SessionLocal()
    try:
        graph = build_graph(db, model=get_chat_model())
        state = {
            "question": question,
            "repo_id": repo_id,
            "session_id": session_id,
            "messages": history,
            "context": [],
            "tool_calls": [],
            "iterations": 0,
        }
        final = None
        for event in graph.stream(state, config={"configurable": {"token_queue": mailbox}}):
            for node, update in event.items():
                mailbox.put(("node", node, update))
                if node == "synthesize":
                    final = update
                    mailbox.put(("citations", update.get("citations", [])))

        if final:
            save_message(db, session_id, "user", question, None)
            save_message(
                db,
                session_id,
                "assistant",
                final.get("answer", ""),
                final.get("citations", []),
            )
        mailbox.put(("done", session_id))
    except Exception as exc:
        logger.exception("agent run failed")
        mailbox.put(("error", str(exc)))
    finally:
        db.close()


def _sse(mailbox: queue.Queue) -> None:
    while True:
        kind, *payload = mailbox.get()
        if kind == "node":
            node, update = payload
            data = json.dumps({"node": node})
            yield f"event: node\ndata: {data}\n\n"
        elif kind == "token":
            data = json.dumps({"text": payload[0]})
            yield f"event: token\ndata: {data}\n\n"
        elif kind == "citations":
            data = json.dumps(payload[0])
            yield f"event: citations\ndata: {data}\n\n"
        elif kind == "error":
            data = json.dumps({"message": payload[0]})
            yield f"event: error\ndata: {data}\n\n"
            break
        elif kind == "done":
            data = json.dumps({"session_id": payload[0]})
            yield f"event: done\ndata: {data}\n\n"
            break


@router.post("/ask")
async def ask(req: AskRequest) -> StreamingResponse:
    db = SessionLocal()
    try:
        repo = resolve_repo(db, req.repo_url, req.session_id)
        session_id = get_or_create_session(db, req.session_id, repo.id)
        history = load_history(db, session_id)
    finally:
        db.close()

    mailbox: queue.Queue = queue.Queue()
    threading.Thread(
        target=_run_agent,
        args=(session_id, req.question, repo.id, history, mailbox),
        daemon=True,
    ).start()

    return StreamingResponse(_sse(mailbox), media_type="text/event-stream")