#!/usr/bin/env python3
"""
向量化处理器 - 用于将txt文件向量化并构建LightRAG索引
支持首次构建索引和增量更新两种模式
"""

import os
import sys
import asyncio
import logging
import traceback
from pathlib import Path
from typing import List, Optional
import numpy as np
from datetime import datetime

# 添加项目路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

try:
    # 标准导入方式 - 假设LightRAG已安装
    from lightrag import LightRAG
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

# 路径配置
INPUT_DIR = "/home/Aalas/RAG/LightRAG/insert/input"
OUTPUT_DIR = "/home/Aalas/RAG/LightRAG/insert/output"
ERROR_REPORT_DIR = "vectorization_errors"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vectorization.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class VectorizationProcessor:
    """向量化处理器类"""

    def __init__(self):
        """初始化向量化处理器"""
        self.input_dir = Path(INPUT_DIR)
        self.output_dir = Path(OUTPUT_DIR)
        self.error_dir = Path(ERROR_REPORT_DIR)

        # 创建目录
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.error_dir.mkdir(exist_ok=True)

        # 初始化LightRAG
        self.rag = None
        self.loop = None

        # 处理统计
        self.stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }

    async def _init_rag(self):
        """异步初始化LightRAG实例"""
        try:
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
                    max_token_size=8192,  # BAAI/bge-m3支持8192上下文
                )

            # 创建LightRAG实例
            self.rag = LightRAG(
                working_dir=str(self.output_dir),
                llm_model_func=llm_model_func,
                embedding_func=EmbeddingFunc(
                    embedding_dim=1024,  # BAAI/bge-m3的向量维度是1024
                    max_token_size=8192,
                    func=embedding_func
                )
            )

            logger.info("LightRAG初始化成功")

        except Exception as e:
            logger.error(f"初始化LightRAG失败: {e}")
            raise

    def _get_txt_files(self, max_files: Optional[int] = None) -> List[Path]:
        """获取要处理的txt文件列表

        Args:
            max_files: 最大处理文件数，None表示处理所有文件

        Returns:
            txt文件路径列表
        """
        # 获取所有txt文件并按文件名排序
        txt_files = list(self.input_dir.glob("*.txt"))
        txt_files.sort()  # 按文件名排序

        if max_files is not None and max_files > 0:
            txt_files = txt_files[:max_files]

        return txt_files

    def _save_error_report(self, file_path: Path, error_msg: str):
        """保存错误报告"""
        error_file = self.error_dir / f"errors_{Path(file_path).stem}.txt"

        try:
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"文件: {file_path}\n")
                f.write(f"错误信息: {error_msg}\n")
                f.write(f"错误详情:\n{traceback.format_exc()}\n")
                f.write("-" * 80 + "\n")
        except Exception as e:
            logger.error(f"保存错误报告失败: {e}")

    async def _process_single_file(self, file_path: Path) -> bool:
        """异步处理单个txt文件

        Args:
            file_path: 文件路径

        Returns:
            处理成功返回True，否则返回False
        """
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            if not content.strip():
                logger.warning(f"文件 {file_path.name} 内容为空，跳过")
                return False

            # 插入到RAG索引 - 使用异步方式
            await self._insert_content_async([content])

            logger.info(f"文件 {file_path.name} 向量化成功")
            return True

        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as file:
                    content = file.read()

                await self._insert_content_async([content])
                logger.info(f"文件 {file_path.name} 向量化成功 (使用GBK编码)")
                return True

            except Exception as e:
                error_msg = f"文件 {file_path.name} 解码失败: {e}"
                logger.error(error_msg)
                self.stats['errors'].append(error_msg)
                self._save_error_report(file_path, error_msg)
                return False

        except Exception as e:
            error_msg = f"处理文件 {file_path.name} 失败: {e}"
            logger.error(error_msg)
            self.stats['errors'].append(error_msg)
            self._save_error_report(file_path, error_msg)
            return False

    async def _insert_content_async(self, contents: List[str]):
        """异步插入内容到RAG索引

        Args:
            contents: 内容列表
        """
        # 使用异步插入方法
        await self.rag.ainsert(contents)

    def _delete_file(self, file_path: Path):
        """删除已处理的文件

        Args:
            file_path: 文件路径
        """
        try:
            file_path.unlink()  # 删除文件
            logger.debug(f"已删除文件: {file_path.name}")
        except Exception as e:
            logger.error(f"删除文件 {file_path.name} 失败: {e}")

    async def _build_index_async(self, max_files: Optional[int] = None, is_first_time: bool = False) -> dict:
        """异步构建索引的核心逻辑

        Args:
            max_files: 最大处理文件数
            is_first_time: 是否首次构建

        Returns:
            处理统计信息
        """
        # 重置统计
        self.stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }

        # 获取要处理的文件
        txt_files = self._get_txt_files(max_files)
        self.stats['total_files'] = len(txt_files)

        if not txt_files:
            logger.info("没有找到txt文件需要处理")
            return self.stats

        logger.info(f"找到 {len(txt_files)} 个txt文件需要处理")

        # 分批处理文件
        batch_size = 5  # 减少批量大小以避免API限制
        successful_files = []

        for i in range(0, len(txt_files), batch_size):
            batch = txt_files[i:i + batch_size]
            logger.info(f"处理第 {i // batch_size + 1} 批文件 (共 {len(batch)} 个文件)")

            # 异步处理批次中的每个文件
            tasks = []
            for file_idx, file_path in enumerate(batch, 1):
                logger.info(f"  处理文件 {i + file_idx}/{len(txt_files)}: {file_path.name}")
                tasks.append(self._process_single_file(file_path))

            # 等待批次中的所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for file_path, result in zip(batch, results):
                if isinstance(result, Exception):
                    error_msg = f"处理文件 {file_path.name} 时发生异常: {result}"
                    logger.error(error_msg)
                    self.stats['errors'].append(error_msg)
                    self.stats['failed'] += 1
                    self._save_error_report(file_path, str(result))
                elif result is True:
                    self.stats['successful'] += 1
                    successful_files.append(file_path)
                else:
                    self.stats['failed'] += 1

            # 每批处理后显示进度
            logger.info(f"  批次进度: 成功 {self.stats['successful']}, 失败 {self.stats['failed']}")

            # 批次之间短暂延迟，避免API限制
            if i + batch_size < len(txt_files):
                await asyncio.sleep(1)

        # 删除已成功处理的文件
        if successful_files:
            logger.info(f"开始删除已成功处理的 {len(successful_files)} 个文件...")
            for file_path in successful_files:
                self._delete_file(file_path)
            logger.info("文件删除完成")

        # 显示统计信息
        self._show_statistics()

        return self.stats

    async def build_index_first_time_async(self, max_files: Optional[int] = None) -> dict:
        """异步首次构建索引

        Args:
            max_files: 最大处理文件数，None表示处理所有文件

        Returns:
            处理统计信息
        """
        logger.info("=" * 60)
        logger.info("开始首次构建索引")
        logger.info(f"输入目录: {self.input_dir}")
        logger.info(f"输出目录: {self.output_dir}")
        logger.info(f"最大处理文件数: {max_files if max_files else '无限制'}")
        logger.info("=" * 60)

        # 初始化RAG
        await self._init_rag()

        return await self._build_index_async(max_files, is_first_time=True)

    async def build_index_incrementally_async(self, max_files: Optional[int] = None) -> dict:
        """异步增量更新索引

        Args:
            max_files: 最大处理文件数，None表示处理所有文件

        Returns:
            处理统计信息
        """
        logger.info("=" * 60)
        logger.info("开始增量更新索引")
        logger.info(f"输入目录: {self.input_dir}")
        logger.info(f"输出目录: {self.output_dir}")
        logger.info(f"最大处理文件数: {max_files if max_files else '无限制'}")
        logger.info("=" * 60)

        # 初始化RAG
        await self._init_rag()

        return await self._build_index_async(max_files, is_first_time=False)

    def build_index_first_time(self, max_files: Optional[int] = None) -> dict:
        """同步首次构建索引（包装异步方法）

        Args:
            max_files: 最大处理文件数，None表示处理所有文件

        Returns:
            处理统计信息
        """
        return asyncio.run(self.build_index_first_time_async(max_files))

    def build_index_incrementally(self, max_files: Optional[int] = None) -> dict:
        """同步增量更新索引（包装异步方法）

        Args:
            max_files: 最大处理文件数，None表示处理所有文件

        Returns:
            处理统计信息
        """
        return asyncio.run(self.build_index_incrementally_async(max_files))

    def _show_statistics(self):
        """显示处理统计信息"""
        logger.info("\n" + "=" * 60)
        logger.info("向量化处理完成!")
        logger.info(f"总文件数: {self.stats['total_files']}")
        logger.info(f"成功数: {self.stats['successful']}")
        logger.info(f"失败数: {self.stats['failed']}")

        if self.stats['failed'] > 0:
            logger.warning(f"错误数: {len(self.stats['errors'])}")
            logger.warning("错误详情已保存到 error_report 目录")

        # 检查output目录中的索引文件
        if self.output_dir.exists():
            # 统计output目录中的文件
            output_files = list(self.output_dir.rglob("*"))
            if output_files:
                logger.info(f"输出目录文件数: {len(output_files)}")

                # 计算总大小
                total_size = sum(f.stat().st_size for f in output_files if f.is_file())
                logger.info(f"索引总大小: {total_size / 1024 / 1024:.2f} MB")
            else:
                logger.warning("输出目录中没有找到索引文件")


# 提供便捷的函数接口
def build_first_index(max_files: Optional[int] = None) -> dict:
    """首次构建索引的便捷函数

    Args:
        max_files: 最大处理文件数

    Returns:
        处理统计信息
    """
    processor = VectorizationProcessor()
    return processor.build_index_first_time(max_files)


def build_incremental_index(max_files: Optional[int] = None) -> dict:
    """增量更新索引的便捷函数

    Args:
        max_files: 最大处理文件数

    Returns:
        处理统计信息
    """
    processor = VectorizationProcessor()
    return processor.build_index_incrementally(max_files)


# 异步便捷函数
async def build_first_index_async(max_files: Optional[int] = None) -> dict:
    """异步首次构建索引的便捷函数

    Args:
        max_files: 最大处理文件数

    Returns:
        处理统计信息
    """
    processor = VectorizationProcessor()
    return await processor.build_index_first_time_async(max_files)


async def build_incremental_index_async(max_files: Optional[int] = None) -> dict:
    """异步增量更新索引的便捷函数

    Args:
        max_files: 最大处理文件数

    Returns:
        处理统计信息
    """
    processor = VectorizationProcessor()
    return await processor.build_index_incrementally_async(max_files)


# 测试函数示例（将在另一个文件中实现）
if __name__ == "__main__":
    # 这里只是示例，实际使用将在另一个文件中
    print("这是一个模块文件，请在其他文件中导入使用")
    print("示例用法:")
    print("  同步版本:")
    print("    from insert_txt import build_first_index, build_incremental_index")
    print("    # 首次构建索引，最多处理50个文件")
    print("    stats = build_first_index(max_files=50)")
    print("    # 增量更新，处理所有新文件")
    print("    stats = build_incremental_index()")
    print()
    print("  异步版本:")
    print("    import asyncio")
    print("    from insert_txt import build_first_index_async")
    print("    # 异步首次构建索引")
    print("    stats = asyncio.run(build_first_index_async(max_files=50))")