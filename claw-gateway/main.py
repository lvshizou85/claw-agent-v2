"""
Claw Gateway - 企业版 AI 助理后端服务
FastAPI + Qoder SDK + 飞书 OAuth2
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from claw_gateway.config import get_settings
from claw_gateway.database.schema import init_db
from claw_gateway.auth.router import router as auth_router
from claw_gateway.routes import chat, sessions, tools

settings = get_settings()

app = FastAPI(
    title="Claw Gateway",
    description="企业版 AI 助理后端服务",
    version="0.1.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
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
async def health():
    """健康检查"""
    return {"status": "ok", "version": "0.1.0", "database": settings.database_url}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={"code": 50000, "message": f"Internal error: {str(exc)}"}
    )
