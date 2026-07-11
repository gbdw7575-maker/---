"""用户档案 Pydantic 模型"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: Optional[str] = Field(None, max_length=50, description="姓名")
    age: Optional[int] = Field(None, ge=0, le=150, description="年龄")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    height: Optional[float] = Field(None, ge=0, le=300, description="身高(cm)")
    weight: Optional[float] = Field(None, ge=0, le=500, description="体重(kg)")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    medical_history: Optional[str] = Field(None, description="病史")


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = Field(None, max_length=10)
    height: Optional[float] = Field(None, ge=0, le=300)
    weight: Optional[float] = Field(None, ge=0, le=500)
    phone: Optional[str] = Field(None, max_length=20)
    medical_history: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    bmi: Optional[float] = None
    phone: Optional[str] = None
    medical_history: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}
