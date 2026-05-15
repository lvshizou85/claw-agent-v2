"""
认证路由 /auth/*
飞书 OAuth2 + JWT
"""

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import RedirectResponse
import httpx

from claw_gateway.config import get_settings
from claw_gateway.auth.jwt import create_token, verify_token
from claw_gateway.database import get_session_local, User

router = APIRouter()
settings = get_settings()


@router.get("/feishu")
async def auth_feishu():
    """跳转到飞书授权页"""
    params = {
        "app_id": settings.feishu_app_id,
        "redirect_uri": settings.feishu_redirect_uri,
        "scope": "contact:user.employee_id:readonly",
        "response_type": "code",
    }
    query_str = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{settings.feishu_api_base}/authen/v1/authorize?{query_str}"
    return RedirectResponse(url=url)


@router.get("/callback")
async def auth_callback(code: str = Query(...)):
    """飞书 OAuth2 回调，换 Token + 登录"""
    try:
        # 1. 换取 Access Token
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                f"{settings.feishu_api_base}/authen/v1/oidc/access_token",
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                    "app_id": settings.feishu_app_id,
                    "app_secret": settings.feishu_app_secret,
                }
            )
            token_data = token_resp.json()
            access_token = token_data["data"]["access_token"]

            # 2. 获取用户信息
            user_resp = await client.get(
                f"{settings.feishu_api_base}/contact/v3/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"user_id_type": "open_id"}
            )
            user_data = user_resp.json()
            user_info = user_data["data"]

        # 3. 创建/更新用户
        db = get_session_local()()
        try:
            user = db.query(User).filter(User.id == user_info["open_id"]).first()
            if not user:
                user = User(
                    id=user_info["open_id"],
                    name=user_info.get("name", ""),
                    department=user_info.get("department", {}).get("name", ""),
                    role="guest",  # 默认角色，上线后配置
                )
                db.add(user)
            else:
                user.name = user_info.get("name", user.name)
            db.commit()
        finally:
            db.close()

        # 4. 生成 JWT
        jwt_token = create_token(
            user_id=user.id,
            open_id=user_info["open_id"],
            name=user_info.get("name", ""),
            role=user.role,
        )

        # 5. 重定向到前端
        redirect_url = f"{settings.frontend_url}/auth/callback?token={jwt_token}"
        return RedirectResponse(url=redirect_url)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"飞书认证失败: {str(e)}")


@router.get("/me")
async def auth_me(token: str = Query(...)):
    """获取当前用户信息"""
    try:
        payload = verify_token(token)
        return {
            "user_id": payload["open_id"],
            "name": payload["name"],
            "role": payload["role"],
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")


@router.post("/refresh")
async def auth_refresh(refresh_token: str):
    """刷新 JWT Token"""
    # TODO: 实现 refresh token
    raise HTTPException(status_code=501, detail="暂未实现")
