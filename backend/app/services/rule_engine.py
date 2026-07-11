"""
医学指标规则引擎

内置常见健康指标的正常范围、风险判定逻辑。
当 AI 不可用时作为降级方案，保证核心评估功能可用。
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple


@dataclass
class IndicatorRule:
    """指标规则定义"""
    name: str                     # 指标名称
    category: str                 # 分类
    unit: str                     # 单位
    normal_min: Optional[float]   # 正常下限
    normal_max: Optional[float]   # 正常上限
    low_risk_min: Optional[float] = None   # 低风险下限
    high_risk_min: Optional[float] = None  # 高风险下限(高于此值)
    high_risk_max: Optional[float] = None  # 高风险上限(低于此值)
    description: str = ""          # 中文描述


# ── 血糖 ──
BLOOD_SUGAR_RULES = [
    IndicatorRule("空腹血糖", "blood_sugar", "mmol/L", 3.9, 6.1, low_risk_min=6.1, high_risk_min=7.0, description="空腹血糖"),
    IndicatorRule("餐后2小时血糖", "blood_sugar", "mmol/L", 3.9, 7.8, low_risk_min=7.8, high_risk_min=11.1, description="餐后2小时血糖"),
    IndicatorRule("糖化血红蛋白", "blood_sugar", "%", 4.0, 6.0, low_risk_min=6.0, high_risk_min=6.5, description="糖化血红蛋白"),
    IndicatorRule("随机血糖", "blood_sugar", "mmol/L", 3.9, 11.1, description="随机血糖"),
]

# ── 血压 ──
BLOOD_PRESSURE_RULES = [
    IndicatorRule("收缩压", "blood_pressure", "mmHg", 90, 120, low_risk_min=120, high_risk_min=140, description="收缩压(高压)"),
    IndicatorRule("舒张压", "blood_pressure", "mmHg", 60, 80, low_risk_min=80, high_risk_min=90, description="舒张压(低压)"),
]

# ── 血脂 ──
BLOOD_FAT_RULES = [
    IndicatorRule("总胆固醇", "blood_fat", "mmol/L", 2.8, 5.2, low_risk_min=5.2, high_risk_min=6.2, description="总胆固醇"),
    IndicatorRule("甘油三酯", "blood_fat", "mmol/L", 0.56, 1.7, low_risk_min=1.7, high_risk_min=2.3, description="甘油三酯"),
    IndicatorRule("高密度脂蛋白", "blood_fat", "mmol/L", 0.9, None, high_risk_max=0.9, description="高密度脂蛋白(HDL)"),
    IndicatorRule("低密度脂蛋白", "blood_fat", "mmol/L", None, 3.4, low_risk_min=3.4, high_risk_min=4.1, description="低密度脂蛋白(LDL)"),
]

# ── 肝功能 ──
LIVER_RULES = [
    IndicatorRule("谷丙转氨酶", "liver", "U/L", 0, 40, low_risk_min=40, high_risk_min=80, description="谷丙转氨酶(ALT)"),
    IndicatorRule("谷草转氨酶", "liver", "U/L", 0, 40, low_risk_min=40, high_risk_min=80, description="谷草转氨酶(AST)"),
    IndicatorRule("总胆红素", "liver", "μmol/L", 3.4, 17.1, low_risk_min=17.1, high_risk_min=34.2, description="总胆红素"),
]

# ── 肾功能 ──
KIDNEY_RULES = [
    IndicatorRule("肌酐", "kidney", "μmol/L", 44, 133, low_risk_min=133, high_risk_min=177, description="肌酐(Cr)"),
    IndicatorRule("尿素氮", "kidney", "mmol/L", 2.9, 8.2, low_risk_min=8.2, high_risk_min=10.5, description="尿素氮(BUN)"),
    IndicatorRule("尿酸", "kidney", "μmol/L", 150, 420, low_risk_min=420, high_risk_min=480, description="尿酸(UA)"),
]

# ── 血常规 ──
BLOOD_ROUTINE_RULES = [
    IndicatorRule("白细胞", "blood_routine", "×10⁹/L", 3.5, 9.5, low_risk_min=9.5, high_risk_min=15.0, description="白细胞计数(WBC)"),
    IndicatorRule("红细胞", "blood_routine", "×10¹²/L", 3.8, 5.1, low_risk_min=5.1, high_risk_min=6.0, description="红细胞计数(RBC)"),
    IndicatorRule("血红蛋白", "blood_routine", "g/L", 115, 150, description="血红蛋白(HGB)"),
    IndicatorRule("血小板", "blood_routine", "×10⁹/L", 125, 350, low_risk_min=350, high_risk_min=500, description="血小板计数(PLT)"),
]

# 所有规则索引
ALL_RULES: Dict[str, List[IndicatorRule]] = {
    "blood_sugar": BLOOD_SUGAR_RULES,
    "blood_pressure": BLOOD_PRESSURE_RULES,
    "blood_fat": BLOOD_FAT_RULES,
    "liver": LIVER_RULES,
    "kidney": KIDNEY_RULES,
    "blood_routine": BLOOD_ROUTINE_RULES,
}

# 分类中文名
CATEGORY_NAMES = {
    "blood_sugar": "血糖",
    "blood_pressure": "血压",
    "blood_fat": "血脂",
    "liver": "肝功能",
    "kidney": "肾功能",
    "blood_routine": "血常规",
}


def _parse_value(value_str: str) -> Optional[float]:
    """将字符串值解析为浮点数"""
    try:
        return float(value_str.replace("↑", "").replace("↓", "").replace(" ", ""))
    except (ValueError, AttributeError):
        return None


def evaluate_indicator(name: str, value_str: str, unit: Optional[str] = None) -> dict:
    """
    评估单个健康指标。

    返回:
    {
        "status": "normal" | "abnormal_high" | "abnormal_low",
        "risk_level": "low" | "medium" | "high" | None,
        "suggestion": str | None
    }
    """
    result = {
        "status": None,
        "risk_level": None,
        "suggestion": None,
    }

    # 在所有分类中查找匹配规则
    rule: Optional[IndicatorRule] = None
    for rules in ALL_RULES.values():
        for r in rules:
            if r.name == name or name in r.description:
                rule = r
                break
        if rule:
            break

    if rule is None:
        return result

    value = _parse_value(value_str)
    if value is None:
        return result

    # 判断状态
    is_high = False
    is_low = False

    if rule.normal_max is not None and value > rule.normal_max:
        is_high = True
    if rule.normal_min is not None and value < rule.normal_min:
        is_low = True

    if is_high:
        result["status"] = "abnormal_high"
    elif is_low:
        result["status"] = "abnormal_low"
    else:
        result["status"] = "normal"
        result["risk_level"] = "low"
        return result

    # 风险等级
    if is_high:
        if rule.high_risk_min is not None and value >= rule.high_risk_min:
            result["risk_level"] = "high"
        elif rule.low_risk_min is not None and value >= rule.low_risk_min:
            result["risk_level"] = "medium"
        else:
            result["risk_level"] = "low"
    elif is_low:
        if rule.high_risk_max is not None and value <= rule.high_risk_max:
            result["risk_level"] = "high"
        else:
            result["risk_level"] = "medium"

    # 建议
    result["suggestion"] = _get_suggestion(rule, result["status"], result["risk_level"])
    return result


def _get_suggestion(rule: IndicatorRule, status: str, risk_level: Optional[str]) -> str:
    """根据规则生成建议"""
    suggestions = {
        "blood_sugar": {
            "abnormal_high": {
                "high": "血糖显著偏高，建议尽快就医内分泌科，完善口服葡萄糖耐量试验，排查糖尿病。",
                "medium": "血糖偏高，建议控制碳水化合物摄入，增加运动频率，1-2周后复查。",
                "low": "血糖轻度偏高，注意饮食控制，减少甜食，定期监测。",
            },
            "abnormal_low": "血糖偏低，注意按时进食，随身携带糖果以防低血糖发作。",
        },
        "blood_pressure": {
            "abnormal_high": {
                "high": "血压显著偏高，建议立即就医心内科，排查高血压并规范治疗。",
                "medium": "血压偏高，建议低盐饮食、规律作息、每日监测血压。",
                "low": "血压轻度偏高，注意减少钠盐摄入，保持规律运动。",
            },
            "abnormal_low": "血压偏低，注意多饮水、增加盐分摄入、避免长时间站立。如有头晕请及时就医。",
        },
        "blood_fat": {
            "abnormal_high": {
                "high": "血脂显著偏高，建议就医检查，可能需要药物干预。注意低脂饮食。",
                "medium": "血脂偏高，建议减少高脂食物摄入，增加有氧运动。",
                "low": "血脂轻度偏高，注意饮食清淡，控制体重。",
            },
            "abnormal_low": {
                "high": "高密度脂蛋白偏低是心血管风险因素，建议增加有氧运动，戒烟。",
                "medium": "高密度脂蛋白偏低，建议规律运动，控制体重。",
            },
        },
        "liver": {
            "abnormal_high": {
                "high": "肝功能指标显著异常，建议立即就医消化内科，完善肝功能全套检查。",
                "medium": "肝功能指标异常，建议避免饮酒、注意休息、一周后复查。",
                "low": "肝功能指标轻度异常，注意规律作息、避免劳累。",
            },
        },
        "kidney": {
            "abnormal_high": {
                "high": "肾功能指标显著异常，建议立即就医肾内科，完善肾功能检查。",
                "medium": "肾功能指标异常，建议低蛋白饮食、多饮水、定期复查。",
                "low": "肾功能指标轻度异常，注意多饮水、低盐饮食。",
            },
            "abnormal_low": {
                "medium": "肌酐偏低，可能与营养不良有关，注意蛋白质摄入。",
            },
        },
        "blood_routine": {
            "abnormal_high": {
                "high": "血常规指标显著异常，建议立即就医血液科进一步检查。",
                "medium": "血常规指标异常，建议复查确认，必要时就医。",
                "low": "血常规指标轻度异常，建议保持良好生活习惯，定期复查。",
            },
            "abnormal_low": {
                "high": "血常规指标显著偏低，建议立即就医血液科排查原因。",
                "medium": "血常规指标偏低，注意营养补充，建议复查。",
                "low": "血常规指标轻度偏低，注意均衡饮食。",
            },
        },
    }

    cat = rule.category
    status_suggestions = suggestions.get(cat, {}).get(status)
    if isinstance(status_suggestions, dict) and risk_level:
        return status_suggestions.get(risk_level, "指标异常，建议定期复查。")
    elif isinstance(status_suggestions, str):
        return status_suggestions

    return "指标异常，建议咨询专业医生。"


def batch_evaluate(indicators: List[dict]) -> List[dict]:
    """批量评估指标"""
    results = []
    for ind in indicators:
        eval_result = evaluate_indicator(ind.get("name", ""), ind.get("value", ""), ind.get("unit"))
        results.append({**ind, **eval_result})
    return results
