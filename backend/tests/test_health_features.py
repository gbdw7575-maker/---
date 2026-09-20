import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import HealthAnalysis, HealthIndicator, User
from app.routers.health import ai_analyze, list_categories


class HealthFeatureTest(unittest.TestCase):
    def test_categories_include_selectable_indicators_and_default_units(self):
        categories = list_categories()
        blood_pressure = next(item for item in categories if item["key"] == "blood_pressure")
        systolic = next(item for item in blood_pressure["indicators"] if item["name"] == "收缩压")
        self.assertEqual(systolic["unit"], "mmHg")

    def test_health_analysis_can_be_persisted(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            user = User(name="测试用户")
            session.add(user)
            session.flush()
            session.add(HealthAnalysis(
                user_id=user.id,
                analysis="测试分析结果",
                source="ai",
                indicator_count=2,
            ))
            session.commit()

            saved = session.query(HealthAnalysis).one()
            self.assertEqual(saved.analysis, "测试分析结果")
            self.assertEqual(saved.indicator_count, 2)

    def test_ai_analyze_endpoint_saves_generated_result(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            user = User(name="测试用户")
            session.add(user)
            session.flush()
            session.add(HealthIndicator(
                user_id=user.id,
                category="blood_pressure",
                name="收缩压",
                value="128",
                unit="mmHg",
                status="abnormal_high",
                risk_level="medium",
            ))
            session.commit()

            with patch(
                "app.services.ai_service.analyze_health_indicators",
                new=AsyncMock(return_value="已生成的健康分析"),
            ):
                response = asyncio.run(ai_analyze(user_id=user.id, db=session))

            self.assertEqual(response["analysis"], "已生成的健康分析")
            self.assertEqual(response["source"], "ai")
            self.assertEqual(session.query(HealthAnalysis).count(), 1)


if __name__ == "__main__":
    unittest.main()
