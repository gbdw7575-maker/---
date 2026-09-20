"""健康数据管理 API"""

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import HealthAnalysis, HealthIndicator, User
from app.schemas.health_indicator import (
    HealthIndicatorCreate, HealthIndicatorUpdate,
    HealthIndicatorResponse, HealthIndicatorBatchCreate, HealthIndicatorBatchDelete,
)
from app.services.health_service import (
    create_indicator_with_evaluation,
    get_risk_summary,
    generate_health_suggestions,
    get_user_or_default,
)
from app.services.rule_engine import ALL_RULES, CATEGORY_NAMES

router = APIRouter(prefix="/api/health", tags=["健康数据"])


@router.get("/indicators", response_model=List[HealthIndicatorResponse])
def list_indicators(
    user_id: Optional[int] = Query(None, description="用户ID"),
    category: Optional[str] = Query(None, description="分类筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: Session = Depends(get_db),
):
    """获取健康指标列表"""
    if user_id is None:
        user = get_user_or_default(db)
        user_id = user.id

    query = db.query(HealthIndicator).filter(HealthIndicator.user_id == user_id)

    if category:
        query = query.filter(HealthIndicator.category == category)
    if status:
        query = query.filter(HealthIndicator.status == status)

    indicators = query.order_by(
        HealthIndicator.measured_at.is_(None),
        HealthIndicator.measured_at.desc(),
        HealthIndicator.created_at.desc(),
    ).all()
    return [i.to_dict() for i in indicators]


@router.post("/indicators", response_model=HealthIndicatorResponse, status_code=201)
def create_indicator(data: HealthIndicatorCreate, db: Session = Depends(get_db)):
    """添加健康指标（自动评估）"""
    # 检查用户存在
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    indicator = create_indicator_with_evaluation(
        db=db,
        user_id=data.user_id,
        category=data.category,
        name=data.name,
        value=data.value,
        unit=data.unit,
        statistic_type=data.statistic_type,
        reference_min=data.reference_min,
        reference_max=data.reference_max,
        source=data.source or "manual",
        measured_at=data.measured_at,
    )
    return indicator.to_dict()


@router.post("/indicators/batch", response_model=List[HealthIndicatorResponse])
def batch_create_indicators(data: HealthIndicatorBatchCreate, db: Session = Depends(get_db)):
    """批量添加指标"""
    results = []
    for item in data.indicators:
        indicator = create_indicator_with_evaluation(
            db=db,
            user_id=item.user_id,
            category=item.category,
            name=item.name,
            value=item.value,
            unit=item.unit,
            statistic_type=item.statistic_type,
            reference_min=item.reference_min,
            reference_max=item.reference_max,
            source=item.source or "manual",
            measured_at=item.measured_at,
        )
        results.append(indicator.to_dict())
    return results


@router.delete("/indicators/batch")
def batch_delete_indicators(data: HealthIndicatorBatchDelete, db: Session = Depends(get_db)):
    deleted = (
        db.query(HealthIndicator)
        .filter(HealthIndicator.id.in_(data.ids))
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"message": "批量删除成功", "deleted_count": deleted}


@router.get("/indicators/{indicator_id}", response_model=HealthIndicatorResponse)
def get_indicator(indicator_id: int, db: Session = Depends(get_db)):
    """获取指标详情"""
    indicator = db.query(HealthIndicator).filter(HealthIndicator.id == indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="指标不存在")
    return indicator.to_dict()


@router.put("/indicators/{indicator_id}", response_model=HealthIndicatorResponse)
def update_indicator(indicator_id: int, data: HealthIndicatorUpdate, db: Session = Depends(get_db)):
    """更新指标"""
    indicator = db.query(HealthIndicator).filter(HealthIndicator.id == indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="指标不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(indicator, key, value)

    # 如果值变了或分类变了，重新评估
    if {"value", "name", "reference_min", "reference_max"} & update_data.keys():
        from app.services.rule_engine import evaluate_indicator
        eval_result = evaluate_indicator(
            indicator.name,
            indicator.value,
            indicator.unit,
            indicator.reference_min,
            indicator.reference_max,
        )
        indicator.status = eval_result.get("status")
        indicator.risk_level = eval_result.get("risk_level")
        indicator.suggestion = eval_result.get("suggestion")
        from app.services.health_service import _format_reference_range, _get_normal_range
        indicator.normal_range = (
            _format_reference_range(indicator.reference_min, indicator.reference_max, indicator.unit)
            or _get_normal_range(indicator.name)
        )

    db.commit()
    db.refresh(indicator)
    return indicator.to_dict()


@router.delete("/indicators/{indicator_id}")
def delete_indicator(indicator_id: int, db: Session = Depends(get_db)):
    """删除指标"""
    indicator = db.query(HealthIndicator).filter(HealthIndicator.id == indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="指标不存在")
    db.delete(indicator)
    db.commit()
    return {"message": "删除成功"}


@router.get("/categories")
def list_categories():
    """获取所有指标分类"""
    return [
        {
            "key": k,
            "name": v,
            "indicators": [
                {"name": rule.name, "unit": rule.unit}
                for rule in ALL_RULES.get(k, [])
            ],
        }
        for k, v in CATEGORY_NAMES.items()
    ]


@router.get("/risk-summary")
def risk_summary(
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """获取健康风险评估摘要"""
    if user_id is None:
        user = get_user_or_default(db)
        user_id = user.id
    return get_risk_summary(db, user_id)


@router.get("/suggestions")
def health_suggestions(
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """获取四维度健康建议"""
    if user_id is None:
        user = get_user_or_default(db)
        user_id = user.id
    return generate_health_suggestions(db, user_id)


@router.post("/ai-analyze")
async def ai_analyze(
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """AI 综合分析所有指标"""
    if user_id is None:
        user = get_user_or_default(db)
        user_id = user.id

    indicators = db.query(HealthIndicator).filter(
        HealthIndicator.user_id == user_id
    ).all()

    if not indicators:
        raise HTTPException(status_code=400, detail="暂无指标数据，请先添加健康指标")

    # 构建指标文本
    lines = []
    for ind in indicators:
        unit_str = f"{ind.unit}" if ind.unit else ""
        status_str = f"({ind.status})" if ind.status else ""
        lines.append(f"{ind.name} {ind.value}{unit_str} {status_str}")

    indicators_text = "\n".join(lines)

    # 获取用户信息
    user_obj = db.query(User).filter(User.id == user_id).first()
    user_info = {
        "年龄": user_obj.age,
        "性别": user_obj.gender,
        "身高": f"{user_obj.height}cm" if user_obj.height else None,
        "体重": f"{user_obj.weight}kg" if user_obj.weight else None,
        "BMI": user_obj.bmi,
        "病史": user_obj.medical_history,
    }

    from app.services.ai_service import analyze_health_indicators
    result = await analyze_health_indicators(indicators_text, user_info)

    source = "ai"
    if result is None:
        # AI 不可用时，使用规则引擎结果
        summary = get_risk_summary(db, user_id)
        suggestions = generate_health_suggestions(db, user_id)
        fallback = "【AI 分析暂时不可用，以下为基于规则库的评估】\n\n"
        fallback += f"共 {summary['total_count']} 项指标，"
        fallback += f"异常 {summary['abnormal_count']} 项，"
        fallback += f"高风险 {summary['high_risk_count']} 项。\n\n"
        for dim, items in suggestions.items():
            if items:
                dim_name = {"diet": "饮食", "exercise": "运动", "lifestyle": "作息", "medical": "就医"}.get(dim, dim)
                fallback += f"**{dim_name}建议**：\n"
                for item in items:
                    fallback += f"- {item}\n"
                fallback += "\n"
        result = fallback
        source = "rule_engine"

    saved = HealthAnalysis(
        user_id=user_id,
        analysis=result,
        source=source,
        indicator_count=len(indicators),
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved.to_dict()


@router.get("/ai-analyses")
def list_ai_analyses(
    user_id: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取已保存的健康分析记录，最新结果在前。"""
    if user_id is None:
        user_id = get_user_or_default(db).id
    records = (
        db.query(HealthAnalysis)
        .filter(HealthAnalysis.user_id == user_id)
        .order_by(HealthAnalysis.created_at.desc(), HealthAnalysis.id.desc())
        .limit(limit)
        .all()
    )
    return [record.to_dict() for record in records]
