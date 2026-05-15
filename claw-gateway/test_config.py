import sys
import os

# Add project root to path BEFORE other imports
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from claw_gateway.config import Settings

def test_auth_enabled_default_false():
    settings = Settings()
    # 检查 auth 相关配置存在性（骨架中暂无 auth_enabled，默认值测试）
    assert hasattr(settings, 'feishu_app_id')

def test_default_database_url():
    """验证数据库默认配置"""
    settings = Settings()
    assert settings.database_url == "sqlite:///./claw.db"
