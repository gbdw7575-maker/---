"""OCR 识别 Pydantic 模型"""

from typing import Optional, List

from pydantic import BaseModel, Field


class OcrRequest(BaseModel):
    image_base64: str = Field(..., description="图片 Base64 编码")


class IndicatorItem(BaseModel):
    """从 OCR 结果中提取的指标项"""
    name: str = Field(..., description="指标名称")
    value: str = Field(..., description="检测值")
    unit: Optional[str] = Field(None, description="单位")
    category: Optional[str] = Field(None, description="分类")


class OcrResponse(BaseModel):
    raw_text: str = Field(..., description="OCR 原始识别文本")
    indicators: List[IndicatorItem] = Field(default_factory=list, description="提取的指标列表")
    detected_info: Optional[dict] = Field(None, description="检测到的个人信息(年龄/性别等)")
