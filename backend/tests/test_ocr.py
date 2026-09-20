import unittest

from app.routers.ocr import _parse_indicators


class OcrParserTest(unittest.TestCase):
    def test_parses_indicator_columns_in_documented_order(self):
        result = _parse_indicators(
            "INDICATOR|空腹血糖|5.6|mmol/L\n"
            "INDICATOR|总胆固醇|4.8|mmol/L"
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "空腹血糖")
        self.assertEqual(result[0].value, "5.6")
        self.assertEqual(result[0].unit, "mmol/L")

    def test_ignores_non_indicator_and_incomplete_lines(self):
        result = _parse_indicators(
            "```text\n"
            "以下是结果\n"
            "INDICATOR|收缩压|120|mmHg\n"
            "INDICATOR||80|mmHg\n"
            "```"
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "收缩压")

    def test_ignores_unsupported_items_and_normalizes_aliases(self):
        result = _parse_indicators(
            "INDICATOR|医院名称|某某医院|\n"
            "INDICATOR|ALT|32|U/L\n"
            "INDICATOR|维生素D|28|ng/mL"
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "谷丙转氨酶")
        self.assertEqual(result[0].category, "liver")

    def test_parses_min_max_average_with_separate_reference_ranges(self):
        result = _parse_indicators(
            "INDICATOR|收缩压|min|95|mmHg|90|110\n"
            "INDICATOR|收缩压|max|138|mmHg|100|135\n"
            "INDICATOR|收缩压|average|118|mmHg|95|125"
        )

        self.assertEqual([item.statistic_type for item in result], ["min", "max", "average"])
        self.assertEqual([item.value for item in result], ["95", "138", "118"])
        self.assertEqual(result[1].reference_min, 100)
        self.assertEqual(result[1].reference_max, 135)


if __name__ == "__main__":
    unittest.main()
