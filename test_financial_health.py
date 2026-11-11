"""Unit tests for the transparent MSME financial health engine."""

import unittest

from core.financial_health import analyze_financial_health


class FinancialHealthTests(unittest.TestCase):
    def record(self, **overrides):
        row = {
            "period_month": "2026-11",
            "revenue": 200000,
            "other_income": 5000,
            "cost_of_goods_sold": 90000,
            "operating_expenses": 40000,
            "owner_drawings": 15000,
            "existing_debt_service": 10000,
        }
        row.update(overrides)
        return row

    def test_calculates_core_totals_and_ratios(self):
        result = analyze_financial_health([self.record()])
        self.assertEqual(205000, result["total_income"])
        self.assertEqual(110000, result["gross_profit"])
        self.assertEqual(75000, result["operating_surplus"])
        self.assertEqual(50000, result["cash_headroom"])
        indicators = {x["name"]: x["value"] for x in result["indicators"]}
        self.assertAlmostEqual(55.0, indicators["Gross margin"])
        self.assertAlmostEqual(750.0 / 2050.0 * 100, indicators["Operating margin"])
        self.assertEqual(7.5, indicators["Debt service coverage proxy"])

    def test_zero_revenue_returns_unavailable_percentages(self):
        result = analyze_financial_health([self.record(revenue=0, other_income=0)])
        indicators = {x["name"]: x["value"] for x in result["indicators"]}
        self.assertIsNone(indicators["Gross margin"])
        self.assertIsNone(indicators["Operating margin"])
        self.assertTrue(any("No positive income" in x for x in result["observations"]))

    def test_negative_cash_headroom_is_flagged(self):
        result = analyze_financial_health([
            self.record(operating_expenses=150000, owner_drawings=20000)
        ])
        self.assertLess(result["cash_headroom"], 0)
        self.assertTrue(any("Cash headroom is negative" in x for x in result["observations"]))

    def test_no_debt_service_has_no_coverage_ratio(self):
        result = analyze_financial_health([self.record(existing_debt_service=0)])
        indicators = {x["name"]: x["value"] for x in result["indicators"]}
        self.assertIsNone(indicators["Debt service coverage proxy"])

    def test_revenue_trend_uses_latest_two_records(self):
        latest = self.record(revenue=220000)
        previous = self.record(period_month="2026-10", revenue=200000)
        result = analyze_financial_health([latest, previous])
        self.assertEqual(10.0, result["revenue_trend"]["revenue_change_percent"])

    def test_zero_previous_revenue_does_not_divide_by_zero(self):
        latest = self.record(revenue=220000)
        previous = self.record(period_month="2026-10", revenue=0)
        result = analyze_financial_health([latest, previous])
        self.assertIsNone(result["revenue_trend"])

    def test_empty_records_and_invalid_values_are_rejected(self):
        with self.assertRaises(ValueError):
            analyze_financial_health([])
        with self.assertRaises(ValueError):
            analyze_financial_health([self.record(revenue=-10)])


if __name__ == "__main__":
    unittest.main()
