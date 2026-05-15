"""
权限 Hook
基于 RBAC 的工具调用拦截
"""

from claw_gateway.database import get_session_local, User

# RBAC 默认权限配置（可在数据库中覆盖）
ROLE_DEFAULTS = {
    "admin": {
        "allowed_tools": ["*"],
        "denied_tools": [],
        "max_file_size_mb": 100,
    },
    "sales": {
        "allowed_tools": ["周报生成", "飞书消息汇总", "文档摘要", "内容创作", "对话"],
        "denied_tools": ["服务器操作", "数据库写入", "git_push", "代码执行"],
        "max_file_size_mb": 20,
    },
    "developer": {
        "allowed_tools": ["代码审查", "Bug分析", "文档生成", "周报生成", "Shell命令", "对话"],
        "denied_tools": ["财务数据访问"],
        "max_file_size_mb": 50,
    },
    "finance": {
        "allowed_tools": ["财务报表", "报销审核", "飞书消息汇总", "周报生成", "对话"],
        "denied_tools": ["服务器操作", "代码执行"],
        "max_file_size_mb": 20,
    },
    "guest": {
        "allowed_tools": ["对话", "文档摘要"],
        "denied_tools": ["*"],
        "max_file_size_mb": 5,
    },
}


def build_permission_hook(session_context: dict):
    """
    构建 Qoder SDK pre_tool_use Hook
    根据外层 RBAC 注入的用户上下文，在工具调用前做权限拦截
    """
    user = session_context.get("user", session_context)
    role = user.get("role", "guest")
    
    # 优先用数据库中的用户权限，否则用默认值
    db = get_session_local()()
    try:
        db_user = db.query(User).filter(User.id == user.get("user_id")).first()
        if db_user and db_user.role:
            role = db_user.role
    except Exception:
        pass
    finally:
        db.close()
    
    role_config = ROLE_DEFAULTS.get(role, ROLE_DEFAULTS["guest"])
    allowed = set(role_config.get("allowed_tools", []))
    denied = set(role_config.get("denied_tools", []))
    max_file_size_mb = role_config.get("max_file_size_mb", 20)

    def permission_hook(input_data: dict, tool_use_id: str, context: dict) -> dict:
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # 1. 黑名单检查
        if "*" in denied or tool_name in denied:
            return {
                "permissionDecision": "deny",
                "permissionDecisionReason": f"[{role}] 角色无权调用 {tool_name}"
            }

        # 2. 白名单检查（非空时生效，* 表示全部允许）
        if allowed and "*" not in allowed and tool_name not in allowed:
            return {
                "permissionDecision": "deny",
                "permissionDecisionReason": f"工具 [{tool_name}] 不在 [{role}] 可用列表中"
            }

        # 3. 参数级限制
        updated_input = tool_input.copy()
        if "file" in tool_input or "path" in tool_input:
            # 可以限制文件大小、路径范围等
            if tool_input.get("size_mb", 0) > max_file_size_mb:
                return {
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"文件大小超过 [{role}] 角色限制 ({max_file_size_mb}MB)"
                }

        return {
            "permissionDecision": "allow",
            "updatedInput": updated_input
        }

    return permission_hook
