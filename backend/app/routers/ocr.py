"""OCR 体检报告识别 API"""

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.ocr import OcrRequest, OcrResponse, IndicatorItem
from app.services.ocr_service import ocr_recognize
from app.services.ai_service import extract_indicators_from_text
from app.services.health_service import create_indicator_with_evaluation, get_user_or_default

router = APIRouter(prefix="/api/ocr", tags=["OCR 识别"])


@router.post("/recognize", response_model=OcrResponse)
async def recognize_report(
    req: OcrRequest,
    auto_save: Optional[bool] = Query(True, description="是否自动保存识别的指标"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    db: Session = Depends(get_db),
):
    """
    识别体检报告图片。

    流程：Kimi 视觉大模型 OCR → DeepSeek 提取指标 → 规则引擎评估 → 保存
    """
    # 1. Kimi OCR
    raw_text = await ocr_recognize(req.image_base64)
    if raw_text is None:
        raise HTTPException(
            status_code=503,
            detail="OCR 服务暂不可用，请检查 Kimi API 密钥配置",
        )

    # 2. DeepSeek 提取指标
    indicator_text = await extract_indicators_from_text(raw_text)

    # 3. 解析指标
    indicators: List[IndicatorItem] = []
    detected_info: Optional[dict] = None

    if indicator_text:
        for line in indicator_text.strip().split("\n"):
            line = line.strip()
            if line.startswith("INDICATOR|"):
                parts = line.split("|")
                if len(parts) >= 4:
                    indicators.append(IndicatorItem(
                        name=parts[2].strip(),
                        value=parts[3].strip(),
                        unit=parts[4].strip() if len(parts) > 4 else None,
                    ))

    # 4. 自动保存
    if auto_save and indicators:
        if user_id is None:
            user = get_user_or_default(db)
            user_id = user.id

        for item in indicators:
            # 指标分类推断
            category = _infer_category(item.name)
            create_indicator_with_evaluation(
                db=db,
                user_id=user_id,
                category=category,
                name=item.name,
                value=item.value,
                unit=item.unit,
                source="ocr",
            )

        # 检测年龄/性别信息
        detected_info = _detect_personal_info(raw_text)
        if detected_info and user_id:
            from app.models import User
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                if detected_info.get("age") and not user.age:
                    user.age = detected_info["age"]
                if detected_info.get("gender") and not user.gender:
                    user.gender = detected_info["gender"]
                db.commit()

    return OcrResponse(
        raw_text=raw_text,
        indicators=indicators,
        detected_info=detected_info,
    )


def _infer_category(name: str) -> str:
    """根据指标名称推断分类"""
    from app.services.rule_engine import ALL_RULES
    for category, rules in ALL_RULES.items():
        for rule in rules:
            if rule.name == name or name in rule.description:
                return category
    return "other"


def _detect_personal_info(text: str) -> dict:
    """从文本中检测个人信息"""
    import re
    info = {}

    # 年龄检测
    age_patterns = [
        r"年龄[：:]\s*(\d+)",
        r"年龄\s*(\d+)\s*岁",
        r"(\d+)\s*岁",
    ]
    for pattern in age_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                age = int(match.group(1))
                if 0 < age < 150:
                    info["age"] = age
                    break
            except ValueError:
                pass

    # 性别检测
    if re.search(r"(男|男性|先生)", text):
        info["gender"] = "男"
    elif re.search(r"(女|女性|女士)", text):
        info["gender"] = "女"

    return info
