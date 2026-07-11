"""会话与聊天消息模型"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Text, DateTime, func, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ChatSession(Base):
    """AI 健康咨询会话"""
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), comment="用户ID"
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="会话标题"
    )
    context: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, default=list, comment="历史消息上下文(摘要)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ChatMessage(Base):
    """聊天消息"""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), comment="会话ID"
    )
    role: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="角色: user / assistant"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")
    content_type: Mapped[Optional[str]] = mapped_column(
        String(20), default="text", comment="内容类型: text / image / mixed"
    )
    extra_data: Mapped[Optional[dict]] = mapped_column(
        "extra_data", JSON, nullable=True, comment="额外元数据(如图片URL等)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "content_type": self.content_type,
            "extra_data": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
