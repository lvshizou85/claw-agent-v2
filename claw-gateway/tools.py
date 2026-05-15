"""
工具路由 /api/tools/*
MCP 工具注册 + 权限过滤
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import uuid

from claw_gateway.auth.jwt import verify_token
from claw_gateway.hooks.permission import ROLE_DEFAULTS

router = APIRouter()


# MCP 工具注册存储（内存，生产环境应使用数据库）
_mcp_tools: dict[str, dict] = {}


# ============ 请求/响应模型 ============

class MCPServerConfig(BaseModel):
    """MCP 服务器配置"""
    type: str = "stdio"  # stdio / sse / http / sdk
    command: Optional[str] = None
    args: list[str] = []
    env: dict[str, str] = {}
    url: Optional[str] = None
    headers: dict[str, str] = {}
    name: Optional[str] = None


class RegisterToolRequest(BaseModel):
    """注册工具请求"""
    name: str
    description: str
    category: str
    mcp_server: Optional[MCPServerConfig] = None
    enabled: bool = True


class ToolResponse(BaseModel):
    """工具响应"""
    id: str
    name: str
    description: str
    category: str
    enabled: bool
    mcp_config: dict | None = None


# ============ 端点 ============

@router.get("/")
async def list_tools(authorization: str = None):
    """
    列出可用工具（含权限过滤）
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证 Token")
    token = authorization.split(" ", 1)[1]
    user = verify_token(token)

    role = user.get("role", "guest")
    role_config = ROLE_DEFAULTS.get(role, ROLE_DEFAULTS["guest"])
    allowed = set(role_config.get("allowed_tools", []))
    denied = set(role_config.get("denied_tools", []))

    # 所有可用工具定义
    ALL_TOOLS = [
        {"name": "对话", "description": "与 AI 对话", "category": "基础"},
        {"name": "周报生成", "description": "生成周报内容", "category": "办公"},
        {"name": "文档摘要", "description": "对文档进行摘要", "category": "办公"},
        {"name": "飞书消息汇总", "description": "汇总飞书消息", "category": "飞书"},
        {"name": "服务器操作", "description": "执行服务器命令", "category": "运维"},
        {"name": "数据库写入", "description": "写入数据库", "category": "运维"},
        {"name": "git_push", "description": "git 推送", "category": "开发"},
        {"name": "代码审查", "description": "审查代码", "category": "开发"},
        {"name": "Bug分析", "description": "分析 Bug", "category": "开发"},
        {"name": "Shell命令", "description": "执行 Shell 命令", "category": "开发"},
        {"name": "财务报表", "description": "查看财务报表", "category": "财务"},
        {"name": "报销审核", "description": "审核报销", "category": "财务"},
        {"name": "内容创作", "description": "创作内容", "category": "创作"},
    ]

    # 按权限过滤
    if "*" in allowed:
        tools = ALL_TOOLS
    else:
        tools = [t for t in ALL_TOOLS if t["name"] in allowed]

    # 排除黑名单
    if "*" in denied:
        tools = []
    else:
        tools = [t for t in tools if t["name"] not in denied]

    # 添加 MCP 自定义工具
    for tool_id, tool in _mcp_tools.items():
        if tool.get("enabled"):
            tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "category": tool.get("category", "自定义"),
                "mcp_tool_id": tool_id,
            })

    return {
        "role": role,
        "tools": tools,
    }


@router.post("/register")
async def register_tool(
    request: RegisterToolRequest,
    authorization: str = None,
):
    """
    注册 MCP 工具（仅管理员）
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证 Token")
    token = authorization.split(" ", 1)[1]
    user = verify_token(token)

    # 仅管理员可注册工具
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可注册工具")

    tool_id = f"mcp_{uuid.uuid4().hex[:8]}"
    tool = {
        "id": tool_id,
        "name": request.name,
        "description": request.description,
        "category": request.category,
        "enabled": request.enabled,
        "mcp_config": request.mcp_server.model_dump() if request.mcp_server else None,
    }
    
    _mcp_tools[tool_id] = tool
    
    return {
        "status": "ok",
        "tool_id": tool_id,
        "tool": tool,
    }


@router.get("/mcp")
async def list_mcp_tools(authorization: str = None):
    """
    列出所有已注册的 MCP 工具
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证 Token")
    token = authorization.split(" ", 1)[1]
    user = verify_token(token)

    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可查看 MCP 工具")

    return {
        "tools": [
            {
                "id": tool_id,
                "name": tool["name"],
                "description": tool["description"],
                "category": tool.get("category"),
                "enabled": tool.get("enabled", True),
                "has_mcp_config": tool.get("mcp_config") is not None,
            }
            for tool_id, tool in _mcp_tools.items()
        ],
    }


@router.put("/mcp/{tool_id}")
async def update_mcp_tool(
    tool_id: str,
    enabled: bool | None = None,
    authorization: str = None,
):
    """
    更新 MCP 工具状态
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证 Token")
    token = authorization.split(" ", 1)[1]
    user = verify_token(token)

    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可更新工具")

    if tool_id not in _mcp_tools:
        raise HTTPException(status_code=404, detail="工具不存在")

    if enabled is not None:
        _mcp_tools[tool_id]["enabled"] = enabled

    return {
        "status": "ok",
        "tool": _mcp_tools[tool_id],
    }


@router.delete("/mcp/{tool_id}")
async def delete_mcp_tool(
    tool_id: str,
    authorization: str = None,
):
    """
    删除 MCP 工具
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证 Token")
    token = authorization.split(" ", 1)[1]
    user = verify_token(token)

    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可删除工具")

    if tool_id not in _mcp_tools:
        raise HTTPException(status_code=404, detail="工具不存在")

    del _mcp_tools[tool_id]

    return {
        "status": "ok",
        "message": f"Tool {tool_id} deleted",
    }


def get_mcp_tool_config(tool_id: str) -> dict | None:
    """
    获取 MCP 工具配置（供其他模块使用）
    """
    return _mcp_tools.get(tool_id)


def get_all_mcp_configs() -> list[dict]:
    """
    获取所有启用的 MCP 配置
    """
    return [
        tool["mcp_config"]
        for tool in _mcp_tools.values()
        if tool.get("enabled") and tool.get("mcp_config")
    ]
