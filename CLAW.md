# Claw Agent — Agent 可执行版开发计划

> 本文档面向 AI Agent，描述如何从零构建 Claw 企业版 AI 助理应用。
> 所有决策、路径、接口均已明确，Agent 应严格按本计划执行。
> 如需偏离计划中的架构决策，必须先与用户确认。

---

## 一、项目概述

### 1.1 项目目标

基于 Qoder SDK 构建企业级 AI 助理应用（Claw），让企业普通用户（非程序员）也能使用 AI 能力。

### 1.2 核心约束

| 约束 | 说明 |
|------|------|
| 内核依赖 | Qoder SDK（闭源专有），不可修改内核 |
| 技术栈 | Python（后端）+ React + Vite（前端） |
| 认证 | 飞书 OAuth2 |
| 数据库 | SQLite（初期）→ PostgreSQL（后期） |

### 1.3 成功标准

- 用户可在 Web 界面与 AI 对话，SSE 流式输出
- RBAC 权限控制生效
- 飞书 OAuth2 登录
- 操作审计日志完整
- 接口响应 P99 < 3s

---

## 二、系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Claw Web UI                          │
│  React + Vite + Tailwind + SSE                         │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────▼────────────────────────────────┐
│               Claw Gateway (Python FastAPI)               │
│                                                         │
│  ├── auth/         飞书 OAuth2 认证                     │
│  ├── middleware/   Session 管理 + RBAC + Rate Limit      │
│  ├── routes/       SSE 流式 + 会话 + 工具路由           │
│  ├── hooks/        权限拦截 Hook（核心）                 │
│  └── vault/        个人凭证库                           │
└────────────────────────┬────────────────────────────────┘
                         │ Python
┌────────────────────────▼────────────────────────────────┐
│              Qoder SDK（Python）                         │
│  src/qoder_agent_sdk/                                    │
│  - query() / QoderAgentSDKClient                        │
│  - Hooks: pre_tool_use / post_tool_use                  │
│  - MCP: create_sdk_mcp_server + @tool 装饰器            │
└────────────────────────┬────────────────────────────────┘
                         │ stdin/stdout JSON-RPC
┌────────────────────────▼────────────────────────────────┐
│              Qoder CLI（闭源内核）                       │
└─────────────────────────────────────────────────────────┘
```

---

## 三、目录结构

```
claw-agent/
├── CLAW.md                    ← Agent 开发计划（本文件）
├── SPEC.md                    ← 详细规格说明（见 §十四）
├── README.md                  ← 项目说明
│
├── claw-gateway/              ← Python FastAPI 后端
│   ├── main.py                ← 入口，FastAPI app 初始化
│   ├── requirements.txt
│   ├── config.py              ← 配置（飞书 App ID/Secret 等）
│   ├── auth/
│   │   ├── router.py          ← /auth/* 路由
│   │   ├── feishu.py          ← 飞书 OAuth2 实现
│   │   └── jwt.py             ← JWT Token 生成与验证
│   ├── middleware/
│   │   ├── session.py          ← Session 中间件
│   │   └── rbac.py            ← RBAC 权限中间件
│   ├── routes/
│   │   ├── chat.py            ← /api/chat/stream（SSE）
│   │   ├── sessions.py        ← /api/sessions/*
│   │   └── tools.py           ← /api/tools/*
│   ├── hooks/
│   │   ├── permission.py       ← RBAC 权限 Hook
│   │   └── audit.py           ← 审计日志 Hook
│   ├── vault/
│   │   ├── models.py          ← UserCredential 模型
│   │   ├── storage.py         ← 加密存储
│   │   └── oauth_refresh.py   ← Token 自动刷新
│   ├── models/
│   │   ├── session.py          ← Session / Message 模型
│   │   └── rbac.py            ← Role / Permission 模型
│   └── database/
│       ├── schema.py           ← SQLAlchemy 模型
│       └── migrations/         ← Alembic 迁移
│
├── claw-ui/                   ← React 前端
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   ├── client.ts      ← API 客户端
│   │   │   └── auth.ts        ← 认证 API
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx  ← 对话窗口（SSE）
│   │   │   ├── ChatInput.tsx  ← 输入框
│   │   │   ├── MessageList.tsx
│   │   │   ├── SessionList.tsx
│   │   │   └── ToolCallPanel.tsx
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Chat.tsx
│   │   │   └── Settings.tsx
│   │   └── hooks/
│   │       ├── useSSE.ts      ← SSE 流式 Hook
│   │       └── useAuth.ts
│   └── index.html
│
├── docs/
│   ├── feishu-design-doc.md   ← 飞书技术方案文档链接
│   └── api/
│       └── openapi.yaml      ← OpenAPI 规格
│
├── third_party/               ← 第三方源码（闭源，仅供研究）
│   ├── qoder-agent-sdk/       ← Qoder SDK 源码
│   ├── claude-wrapper/        ← 参考：认证层
│   ├── claude-web/            ← 参考：SSE 通信
│   ├── Ani-Claw/              ← 参考：多 Provider 路由
│   └── claude-code-webui/     ← 参考：完整企业封装
│
└── scripts/
    ├── setup.sh               ← 本地开发环境搭建
    ├── docker-build.sh        ← Docker 镜像构建
    └── seed_rbac.py           ← RBAC 初始数据
```

---

## 四、关键技术决策

### 4.1 SSE 流式通信

**决策**：使用 Server-Sent Events（SSE）而非 WebSocket。

**理由**：
- Qoder SDK 的 query() 返回 AsyncIterator，天然适配 SSE
- 前端实现简单，原生 EventSource API
- 参考项目 claude-web 已验证此方案

**实现要求**：
```python
# claw-gateway/routes/chat.py
from fastapi.responses import StreamingResponse

async def chat_stream(request: ChatRequest):
    async def event_generator():
        async for msg in qoder_query(request.message, context={"user": request.user}):
            # 格式: data: {"content": "...", "done": false}\n\n
            yield f"data: {json.dumps(msg.to_dict())}\n\n"
        yield "data: {\"done\": true}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
```

### 4.2 会话管理

**决策**：SQLite 持久化，异步写入。

**表结构**：
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT DEFAULT '',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    archived INTEGER DEFAULT 0
);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,       -- user / assistant / system
    content TEXT NOT NULL,
    tool_calls TEXT,          -- JSON
    created_at REAL NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_sessions_user ON sessions(user_id);
```

### 4.3 认证流程

```
用户 → GET /auth/feishu
     → 重定向到飞书授权页
     → 用户授权
     → GET /auth/callback?code=xxx
     → 换取飞书 Access Token
     → 查询用户信息（姓名、部门）
     → 生成 JWT（2小时有效期）
     → 前端存储 JWT，后续请求 Header 携带
```

### 4.4 两层认证关联

```python
# 第一层：外层 Gateway 认证
# 请求进来，验证 JWT，确定用户身份
user = jwt_verify(token)
session_context = {
    "user_id": user["open_id"],
    "role": user["role"],           # 从数据库查 RBAC
    "allowed_tools": [...],          # 从 RBAC 查
    "denied_tools": [...],
}

# 第二层：内层 Qoder SDK Hook
# 将 session_context 注入 Qoder SDK
async for msg in query(
    prompt=user_message,
    options=Options(
        mcp_servers={"enterprise": enterprise_mcp},
        allowed_tools=["周报生成", "文档摘要"],
        permission_mode="acceptedEdits",
        hooks=Hooks(pre_tool_use=permission_hook),
    ),
    context={"user": session_context}   # 关键：传递用户上下文
):
    yield msg
```

---

## 五、开发阶段

### Phase 1：基础骨架（Week 1 Day 1-2）

**目标**：可运行空服务，CI/CD 就绪。

**交付物**：
- `claw-gateway/` 项目骨架（FastAPI + SQLAlchemy + Alembic）
- `claw-ui/` 项目骨架（React + Vite + Tailwind）
- Dockerfile / docker-compose.yml
- GitHub Actions CI（lint + test）

**关键文件**：
```
claw-gateway/
├── main.py                    # 基础 FastAPI app，无业务逻辑
├── requirements.txt
├── config.py                  # 环境变量配置
└── database/
    ├── base.py
    └── session.py

claw-ui/
├── package.json
├── vite.config.ts
└── src/main.tsx               # 基础 React 入口
```

**验收标准**：
- `curl http://localhost:8000/health` 返回 `{"status": "ok"}`
- `curl http://localhost:5173` 返回前端页面

---

### Phase 2：认证框架（Week 1 Day 3-4）

> **开发策略**：认证框架先完整建好，但默认 bypass，用 guest 模式跑通全链路。后续稳定后通过 `AUTH_ENABLED=true` 开启飞书 OAuth2。
> 
> **理由**：Phase 2-5 可以并行测试 AI 对话能力，不需要等飞书应用创建完成。

**目标**：认证框架就绪，guest 模式可切换。

**关键文件**：
```
claw-gateway/auth/
├── bypass.py            # Guest 模式 bypass（新增）
├── feishu.py            # 飞书 OAuth2 实现（先建好，暂不启用）
│                       # 参考: third_party/claude-wrapper/app/src/auth/index.ts
├── jwt.py               # JWT 生成与验证
│                       # 参考: third_party/claude-wrapper/app/src/auth/jwt.ts
└── router.py            # /auth/feishu, /auth/callback, /auth/refresh
```

**飞书 OAuth2 配置**（写入 config.py）：
```python
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_REDIRECT_URI = os.getenv("FEISHU_REDIRECT_URI", "http://localhost:8000/auth/callback")

# 认证开关（默认 False = guest 模式，用于开发调试）
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
```

**Guest 模式 Bypass**：
```python
# claw-gateway/middleware/session.py
def get_session_context(auth_enabled: bool = AUTH_ENABLED) -> dict:
    """获取会话上下文"""
    
    if auth_enabled:
        # 正式模式：从 JWT 解析用户身份
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user = jwt_verify(token)
        return load_user_rbac(user["open_id"])
    
    # 开发模式：默认 guest 用户，跳过飞书 OAuth
    # Qoder SDK 本身的 License 认证依然生效
    return {
        "user_id": "guest",
        "name": "Guest User",
        "department": "开发测试",
        "role": "guest",           # guest 角色有基础工具权限
        "allowed_tools": ["对话", "文档摘要", "周报生成"],
        "denied_tools": ["服务器操作", "git_push"],
        "max_file_size_mb": 20,
        "audit_log": True,
    }
```

**前端 Login 页面**：
```typescript
// claw-ui/src/pages/Login.tsx
export function Login() {
    const authEnabled = import.meta.env.VITE_AUTH_ENABLED;
    
    if (!authEnabled) {
        // Guest 模式：直接进入对话页
        navigate("/chat");
        return null;
    }
    
    // 正式模式：点击跳飞书授权
    return (
        <div className="login-container">
            <h1>Claw AI 助理</h1>
            <button onClick={() => window.location.href = "/auth/feishu"}>
                使用飞书登录
            </button>
        </div>
    );
}
```

**验收标准**：
- `AUTH_ENABLED=false`（默认）时，跳过登录页直接进对话
- `AUTH_ENABLED=true` 时，访问 `/auth/feishu` 跳转飞书授权页
- JWT Token 验证逻辑就绪（暂不触发）
- **开发测试流程**：启动后可直接对话，无需配置飞书凭证

---

### Phase 3：SSE 流式通信（Week 1 Day 5）

**目标**：后端 SSE 接口可用，前端流式显示。

**关键文件**：
```
claw-gateway/routes/
└── chat.py            # /api/chat/stream SSE 接口
                       # 参考: third_party/claude-web/server.py

claw-ui/src/
├── api/client.ts      # SSE 客户端封装
└── hooks/useSSE.ts   # useSSE Hook
```

**参考实现**（来自 claude-web/server.py）：
```python
# 伪代码，详见 third_party/claude-web/server.py 完整实现
async def stream_chat(request):
    proc = await asyncio.create_subprocess_exec(
        "claude", "--print", "--no-input",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE
    )
    await proc.stdin.write(json.dumps({"message": request}).encode())
    async for line in proc.stdout:
        yield f"data: {line.decode()}\n\n"
```

**验收标准**：
- `POST /api/chat/stream` 返回 SSE 流
- 前端实时显示 AI 响应（打字机效果）
- 断流自动重连

---

### Phase 4：Qoder SDK 集成（Week 2 Day 1-2）

**目标**：Gateway 调用 Qoder SDK，AI 对话可用。

**关键文件**：
```
claw-gateway/
├── services/
│   └── qoder.py       # Qoder SDK 封装
│                     # 参考: third_party/qoder-agent-sdk/examples/
└── routes/chat.py     # 替换 subprocess 为 Qoder SDK 调用
```

**Qoder SDK 集成代码**：
```python
# claw-gateway/services/qoder.py
from qoder_agent_sdk import query, Options, QoderAgentSDKClient, Hooks
from qoder_agent_sdk.types import HookMatcher

from claw_gateway.hooks.permission import build_permission_hook
from claw_gateway.vault import CredentialVault

vault = CredentialVault()

async def chat_with_qoder(
    prompt: str,
    session_context: dict,
    session_id: str = None
) -> AsyncIterator[dict]:
    """Qoder SDK 对话封装"""
    # 构建权限 Hook
    permission_hook = build_permission_hook(session_context)
    
    options = Options(
        allowed_tools=session_context.get("allowed_tools", []),
        permission_mode="acceptedEdits",
        hooks=Hooks(
            pre_tool_use=[
                HookMatcher(matcher=".*", hooks=[permission_hook]),
            ]
        ),
    )
    
    # 注入用户上下文
    async for msg in query(
        prompt=prompt,
        options=options,
        context={"user": session_context}
    ):
        yield msg.to_dict()
```

**验收标准**：
- 用户消息经 Gateway → Qoder SDK → AI 响应 → SSE 返回前端
- 工具调用经权限 Hook 拦截
- 审计日志写入

---

### Phase 5：Session 管理（Week 2 Day 3-4）

**目标**：会话持久化，加载历史对话。

**关键文件**：
```
claw-gateway/
├── models/session.py    # Session / Message SQLAlchemy 模型
├── database/schema.py    # 数据库表定义
└── routes/
    └── sessions.py      # /api/sessions/* CRUD
```

**验收标准**：
- 新建会话、加载历史会话
- 对话内容持久化到 SQLite
- 刷新页面不丢失会话

---

### Phase 6：RBAC Hook + 测试（Week 2 Day 5）

**目标**：权限控制生效，核心流程测试通过。

**关键文件**：
```
claw-gateway/
├── hooks/
│   ├── permission.py    # pre_tool_use 权限拦截
│   └── audit.py         # post_tool_use 审计写入
└── models/rbac.py       # Role / Permission 模型
```

**权限 Hook 实现**：
```python
# claw-gateway/hooks/permission.py
from qoder_agent_sdk import PermissionResultAllow, PermissionResultDeny

def build_permission_hook(session_context: dict):
    user = session_context
    allowed = set(user.get("allowed_tools", []))
    denied = set(user.get("denied_tools", []))
    
    def permission_hook(input_data: dict, tool_use_id: str, context: dict) -> dict:
        tool_name = input_data.get("tool_name", "")
        
        if tool_name in denied:
            return {
                "permissionDecision": "deny",
                "permissionDecisionReason": f"[{user['role']}] 角色无权调用 {tool_name}"
            }
        
        if allowed and tool_name not in allowed:
            return {
                "permissionDecision": "deny",
                "permissionDecisionReason": f"工具 [{tool_name}] 不在 [{user['role']}] 的可用列表中"
            }
        
        return {"permissionDecision": "allow"}
    
    return permission_hook
```

**RBAC 初始数据**（scripts/seed_rbac.py）：
```python
ROLES = {
    "admin": {
        "allowed_tools": ["*"],      # 所有工具
        "denied_tools": []
    },
    "sales": {
        "allowed_tools": ["周报生成", "飞书消息汇总", "文档摘要"],
        "denied_tools": ["服务器操作", "数据库写入", "git_push"]
    },
    "developer": {
        "allowed_tools": ["代码审查", "Bug分析", "文档生成", "周报生成"],
        "denied_tools": ["财务数据访问"]
    },
    "guest": {
        "allowed_tools": ["对话", "文档摘要"],
        "denied_tools": ["*"]
    }
}
```

**验收标准**：
- 销售角色无法调用服务器操作工具（Hook 拦截）
- 管理员可调用所有工具
- 审计日志记录每次工具调用

---

### Phase 7：企业功能（Week 3-4）

**目标**：MCP 工具、审计日志、凭证库完整可用。

#### Week 3

| Day | 任务 | 关键参考 |
|-----|------|---------|
| D1-2 | MCP 工具注册 | `third_party/qoder-agent-sdk/examples/mcp_*.py` |
| D3-4 | 审计日志 | `third_party/claude-wrapper/app/src/routes/chat.ts` audit 部分 |
| D5 | 凭证库基础（API Key） | `docs/` 凭证设计文档 |

#### Week 4

| Day | 任务 | 关键参考 |
|-----|------|---------|
| D1-2 | 飞书 OAuth2 OBO | `docs/` 凭证集成方案 |
| D3-4 | 性能优化 + 压测 | `third_party/claude-web/server.py` SSE 优化 |
| D5 | 灰度上线 | 首批 10 用户试用 |

---

## 六、API 接口规格

### 6.1 认证接口

```
GET  /auth/feishu
     → 重定向到飞书授权页

GET  /auth/callback?code=xxx
     ← {"access_token": "xxx", "expires_in": 7200}

POST /auth/refresh
     Body: {"refresh_token": "xxx"}
     ← {"access_token": "xxx", "expires_in": 7200}

GET  /auth/me
     Header: Authorization: Bearer <jwt>
     ← {"user_id": "ou_xxx", "name": "张三", "role": "sales"}
```

### 6.2 对话接口

```
POST /api/chat/stream
     Header: Authorization: Bearer <jwt>
     Body: {"session_id": "sess_xxx", "message": "帮我生成周报"}
     ← SSE Stream:
       event: message
       data: {"type": "text", "content": "好的，"}
       data: {"type": "text", "content": "开始生成..."}
       event: tool_call
       data: {"tool": "周报生成", "input": {"period": "本周"}}
       event: done
       data: {"session_id": "sess_xxx", "usage": {...}}
```

### 6.3 会话接口

```
GET    /api/sessions              ← 列出用户所有会话
POST   /api/sessions              ← 创建新会话
GET    /api/sessions/{id}         ← 获取会话详情
DELETE /api/sessions/{id}         ← 删除会话
GET    /api/sessions/{id}/messages ← 获取会话历史消息
```

### 6.4 工具接口

```
GET  /api/tools                  ← 列出可用工具（含权限过滤）
POST /api/tools/test             ← 测试工具调用（无需走 AI）
```

---

## 七、数据模型

### 7.1 数据库 ER

```
users (from 飞书 OAuth)
  │
  ├── 1:N ─→ sessions
  │             │
  │             └── 1:N ─→ messages
  │
  └── 1:N ─→ user_credentials (Credential Vault)
                    │
                    └── system (飞书/ERP/CRM...)

roles
  │
  └── 1:N ─→ role_permissions

sessions
  ├── user_id (FK → users)
  ├── title
  ├── created_at / updated_at
  └── archived

messages
  ├── session_id (FK → sessions)
  ├── role (user/assistant/system)
  ├── content
  ├── tool_calls (JSON, nullable)
  └── created_at
```

### 7.2 Pydantic 模型

```python
# claw-gateway/models/session.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SessionCreate(BaseModel):
    title: Optional[str] = ""

class SessionResponse(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    archived: bool

class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    tool_calls: Optional[dict]
    created_at: datetime

# claw-gateway/models/rbac.py
class Role(BaseModel):
    name: str
    allowed_tools: List[str]
    denied_tools: List[str]

class SessionContext(BaseModel):
    user_id: str
    name: str
    department: str
    role: str
    allowed_tools: List[str]
    denied_tools: List[str]
    max_file_size_mb: int = 20
    audit_log: bool = True
```

---

## 八、配置与环境变量

### 8.1 必需环境变量

```bash
# .env 文件（勿提交到 Git）

# 认证开关（开发调试用，Phase 2-5 阶段默认 false）
AUTH_ENABLED=false                 # false=guest模式直连，true=启用飞书 OAuth2

# 飞书 OAuth2（AUTH_ENABLED=true 时填写）
FEISHU_APP_ID=cli_xxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FEISHU_REDIRECT_URI=http://localhost:8000/auth/callback

# 数据库
DATABASE_URL=sqlite:///./claw.db
# DATABASE_URL=postgresql://user:pass@localhost:5432/claw

# JWT
JWT_SECRET=your-256-bit-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120

# Qoder SDK
QODER_CLI_PATH=                    # 可选，默认用 pip 安装的
QODER_LICENSE_KEY=                 # Qoder SDK License

# 前端
VITE_API_BASE=http://localhost:8000
VITE_AUTH_ENABLED=false            # false=开发模式（guest），true=启用飞书 OAuth
```

### 8.2 本地开发启动

```bash
# 终端 1: 后端
cd claw-gateway
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 填写 .env 中的飞书 App ID/Secret
uvicorn main:app --reload --port 8000

# 终端 2: 前端
cd claw-ui
npm install
npm run dev

# 访问 http://localhost:5173
```

---

## 九、测试策略

### 9.1 单元测试（pytest）

```
claw-gateway/tests/
├── test_auth.py           # JWT / OAuth 测试
├── test_chat.py           # SSE / Qoder SDK 集成测试
├── test_hooks.py          # 权限 Hook 测试
├── test_vault.py         # 凭证库测试
└── test_sessions.py       # 会话管理测试
```

**权限 Hook 测试用例**：
```python
def test_permission_hook_denies_blocked_tool():
    ctx = {"user": {"role": "sales", "allowed_tools": ["周报生成"], "denied_tools": ["git_push"]}}
    hook = build_permission_hook(ctx)
    result = hook({"tool_name": "git_push", "tool_input": {}}, "t1", {})
    assert result["permissionDecision"] == "deny"

def test_permission_hook_allows_whitelisted():
    ctx = {"user": {"role": "sales", "allowed_tools": ["周报生成"], "denied_tools": []}}
    hook = build_permission_hook(ctx)
    result = hook({"tool_name": "周报生成", "tool_input": {}}, "t1", {})
    assert result["permissionDecision"] == "allow"
```

### 9.2 E2E 测试（Playwright）

```typescript
// claw-ui/e2e/chat.spec.ts
test('用户可与 AI 对话并收到流式响应', async ({ page }) => {
  await page.goto('/chat');
  await page.getByPlaceholder('输入消息...').fill('你好');
  await page.getByRole('button', { name: '发送' }).click();
  
  // 等待 SSE 流式响应出现
  const response = page.locator('.message-assistant');
  await expect(response).toBeVisible({ timeout: 10000 });
});
```

### 9.3 压测

```bash
# 使用 wrk 压测 SSE 接口
wrk -t4 -c100 -d30s -s post.lua http://localhost:8000/api/chat/stream
```

**达标标准**：10 并发用户，SSE 不断流，P99 响应 < 3s。

---

## 十、部署

### 10.1 Docker Compose

```yaml
# docker-compose.yml
services:
  claw-gateway:
    build: ./claw-gateway
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./claw.db:/app/claw.db
    restart: unless-stopped

  claw-ui:
    build: ./claw-ui
    ports:
      - "5173:80"
    depends_on:
      - claw-gateway
    environment:
      - VITE_API_BASE=http://localhost:8000
```

### 10.2 Nginx 配置（SSE 支持）

```nginx
location /api/ {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_buffering off;
    proxy_cache off;
}
```

---

## 十一、参考项目索引

| 项目 | 用途 | 关键参考文件 |
|------|------|------------|
| qoder-agent-sdk | Qoder SDK 源码 | `src/qoder_agent_sdk/query.py`, `client.py`, `types.py` |
| claude-web | SSE 通信原型 | `server.py`, `static/index.html` |
| claude-wrapper | 认证 + Session 管理 | `app/src/auth/`, `app/src/routes/chat.ts` |
| Ani-Claw | 多 Provider 路由 | `internal/agent/loop.go`, `web/` |
| claude-code-webui | 完整企业封装 | `backend/`, `frontend/src/` |

---

## 十二、飞书集成说明

### 12.1 飞书应用创建

1. 登录 [飞书开放平台](https://open.feishu.cn/app)
2. 创建企业自建应用
3. 获取 App ID 和 App Secret
4. 配置重定向 URL：`http://localhost:8000/auth/callback`
5. 申请权限：`contact:user.employee_id:readonly`

### 12.2 飞书 OAuth2 权限

```python
FEISHU_SCOPES = [
    "contact:user.employee_id:readonly",  # 获取用户 employee_id
    "im:message",                         # 发送消息
]
```

---

## 十三、凭证库设计

### 13.1 三种授权模式

| 模式 | 实现 | 适用场景 |
|------|------|---------|
| 个人 API Key | 用户填 Key → 加密存储 | 内部系统、无 OAuth |
| OAuth2 用户授权 | 飞书 OAuth 授权页 | 飞书/企微/钉钉 |
| OAuth2 OBO | On-Behalf-Of 换 Token | 需代表用户调用 |

### 13.2 加密存储

```python
# claw-gateway/vault/storage.py
from cryptography.fernet import Fernet

class CredentialStorage:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def store(self, user_id: str, system: str, token: str):
        encrypted = self.cipher.encrypt(token.encode())
        # 存入数据库
        db.execute(
            "INSERT INTO user_credentials VALUES (?, ?, ?)",
            (user_id, system, encrypted)
        )
    
    def retrieve(self, user_id: str, system: str) -> str:
        encrypted = db.query("SELECT token FROM user_credentials WHERE ...")
        return self.cipher.decrypt(encrypted).decode()
```

---

## 十四、详细规格（SPEC.md）

以下规格写入 `SPEC.md` 文件，作为开发时的详细参考。

### 14.1 SSE 事件格式

```typescript
// 客户端收到的 SSE 事件格式
type SSEEvent =
  | { type: "text"; content: string; done: false }
  | { type: "tool_call"; tool: string; input: Record<string, unknown> }
  | { type: "tool_result"; tool: string; result: unknown }
  | { type: "done"; session_id: string; usage: Usage }
  | { type: "error"; message: string }
```

### 14.2 错误码

```python
# claw-gateway/routes/errors.py
class APIError(Exception):
    code: int
    message: str

ERRORS = {
    10001: "参数校验失败",
    10002: "资源不存在",
    10003: "权限不足",
    10004: "会话不存在",
    10005: "飞书认证失败",
    10006: "Qoder SDK 调用失败",
    10007: "Token 已过期",
    10008: "工具调用被拦截",
}
```

### 14.3 日志格式

```python
# 审计日志写入
{
    "timestamp": "2026-05-10T00:00:00+08:00",
    "level": "INFO",
    "event": "tool_call",
    "user_id": "ou_xxx",
    "user_name": "张三",
    "role": "sales",
    "session_id": "sess_xxx",
    "tool_name": "周报生成",
    "tool_input": {"period": "本周"},
    "decision": "allow",           # allow / deny
    "reason": "",                  # deny 时记录原因
    "request_id": "req_xxx",
}
```

---

## 十五、常见问题

### Q: Qoder SDK 报 CLINotFoundError 怎么办？
A: 运行 `pip install qoder-agent-sdk`，或设置 `QODER_CLI_PATH` 环境变量。

### Q: SSE 在 Nginx 代理后断开？
A: 确保 Nginx 配置 `proxy_http_version 1.1` + `proxy_buffering off`。

### Q: 飞书 OAuth 报错 invalid app_id？
A: 检查 `.env` 中 `FEISHU_APP_ID` 是否正确，格式应为 `cli_xxx`。

### Q: 如何扩展新的 MCP 工具？
A: 在 `claw-gateway/services/mcp/` 下创建新工具模块，参考 `third_party/qoder-agent-sdk/examples/mcp_calculator.py`。

---

## 十六、Checklist（开发完成标准）

每个 Phase 完成后，对照检查：

- [ ] Phase 1: 服务可启动，CI 通过
- [ ] Phase 2: 认证框架就绪，`AUTH_ENABLED=false` 可直接对话，`AUTH_ENABLED=true` 飞书登录可用
- [ ] Phase 3: SSE 流式响应，延迟 < 1s
- [ ] Phase 4: 完整对话链路通
- [ ] Phase 5: 会话持久化，历史可加载
- [ ] Phase 6: RBAC 拦截生效，审计日志完整
- [ ] Phase 7: MCP 工具可用，凭证库可用
- [ ] 压测通过：10 并发，P99 < 3s
- [ ] 安全审核通过
- [ ] 上线文档完整
