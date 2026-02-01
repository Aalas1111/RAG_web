#!/usr/bin/env python3
"""
测试 insert_txt.py 脚本
执行首次构建索引，处理200篇txt文件
"""

import sys
import os
import time
import asyncio
from datetime import datetime

# 确保可以导入 insert_txt 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from insert_txt import build_first_index, build_first_index_async

    print("导入 insert_txt 成功")
except ImportError as e:
    print(f"导入失败: {e}")
    print("请确保 insert_txt.py 文件在同一目录下")
    sys.exit(1)


async def test_first_time_build_async():
    """异步测试首次构建索引"""
    print("=" * 60)
    print("南京大学新闻RAG系统 - 向量化构建测试 (异步)")
    print("=" * 60)
    print(f"测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 显示测试配置
    max_files = 200
    print("测试配置:")
    print(f"  模式: 首次构建索引 (异步)")
    print(f"  最大处理文件数: {max_files}")
    print(f"  输入目录: /home/Aalas/RAG/LightRAG/insert/input")
    print(f"  输出目录: /home/Aalas/RAG/LightRAG/insert/output")
    print(f"  错误报告目录: vectorization_errors")
    print()

    # 检查输入目录
    input_dir = "/home/Aalas/RAG/LightRAG/insert/input"
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录不存在: {input_dir}")
        return False

    # 检查输入目录中的文件
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    print(f"输入目录中找到 {len(txt_files)} 个txt文件")

    if len(txt_files) == 0:
        print("错误: 输入目录中没有txt文件")
        return False

    if max_files and len(txt_files) < max_files:
        print(f"注意: 输入目录中只有 {len(txt_files)} 个文件，但请求处理 {max_files} 个")
        print(f"将处理所有 {len(txt_files)} 个文件")
        actual_max = len(txt_files)
    else:
        actual_max = max_files

    print()
    print("开始构建索引...")
    print("-" * 40)

    # 记录开始时间
    start_time = time.time()

    try:
        # 调用异步首次构建函数
        stats = await build_first_index_async(max_files=actual_max)

        # 计算耗时
        elapsed_time = time.time() - start_time

        # 显示结果
        print()
        print("=" * 60)
        print("测试结果")
        print("=" * 60)
        print(f"总耗时: {elapsed_time:.2f} 秒")
        if stats['total_files'] > 0:
            print(f"平均每个文件: {elapsed_time / stats['total_files']:.2f} 秒")
        print()
        print("处理统计:")
        print(f"  总文件数: {stats['total_files']}")
        print(f"  成功数: {stats['successful']}")
        print(f"  失败数: {stats['failed']}")

        if stats['failed'] > 0:
            print(f"  错误数: {len(stats['errors'])}")
            print()
            print("错误详情:")
            for i, error in enumerate(stats['errors'][:5], 1):  # 只显示前5个错误
                print(f"  {i}. {error}")

            if len(stats['errors']) > 5:
                print(f"  ... 还有 {len(stats['errors']) - 5} 个错误未显示")

        # 检查输出目录
        output_dir = "/home/Aalas/RAG/LightRAG/insert/output"
        if os.path.exists(output_dir):
            output_files = [f for f in os.listdir(output_dir) if not f.startswith('.')]
            print()
            print("输出目录内容:")
            print(f"  文件数: {len(output_files)}")

            if output_files:
                # 计算总大小
                total_size = 0
                for f in output_files:
                    filepath = os.path.join(output_dir, f)
                    if os.path.isfile(filepath):
                        total_size += os.path.getsize(filepath)

                print(f"  总大小: {total_size / 1024 / 1024:.2f} MB")

        # 检查输入目录剩余文件
        remaining_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
        print()
        print("输入目录剩余文件:")
        print(f"  txt文件数: {len(remaining_files)}")

        if remaining_files:
            print("  剩余文件示例:")
            for f in remaining_files[:5]:
                filepath = os.path.join(input_dir, f)
                size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
                print(f"    {f} ({size / 1024:.1f} KB)")

            if len(remaining_files) > 5:
                print(f"  ... 还有 {len(remaining_files) - 5} 个文件未显示")

        print()
        print("测试完成!")

        # 返回成功标志
        return stats['failed'] == 0

    except Exception as e:
        print(f"构建过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_first_time_build_sync():
    """同步测试首次构建索引"""
    print("=" * 60)
    print("南京大学新闻RAG系统 - 向量化构建测试 (同步)")
    print("=" * 60)

    # 显示测试配置
    max_files = 50  # 同步版本处理较少文件
    print(f"测试配置: 同步版本，最多处理 {max_files} 个文件")

    try:
        start_time = time.time()
        stats = build_first_index(max_files=max_files)
        elapsed_time = time.time() - start_time

        print(f"同步处理耗时: {elapsed_time:.2f} 秒")
        print(f"成功数: {stats['successful']}, 失败数: {stats['failed']}")

        return stats['failed'] == 0
    except Exception as e:
        print(f"同步构建失败: {e}")
        return False


async def main():
    """主函数"""
    print("测试脚本启动...")
    print()

    # 运行异步首次构建测试
    success = await test_first_time_build_async()

    print()
    print("=" * 60)
    if success:
        print("✅ 测试通过！首次构建索引完成")
        print("=" * 60)
    else:
        print("❌ 测试失败！请检查错误信息")
        print("=" * 60)

    print()
    print("测试脚本结束")

    # 根据测试结果返回适当的退出码
    return success


if __name__ == "__main__":
    # 运行异步主函数
    success = asyncio.run(main())
    sys.exit(0 if success else 1)