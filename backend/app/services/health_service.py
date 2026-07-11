"""
健康服务 — 业务逻辑层

组合规则引擎、AI 服务，提供完整的健康分析功能。
"""

from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from app.models import User, HealthIndicator
from app.services.rule_engine import evaluate_indicator, batch_evaluate, CATEGORY_NAMES
from app.services.ai_service import analyze_health_indicators


def get_user_or_default(db: Session) -> User:
    """获取第一个用户（演示模式），如果没有则创建默认用户"""
    user = db.query(User).first()
    if user is None:
        user = User(name="默认用户")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def create_indicator_with_evaluation(
    db: Session,
    user_id: int,
    category: str,
    name: str,
    value: str,
    unit: Optional[str] = None,
    source: str = "manual",
    measured_at: Optional[str] = None,
) -> HealthIndicator:
    """创建指标并自动评估"""
    # 规则引擎评估
    eval_result = evaluate_indicator(name, value, unit)

    indicator = HealthIndicator(
        user_id=user_id,
        category=category,
        name=name,
        value=value,
        unit=unit,
        normal_range=_get_normal_range(name),
        status=eval_result.get("status"),
        risk_level=eval_result.get("risk_level"),
        suggestion=eval_result.get("suggestion"),
        source=source,
        measured_at=measured_at,
    )
    db.add(indicator)
    db.commit()
    db.refresh(indicator)
    return indicator


def _get_normal_range(name: str) -> Optional[str]:
    """查询指标的正常范围描述"""
    from app.services.rule_engine import ALL_RULES
    for rules in ALL_RULES.values():
        for rule in rules:
            if rule.name == name:
                if rule.normal_min is not None and rule.normal_max is not None:
                    return f"{rule.normal_min} - {rule.normal_max} {rule.unit}"
                elif rule.normal_min is not None:
                    return f"> {rule.normal_min} {rule.unit}"
                elif rule.normal_max is not None:
                    return f"< {rule.normal_max} {rule.unit}"
    return None


def get_risk_summary(db: Session, user_id: int) -> Dict[str, Any]:
    """获取用户健康风险评估摘要"""
    indicators = db.query(HealthIndicator).filter(
        HealthIndicator.user_id == user_id
    ).all()

    # 按分类汇总
    by_category: Dict[str, list] = {}
    for ind in indicators:
        by_category.setdefault(ind.category, []).append(ind)

    summary = {
        "total_count": len(indicators),
        "normal_count": sum(1 for i in indicators if i.status == "normal"),
        "abnormal_count": sum(1 for i in indicators if i.status and "abnormal" in i.status),
        "high_risk_count": sum(1 for i in indicators if i.risk_level == "high"),
        "categories": {},
        "overall_risk": "low",
    }

    for cat, items in by_category.items():
        cat_high = sum(1 for i in items if i.risk_level == "high")
        cat_medium = sum(1 for i in items if i.risk_level == "medium")
        summary["categories"][cat] = {
            "name": CATEGORY_NAMES.get(cat, cat),
            "total": len(items),
            "high": cat_high,
            "medium": cat_medium,
            "normal": sum(1 for i in items if i.status == "normal"),
        }

    # 整体风险等级
    if summary["high_risk_count"] > 0:
        summary["overall_risk"] = "high"
    elif sum(1 for i in indicators if i.risk_level == "medium") > 0:
        summary["overall_risk"] = "medium"

    return summary


def generate_health_suggestions(db: Session, user_id: int) -> Dict[str, list]:
    """生成四维度健康建议"""
    indicators = db.query(HealthIndicator).filter(
        HealthIndicator.user_id == user_id,
        HealthIndicator.status != "normal",
    ).all()

    abnormal_names = [ind.name for ind in indicators]
    user = db.query(User).filter(User.id == user_id).first()

    suggestions = {
        "diet": [],
        "exercise": [],
        "lifestyle": [],
        "medical": [],
    }

    if not abnormal_names:
        suggestions["diet"] = ["继续保持均衡饮食，多吃蔬菜水果，适量摄入优质蛋白。"]
        suggestions["exercise"] = ["保持规律运动习惯，建议每周运动3-5次。"]
        suggestions["lifestyle"] = ["保持良好的作息习惯，保证充足睡眠。"]
        suggestions["medical"] = ["建议每年进行一次常规体检。"]
        return suggestions

    # 根据异常指标生成建议
    sugar_related = any(n in abnormal_names for n in ["空腹血糖", "餐后2小时血糖", "糖化血红蛋白"])
    pressure_related = any(n in abnormal_names for n in ["收缩压", "舒张压"])
    fat_related = any(n in abnormal_names for n in ["总胆固醇", "甘油三酯", "低密度脂蛋白"])
    liver_related = any(n in abnormal_names for n in ["谷丙转氨酶", "谷草转氨酶", "总胆红素"])
    kidney_related = any(n in abnormal_names for n in ["肌酐", "尿素氮", "尿酸"])
    uric_acid = "尿酸" in abnormal_names

    if sugar_related:
        suggestions["diet"].append("血糖异常：控制碳水化合物摄入，减少精制糖和含糖饮料，选择低GI食物。")
        suggestions["exercise"].append("血糖异常：建议餐后30分钟散步，每周有氧运动累计150分钟以上。")
        suggestions["medical"].append("血糖异常：建议就诊内分泌科，完善口服葡萄糖耐量试验。")

    if pressure_related:
        suggestions["diet"].append("血压偏高：严格低盐饮食（每日盐<5g），增加钾摄入（香蕉、土豆）。")
        suggestions["exercise"].append("血压偏高：规律有氧运动（快走、游泳），避免剧烈运动。")
        suggestions["lifestyle"].append("血压偏高：保持情绪稳定、规律作息，建议每日早晚各测一次血压。")
        suggestions["medical"].append("血压偏高：建议就诊心内科，排除继发性高血压。")

    if fat_related:
        suggestions["diet"].append("血脂异常：低脂饮食，减少动物内脏、油炸食品，增加膳食纤维。")
        suggestions["exercise"].append("血脂异常：建议中高强度有氧运动（跑步、游泳），每周累计>150分钟。")
        suggestions["medical"].append("血脂异常：建议复查血脂全套，必要时药物干预。")

    if liver_related:
        suggestions["diet"].append("肝功能异常：戒酒，避免油腻食物和加工食品。")
        suggestions["lifestyle"].append("肝功能异常：避免熬夜，保证充足休息，避免滥用药物。")
        suggestions["medical"].append("肝功能异常：建议就诊消化内科，完善肝功能全套及腹部B超。")

    if kidney_related:
        suggestions["diet"].append("肾功能相关：低蛋白饮食，控制盐分摄入。")
        suggestions["medical"].append(f"肾功能指标异常：建议就诊肾内科进一步检查。")
        if uric_acid:
            suggestions["diet"].append("尿酸偏高：低嘌呤饮食，避免动物内脏、海鲜、啤酒，多饮水。")

    if not any([suggestions[k] for k in suggestions]):
        suggestions["medical"].append(f"指标异常：{', '.join(abnormal_names)}，建议就医复查。")

    return suggestions
