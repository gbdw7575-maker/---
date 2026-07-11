"""Common skin-condition image screening API."""

import base64
import binascii
from io import BytesIO
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

from app.classifier.model import (
    CLASS_DESCRIPTIONS,
    CLASS_NAMES,
    CLASS_RISK,
    CLASS_SHORT,
    MODEL_LICENSE,
    MODEL_NAME,
    MODEL_SOURCE,
    MODEL_VERSION,
    ONNX_AVAILABLE,
    get_classifier,
)

router = APIRouter(prefix="/api/classify", tags=["影像分类"])
classifier = get_classifier()
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000


class SkinClassifyRequest(BaseModel):
    image_base64: str = Field(..., min_length=16, description="图片 Base64 编码")


class ClassifyResponse(BaseModel):
    success: bool
    predictions: list = Field(default_factory=list)
    uncertain: bool = True
    notice: Optional[str] = None
    error: Optional[str] = None


@router.post("/skin", response_model=ClassifyResponse)
async def classify_skin(
    request: SkinClassifyRequest,
    topk: int = Query(3, ge=1, le=5, description="返回前 k 个相似类别"),
):
    """Screen a visible skin condition from a user-provided photo."""
    try:
        encoded = request.image_base64.split(",", 1)[-1]
        image_data = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(status_code=400, detail="图片编码无效") from exc

    if len(image_data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="图片不能超过 8 MB")

    try:
        image = Image.open(BytesIO(image_data))
        width, height = image.size
        if width * height > MAX_IMAGE_PIXELS:
            raise HTTPException(status_code=413, detail="图片像素尺寸过大")
        image.load()
        image = image.convert("RGB")
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="无法读取图片文件") from exc

    return classifier.predict(image, topk=topk)


@router.get("/classes")
def list_classes():
    return [
        {
            "short": short,
            "name": name,
            "description": CLASS_DESCRIPTIONS[short],
            "risk_level": CLASS_RISK[short],
        }
        for short, name in zip(CLASS_SHORT, CLASS_NAMES)
    ]


@router.get("/status")
def model_status():
    model_path = Path(classifier.model_path)
    return {
        "loaded": classifier.model is not None,
        "model_file_exists": model_path.is_file(),
        "runtime_available": ONNX_AVAILABLE,
        "runtime": "ONNX Runtime",
        "device": classifier.device,
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "model_source": MODEL_SOURCE,
        "model_license": MODEL_LICENSE,
        "model_size_mb": round(model_path.stat().st_size / 1_000_000, 1)
        if model_path.is_file()
        else None,
        "intended_use": "健康教育与初步筛查提示，不用于医疗诊断",
    }
