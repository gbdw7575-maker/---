"""健康指标 Pydantic 模型"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class HealthIndicatorCreate(BaseModel):
    user_id: int = Field(..., description="用户ID")
    category: str = Field(..., max_length=30, description="分类")
    name: str = Field(..., max_length=50, description="指标名称")
    value: str = Field(..., max_length=50, description="检测值")
    statistic_type: Optional[str] = Field(None, max_length=20)
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=20, description="单位")
    normal_range: Optional[str] = Field(None, max_length=100, description="正常范围")
    status: Optional[str] = Field(None, max_length=20, description="状态")
    risk_level: Optional[str] = Field(None, max_length=20, description="风险等级")
    suggestion: Optional[str] = Field(None, description="建议")
    source: Optional[str] = Field("manual", max_length=20, description="来源")
    measured_at: Optional[str] = Field(None, description="测量时间(ISO格式)")


class HealthIndicatorUpdate(BaseModel):
    category: Optional[str] = Field(None, max_length=30)
    name: Optional[str] = Field(None, max_length=50)
    value: Optional[str] = Field(None, max_length=50)
    statistic_type: Optional[str] = Field(None, max_length=20)
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=20)
    normal_range: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=20)
    risk_level: Optional[str] = Field(None, max_length=20)
    suggestion: Optional[str] = None
    measured_at: Optional[str] = None


class HealthIndicatorResponse(BaseModel):
    id: int
    user_id: int
    category: str
    name: str
    value: str
    statistic_type: Optional[str] = None
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    unit: Optional[str] = None
    normal_range: Optional[str] = None
    status: Optional[str] = None
    risk_level: Optional[str] = None
    suggestion: Optional[str] = None
    source: Optional[str] = None
    measured_at: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class HealthIndicatorBatchCreate(BaseModel):
    indicators: List[HealthIndicatorCreate]


class HealthIndicatorBatchDelete(BaseModel):
    ids: List[int] = Field(..., min_length=1, max_length=500)
