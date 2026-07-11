"""健康指标模型"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, DateTime, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class HealthIndicator(Base):
    """健康指标记录"""
    __tablename__ = "health_indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), comment="用户ID"
    )
    category: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="分类: blood_sugar / blood_pressure / blood_fat / liver / kidney / blood_routine / other"
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="指标名称")
    value: Mapped[str] = mapped_column(String(50), nullable=False, comment="检测值")
    unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="单位")
    normal_range: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="正常范围描述")
    status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="状态: normal / abnormal_high / abnormal_low"
    )
    risk_level: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="风险等级: low / medium / high"
    )
    suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="建议")
    source: Mapped[Optional[str]] = mapped_column(
        String(20), default="manual", comment="来源: manual / ocr / ai"
    )
    measured_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="测量时间")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category": self.category,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "normal_range": self.normal_range,
            "status": self.status,
            "risk_level": self.risk_level,
            "suggestion": self.suggestion,
            "source": self.source,
            "measured_at": self.measured_at.isoformat() if self.measured_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
