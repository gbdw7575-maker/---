"""应用配置"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "智能化健康管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库 — 默认使用 SQLite 方便开发
    DATABASE_URL: str = "sqlite:///./health.db"

    # Kimi 视觉大模型 (OCR)
    KIMI_API_KEY: str = ""
    KIMI_BASE_URL: str = "https://api.moonshot.cn/v1"
    KIMI_MODEL: str = "moonshot-v1-32k-vision-preview"

    # DeepSeek (AI 分析)
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent
