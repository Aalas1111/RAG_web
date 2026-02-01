"""管理员认证：用户名密码校验 + JWT"""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=24)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload.get("sub")
    except JWTError:
        return None


def verify_admin(username: str, password: str) -> bool:
    return username == settings.admin_username and password == settings.admin_password


async def get_current_admin(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证信息")
    username = decode_token(credentials.credentials)
    if not username or username != settings.admin_username:
        raise HTTPException(status_code=401, detail="无效或过期的令牌")
    return username
