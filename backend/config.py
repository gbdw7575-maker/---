"""应用配置"""

from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "智能化健康管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库 — 默认使用 SQLite 方便开发
    DATABASE_URL: str = "sqlite:///./health.db"

    # DeepSeek（AI 分析 + 体检报告 OCR）
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_VISION_MODEL: str = "deepseek-flash"  # 视觉模型，用于体检报告 OCR

    model_config = {
        "env_file": BASE_DIR / ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
