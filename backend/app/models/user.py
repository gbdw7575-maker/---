"""用户档案模型"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, Date, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="姓名")
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="年龄")
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, comment="性别")
    height: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="身高(cm)")
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="体重(kg)")
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="手机号")
    medical_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="病史")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    @property
    def bmi(self) -> Optional[float]:
        """自动计算 BMI"""
        if self.height and self.weight and self.height > 0:
            h = self.height / 100
            return round(self.weight / (h * h), 1)
        return None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "height": self.height,
            "weight": self.weight,
            "bmi": self.bmi,
            "phone": self.phone,
            "medical_history": self.medical_history,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
