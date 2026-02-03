"""管理员 API：登录、图谱 CRUD、统计、限额、环境变量"""
import shutil
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.config import GRAPHS_DIR, PROJECT_ROOT, ensure_dirs
from app.database import (
    graph_list,
    graph_get,
    graph_create,
    graph_update_meta,
    graph_set_daily_limit,
    graph_delete as db_graph_delete,
    query_stat_get_today_all,
    user_list,
    user_get,
    query_history_list_by_user,
    user_update_password,
)
from app.auth import verify_admin, create_access_token, get_current_admin, hash_password
from app.rag_service import insert_async

router = APIRouter()


# --- 登录 ---
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
def admin_login(req: LoginRequest):
    """管理员登录：返回 admin 角色 token。"""
    if not verify_admin(req.username, req.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(req.username, role="admin")
    return LoginResponse(access_token=token)


# --- 图谱管理（需认证）---
@router.get("/graphs")
def admin_list_graphs(admin: str = Depends(get_current_admin)):
    return graph_list(include_private=True)


class CreateGraphRequest(BaseModel):
    name: str
    description: str = ""
    daily_limit: int = 100


def _read_txt_file(content: bytes, filename: str) -> str:
    """解码单个 txt 文件内容，支持 UTF-8 / GBK"""
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return content.decode("gbk")
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=f"文件「{filename}」编码不支持，请使用 UTF-8 或 GBK",
            )


@router.post("/graphs")
async def create_graph(
    name: str = Form(...),
    description: str = Form(""),
    daily_limit: int = Form(100),
    files: List[UploadFile] = File(..., description="一个或多个 .txt 文件"),
    admin: str = Depends(get_current_admin),
):
    """上传一个或多个 txt 文件，创建新图谱。"""
    ensure_dirs()
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一个 .txt 文件")
    texts: List[str] = []
    for f in files:
        if not f.filename or not f.filename.lower().endswith(".txt"):
            raise HTTPException(status_code=400, detail=f"请上传 .txt 文件，当前文件: {f.filename or '未知'}")
        content = await f.read()
        text = _read_txt_file(content, f.filename)
        if text.strip():
            texts.append(text)
    if not texts:
        raise HTTPException(status_code=400, detail="所有文件内容均为空，请上传有内容的 .txt 文件")

    working_dir = ""
    graph_id = None
    try:
        graph_id = graph_create(name=name.strip(), description=description.strip(), working_dir=None, daily_limit=daily_limit)
        working_dir = str(GRAPHS_DIR / f"graph_{graph_id}")
        Path(working_dir).mkdir(parents=True, exist_ok=True)
        from app.database import get_db
        with get_db() as conn:
            conn.execute("UPDATE graphs SET working_dir = ? WHERE id = ?", (working_dir, graph_id))
        await insert_async(working_dir, texts, is_first_time=True)
    except Exception as e:
        if graph_id:
            db_graph_delete(graph_id)
            p = Path(working_dir)
            if p.exists():
                shutil.rmtree(p, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"创建图谱失败: {str(e)}")
    return {"id": graph_id, "name": name, "description": description, "working_dir": working_dir}


@router.post("/graphs/{graph_id}/update")
async def incremental_update(
    graph_id: int,
    files: List[UploadFile] = File(..., description="一个或多个 .txt 文件"),
    admin: str = Depends(get_current_admin),
):
    """对已有图谱增量更新：上传一个或多个 txt 文件。"""
    g = graph_get(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail="图谱不存在")
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一个 .txt 文件")
    texts: List[str] = []
    for f in files:
        if not f.filename or not f.filename.lower().endswith(".txt"):
            raise HTTPException(status_code=400, detail=f"请上传 .txt 文件，当前文件: {f.filename or '未知'}")
        content = await f.read()
        text = _read_txt_file(content, f.filename)
        if text.strip():
            texts.append(text)
    if not texts:
        raise HTTPException(status_code=400, detail="所有文件内容均为空")
    try:
        await insert_async(g["working_dir"], texts, is_first_time=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"增量更新失败: {str(e)}")
    return {"message": "增量更新成功"}


@router.delete("/graphs/{graph_id}")
def delete_graph(graph_id: int, admin: str = Depends(get_current_admin)):
    working_dir = db_graph_delete(graph_id)
    if working_dir:
        p = Path(working_dir)
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
    return {"message": "已删除"}


class UpdateGraphMetaRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


@router.patch("/graphs/{graph_id}")
def update_graph_meta(
    graph_id: int,
    body: UpdateGraphMetaRequest,
    admin: str = Depends(get_current_admin),
):
    g = graph_get(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail="图谱不存在")
    graph_update_meta(graph_id, name=body.name, description=body.description)
    return {"message": "已更新"}


# --- 统计与限额 ---
@router.get("/stats")
def get_today_stats(admin: str = Depends(get_current_admin)):
    """今日各图谱查询次数及每日限额"""
    return query_stat_get_today_all()


class SetLimitRequest(BaseModel):
    daily_limit: int


@router.patch("/graphs/{graph_id}/limit")
def set_daily_limit(
    graph_id: int,
    body: SetLimitRequest,
    admin: str = Depends(get_current_admin),
):
    daily_limit = body.daily_limit
    if daily_limit < 0:
        raise HTTPException(status_code=400, detail="每日限额不能为负数")
    g = graph_get(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail="图谱不存在")
    graph_set_daily_limit(graph_id, daily_limit)
    return {"message": "已更新", "daily_limit": daily_limit}


# --- 环境变量（仅允许修改，敏感项不返回原值）---
# 允许在管理界面编辑的 .env 键（与 config.Settings 对应的大写形式）
ENV_KEYS_ALLOWED = [
    "DEEPSEEK_API_KEY", "DEEPSEEK_API_BASE", "DEEPSEEK_MODEL",
    "SILICONCLOUD_API_KEY", "SILICONCLOUD_EMBEDDING_MODEL", "SILICONCLOUD_RERANK_MODEL",
    "ADMIN_USERNAME", "ADMIN_PASSWORD", "SECRET_KEY",
    "DATABASE_URL",
]
# 敏感键：接口不返回真实值，只显示“已设置”占位
ENV_KEYS_SENSITIVE = {
    "DEEPSEEK_API_KEY", "SILICONCLOUD_API_KEY", "ADMIN_PASSWORD", "SECRET_KEY",
}


def _read_env_file() -> Dict[str, str]:
    """读取 .env 文件为 key -> value，只保留允许的键。"""
    env_path = PROJECT_ROOT / ".env"
    result = {}
    if not env_path.exists():
        return result
    for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
        if m and m.group(1).upper() in (k.upper() for k in ENV_KEYS_ALLOWED):
            key = m.group(1).upper()
            value = m.group(2).strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1].replace('\\"', '"')
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1].replace("\\'", "'")
            result[key] = value
    return result


def _write_env_file(updates: Dict[str, str]) -> None:
    """用 updates 更新 .env：已存在的键替换，不存在的键追加；只允许 ENV_KEYS_ALLOWED。"""
    env_path = PROJECT_ROOT / ".env"
    current = _read_env_file()
    for k, v in updates.items():
        key_upper = k.upper()
        if any(key_upper == x.upper() for x in ENV_KEYS_ALLOWED):
            current[key_upper] = v
    lines = []
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                lines.append(line)
                continue
            m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
            if m and m.group(1).upper() in (x.upper() for x in ENV_KEYS_ALLOWED):
                key = m.group(1).upper()
                if key in current:
                    lines.append(f"{key}={current[key]}")
                    del current[key]
                else:
                    lines.append(line)
            else:
                lines.append(line)
    for k, v in current.items():
        lines.append(f"{k}={v}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class EnvItemResponse(BaseModel):
    key: str
    value: str
    masked: bool


@router.get("/env", response_model=List[EnvItemResponse])
def get_env_masked(admin: str = Depends(get_current_admin)):
    """返回可编辑的环境变量列表；敏感键只返回占位，不返回真实值。"""
    data = _read_env_file()
    out = []
    for key in ENV_KEYS_ALLOWED:
        if key in data:
            val = data[key]
            if key in ENV_KEYS_SENSITIVE:
                out.append(EnvItemResponse(key=key, value="****", masked=True))
            else:
                out.append(EnvItemResponse(key=key, value=val, masked=False))
        else:
            out.append(EnvItemResponse(key=key, value="", masked=key in ENV_KEYS_SENSITIVE))
    return out


class EnvUpdateRequest(BaseModel):
    env: Dict[str, str]


@router.patch("/env")
def patch_env(body: EnvUpdateRequest, admin: str = Depends(get_current_admin)):
    """仅更新 .env 中允许的键；敏感键若传入空字符串则跳过（不覆盖原值）。"""
    updates = {}
    for k, v in body.env.items():
        key_upper = k.upper()
        if key_upper not in (x.upper() for x in ENV_KEYS_ALLOWED):
            continue
        if key_upper in ENV_KEYS_SENSITIVE and (v is None or str(v).strip() == ""):
            continue
        updates[key_upper] = str(v).strip()
    if not updates:
        return {"message": "无有效更新"}
    _write_env_file(updates)
    return {"message": "已更新"}


# --- 账号管理（仅管理员）---

@router.get("/users")
def admin_list_users(
    search: Optional[str] = None,
    admin: str = Depends(get_current_admin),
):
    """用户列表，可选按用户名搜索。"""
    return user_list(search=search)


class UpdatePasswordRequest(BaseModel):
    new_password: str


@router.patch("/users/{user_id}/password")
def admin_update_user_password(
    user_id: int,
    body: UpdatePasswordRequest,
    admin: str = Depends(get_current_admin),
):
    u = user_get(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not body.new_password or len(body.new_password.strip()) < 1:
        raise HTTPException(status_code=400, detail="新密码不能为空")
    user_update_password(user_id, hash_password(body.new_password))
    return {"message": "已更新"}


@router.get("/users/{user_id}/history")
def admin_get_user_history(
    user_id: int,
    admin: str = Depends(get_current_admin),
):
    """某用户 7 天内全部查询记录。"""
    u = user_get(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    return query_history_list_by_user(user_id)
