"""应用配置 - 从 .env 加载"""
from pathlib import Path

from pydantic_settings import BaseSettings


# 项目根目录（backend 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# 数据目录：存放各图谱的 working_dir 和元数据
DATA_DIR = PROJECT_ROOT / "data"
GRAPHS_DIR = DATA_DIR / "graphs"  # 每个图谱一个子目录 graph_<id>


class Settings(BaseSettings):
    """从环境变量 / .env 读取配置"""
    # API Keys
    deepseek_api_key: str = ""
    deepseek_api_base: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    siliconcloud_api_key: str = ""
    siliconcloud_embedding_model: str = "BAAI/bge-m3"
    siliconcloud_rerank_model: str = "BAAI/bge-reranker-v2-m3"

    # 管理员
    admin_username: str = "admin"
    admin_password: str = "admin123"
    secret_key: str = "your-secret-key-change-in-production"

    # 数据库
    database_url: str = ""

    # 重启网站：可选，填脚本相对项目根的路径（如 scripts/restart.sh），管理界面“重启网站”会执行该脚本
    restart_script: str = ""

    class Config:
        env_file = PROJECT_ROOT / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


def get_settings() -> Settings:
    return Settings()


def ensure_dirs():
    """确保数据目录存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
