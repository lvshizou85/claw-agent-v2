"""
JWT Token 工具
"""

import jwt
from datetime import datetime, timedelta
from claw_gateway.config import get_settings

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
    """验证 JWT Token"""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
