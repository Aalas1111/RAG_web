#!/usr/bin/env python3
"""
增量更新脚本 - 将新的txt文件添加到现有索引中
处理input目录中的100个txt文件
"""

import os
import sys
import asyncio
import logging
import traceback
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

# 添加项目路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

try:
    # 导入LightRAG相关模块
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

# 路径配置
INPUT_DIR = "/home/Aalas/RAG/LightRAG/insert/input"
OUTPUT_DIR = "/home/Aalas/RAG/LightRAG/insert/output"
ERROR_REPORT_DIR = "incremental_errors"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('incremental_update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class IncrementalUpdater:
    """增量更新器"""

    def __init__(self, max_files: int = 100):
        """初始化增量更新器

        Args:
            max_files: 最大处理文件数
        """
        self.input_dir = Path(INPUT_DIR)
        self.output_dir = Path(OUTPUT_DIR)
        self.error_dir = Path(ERROR_REPORT_DIR)
        self.max_files = max_files

        # 创建错误报告目录
        self.error_dir.mkdir(exist_ok=True)

        # 初始化LightRAG
        self.rag = None

        # 处理统计
        self.stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'errors': [],
            'processed_files': []
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

            # 创建LightRAG实例 - 使用现有的工作目录
            self.rag = LightRAG(
                working_dir=str(self.output_dir),
                llm_model_func=llm_model_func,
                embedding_func=EmbeddingFunc(
                    embedding_dim=1024,  # BAAI/bge-m3的向量维度是1024
                    max_token_size=8192,
                    func=embedding_func
                )
            )

            logger.info("LightRAG初始化成功，已加载现有索引")

        except Exception as e:
            logger.error(f"初始化LightRAG失败: {e}")
            raise

    def _get_txt_files(self) -> List[Path]:
        """获取要处理的txt文件列表"""
        # 获取所有txt文件并按文件名排序
        txt_files = list(self.input_dir.glob("*.txt"))
        txt_files.sort()  # 按文件名排序

        # 限制处理数量
        if self.max_files and self.max_files > 0:
            txt_files = txt_files[:self.max_files]

        return txt_files

    def _save_error_report(self, file_path: Path, error_msg: str):
        """保存错误报告"""
        error_file = self.error_dir / f"error_{Path(file_path).stem}.txt"

        try:
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"文件: {file_path}\n")
                f.write(f"错误信息: {error_msg}\n")
                f.write(f"错误详情:\n{traceback.format_exc()}\n")
                f.write("-" * 80 + "\n")
        except Exception as e:
            logger.error(f"保存错误报告失败: {e}")

    async def _process_single_file(self, file_path: Path) -> Tuple[bool, str]:
        """处理单个txt文件

        Args:
            file_path: 文件路径

        Returns:
            (是否成功, 错误信息或成功消息)
        """
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            if not content.strip():
                msg = f"文件 {file_path.name} 内容为空"
                logger.warning(msg)
                return False, msg

            # 插入到RAG索引 - 使用同步方法
            self.rag.insert([content])

            msg = f"文件 {file_path.name} 成功添加到索引"
            logger.info(msg)
            return True, msg

        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as file:
                    content = file.read()

                self.rag.insert([content])
                msg = f"文件 {file_path.name} 成功添加到索引 (使用GBK编码)"
                logger.info(msg)
                return True, msg

            except Exception as e:
                error_msg = f"文件 {file_path.name} 解码失败: {e}"
                logger.error(error_msg)
                self._save_error_report(file_path, error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"处理文件 {file_path.name} 失败: {e}"
            logger.error(error_msg)
            self._save_error_report(file_path, error_msg)
            return False, error_msg

    def _delete_file(self, file_path: Path):
        """删除已处理的文件

        Args:
            file_path: 文件路径
        """
        try:
            file_path.unlink()  # 删除文件
            logger.info(f"已删除文件: {file_path.name}")
            return True
        except Exception as e:
            logger.error(f"删除文件 {file_path.name} 失败: {e}")
            return False

    async def _process_batch(self, txt_files: List[Path]):
        """处理一批文件"""
        for i, file_path in enumerate(txt_files, 1):
            logger.info(f"处理文件 {i}/{len(txt_files)}: {file_path.name}")

            # 处理单个文件
            success, message = await self._process_single_file(file_path)

            if success:
                self.stats['successful'] += 1
                self.stats['processed_files'].append(file_path)
                logger.info(f"  ✓ {message}")
            else:
                self.stats['failed'] += 1
                self.stats['errors'].append(message)
                logger.error(f"  ✗ {message}")

            # 每处理5个文件后短暂延迟，避免API限制
            if i % 5 == 0 and i < len(txt_files):
                logger.info(f"  已处理 {i} 个文件，等待2秒...")
                await asyncio.sleep(2)

    async def run_update(self) -> bool:
        """运行增量更新

        Returns:
            是否成功完成
        """
        print("=" * 60)
        print("增量更新脚本启动")
        print("=" * 60)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 检查输入目录
        if not self.input_dir.exists():
            print(f"错误: 输入目录不存在: {self.input_dir}")
            return False

        # 检查输出目录（索引目录）
        if not self.output_dir.exists():
            print(f"错误: 索引目录不存在: {self.output_dir}")
            print("请先运行 insert_txt.py 构建初始索引")
            return False

        # 获取要处理的文件
        txt_files = self._get_txt_files()
        self.stats['total_files'] = len(txt_files)

        if not txt_files:
            print("没有找到txt文件需要处理")
            return True  # 没有文件也是一种成功状态

        print(f"找到 {len(txt_files)} 个txt文件需要处理")
        print(f"最大处理限制: {self.max_files}")
        print()

        # 显示前10个文件
        print("前10个文件:")
        for i, file_path in enumerate(txt_files[:10], 1):
            size = file_path.stat().st_size if file_path.exists() else 0
            print(f"  {i}. {file_path.name} ({size / 1024:.1f} KB)")

        if len(txt_files) > 10:
            print(f"  ... 还有 {len(txt_files) - 10} 个文件")

        print()

        # 初始化RAG
        try:
            await self._init_rag()
        except Exception as e:
            print(f"初始化RAG失败: {e}")
            return False

        # 处理文件
        print("开始处理文件...")
        print("-" * 40)

        start_time = datetime.now()

        try:
            await self._process_batch(txt_files)
        except Exception as e:
            logger.error(f"处理过程中发生错误: {e}")
            return False

        # 删除已成功处理的文件
        if self.stats['processed_files']:
            print(f"\n开始删除已成功处理的 {len(self.stats['processed_files'])} 个文件...")
            deleted_count = 0
            for file_path in self.stats['processed_files']:
                if self._delete_file(file_path):
                    deleted_count += 1

            print(f"成功删除 {deleted_count} 个文件")

        # 计算耗时
        end_time = datetime.now()
        duration = end_time - start_time

        # 显示统计信息
        self._show_statistics(duration)

        return True

    def _show_statistics(self, duration):
        """显示统计信息"""
        print("\n" + "=" * 60)
        print("增量更新完成!")
        print("=" * 60)

        print(f"处理时间: {duration.total_seconds():.1f} 秒")
        if self.stats['total_files'] > 0:
            print(f"平均每个文件: {duration.total_seconds() / self.stats['total_files']:.2f} 秒")

        print()
        print("处理统计:")
        print(f"  总文件数: {self.stats['total_files']}")
        print(f"  成功数: {self.stats['successful']}")
        print(f"  失败数: {self.stats['failed']}")

        if self.stats['failed'] > 0:
            print(f"  错误数: {len(self.stats['errors'])}")
            print()
            print("错误详情:")
            for i, error in enumerate(self.stats['errors'][:5], 1):  # 只显示前5个错误
                print(f"  {i}. {error}")

            if len(self.stats['errors']) > 5:
                print(f"  ... 还有 {len(self.stats['errors']) - 5} 个错误未显示")

        # 检查索引目录中的文件变化
        if self.output_dir.exists():
            output_files = [f for f in self.output_dir.rglob("*") if f.is_file()]
            if output_files:
                total_size = sum(f.stat().st_size for f in output_files)
                print()
                print("索引目录信息:")
                print(f"  文件数: {len(output_files)}")
                print(f"  总大小: {total_size / 1024 / 1024:.2f} MB")

        # 检查输入目录剩余文件
        remaining_files = list(self.input_dir.glob("*.txt"))
        print()
        print("输入目录剩余文件:")
        print(f"  txt文件数: {len(remaining_files)}")

        if remaining_files:
            print("  剩余文件示例:")
            for i, file_path in enumerate(remaining_files[:5], 1):
                size = file_path.stat().st_size if file_path.exists() else 0
                print(f"    {i}. {file_path.name} ({size / 1024:.1f} KB)")

            if len(remaining_files) > 5:
                print(f"    ... 还有 {len(remaining_files) - 5} 个文件")


async def main_async():
    """异步主函数"""
    # 设置最大处理文件数
    max_files = 100

    print("增量更新配置:")
    print(f"  输入目录: {INPUT_DIR}")
    print(f"  索引目录: {OUTPUT_DIR}")
    print(f"  最大处理文件数: {max_files}")
    print(f"  错误报告目录: {ERROR_REPORT_DIR}")
    print()

    # 创建更新器
    updater = IncrementalUpdater(max_files=max_files)

    # 运行更新
    success = await updater.run_update()

    return success


def main():
    """主函数"""
    try:
        # 运行异步主函数
        success = asyncio.run(main_async())

        print("\n" + "=" * 60)
        if success:
            print("✅ 增量更新完成!")
            print("=" * 60)
            sys.exit(0)
        else:
            print("❌ 增量更新失败!")
            print("=" * 60)
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n增量更新被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n增量更新过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()