import sys
import os

# Add project root to path BEFORE other imports
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi.testclient import TestClient
from claw_gateway.main import app

client = TestClient(app)

def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data

def test_health_no_auth_required():
    """Guest 模式下 health 接口无需认证"""
    response = client.get("/health")
    assert response.status_code == 200
