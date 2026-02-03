"""公开 API：图谱列表、查询、用户注册/登录、查询记录"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.database import (
    graph_list,
    graph_get,
    can_query_today,
    query_stat_inc,
    query_stat_get_today,
    user_create,
    user_get_by_username,
    query_history_add,
    query_history_list,
)
from app.rag_service import query_async, VALID_MODES
from app.auth import hash_password, verify_password, create_access_token, get_current_user_optional

router = APIRouter()


class QueryRequest(BaseModel):
    graph_id: int
    query: str
    mode: str = "hybrid"


class QueryResponse(BaseModel):
    answer: str
    today_used: int
    daily_limit: int


class RegisterRequest(BaseModel):
    username: str
    password: str
    password_confirm: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class HistoryItem(BaseModel):
    id: int
    user_id: int
    graph_id: int
    query_text: str
    answer: str
    created_at: str


@router.get("/graphs")
def list_graphs():
    """前端主界面：获取所有图谱（仅名字和简介）"""
    return graph_list(include_private=False)


@router.get("/graphs_with_usage")
def list_graphs_with_usage():
    """前端选择知识图谱弹窗：图谱列表 + 今日已用次数、每日限额（用于展示剩余次数）"""
    graphs = graph_list(include_private=False)
    out = []
    for g in graphs:
        gid = g["id"]
        used = query_stat_get_today(gid)
        limit = graph_get(gid)["daily_limit"]
        out.append({
            **g,
            "today_used": used,
            "daily_limit": limit,
        })
    return out


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    """用户注册；成功后直接返回 token。"""
    if not req.username or not req.username.strip():
        raise HTTPException(status_code=400, detail="账号不能为空")
    if not req.password:
        raise HTTPException(status_code=400, detail="密码不能为空")
    if req.password != req.password_confirm:
        raise HTTPException(status_code=400, detail="两次密码不一致")
    username = req.username.strip()
    if user_get_by_username(username):
        raise HTTPException(status_code=400, detail="该账号已存在")
    password_hash = hash_password(req.password)
    user_create(username, password_hash)
    token = create_access_token(username, role="user")
    return TokenResponse(access_token=token, username=username)


@router.post("/user/login", response_model=TokenResponse)
def user_login(req: LoginRequest):
    """用户登录；返回 user 角色 token。"""
    u = user_get_by_username(req.username.strip() if req.username else "")
    if not u or not verify_password(req.password or "", u["password_hash"]):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    token = create_access_token(u["username"], role="user")
    return TokenResponse(access_token=token, username=u["username"])


@router.get("/user/me")
def user_me(username: str | None = Depends(get_current_user_optional)):
    """当前登录用户信息（可选认证）。"""
    if not username:
        return {"username": None}
    return {"username": username}


@router.get("/query_history", response_model=list)
def get_query_history(
    graph_id: int,
    username: str | None = Depends(get_current_user_optional),
):
    """当前用户在某图谱下、7 天内的查询记录；未登录返回空列表。"""
    if not username:
        return []
    u = user_get_by_username(username)
    if not u:
        return []
    items = query_history_list(u["id"], graph_id)
    return items


@router.post("/query", response_model=QueryResponse)
async def query(
    req: QueryRequest,
    username: str | None = Depends(get_current_user_optional),
):
    """对指定图谱进行 query，返回 AI 回答；已登录则保存查询记录（仅保留 7 天）。"""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="查询内容不能为空")
    mode = req.mode.strip().lower() if req.mode else "hybrid"
    if mode not in VALID_MODES:
        mode = "hybrid"

    g = graph_get(req.graph_id)
    if not g:
        raise HTTPException(status_code=404, detail="图谱不存在")
    can_do, used, limit = can_query_today(req.graph_id)
    if not can_do:
        raise HTTPException(
            status_code=429,
            detail=f"今日查询次数已达上限（{limit} 次），请明日再试。"
        )

    try:
        answer = await query_async(g["working_dir"], req.query, mode=mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

    if answer is None:
        raise HTTPException(status_code=500, detail="查询失败，模型返回为空，请稍后重试")

    query_stat_inc(req.graph_id)
    used_after = used + 1

    if username:
        u = user_get_by_username(username)
        if u:
            query_history_add(u["id"], req.graph_id, req.query.strip(), answer)

    return QueryResponse(answer=answer, today_used=used_after, daily_limit=limit)
