"""
对话路由 /api/chat/*
SSE 流式响应 + Qoder SDK 集成 + 消息入库
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json
import uuid
import time

from claw_gateway.auth.jwt import verify_token
from claw_gateway.database import get_session_local, Session, Message, User
from claw_gateway.services.qoder import chat_stream

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


def get_current_user(token: str = Depends(lambda: None)):
    """从 Authorization Header 获取用户"""
    def _get(token_str: str = None):
        if not token_str:
            raise HTTPException(status_code=401, detail="未提供认证 Token")
        try:
            return verify_token(token_str)
        except Exception:
            raise HTTPException(status_code=401, detail="Token 无效或已过期")
    return _get


def _ensure_session(session_id: str, user_id: str, db) -> Session:
    """确保会话存在，不存在则创建"""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        # 创建新会话
        session = Session(
            id=session_id,
            user_id=user_id,
            title="新对话",
            created_at=time.time(),
            updated_at=time.time(),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def _save_message(session_id: str, role: str, content: str, tool_calls: str | None = None) -> Message | None:
    """保存消息到数据库"""
    db = get_session_local()()
    try:
        message = Message(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            created_at=time.time(),
        )
        db.add(message)
        
        # 更新 session.updated_at
        session = db.query(Session).filter(Session.id == session_id).first()
        if session:
            session.updated_at = time.time()
        
        db.commit()
        db.refresh(message)
        return message
    except Exception as e:
        db.rollback()
        print(f"Failed to save message: {e}")
        return None
    finally:
        db.close()


@router.post("/stream")
async def chat_stream_endpoint(
    request: ChatRequest,
    authorization: str = None,
):
    """
    SSE 流式对话接口
    
    请求：
    POST /api/chat/stream
    Authorization: Bearer <jwt>
    Body: {"session_id": "sess_xxx", "message": "帮我生成周报"}
    
    响应：SSE Stream
    """
    # 验证 Token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证 Token")
    
    token = authorization.split(" ", 1)[1]
    try:
        user = verify_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")

    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:12]}"

    async def event_generator():
        db = get_session_local()()
        try:
            # 确保会话存在
            _ensure_session(session_id, user["open_id"], db)
            
            # 保存用户消息
            _save_message(session_id, "user", request.message)
        finally:
            db.close()

        # 用于收集 assistant 的完整响应
        assistant_content_parts = []
        assistant_tool_calls = []
        is_tool_call = False
        current_tool_call = None
        
        try:
            # 构建用户上下文
            session_context = {
                "user_id": user["open_id"],
                "user_name": user["name"],
                "role": user["role"],
                "session_id": session_id,
            }

            # 调用 Qoder SDK
            async for msg in chat_stream(
                prompt=request.message,
                session_context=session_context,
            ):
                msg_type = msg.get("type", "")
                
                # 收集文本内容用于保存
                if msg_type == "text":
                    assistant_content_parts.append(msg.get("content", ""))
                elif msg_type == "tool_call":
                    is_tool_call = True
                    tool_info = {
                        "id": msg.get("id", ""),
                        "tool": msg.get("tool", ""),
                        "input": msg.get("input", {}),
                    }
                    assistant_tool_calls.append(tool_info)
                    current_tool_call = tool_info
                elif msg_type == "tool_result":
                    is_tool_call = False
                    current_tool_call = None
                
                # SSE 格式：data: {...}\n\n
                yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
            
            # 保存 assistant 消息
            final_content = "".join(assistant_content_parts)
            tool_calls_json = json.dumps(assistant_tool_calls) if assistant_tool_calls else None
            _save_message(session_id, "assistant", final_content, tool_calls_json)
            
            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    authorization: str = None,
):
    """获取对话历史"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证 Token")
    
    token = authorization.split(" ", 1)[1]
    try:
        user = verify_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")

    db = get_session_local()()
    try:
        # 验证会话归属
        session = db.query(Session).filter(
            Session.id == session_id,
            Session.user_id == user["open_id"],
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 获取消息列表
        messages = db.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at).all()
        
        return {
            "session": {
                "id": session.id,
                "title": session.title,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
            },
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "tool_calls": json.loads(m.tool_calls) if m.tool_calls else None,
                    "created_at": m.created_at,
                }
                for m in messages
            ],
        }
    finally:
        db.close()


@router.delete("/history/{session_id}")
async def delete_chat_history(
    session_id: str,
    authorization: str = None,
):
    """删除对话"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证 Token")
    
    token = authorization.split(" ", 1)[1]
    try:
        user = verify_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")

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
        
        return {"status": "ok", "message": "会话已删除"}
    finally:
        db.close()
