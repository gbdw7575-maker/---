"""AI 咨询 Pydantic 模型"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    user_id: int = Field(..., description="用户ID")
    title: Optional[str] = Field(None, max_length=100, description="会话标题")


class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    session_id: int = Field(..., description="会话ID")
    role: str = Field(..., max_length=10, description="角色: user/assistant")
    content: str = Field(..., description="消息内容")
    content_type: Optional[str] = Field("text", max_length=20)
    extra_data: Optional[Dict[str, Any]] = None


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    content_type: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    """用户发送聊天请求"""
    session_id: int = Field(..., description="会话ID")
    message: str = Field(..., description="用户消息")
    image_base64: Optional[str] = Field(None, description="附带图片(Base64)")


class ChatResponse(BaseModel):
    """AI 回复"""
    session_id: int
    reply: str
