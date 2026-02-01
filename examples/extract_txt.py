#!/usr/bin/env python3
"""
从数据库提取2025年未向量化的新闻，生成txt文件
"""

import pymysql
import json
import os
import re
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extract_txt.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'aalas',
    'password': 'aalas',
    'database': 'nju_news_server',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# 输出目录配置
OUTPUT_DIR = "/home/Aalas/RAG/LightRAG/insert/input"
ERROR_REPORT_DIR = "extract_fault_report"

# 分类到表名的映射
CATEGORY_TABLE_MAP = {
    "综合新闻": "general_news",
    "校园动态": "campus_dynamics",
    "媒体传真": "media_fax",
    "科技动态": "technology_dynamics",
    "社科动态": "social_science_dynamics",
    "理论园地": "theory_garden",
    "讲话与部署": "speech_deployment",
    "影像南大": "image_nju"
}


class NewsExtractor:
    """新闻提取器"""

    def __init__(self, config=None):
        """初始化"""
        self.config = config or DB_CONFIG
        self.connection = None
        self.cursor = None

        # 文件名长度限制
        self.MAX_FILENAME_LENGTH = 100  # 最大文件名长度（不含路径和扩展名）
        self.MAX_PATH_LENGTH = 255  # Linux最大路径长度

        # 创建输出目录
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(ERROR_REPORT_DIR, exist_ok=True)

    def connect(self):
        """连接到MySQL数据库"""
        try:
            self.connection = pymysql.connect(**self.config)
            self.cursor = self.connection.cursor()
            logger.info("成功连接到MySQL数据库")
            return True
        except pymysql.Error as e:
            logger.error(f"连接数据库时发生错误: {e}")
            return False

    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("已断开数据库连接")

    def clean_filename(self, filename: str, max_length: int = None) -> str:
        """清理文件名，移除非法字符并限制长度"""
        if max_length is None:
            max_length = self.MAX_FILENAME_LENGTH

        # 移除非法文件名字符
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # 移除多余空格
        filename = re.sub(r'\s+', ' ', filename).strip()
        # 限制长度
        if len(filename) > max_length:
            filename = filename[:max_length]
        return filename

    def generate_filename(self, news_record: Dict) -> str:
        """生成文件名，处理文件名过长问题"""
        title = news_record.get('title', '无标题')
        publish_date = news_record.get('publish_date', '')

        # 清理标题
        clean_title = self.clean_filename(title, self.MAX_FILENAME_LENGTH - 15)  # 为日期和ID留空间

        # 生成文件名
        if publish_date:
            if isinstance(publish_date, str):
                date_part = publish_date[:10]
            else:
                date_part = str(publish_date)

            # 基础文件名
            base_filename = f"{date_part}_{clean_title}.txt"

            # 如果文件名仍然太长，进一步缩短
            if len(base_filename) > self.MAX_FILENAME_LENGTH:
                # 缩短标题部分
                title_length = self.MAX_FILENAME_LENGTH - len(date_part) - 6  # -6 为下划线和扩展名
                if title_length > 0:
                    clean_title = clean_title[:title_length]
                    base_filename = f"{date_part}_{clean_title}.txt"

            # 最终检查并返回
            return base_filename[:self.MAX_FILENAME_LENGTH]
        else:
            # 没有日期，只使用标题
            return f"{clean_title}.txt"

    def generate_unique_filepath(self, filename: str) -> str:
        """生成唯一的文件路径，处理文件名冲突"""
        base_name, ext = os.path.splitext(filename)
        filepath = os.path.join(OUTPUT_DIR, filename)

        # 如果文件已存在，添加后缀
        counter = 1
        original_filepath = filepath
        while os.path.exists(filepath):
            # 检查文件路径长度
            if len(original_filepath) > self.MAX_PATH_LENGTH - 10:  # 为后缀留空间
                # 缩短基础名称
                name_length = len(base_name)
                if name_length > 50:  # 保留50个字符
                    base_name = base_name[:50]
                    original_filepath = os.path.join(OUTPUT_DIR, f"{base_name}{ext}")

            # 添加后缀
            new_filename = f"{base_name}_{counter}{ext}"
            filepath = os.path.join(OUTPUT_DIR, new_filename)
            counter += 1

            # 防止无限循环
            if counter > 100:
                # 使用哈希作为文件名
                import hashlib
                hash_id = hashlib.md5(filename.encode()).hexdigest()[:8]
                new_filename = f"news_{hash_id}{ext}"
                filepath = os.path.join(OUTPUT_DIR, new_filename)
                break

        return filepath

    def extract_text_content(self, content_json: str) -> str:
        """从JSON内容中提取所有包含text键的内容"""
        try:
            content_data = json.loads(content_json)
            if not isinstance(content_data, list):
                return ""

            # 提取所有包含text键的项，并按order排序
            text_items = []
            for item in content_data:
                if 'text' in item and item['text']:  # 只要有text键并且内容不为空
                    text_items.append(item)

            # 按order排序
            text_items.sort(key=lambda x: x.get('order', 0))

            # 提取文本内容
            text_contents = [item['text'] for item in text_items]

            # 合并文本，段落之间用换行分隔
            return '\n'.join(text_contents)

        except Exception as e:
            logger.error(f"提取文本内容失败: {e}")
            return ""

    def generate_txt_content(self, news_record: Dict) -> str:
        """生成txt文件内容"""
        title = news_record.get('title', '无标题')
        subtitle = news_record.get('subtitle', '')
        publish_date = news_record.get('publish_date', '')
        url = news_record.get('url', '')

        # 提取正文内容
        content_json = news_record.get('content_json', '[]')
        content_text = self.extract_text_content(content_json)

        # 构建txt内容
        txt_content = f"标题：{title}\n"

        if subtitle:
            txt_content += f"副标题：{subtitle}\n"

        if publish_date:
            # 确保日期格式正确
            if isinstance(publish_date, str):
                publish_date = publish_date[:10]  # 只取日期部分
            else:
                publish_date = str(publish_date)
            txt_content += f"发布时间：{publish_date}\n"

        if url:
            txt_content += f"URL：{url}\n"

        txt_content += f"\n正文：\n{content_text}"

        return txt_content

    def save_error_report(self, table_name: str, news_id: str, error_msg: str):
        """保存错误报告"""
        error_file = os.path.join(ERROR_REPORT_DIR, f"errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

        with open(error_file, 'a', encoding='utf-8') as f:
            f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"表名: {table_name}\n")
            f.write(f"新闻ID: {news_id}\n")
            f.write(f"错误信息: {error_msg}\n")
            f.write("-" * 80 + "\n")

    def extract_from_table(self, table_name: str, category_name: str) -> Dict:
        """从指定表提取新闻"""
        stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }

        try:
            # 查询2025年未向量化的新闻
            query = f"""
            SELECT id, news_hash, title, subtitle, publish_date, 
                   url, content_json, news_id, is_vectorized
            FROM {table_name} 
            WHERE publish_date LIKE '2025%' 
              AND is_vectorized = FALSE
            ORDER BY publish_date DESC
            """

            self.cursor.execute(query)
            news_list = self.cursor.fetchall()

            logger.info(f"表 {table_name} 找到 {len(news_list)} 条2025年未向量化的新闻")

            for news in news_list:
                stats['total_processed'] += 1
                news_id = news.get('news_id', str(news.get('id', '')))

                try:
                    # 生成文件名和内容
                    filename = self.generate_filename(news)
                    filepath = self.generate_unique_filepath(filename)

                    # 生成txt内容
                    txt_content = self.generate_txt_content(news)

                    # 保存到文件
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(txt_content)

                    logger.debug(f"生成文件: {os.path.basename(filepath)}")

                    # 更新数据库标记
                    update_query = f"""
                    UPDATE {table_name} 
                    SET is_vectorized = TRUE 
                    WHERE id = %s
                    """

                    self.cursor.execute(update_query, (news['id'],))

                    stats['successful'] += 1

                except Exception as e:
                    error_msg = f"处理新闻ID {news_id} 失败: {str(e)}"
                    logger.error(error_msg)
                    stats['failed'] += 1
                    stats['errors'].append(error_msg)

                    # 保存错误报告
                    self.save_error_report(table_name, news_id, error_msg)

            # 提交事务
            self.connection.commit()

            return stats

        except Exception as e:
            logger.error(f"从表 {table_name} 提取新闻时发生错误: {e}")
            # 回滚事务
            self.connection.rollback()

            stats['errors'].append(f"表级错误: {str(e)}")
            return stats

    def extract_all_tables(self):
        """提取所有表的新闻"""
        if not self.connect():
            return False

        try:
            logger.info(f"开始提取2025年未向量化的新闻...")
            logger.info(f"输出目录: {OUTPUT_DIR}")
            logger.info(f"错误报告目录: {ERROR_REPORT_DIR}")

            all_stats = {
                'start_time': datetime.now(),
                'tables': {},
                'total_processed': 0,
                'total_successful': 0,
                'total_failed': 0
            }

            # 处理每个表
            for category_name, table_name in CATEGORY_TABLE_MAP.items():
                logger.info(f"\n处理分类: {category_name} (表: {table_name})")

                stats = self.extract_from_table(table_name, category_name)
                all_stats['tables'][category_name] = stats

                all_stats['total_processed'] += stats['total_processed']
                all_stats['total_successful'] += stats['successful']
                all_stats['total_failed'] += stats['failed']

                logger.info(f"  处理完成: 总数 {stats['total_processed']}, "
                            f"成功 {stats['successful']}, 失败 {stats['failed']}")

                if stats['errors']:
                    logger.warning(f"  错误数: {len(stats['errors'])}")

            # 计算总耗时
            all_stats['end_time'] = datetime.now()
            all_stats['duration'] = all_stats['end_time'] - all_stats['start_time']

            # 显示总统计信息
            logger.info("\n" + "=" * 60)
            logger.info("提取完成!")
            logger.info(f"总处理新闻数: {all_stats['total_processed']}")
            logger.info(f"成功生成文件数: {all_stats['total_successful']}")
            logger.info(f"失败数: {all_stats['total_failed']}")
            logger.info(f"总耗时: {all_stats['duration']}")

            # 显示各表统计
            logger.info("\n各分类详细统计:")
            for category_name, stats in all_stats['tables'].items():
                if stats['total_processed'] > 0:
                    success_rate = (stats['successful'] / stats['total_processed'] * 100) if stats[
                                                                                                 'total_processed'] > 0 else 0
                    logger.info(f"  {category_name}: "
                                f"处理 {stats['total_processed']} 条, "
                                f"成功 {stats['successful']} ({success_rate:.1f}%), "
                                f"失败 {stats['failed']}")

            # 显示输出目录信息
            if os.path.exists(OUTPUT_DIR):
                txt_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.txt')]
                logger.info(f"\n输出目录文件数: {len(txt_files)} 个txt文件")

                if txt_files:
                    # 显示文件大小信息
                    total_size = 0
                    for f in txt_files[:10]:  # 只统计前10个文件的大小
                        filepath = os.path.join(OUTPUT_DIR, f)
                        if os.path.exists(filepath):
                            total_size += os.path.getsize(filepath)

                    logger.info(f"输出目录总大小: {total_size / 1024 / 1024:.2f} MB")

            # 显示错误报告信息
            if os.path.exists(ERROR_REPORT_DIR):
                error_files = [f for f in os.listdir(ERROR_REPORT_DIR) if
                               f.startswith('errors_') and f.endswith('.txt')]
                if error_files:
                    logger.info(f"\n错误报告文件: {len(error_files)} 个")
                    for error_file in error_files[-3:]:  # 显示最新的3个错误文件
                        error_path = os.path.join(ERROR_REPORT_DIR, error_file)
                        if os.path.exists(error_path):
                            with open(error_path, 'r', encoding='utf-8') as f:
                                error_count = len(f.read().split('时间: ')) - 1
                            logger.info(f"  {error_file}: {error_count} 个错误")

            return True

        except Exception as e:
            logger.error(f"提取过程中发生错误: {e}")
            logger.error(f"错误详情:\n{traceback.format_exc()}")
            return False

        finally:
            self.disconnect()


def main():
    """主函数"""
    print("=" * 60)
    print("南京大学新闻 - 文本提取工具")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    print("配置信息:")
    print(f"  数据库: {DB_CONFIG['database']}@{DB_CONFIG['host']}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"  错误报告目录: {ERROR_REPORT_DIR}")
    print(f"  处理范围: 2025年未向量化的新闻")
    print()

    print("执行以下操作:")
    print("1. 查询所有表中2025年且 is_vectorized = FALSE 的新闻")
    print("2. 提取标题、副标题、发布时间、URL和正文内容")
    print("3. 生成txt文件到输出目录")
    print("4. 将成功处理的新闻标记为已向量化")
    print("5. 保存错误报告到指定目录")
    print()

    # 检查输出目录
    if not os.path.exists(OUTPUT_DIR):
        print(f"创建输出目录: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 自动开始，不需要确认
    print("开始提取...")

    extractor = NewsExtractor()
    success = extractor.extract_all_tables()

    if success:
        print("\n" + "=" * 60)
        print("提取任务成功完成!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("提取任务失败，请查看日志文件了解详细信息")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()