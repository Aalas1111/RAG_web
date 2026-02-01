#!/usr/bin/env python3
"""
初始化数据库向量化字段
为所有新闻表添加 is_vectorized 字段，并将所有记录的该字段设置为 FALSE
"""

import pymysql
import logging
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('init_vector.log'),
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


class VectorDBInitializer:
    """数据库向量化字段初始化器"""

    def __init__(self, config=None):
        """初始化数据库连接"""
        self.config = config or DB_CONFIG
        self.connection = None
        self.cursor = None

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

    def add_vectorized_column(self, table_name: str) -> bool:
        """为指定表添加 is_vectorized 字段"""
        try:
            # 检查字段是否已存在
            check_column_query = """
                                 SELECT COUNT(*) as column_exists
                                 FROM information_schema.columns
                                 WHERE table_schema = %s
                                   AND table_name = %s
                                   AND column_name = 'is_vectorized' \
                                 """

            self.cursor.execute(check_column_query, (self.config['database'], table_name))
            result = self.cursor.fetchone()

            if result and result['column_exists'] > 0:
                logger.info(f"表 {table_name} 已存在 is_vectorized 字段")
                return True

            # 添加字段
            add_column_query = f"""
            ALTER TABLE {table_name} 
            ADD COLUMN is_vectorized BOOLEAN DEFAULT FALSE,
            ADD INDEX idx_vectorized (is_vectorized)
            """

            self.cursor.execute(add_column_query)
            self.connection.commit()
            logger.info(f"成功为表 {table_name} 添加 is_vectorized 字段")
            return True

        except pymysql.Error as e:
            logger.error(f"为表 {table_name} 添加字段时发生错误: {e}")
            return False

    def reset_all_vectorized_flags(self, table_name: str) -> bool:
        """重置指定表的所有 is_vectorized 字段为 FALSE"""
        try:
            update_query = f"UPDATE {table_name} SET is_vectorized = FALSE"

            self.cursor.execute(update_query)
            affected_rows = self.cursor.rowcount
            self.connection.commit()

            logger.info(f"重置表 {table_name} 的 {affected_rows} 条记录的 is_vectorized 为 FALSE")
            return True

        except pymysql.Error as e:
            logger.error(f"重置表 {table_name} 的字段时发生错误: {e}")
            return False

    def get_table_stats(self, table_name: str) -> dict:
        """获取表的统计信息"""
        try:
            # 获取总记录数
            count_query = f"SELECT COUNT(*) as total_count FROM {table_name}"
            self.cursor.execute(count_query)
            count_result = self.cursor.fetchone()

            # 获取已向量化的记录数
            vectorized_query = f"SELECT COUNT(*) as vectorized_count FROM {table_name} WHERE is_vectorized = TRUE"
            self.cursor.execute(vectorized_query)
            vectorized_result = self.cursor.fetchone()

            # 获取最新发布时间
            date_query = f"SELECT MAX(publish_date) as latest_date FROM {table_name}"
            self.cursor.execute(date_query)
            date_result = self.cursor.fetchone()

            return {
                'table_name': table_name,
                'total_count': count_result['total_count'] if count_result else 0,
                'vectorized_count': vectorized_result['vectorized_count'] if vectorized_result else 0,
                'latest_date': date_result['latest_date'] if date_result else None
            }

        except pymysql.Error as e:
            logger.error(f"获取表 {table_name} 统计信息失败: {e}")
            return {
                'table_name': table_name,
                'error': str(e)
            }

    def initialize_all_tables(self):
        """初始化所有表"""
        if not self.connect():
            return False

        try:
            logger.info("开始初始化所有表的向量化字段...")

            # 为每个表添加字段
            for category, table_name in CATEGORY_TABLE_MAP.items():
                logger.info(f"处理表: {table_name} ({category})")

                # 添加字段
                if not self.add_vectorized_column(table_name):
                    logger.warning(f"添加字段到表 {table_name} 失败，跳过")
                    continue

                # 重置所有标志为 FALSE
                if not self.reset_all_vectorized_flags(table_name):
                    logger.warning(f"重置表 {table_name} 的标志失败")

            # 显示所有表的统计信息
            logger.info("\n所有表统计信息:")
            for category, table_name in CATEGORY_TABLE_MAP.items():
                stats = self.get_table_stats(table_name)

                if 'error' in stats:
                    logger.info(f"  {category} ({table_name}): 错误 - {stats['error']}")
                else:
                    vectorized_percent = (stats['vectorized_count'] / stats['total_count'] * 100) if stats[
                                                                                                         'total_count'] > 0 else 0
                    logger.info(f"  {category} ({table_name}): {stats['total_count']} 条记录, "
                                f"已向量化: {stats['vectorized_count']} ({vectorized_percent:.1f}%), "
                                f"最新日期: {stats['latest_date']}")

            logger.info("\n数据库向量化字段初始化完成!")
            return True

        except Exception as e:
            logger.error(f"初始化过程中发生错误: {e}")
            import traceback
            logger.error(f"错误详情:\n{traceback.format_exc()}")
            return False

        finally:
            self.disconnect()


def main():
    """主函数"""
    print("=" * 60)
    print("南京大学新闻数据库 - 向量化字段初始化工具")
    print("=" * 60)

    initializer = VectorDBInitializer()

    print("执行以下操作:")
    print("1. 为所有新闻表添加 is_vectorized 字段")
    print("2. 将所有现有记录的 is_vectorized 设置为 FALSE")
    print("3. 显示所有表的统计信息")
    print()

    # 自动开始，不需要确认
    print("开始初始化...")

    success = initializer.initialize_all_tables()

    if success:
        print("\n" + "=" * 60)
        print("初始化成功完成!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("初始化失败，请查看日志文件了解详细信息")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()