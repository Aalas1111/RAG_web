#!/usr/bin/env python3
"""
测试查询脚本 - 测试LightRAG的不同检索模式
修复版本：正确处理异步调用
"""

import os
import sys
import asyncio
import numpy as np
from datetime import datetime

# 添加项目路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

try:
    # 标准导入方式 - 假设LightRAG已安装
    from lightrag import LightRAG, QueryParam
    from lightrag.utils import EmbeddingFunc
    from lightrag.llm import openai_complete_if_cache, siliconcloud_embedding

    print("成功导入LightRAG模块")

except ImportError as e:
    print(f"导入失败: {e}")
    print("请确保已安装LightRAG库:")
    print("  1. cd /home/Aalas/RAG/LightRAG")
    print("  2. pip install . 或 pip install -e .")
    sys.exit(1)

# === API配置 ===
# DeepSeek (LLM) 配置
DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_API_KEY = "sk-c2f96e5922874401825f0f906432b1bb"
DEEPSEEK_MODEL = "deepseek-chat"

# SiliconCloud (Embedding) 配置
SILICONCLOUD_EMBEDDING_MODEL = "BAAI/bge-m3"
SILICONCLOUD_API_KEY = "sk-zzsidapbtweemvltynzpxzmkfjuzgmfgiuificecwfgpzozt"

# 工作目录配置（与insert_txt.py中使用的目录一致）
WORKING_DIR = "/home/Aalas/RAG/LightRAG/insert/output"


def check_index_files():
    """检查索引文件是否存在"""
    print("检查索引文件...")

    if not os.path.exists(WORKING_DIR):
        print(f"错误: 工作目录不存在: {WORKING_DIR}")
        return False

    # 检查目录中的文件
    files = os.listdir(WORKING_DIR)
    if not files:
        print(f"警告: 工作目录为空: {WORKING_DIR}")
        print("请先运行 insert_txt.py 构建索引")
        return False

    print(f"工作目录: {WORKING_DIR}")
    print(f"找到 {len(files)} 个索引文件")

    # 显示文件类型统计
    file_types = {}
    for f in files:
        if not f.startswith('.'):  # 忽略隐藏文件
            ext = os.path.splitext(f)[1].lower() or '无扩展名'
            file_types[ext] = file_types.get(ext, 0) + 1

    for ext, count in file_types.items():
        print(f"  {ext}: {count} 个文件")

    # 计算总大小
    total_size = 0
    for f in files:
        if not f.startswith('.'):
            filepath = os.path.join(WORKING_DIR, f)
            if os.path.isfile(filepath):
                total_size += os.path.getsize(filepath)

    print(f"索引总大小: {total_size / 1024 / 1024:.2f} MB")
    return True


async def initialize_rag():
    """初始化RAG系统"""
    print("初始化LightRAG...")

    # 自定义Chat模型 (使用DeepSeek)
    async def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs) -> str:
        return await openai_complete_if_cache(
            model=DEEPSEEK_MODEL,
            prompt=prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_API_BASE,
            **kwargs
        )

    # 自定义Embedding模型 (使用SiliconCloud)
    async def embedding_func(texts: list[str]) -> np.ndarray:
        return await siliconcloud_embedding(
            texts,
            model=SILICONCLOUD_EMBEDDING_MODEL,
            api_key=SILICONCLOUD_API_KEY,
            max_token_size=8192,
        )

    # 创建LightRAG实例
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=1024,  # BAAI/bge-m3的向量维度是1024
            max_token_size=8192,
            func=embedding_func
        )
    )

    print("LightRAG初始化完成")
    return rag


async def test_query_modes(rag, query_text):
    """测试不同的查询模式 - 修复异步调用"""
    print("\n" + "=" * 60)
    print(f"测试查询: {query_text}")
    print("=" * 60)

    results = {}

    # 1. naive检索 (纯向量检索)
    print("\n=== naive检索结果 (纯向量检索) ===")
    print("模式说明: 基于向量相似度的简单检索，返回最相关的文档片段")
    try:
        # 使用异步的aquery方法
        naive_result = await rag.aquery(query_text, param=QueryParam(mode="naive"))
        results['naive'] = naive_result
        print(f"结果: {naive_result}")
    except Exception as e:
        error_msg = str(e)
        print(f"naive检索失败: {error_msg}")
        results['naive'] = f"错误: {error_msg}"

    # 2. local检索 (基于图谱的局部检索)
    print("\n=== local检索结果 (基于图谱的局部检索) ===")
    print("模式说明: 在知识图谱的局部范围内进行检索，关注相关性")
    try:
        local_result = await rag.aquery(query_text, param=QueryParam(mode="local"))
        results['local'] = local_result
        print(f"结果: {local_result}")
    except Exception as e:
        error_msg = str(e)
        print(f"local检索失败: {error_msg}")
        results['local'] = f"错误: {error_msg}"

    # 3. global检索 (基于图谱的全局检索)
    print("\n=== global检索结果 (基于图谱的全局检索) ===")
    print("模式说明: 在知识图谱的全局范围内进行检索，考虑全局结构")
    try:
        global_result = await rag.aquery(query_text, param=QueryParam(mode="global"))
        results['global'] = global_result
        print(f"结果: {global_result}")
    except Exception as e:
        error_msg = str(e)
        print(f"global检索失败: {error_msg}")
        results['global'] = f"错误: {error_msg}"

    # 4. hybrid检索 (混合检索)
    print("\n=== hybrid检索结果 (混合检索) ===")
    print("模式说明: 结合多种检索策略的混合模式")
    try:
        hybrid_result = await rag.aquery(query_text, param=QueryParam(mode="hybrid"))
        results['hybrid'] = hybrid_result
        print(f"结果: {hybrid_result}")
    except Exception as e:
        error_msg = str(e)
        print(f"hybrid检索失败: {error_msg}")
        results['hybrid'] = f"错误: {error_msg}"

    return results


async def test_single_query_simple(rag, query_text):
    """简单的单个查询测试，避免复杂模式"""
    print(f"\n查询: {query_text}")
    print("-" * 40)

    try:
        # 使用global模式进行测试，注意使用异步调用
        result = await rag.aquery(query_text, param=QueryParam(mode="global"))
        print(f"结果: {result}")
        return True, result
    except Exception as e:
        print(f"查询失败: {e}")
        return False, str(e)


async def run_simple_tests():
    """运行简化的测试"""
    print("=" * 60)
    print("南京大学新闻RAG系统 - 简化查询测试")
    print("=" * 60)
    print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 检查索引文件
    if not check_index_files():
        return False

    print()
    print("配置信息:")
    print(f"  工作目录: {WORKING_DIR}")
    print(f"  LLM模型: {DEEPSEEK_MODEL}")
    print(f"  嵌入模型: {SILICONCLOUD_EMBEDDING_MODEL}")
    print(f"  向量维度: 1024")
    print()

    # 初始化RAG
    try:
        rag = await initialize_rag()
    except Exception as e:
        print(f"初始化RAG失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 定义测试查询
    test_queries = [
        "南京大学新闻主要涉及哪些主题的内容",
        "南京大学在2025年有哪些重要的科研成果",
        "南京大学的校园文化活动有哪些",
        "南京大学与国际高校有哪些合作交流",
        "南京大学在人才培养方面有什么特色"
    ]

    all_results = {}

    # 对每个查询进行简单测试
    for i, query_text in enumerate(test_queries, 1):
        print(f"\n{'=' * 60}")
        print(f"测试 {i}/{len(test_queries)}")

        success, result = await test_single_query_simple(rag, query_text)
        all_results[query_text] = {
            'success': success,
            'result': result
        }

        # 等待一下，避免API限制
        if i < len(test_queries):
            print(f"\n等待3秒后继续下一个测试...")
            await asyncio.sleep(3)

    # 显示总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    success_count = 0
    for query_text, info in all_results.items():
        print(f"\n查询: {query_text}")
        if info['success']:
            success_count += 1
            # 截断过长的结果以便显示
            result = info['result']
            if result and len(result) > 300:
                result = result[:300] + "..."
            print(f"  状态: ✅ 成功")
            print(f"  结果: {result}")
        else:
            print(f"  状态: ❌ 失败")
            print(f"  错误: {info['result']}")

    print(f"\n总成功率: {success_count}/{len(test_queries)} ({success_count / len(test_queries) * 100:.1f}%)")

    return success_count > 0


async def run_full_tests():
    """运行完整测试（四种模式）"""
    print("=" * 60)
    print("南京大学新闻RAG系统 - 完整查询测试")
    print("=" * 60)

    # 检查索引文件
    if not check_index_files():
        return False

    # 初始化RAG
    try:
        rag = await initialize_rag()
    except Exception as e:
        print(f"初始化RAG失败: {e}")
        return False

    # 测试单个查询
    query_text = "南京大学新闻主要涉及哪些主题的内容"
    results = await test_query_modes(rag, query_text)

    return results


async def main():
    """主函数"""
    print("测试脚本启动...")
    print()

    print("请选择测试模式:")
    print("1. 简单测试（只测试global模式）")
    print("2. 完整测试（测试所有四种模式）")
    print("3. 退出")

    choice = input("\n请选择 (1/2/3): ").strip()

    if choice == "1":
        # 运行简单测试
        success = await run_simple_tests()

        print("\n" + "=" * 60)
        if success:
            print("✅ 简单查询测试完成!")
            print("=" * 60)
            return True
        else:
            print("❌ 简单查询测试失败!")
            print("=" * 60)
            return False

    elif choice == "2":
        # 运行完整测试
        results = await run_full_tests()

        print("\n" + "=" * 60)
        if results:
            print("✅ 完整查询测试完成!")
            print("=" * 60)
            return True
        else:
            print("❌ 完整查询测试失败!")
            print("=" * 60)
            return False

    elif choice == "3":
        print("退出测试")
        return True
    else:
        print("无效选择")
        return False


if __name__ == "__main__":
    try:
        # 运行异步主函数
        success = asyncio.run(main())

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)