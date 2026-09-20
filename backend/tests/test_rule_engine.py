import unittest

from app.services.rule_engine import evaluate_indicator


class RuleEngineReferenceRangeTest(unittest.TestCase):
    def test_report_reference_range_overrides_default_range(self):
        result = evaluate_indicator(
            "收缩压",
            "128",
            "mmHg",
            reference_min=100,
            reference_max=130,
        )
        self.assertEqual(result["status"], "normal")

    def test_value_above_statistic_specific_range_is_high(self):
        result = evaluate_indicator(
            "收缩压",
            "138",
            "mmHg",
            reference_min=100,
            reference_max=135,
        )
        self.assertEqual(result["status"], "abnormal_high")


if __name__ == "__main__":
    unittest.main()
