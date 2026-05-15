"""
数据库模型
SQLAlchemy + SQLite（开发）/ PostgreSQL（生产）
"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import time

from claw_gateway.config import get_settings

Base = declarative_base()
settings = get_settings()

# 引擎和 Session 工厂
_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
        )
    return _engine


def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


# ============ 数据模型 ============

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)        # 飞书 open_id
    name = Column(String, default="")
    department = Column(String, default="")
    role = Column(String, default="guest")      # RBAC 角色
    created_at = Column(Float, default=time.time)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    credentials = relationship("UserCredential", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)        # sess_xxx
    user_id = Column(String, ForeignKey("users.id"), index=True)
    title = Column(String, default="")
    cwd = Column(String, default="")
    pinned = Column(Boolean, default=False)
    archived = Column(Boolean, default=False)
    created_at = Column(Float, default=time.time)
    updated_at = Column(Float, default=time.time)

    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id"), index=True)
    role = Column(String)                        # user / assistant / system
    content = Column(Text)
    tool_calls = Column(Text, nullable=True)    # JSON string
    created_at = Column(Float, default=time.time)

    session = relationship("Session", back_populates="messages")


class UserCredential(Base):
    __tablename__ = "user_credentials"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    system = Column(String)                      # feishu / erp / crm
    auth_type = Column(String)                    # oauth2 / api_key
    encrypted_token = Column(Text)               # AES 加密存储
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(Float)
    scope = Column(Text, nullable=True)
    created_at = Column(Float, default=time.time)

    user = relationship("User", back_populates="credentials")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    timestamp = Column(Float, default=time.time)
    level = Column(String, default="INFO")       # INFO / WARN / ERROR
    event = Column(String)                        # tool_call / login / ...
    user_id = Column(String, index=True)
    session_id = Column(String, nullable=True)
    action = Column(String)
    detail = Column(Text, nullable=True)         # JSON string
    decision = Column(String, nullable=True)     # allow / deny
    reason = Column(Text, nullable=True)


# ============ 初始化 ============

def init_db():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
