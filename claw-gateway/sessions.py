"""
会话管理路由 /api/sessions/*
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import uuid
import time

from claw_gateway.database import get_session_local, Session, Message
from claw_gateway.auth.jwt import verify_token

router = APIRouter()


class SessionCreate(BaseModel):
    title: str = ""


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: float
    updated_at: float
    archived: bool


# ============ 路由实现 ============

@router.get("/")
async def list_sessions(authorization: str = None):
    """列出用户所有会话"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证 Token")
    token = authorization.split(" ", 1)[1]
    user = verify_token(token)

    db = get_session_local()()
    try:
        sessions = db.query(Session).filter(
            Session.user_id == user["open_id"],
            Session.archived == False,
        ).order_by(Session.updated_at.desc()).all()

        return [
            SessionResponse(
                id=s.id,
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at,
                archived=s.archived,
            )
            for s in sessions
        ]
    finally:
        db.close()


@router.post("/")
async def create_session(body: SessionCreate, authorization: str = None):
    """创建新会话"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证 Token")
    token = authorization.split(" ", 1)[1]
    user = verify_token(token)

    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    now = time.time()

    db = get_session_local()()
    try:
        session = Session(
            id=session_id,
            user_id=user["open_id"],
            title=body.title or "新对话",
            created_at=now,
            updated_at=now,
        )
        db.add(session)
        db.commit()

        return SessionResponse(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            archived=session.archived,
        )
    finally:
        db.close()


@router.get("/{session_id}")
async def get_session(session_id: str, authorization: str = None):
    """获取会话详情"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证 Token")
    token = authorization.split(" ", 1)[1]
    user = verify_token(token)

    db = get_session_local()()
    try:
        session = db.query(Session).filter(
            Session.id == session_id,
            Session.user_id == user["open_id"],
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        return {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
        }
    finally:
        db.close()


@router.delete("/{session_id}")
async def delete_session(session_id: str, authorization: str = None):
    """删除会话"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证 Token")
    token = authorization.split(" ", 1)[1]
    user = verify_token(token)

    db = get_session_local()()
    try:
        session = db.query(Session).filter(
            Session.id == session_id,
            Session.user_id == user["open_id"],
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        db.delete(session)
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()


@router.get("/{session_id}/messages")
async def get_messages(session_id: str, authorization: str = None):
    """获取会话历史消息"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证 Token")
    token = authorization.split(" ", 1)[1]
    user = verify_token(token)

    db = get_session_local()()
    try:
        session = db.query(Session).filter(
            Session.id == session_id,
            Session.user_id == user["open_id"],
        ).first()

        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")

        messages = db.query(Message).filter(
            Message.session_id == session_id,
        ).order_by(Message.created_at).all()

        import json
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "tool_calls": json.loads(m.tool_calls) if m.tool_calls else None,
                "created_at": m.created_at,
            }
            for m in messages
        ]
    finally:
        db.close()
