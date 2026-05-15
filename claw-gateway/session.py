"""
数据库会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from claw_gateway.config import get_settings

settings = get_settings()

# 创建引擎
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖注入函数
    用于 FastAPI 路由中注入数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
