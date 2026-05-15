"""
审计 Hook
记录 tool_call / login / logout 事件到 audit_logs 表
"""

import json
import time
import uuid
from typing import Any

from claw_gateway.database import get_session_local, AuditLog


def write_audit_log(
    event: str,
    action: str,
    user_id: str | None = None,
    session_id: str | None = None,
    detail: dict | None = None,
    decision: str | None = None,
    reason: str | None = None,
    level: str = "INFO",
) -> AuditLog | None:
    """
    写入审计日志
    
    Args:
        event: 事件类型 (tool_call / login / logout / permission_deny)
        action: 具体动作描述
        user_id: 用户 ID
        session_id: 会话 ID
        detail: 详细信息 (dict，会序列化为 JSON)
        decision: 决策 (allow / deny)
        reason: 拒绝原因
        level: 日志级别 (INFO / WARN / ERROR)
    
    Returns:
        AuditLog: 创建的审计日志记录
    """
    db = get_session_local()()
    try:
        audit_log = AuditLog(
            id=f"audit_{uuid.uuid4().hex[:12]}",
            timestamp=time.time(),
            level=level,
            event=event,
            user_id=user_id,
            session_id=session_id,
            action=action,
            detail=json.dumps(detail, ensure_ascii=False) if detail else None,
            decision=decision,
            reason=reason,
        )
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log
    except Exception as e:
        db.rollback()
        print(f"Failed to write audit log: {e}")
        return None
    finally:
        db.close()


def build_audit_hook(session_context: dict):
    """
    构建 Qoder SDK post_tool_use Hook
    记录工具调用审计日志
    """
    user = session_context.get("user", session_context)
    user_id = user.get("user_id")
    session_id = session_context.get("session_id")
    role = user.get("role", "guest")

    def audit_hook(input_data: dict, output_data: Any, context: dict) -> dict:
        """
        审计 Hook 回调
        
        Args:
            input_data: 包含 hook_event_name, tool_name, tool_input 等
            output_data: 工具执行结果
            context: 上下文信息
        
        Returns:
            dict: Hook 输出（这里直接透传）
        """
        tool_name = input_data.get("tool_name", "unknown")
        tool_input = input_data.get("tool_input", {})
        
        # 记录审计日志
        write_audit_log(
            event="tool_call",
            action=f"execute:{tool_name}",
            user_id=user_id,
            session_id=session_id,
            detail={
                "tool_name": tool_name,
                "tool_input": tool_input,
                "output_type": type(output_data).__name__,
                "role": role,
            },
            decision="allow",
            level="INFO",
        )
        
        return {}

    return audit_hook


def log_login(
    user_id: str,
    username: str,
    login_type: str = "jwt",
    success: bool = True,
    reason: str | None = None,
):
    """
    记录登录事件
    
    Args:
        user_id: 用户 ID
        username: 用户名
        login_type: 登录类型 (jwt / oauth2 / sso)
        success: 是否成功
        reason: 失败原因
    """
    write_audit_log(
        event="login",
        action=f"login:{login_type}",
        user_id=user_id,
        detail={
            "username": username,
            "login_type": login_type,
            "success": success,
        },
        decision="allow" if success else "deny",
        reason=reason,
        level="INFO" if success else "WARN",
    )


def log_logout(
    user_id: str,
    reason: str | None = None,
):
    """
    记录登出事件
    
    Args:
        user_id: 用户 ID
        reason: 登出原因 (主动 / 超时 / 被踢)
    """
    write_audit_log(
        event="logout",
        action="logout",
        user_id=user_id,
        detail={
            "reason": reason or "normal",
        },
        level="INFO",
    )


def log_permission_deny(
    user_id: str | None,
    session_id: str | None,
    tool_name: str,
    role: str,
    reason: str,
):
    """
    记录权限拒绝事件
    
    Args:
        user_id: 用户 ID
        session_id: 会话 ID
        tool_name: 被拒绝的工具名
        role: 用户角色
        reason: 拒绝原因
    """
    write_audit_log(
        event="permission_deny",
        action=f"deny:{tool_name}",
        user_id=user_id,
        session_id=session_id,
        detail={
            "tool_name": tool_name,
            "role": role,
        },
        decision="deny",
        reason=reason,
        level="WARN",
    )


def get_audit_logs(
    user_id: str | None = None,
    session_id: str | None = None,
    event: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """
    查询审计日志
    
    Args:
        user_id: 按用户过滤
        session_id: 按会话过滤
        event: 按事件类型过滤
        limit: 返回条数限制
    
    Returns:
        list[dict]: 审计日志列表
    """
    db = get_session_local()()
    try:
        query = db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if session_id:
            query = query.filter(AuditLog.session_id == session_id)
        if event:
            query = query.filter(AuditLog.event == event)
        
        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        return [
            {
                "id": log.id,
                "timestamp": log.timestamp,
                "level": log.level,
                "event": log.event,
                "user_id": log.user_id,
                "session_id": log.session_id,
                "action": log.action,
                "detail": json.loads(log.detail) if log.detail else None,
                "decision": log.decision,
                "reason": log.reason,
            }
            for log in logs
        ]
    finally:
        db.close()
