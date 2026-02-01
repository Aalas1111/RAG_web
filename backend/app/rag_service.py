"""LightRAG 封装：按 working_dir 初始化、查询、插入"""
import asyncio
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

import numpy as np
import aiohttp

# 确保可导入 lightrag（项目根或已安装 lightrag-hku）
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# 兼容不同版本 lightrag-hku：1.4.9.11 中 lightrag.llm 为空，LLM/Embedding 在 lightrag.llm.openai
# 硅基流动使用 OpenAI 兼容接口，用 openai_embed + base_url 实现，不依赖 siliconcloud_embedding
LightRAG = None
QueryParam = None
EmbeddingFunc = None
openai_complete_if_cache = None
openai_embed = None  # 用于硅基流动：openai_embed(texts, model=..., api_key=..., base_url=硅基流动)
_import_error = None

SILICONFLOW_EMBED_BASE = "https://api.siliconflow.cn/v1"  # 硅基流动 OpenAI 兼容 embedding 地址
SILICONFLOW_RERANK_URL = "https://api.siliconflow.cn/v1/rerank"  # 硅基流动 rerank 接口

def _load_lightrag_llm():
    global LightRAG, QueryParam, EmbeddingFunc, openai_complete_if_cache, openai_embed, _import_error
    try:
        from lightrag import LightRAG, QueryParam
        from lightrag.utils import EmbeddingFunc
        from lightrag.llm.openai import openai_complete_if_cache, openai_embed
    except ImportError as e2:
        _import_error = e2
        LightRAG = None
        QueryParam = None
        EmbeddingFunc = None
        openai_complete_if_cache = None
        openai_embed = None

_load_lightrag_llm()

from app.config import get_settings

VALID_MODES = ("naive", "local", "global", "hybrid")


def _check_rag_deps():
    """校验 LightRAG 依赖是否可用，不可用时抛出明确错误"""
    if _import_error is not None:
        raise ValueError(
            f"LightRAG 或依赖未正确安装（{_import_error}）。"
            "请执行: pip install lightrag-hku，并确保能执行: from lightrag.llm.openai import openai_complete_if_cache, openai_embed"
        )
    if LightRAG is None or not callable(LightRAG):
        raise ValueError("LightRAG 未正确安装，请执行: pip install lightrag-hku")
    if openai_complete_if_cache is None or not callable(openai_complete_if_cache):
        raise ValueError(
            "lightrag.llm.openai.openai_complete_if_cache 不可用。请确认已安装 lightrag-hku。"
        )
    if openai_embed is None:
        raise ValueError(
            "lightrag.llm.openai.openai_embed 不可用。硅基流动将通过 openai_embed + base_url 实现。"
        )
    if EmbeddingFunc is None:
        raise ValueError("lightrag.utils.EmbeddingFunc 不可用，请重新安装 lightrag-hku")


async def _siliconflow_rerank(
    query: str,
    documents: List[str],
    top_n: Optional[int] = None,
    api_key: str = "",
    model: str = "BAAI/bge-reranker-v2-m3",
) -> List[Dict[str, Any]]:
    """硅基流动 rerank，返回 [{"index": int, "relevance_score": float}, ...]"""
    if not documents:
        return []
    payload: Dict[str, Any] = {
        "model": model,
        "query": query,
        "documents": documents,
    }
    if top_n is not None:
        payload["top_n"] = top_n
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    async with aiohttp.ClientSession() as session:
        async with session.post(SILICONFLOW_RERANK_URL, headers=headers, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"硅基流动 rerank 请求失败 {resp.status}: {text}")
            data = await resp.json()
    results = data.get("results") or []
    out = []
    for i, r in enumerate(results):
        idx = r.get("index", i)
        score = r.get("relevance_score") or r.get("score", 0.0)
        out.append({"index": idx, "relevance_score": float(score)})
    return out


def _make_rag(working_dir: str):
    """创建 LightRAG 实例（同步包装异步初始化）"""
    _check_rag_deps()
    settings = get_settings()
    if not settings.deepseek_api_key or not settings.siliconcloud_api_key:
        raise ValueError("请在 .env 中配置 DEEPSEEK_API_KEY 和 SILICONCLOUD_API_KEY")

    # DeepSeek 不支持 response_format（GPTKeywordExtractionFormat），用底层 .func 只传必要参数
    _complete_func = getattr(openai_complete_if_cache, "func", openai_complete_if_cache)

    async def llm_model_func(prompt, system_prompt=None, history_messages=None, **kwargs) -> str:
        history_messages = history_messages or []
        # 只传必要参数，不传 response_format（DeepSeek 不支持该参数，传 None 会报 Unsupported response_format type）
        return await _complete_func(
            model=settings.deepseek_model,
            prompt=prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_api_base,
        )

    # 硅基流动为 OpenAI 兼容接口，用 openai_embed + base_url 实现（与 examples/insert_txt 等效）
    _embed_func = getattr(openai_embed, "func", openai_embed)

    async def embedding_func(texts: List[str]) -> np.ndarray:
        return await _embed_func(
            texts,
            model=settings.siliconcloud_embedding_model,
            api_key=settings.siliconcloud_api_key,
            base_url=SILICONFLOW_EMBED_BASE,
            max_token_size=8192,
        )

    # 硅基流动 BAAI/bge-reranker-v2-m3 作为 rerank 模型，与 embedding 共用 api_key（参数名需与 LightRAG 调用一致：query, documents, top_n）
    async def rerank_func(query: str, documents: List[str], top_n: Optional[int] = None, **kwargs: Any) -> List[Dict[str, Any]]:
        return await _siliconflow_rerank(
            query=query,
            documents=documents,
            top_n=top_n,
            api_key=settings.siliconcloud_api_key,
            model=settings.siliconcloud_rerank_model,
        )

    rag = LightRAG(
        working_dir=working_dir,
        llm_model_func=llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=1024,
            max_token_size=8192,
            func=embedding_func
        ),
        rerank_model_func=rerank_func,
    )
    return rag


async def query_async(working_dir: str, query_text: str, mode: str = "hybrid") -> str:
    """异步查询。mode: naive | local | global | hybrid"""
    if mode not in VALID_MODES:
        mode = "hybrid"
    rag = _make_rag(working_dir)
    await rag.initialize_storages()
    param = QueryParam(mode=mode)
    return await rag.aquery(query_text, param=param)


async def insert_async(working_dir: str, contents: List[str], is_first_time: bool = True) -> None:
    """异步插入内容。is_first_time=True 表示新建图谱；False 表示增量更新"""
    rag = _make_rag(working_dir)
    await rag.initialize_storages()
    await rag.ainsert(contents)


def query_sync(working_dir: str, query_text: str, mode: str = "hybrid") -> str:
    return asyncio.run(query_async(working_dir, query_text, mode))


def insert_sync(working_dir: str, contents: List[str], is_first_time: bool = True) -> None:
    asyncio.run(insert_async(working_dir, contents, is_first_time))
