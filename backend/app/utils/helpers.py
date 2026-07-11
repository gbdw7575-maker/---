"""通用工具函数"""

from datetime import datetime
from typing import Optional


def parse_float(value: Optional[str]) -> Optional[float]:
    """安全解析浮点数"""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def now() -> datetime:
    """获取当前 UTC 时间"""
    return datetime.utcnow()
