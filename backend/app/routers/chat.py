"""AI 健康咨询 API"""

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import ChatSession, ChatMessage, User
from app.schemas.chat import (
    ChatSessionCreate, ChatSessionResponse,
    ChatMessageCreate, ChatMessageResponse,
    ChatRequest, ChatResponse,
)
from app.services.ai_service import chat_with_ai

router = APIRouter(prefix="/api/chat", tags=["AI 健康咨询"])


@router.get("/sessions", response_model=List[ChatSessionResponse])
def list_sessions(
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """获取会话列表（按更新时间倒序）"""
    if user_id is None:
        user = db.query(User).first()
        if not user:
            return []
        user_id = user.id

    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(desc(ChatSession.updated_at))
        .all()
    )
    return [s.to_dict() for s in sessions]


@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
def create_session(data: ChatSessionCreate, db: Session = Depends(get_db)):
    """创建新会话"""
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    session = ChatSession(
        user_id=data.user_id,
        title=data.title or "新会话",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session.to_dict()


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)):
    """获取会话详情"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return session.to_dict()


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    """删除会话及其所有消息"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    db.delete(session)  # 级联删除消息
    db.commit()
    return {"message": "删除成功"}


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def list_messages(session_id: int, db: Session = Depends(get_db)):
    """获取会话消息历史"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return [m.to_dict() for m in messages]


@router.post("/send", response_model=ChatResponse)
async def send_message(req: ChatRequest, db: Session = Depends(get_db)):
    """发送消息并获取 AI 回复"""
    session = db.query(ChatSession).filter(ChatSession.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 保存用户消息
    user_msg = ChatMessage(
        session_id=req.session_id,
        role="user",
        content=req.message,
        content_type="image" if req.image_base64 else "text",
        extra_data={"image_base64": req.image_base64} if req.image_base64 else None,
    )
    db.add(user_msg)
    db.commit()

    # 获取历史消息（最近10条作为上下文）
    history_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == req.session_id)
        .order_by(ChatMessage.created_at)
        .limit(20)
        .all()
    )

    history = [
        {"role": m.role, "content": m.content}
        for m in history_messages
    ]

    # 调用 AI
    reply_text = await chat_with_ai(
        message=req.message,
        history=history[:-1],  # 排除刚发的用户消息
        image_base64=req.image_base64,
    )

    if reply_text is None:
        # AI 不可用时降级回复
        reply_text = "😊 您好！我是康康，您的健康管理助手。\n\n目前 AI 服务暂不可用（API 密钥未配置），请先在 `.env` 文件中配置 DeepSeek API Key 后重试。\n\n您也可以先手动添加健康指标，系统会基于内置规则库为您提供基础评估。"

    # 保存 AI 回复
    assistant_msg = ChatMessage(
        session_id=req.session_id,
        role="assistant",
        content=reply_text,
    )
    db.add(assistant_msg)

    # 更新会话标题（第一条回复时自动生成）
    if not session.title or session.title == "新会话":
        session.title = req.message[:50] + ("..." if len(req.message) > 50 else "")

    db.commit()

    return ChatResponse(session_id=req.session_id, reply=reply_text)
