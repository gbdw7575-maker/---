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

IMPORTANT_INDICATOR_ALIASES = {
    # 血糖
    "葡萄糖": "空腹血糖",
    "GLU": "空腹血糖",
    "餐后2h血糖": "餐后2小时血糖",
    "餐后两小时血糖": "餐后2小时血糖",
    "HbA1c": "糖化血红蛋白",
    # 肝功能
    "ALT": "谷丙转氨酶",
    "AST": "谷草转氨酶",
    "TBIL": "总胆红素",
    "TB": "总胆红素",
    "DBIL": "直接胆红素",
    "ALP": "碱性磷酸酶",
    "AKP": "碱性磷酸酶",
    "TP": "总蛋白",
    "ALB": "白蛋白",
    "TBA": "总胆汁酸",
    # 血脂
    "总胆固醇(TC)": "总胆固醇",
    "TC": "总胆固醇",
    "CHOL": "总胆固醇",
    "甘油三酯(TG)": "甘油三酯",
    "TG": "甘油三酯",
    "高密度脂蛋白胆固醇": "高密度脂蛋白",
    "HDLC": "高密度脂蛋白",
    "HDL": "高密度脂蛋白",
    "低密度脂蛋白胆固醇": "低密度脂蛋白",
    "LDLC": "低密度脂蛋白",
    "LDL": "低密度脂蛋白",
    "ApoA1": "载脂蛋白A1",
    "ApoB": "载脂蛋白B",
    "Lp(a)": "脂蛋白a",
    # 肾功能
    "Cr": "肌酐",
    "CRE": "肌酐",
    "BUN": "尿素氮",
    "UA": "尿酸",
    # 血常规
    "WBC": "白细胞",
    "RBC": "红细胞",
    "HGB": "血红蛋白",
    "Hb": "血红蛋白",
    "PLT": "血小板",
    # 甲状腺
    "TSH": "促甲状腺激素",
    "FT3": "游离三碘甲状腺原氨酸",
    "FT4": "游离甲状腺素",
    "TT3": "总三碘甲状腺原氨酸",
    "TT4": "总甲状腺素",
    # 电解质
    "K": "钾",
    "Na": "钠",
    "Cl": "氯",
    "Ca": "钙",
    "P": "磷",
    "Mg": "镁",
    # 心血管/心肌酶
    "CK": "肌酸激酶",
    "CK-MB": "肌酸激酶同工酶",
    "LDH": "乳酸脱氢酶",
    "hs-CRP": "超敏C反应蛋白",
    # 肿瘤标志物
    "AFP": "甲胎蛋白",
    "CEA": "癌胚抗原",
    "CA125": "糖类抗原125",
    "CA19-9": "糖类抗原19-9",
}


@router.post("/recognize", response_model=OcrResponse)
async def recognize_report(
    req: OcrRequest,
    auto_save: Optional[bool] = Query(True, description="是否自动保存识别的指标"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    db: Session = Depends(get_db),
):
    """
    识别体检报告图片。

    流程：DeepSeek 视觉模型 OCR → DeepSeek 提取指标 → 规则引擎评估 → 保存
    """
    # 1. DeepSeek OCR
    raw_text = await ocr_recognize(req.image_base64)
    if raw_text is None:
        raise HTTPException(
            status_code=503,
            detail="OCR 服务暂不可用，请检查 DeepSeek API 密钥配置",
        )

    # 2. DeepSeek 提取指标
    indicator_text = await extract_indicators_from_text(raw_text)

    # 3. 解析指标
    indicators: List[IndicatorItem] = []
    detected_info: Optional[dict] = None

    if indicator_text:
        indicators = _parse_indicators(indicator_text)

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
                statistic_type=item.statistic_type,
                reference_min=item.reference_min,
                reference_max=item.reference_max,
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


def _parse_indicators(text: str) -> List[IndicatorItem]:
    """Parse detailed indicator lines while remaining compatible with old output."""
    indicators = []
    for raw_line in text.strip().splitlines():
        line = raw_line.strip().strip("`")
        if not line.startswith("INDICATOR|"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 4 or not parts[1]:
            continue
        if len(parts) >= 7:
            statistic_type, value, unit = parts[2], parts[3], parts[4]
            reference_min = _optional_float(parts[5])
            reference_max = _optional_float(parts[6])
        else:
            statistic_type, value, unit = "single", parts[2], parts[3]
            reference_min = reference_max = None
        if statistic_type not in {"single", "min", "max", "average"} or not value:
            continue
        name = IMPORTANT_INDICATOR_ALIASES.get(parts[1], parts[1])
        category = _infer_category(name)
        if category == "other":
            continue
        indicators.append(
            IndicatorItem(
                name=name,
                value=value,
                unit=unit or None,
                category=category,
                statistic_type=statistic_type,
                reference_min=reference_min,
                reference_max=reference_max,
            )
        )
    return indicators


def _optional_float(value: str) -> Optional[float]:
    if not value:
        return None
    try:
        return float(value.replace("≤", "").replace("≥", "").strip())
    except ValueError:
        return None


def _infer_category(name: str) -> str:
    """根据指标名称推断分类"""
    from app.services.rule_engine import ALL_RULES
    # 先精确匹配名称，避免子串误匹配（如"血红蛋白"误中"糖化血红蛋白"）
    for category, rules in ALL_RULES.items():
        for rule in rules:
            if rule.name == name:
                return category
    # 再回退到描述子串匹配
    for category, rules in ALL_RULES.items():
        for rule in rules:
            if name in rule.description:
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
