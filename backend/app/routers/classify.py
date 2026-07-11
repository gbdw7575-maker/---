"""医学影像分类 API"""

from io import BytesIO
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from PIL import Image

from app.classifier import SkinClassifier

router = APIRouter(prefix="/api/classify", tags=["影像分类"])

# 全局分类器实例
classifier = SkinClassifier()


class ClassifyResponse(BaseModel):
    success: bool
    predictions: list = Field(default_factory=list)
    error: Optional[str] = None


class SkinClassifyRequest(BaseModel):
    image_base64: str = Field(..., description="图片 Base64 编码")


@router.post("/skin", response_model=ClassifyResponse)
async def classify_skin(
    req: SkinClassifyRequest,
    topk: Optional[int] = Query(3, ge=1, le=7, description="返回前 k 个结果"),
):
    """
    皮肤病变分类。

    上传皮肤照片进行 AI 分类识别。支持 7 类皮肤病变。
    注意：本分类仅供参考，不构成医疗诊断。
    """
    try:
        # 解码 Base64
        import base64
        image_data = base64.b64decode(req.image_base64)
        image = Image.open(BytesIO(image_data)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="图片解码失败，请确认是有效的 Base64 编码")

    result = classifier.predict(image, topk=topk)
    return result


@router.get("/classes")
def list_classes():
    """获取支持的所有分类"""
    from app.classifier.model import CLASS_NAMES, CLASS_SHORT, CLASS_DESCRIPTIONS
    return [
        {"short": s, "name": n, "description": CLASS_DESCRIPTIONS.get(s, "")}
        for s, n in zip(CLASS_SHORT, CLASS_NAMES)
    ]


@router.get("/status")
def model_status():
    """检查模型加载状态"""
    from app.classifier.model import TORCH_AVAILABLE

    loaded = classifier.model is not None
    model_path = classifier.model_path
    exists = __import__("os").path.exists(model_path)
    return {
        "loaded": loaded,
        "model_path": model_path,
        "model_file_exists": exists,
        "torch_available": TORCH_AVAILABLE,
        "device": classifier.device,
    }
