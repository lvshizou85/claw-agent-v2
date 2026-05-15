# Claw Agent — 详细规格说明 (SPEC.md)

> 本文档是 CLAW.md 的补充，提供每个模块的详细实现规格。

---

## A. Claw Gateway 详细规格

### A1. main.py 入口

```python
# claw-gateway/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from claw_gateway.auth.router import router as auth_router
from claw_gateway.routes import chat, sessions, tools
from claw_gateway.database.schema import init_db

app = FastAPI(title="Claw Gateway", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 开发环境
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
init_db()

# 注册路由
app.include_router(auth_router, prefix="/auth", tags=["认证"])
app.include_router(chat.router, prefix="/api/chat", tags=["对话"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["会话"])
app.include_router(tools.router, prefix="/api/tools", tags=["工具"])

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
```

### A2. 配置 config.py

```python
# claw-gateway/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # 飞书 OAuth2
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_redirect_uri: str = "http://localhost:8000/auth/callback"
    feishu_api_base: str = "https://open.feishu.cn/open-apis"

    # 数据库
    database_url: str = "sqlite:///./claw.db"

    # JWT
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120

    # Qoder SDK
    qoder_cli_path: str = ""  # 空=用pip安装的
    qoder_license_key: str = ""

    # 前端
    frontend_url: str = "http://localhost:5173"

    # 认证开关（开发调试用，默认关闭）
    # False = guest 模式，跳过飞书 OAuth，直接以 guest 用户运行
    # True = 启用飞书 OAuth2 认证
    auth_enabled: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### A3. 飞书认证 feishu.py

```python
# claw-gateway/auth/feishu.py
import httpx
from settings import get_settings

settings = get_settings()

FEISHU_TOKEN_URL = f"{settings.feishu_api_base}/authen/v1/oidc/access_token"
FEISHU_USERINFO_URL = f"{settings.feishu_api_base}/contact/v3/users/me"

async def exchange_code_for_token(code: str) -> dict:
    """用授权码换取飞书 Access Token"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            FEISHU_TOKEN_URL,
            json={
                "grant_type": "authorization_code",
                "code": code,
                "app_id": settings.feishu_app_id,
                "app_secret": settings.feishu_app_secret,
            }
        )
        resp.raise_for_status()
        return resp.json()

async def get_user_info(access_token: str) -> dict:
    """获取用户基本信息"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            FEISHU_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            params={"user_id_type": "open_id"}
        )
        resp.raise_for_status()
        return resp.json()
```

### A4. JWT 工具 jwt.py

```python
# claw-gateway/auth/jwt.py
import jwt
from datetime import datetime, timedelta
from settings import get_settings

settings = get_settings()

def create_token(user_id: str, open_id: str, name: str, role: str = "guest") -> str:
    """生成 JWT Token"""
    payload = {
        "sub": user_id,
        "open_id": open_id,
        "name": name,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def verify_token(token: str) -> dict:
    """验证并解码 JWT Token"""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
```

### A5. 权限 Hook permission.py

```python
# claw-gateway/hooks/permission.py
from qoder_agent_sdk import PermissionResultAllow, PermissionResultDeny

def build_permission_hook(session_context: dict):
    """
    构建 Qoder SDK pre_tool_use Hook。
    根据外层 RBAC 注入的用户上下文，在工具调用前做权限拦截。
    """
    user = session_context.get("user", {})
    role = user.get("role", "guest")
    allowed = set(user.get("allowed_tools", []))
    denied = set(user.get("denied_tools", []))
    max_file_size_mb = user.get("max_file_size_mb", 20)

    def permission_hook(input_data: dict, tool_use_id: str, context: dict) -> dict:
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # 1. 黑名单检查
        if tool_name in denied or "*" in denied:
            return {
                "permissionDecision": "deny",
                "permissionDecisionReason": f"[{role}] 角色无权调用 {tool_name}"
            }

        # 2. 白名单检查（非空时生效）
        if allowed and "*" not in allowed and tool_name not in allowed:
            return {
                "permissionDecision": "deny",
                "permissionDecisionReason": f"工具 [{tool_name}] 不在 [{role}] 可用列表中"
            }

        # 3. 参数级限制
        updated_input = tool_input.copy()
        if tool_name in ["文件读取", "文件写入"]:
            # 限制文件操作路径
            pass

        return {
            "permissionDecision": "allow",
            "updatedInput": updated_input
        }

    return permission_hook
```

### A6. 审计 Hook audit.py

```python
# claw-gateway/hooks/audit.py
import json
import time
import uuid
from datetime import datetime

async def audit_hook(input_data: dict, tool_use_id: str, context: dict) -> dict:
    """Qoder SDK post_tool_use Hook，写入审计日志"""
    user = context.get("user", {})
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    decision = input_data.get("permissionDecision", "unknown")

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": "INFO" if decision == "allow" else "WARN",
        "event": "tool_call",
        "log_id": f"log_{uuid.uuid4().hex[:12]}",
        "user_id": user.get("user_id", ""),
        "user_name": user.get("name", ""),
        "role": user.get("role", ""),
        "session_id": context.get("session_id", ""),
        "tool_name": tool_name,
        "tool_input": tool_input,
        "decision": decision,
        "reason": input_data.get("permissionDecisionReason", ""),
        "tool_use_id": tool_use_id,
    }

    # 写入审计日志（可接 Elasticsearch / Loki）
    print(f"[AUDIT] {json.dumps(log_entry)}")

    return {}
```

---

## B. 数据库模型

```python
# claw-gateway/database/schema.py
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import time

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)       # open_id
    name = Column(String)
    department = Column(String)
    role = Column(String, default="guest")
    created_at = Column(Float, default=time.time)

class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)       # sess_xxx
    user_id = Column(String, ForeignKey("users.id"), index=True)
    title = Column(String, default="")
    cwd = Column(String, default="")
    pinned = Column(Boolean, default=False)
    archived = Column(Boolean, default=False)
    created_at = Column(Float, default=time.time)
    updated_at = Column(Float, default=time.time)

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), index=True)
    role = Column(String)                      # user / assistant / system
    content = Column(Text)
    tool_calls = Column(Text)                  # JSON
    created_at = Column(Float, default=time.time)

    session = relationship("Session", back_populates="messages")

class UserCredential(Base):
    __tablename__ = "user_credentials"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    system = Column(String)                     # feishu / erp / crm
    auth_type = Column(String)                  # oauth2 / api_key
    encrypted_token = Column(Text)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(Float)
    scope = Column(Text)
    created_at = Column(Float, default=time.time)

def init_db():
    from sqlalchemy import create_engine
    from settings import get_settings
    settings = get_settings()
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(engine)
```

---

## C. Qoder SDK 使用规格

### C1. query() 基本用法

```python
from qoder_agent_sdk import query, Options

async def chat(prompt: str, context: dict):
    async for msg in query(
        prompt=prompt,
        options=Options(
            max_turns=10,
            permission_mode="acceptedEdits",
        ),
        context=context
    ):
        yield msg
```

### C2. QoderAgentSDKClient（支持 Hook）

```python
from qoder_agent_sdk import QoderAgentSDKClient, Options, Hooks, HookMatcher

async with QoderAgentSDKClient(options=Options(
    allowed_tools=["周报生成", "飞书消息汇总"],
    hooks=Hooks(
        pre_tool_use=[HookMatcher(matcher=".*", hooks=[permission_hook])],
        post_tool_use=[HookMatcher(matcher=".*", hooks=[audit_hook])],
    )
)) as client:
    await client.query(user_message)
    async for msg in client.receive_response():
        yield msg
```

### C3. 自定义 MCP 工具

```python
from qoder_agent_sdk import tool, create_sdk_mcp_server

@tool("生成周报", "根据输入生成周报内容", {
    "period": str,      # 周报周期，如 "本周"
    "department": str,  # 部门
})
async def generate_weekly_report(args):
    # 实际调用飞书/ERP 获取数据，生成周报
    content = await fetch_data_and_generate(args["period"], args["department"])
    return {"content": [{"type": "text", "text": content}]}

mcp_server = create_sdk_mcp_server(
    name="enterprise-tools",
    version="1.0.0",
    tools=[generate_weekly_report]
)

options = Options(
    mcp_servers={"enterprise": mcp_server},
    allowed_tools=["mcp__enterprise-tools__生成周报"],
)
```

---

## D. 前端 SSE 客户端

```typescript
// claw-ui/src/hooks/useSSE.ts
import { useState, useCallback, useRef } from 'react';

interface SSEOptions {
  onMessage: (data: any) => void;
  onDone: () => void;
  onError: (err: Error) => void;
}

export function useSSE(url: string, options: SSEOptions) {
  const eventSourceRef = useRef<EventSource | null>(null);

  const send = useCallback((body: object) => {
    // 由于 SSE 不支持 POST，我们用 Fetch + ReadableStream
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify(body),
    }).then(async (res) => {
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            if (data.done) {
              options.onDone();
            } else {
              options.onMessage(data);
            }
          }
        }
      }
    }).catch(options.onError);
  }, [url, options]);

  return { send };
}
```

---

## E. RBAC 初始数据

```python
# scripts/seed_rbac.py
ROLES_PERMISSIONS = {
    "admin": {
        "description": "管理员",
        "allowed_tools": ["*"],
        "denied_tools": [],
    },
    "sales": {
        "description": "销售部",
        "allowed_tools": ["对话", "周报生成", "飞书消息汇总", "文档摘要", "内容创作"],
        "denied_tools": ["服务器操作", "数据库写入", "git_push", "代码执行"],
    },
    "developer": {
        "description": "研发部",
        "allowed_tools": ["对话", "代码审查", "Bug分析", "文档生成", "周报生成", "Shell命令"],
        "denied_tools": ["财务数据访问"],
    },
    "finance": {
        "description": "财务部",
        "allowed_tools": ["对话", "财务报表", "报销审核", "飞书消息汇总", "周报生成"],
        "denied_tools": ["服务器操作", "代码执行"],
    },
    "guest": {
        "description": "访客",
        "allowed_tools": ["对话", "文档摘要"],
        "denied_tools": ["*"],
    },
}

# 飞书部门到角色的默认映射
DEPARTMENT_ROLE_MAP = {
    "销售部": "sales",
    "研发部": "developer",
    "财务部": "finance",
    "信息安全部": "admin",
}
```
