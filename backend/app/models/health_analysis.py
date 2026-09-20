"""持久化的 AI 健康分析结果。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class HealthAnalysis(Base):
    """一次健康指标综合分析记录。"""

    __tablename__ = "health_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"
    )
    analysis: Mapped[str] = mapped_column(Text, nullable=False, comment="分析结果")
    source: Mapped[str] = mapped_column(String(20), nullable=False, comment="ai / rule_engine")
    indicator_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="分析指标数")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, comment="创建时间"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "analysis": self.analysis,
            "source": self.source,
            "indicator_count": self.indicator_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
