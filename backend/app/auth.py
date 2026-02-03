"""认证：管理员（.env）+ 普通用户（数据库），JWT；密码用 bcrypt 直接处理"""
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)

# bcrypt 密码最大 72 字节
MAX_PASSWORD_BYTES = 72


def _truncate_password_bytes(raw: str) -> bytes:
    b = raw.encode("utf-8")
    if len(b) > MAX_PASSWORD_BYTES:
        return b[:MAX_PASSWORD_BYTES]
    return b


def hash_password(password: str) -> str:
    """密码转 UTF-8 字节，超过 72 字节截断，再 bcrypt 哈希，返回字符串。"""
    b = _truncate_password_bytes(password)
    return bcrypt.hashpw(b, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """明文与哈希校验，明文同样做 72 字节截断。"""
    try:
        plain_b = _truncate_password_bytes(plain)
        hashed_b = hashed.encode("utf-8")
        return bcrypt.checkpw(plain_b, hashed_b)
    except Exception:
        return False


def create_access_token(username: str, role: str = "user") -> str:
    """role: 'admin' | 'user'"""
    expire = datetime.utcnow() + timedelta(hours=24)
    payload = {"sub": username, "exp": expire, "role": role}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> Optional[tuple[str, str]]:
    """成功返回 (username, role)，失败返回 None。"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        sub = payload.get("sub")
        role = payload.get("role", "user")
        if sub:
            return (sub, role)
    except JWTError:
        pass
    return None


def verify_admin(username: str, password: str) -> bool:
    """管理员：与 .env 中的账号密码比对（明文比对，与现有逻辑一致）。"""
    return username == settings.admin_username and password == settings.admin_password


async def get_current_admin(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """仅管理员通过：校验 token 且 role=admin 且 sub 为配置的管理员名。"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证信息")
    decoded = decode_token(credentials.credentials)
    if not decoded:
        raise HTTPException(status_code=401, detail="无效或过期的令牌")
    username, role = decoded
    if role != "admin" or username != settings.admin_username:
        raise HTTPException(status_code=401, detail="需要管理员权限")
    return username


async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """可选用户：有有效 user token 则返回用户名，否则返回 None。不校验管理员。"""
    if not credentials:
        return None
    decoded = decode_token(credentials.credentials)
    if not decoded:
        return None
    username, role = decoded
    if role != "user":
        return None
    return username
