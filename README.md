# Claw Agent

企业版 AI 助理应用，基于 Qoder SDK 构建，为企业普通用户提供安全的 AI 对话与工具调用能力。

## 项目结构

```
claw-agent/
├── CLAW.md           ← Agent 开发计划（AI 可执行版）
├── SPEC.md           ← 详细技术规格
├── claw-gateway/     ← Python FastAPI 后端
├── claw-ui/          ← React 前端
├── third_party/      ← 第三方源码（参考）
│   ├── qoder-agent-sdk/
│   ├── claude-wrapper/
│   ├── claude-web/
│   ├── Ani-Claw/
│   └── claude-code-webui/
├── docs/
└── scripts/
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React + Vite + Tailwind + TypeScript |
| 后端 | Python + FastAPI + SQLAlchemy |
| 数据库 | SQLite（初期）/ PostgreSQL（后期） |
| AI 内核 | Qoder SDK（闭源） |
| 认证 | 飞书 OAuth2 + JWT |
| 部署 | Docker + Docker Compose |

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/lvshizou85/claw-agent.git
cd claw-agent

# 2. 配置环境变量
cp claw-gateway/.env.example claw-gateway/.env
# 编辑 .env，填写飞书 App ID/Secret

# 3. 启动后端
cd claw-gateway
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 4. 启动前端
cd claw-ui
npm install
npm run dev
```

访问 http://localhost:5173

## 飞书 OAuth2 配置

1. 登录 [飞书开放平台](https://open.feishu.cn/app)，创建企业自建应用
2. 获取 App ID (`cli_xxx`) 和 App Secret
3. 在应用设置中，添加重定向 URL：`http://localhost:8000/auth/callback`
4. 申请权限：`contact:user.employee_id:readonly`
5. 将 App ID 和 App Secret 填入 `.env`

## 架构

```
用户浏览器
    ↓
Claw UI（React + SSE）
    ↓
Claw Gateway（FastAPI）
    ├── 认证层：飞书 OAuth2 + JWT
    ├── 权限层：RBAC + Hook 拦截
    └── 会话层：SQLite 持久化
    ↓
Qoder SDK（Python）
    ↓
Qoder CLI（闭源内核）
```

详见 [CLAW.md](./CLAW.md)

## 参考文档

- 飞书技术方案：[Claw 企业版 AI 助理应用技术方案](https://www.feishu.cn/docx/TWmXdPtOAoxCOdxBTTCcr6TFnUc)
- 参考项目：
  - [claude-web](https://github.com/heng1234/claude-web) — SSE 通信原型
  - [claude-wrapper](https://github.com/ChrisColeTech/claude-wrapper) — 认证 + Session 管理
  - [Ani-Claw](https://github.com/Dannykkh/Ani-Claw) — 多 Provider 路由

## License

Proprietary. Internal use only.
