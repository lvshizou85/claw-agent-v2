"""
配置管理
所有配置从环境变量读取，支持 .env 文件
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


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
    qoder_cli_path: str = ""
    qoder_license_key: str = ""

    # 前端
    frontend_url: str = "http://localhost:5173"

    # 凭证库加密
    vault_encryption_key: str = "CHANGE_ME_IN_PRODUCTION"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
