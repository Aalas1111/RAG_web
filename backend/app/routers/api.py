"""公开 API：图谱列表、查询"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import graph_list, graph_get, can_query_today, query_stat_inc, query_stat_get_today
from app.rag_service import query_async, VALID_MODES

router = APIRouter()


class QueryRequest(BaseModel):
    graph_id: int
    query: str
    mode: str = "hybrid"


class QueryResponse(BaseModel):
    answer: str
    today_used: int
    daily_limit: int


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


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    """对指定图谱进行 query，返回 AI 回答；并增加今日查询次数"""
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
    return QueryResponse(answer=answer, today_used=used_after, daily_limit=limit)
