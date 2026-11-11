import unittest

from core.cash_flow_outlook import build_cash_flow_outlook


class CashFlowOutlookTests(unittest.TestCase):
    def setUp(self):
        self.months = [
            {"month": "2026-09", "inflows": 100000, "outflows": 70000},
            {"month": "2026-10", "inflows": 120000, "outflows": 80000},
            {"month": "2026-11", "inflows": 110000, "outflows": 75000},
        ]

    def test_three_month_average_baseline(self):
        result = build_cash_flow_outlook(self.months, forecast_months=2, reserve_pct=20)
        row = result["forecast_months"][0]
        self.assertEqual(row["baseline_inflows"], 110000)
        self.assertEqual(row["baseline_outflows"], 75000)
        self.assertEqual(row["baseline_net"], 35000)
        self.assertEqual(row["planning_headroom"], 28000)
        self.assertEqual(len(result["forecast_months"]), 2)

    def test_stress_scenario_applied_to_receipts_and_costs(self):
        result = build_cash_flow_outlook(
            self.months, forecast_months=1, reserve_pct=0,
            receipt_shock_pct=10, cost_increase_pct=10
        )
        row = result["forecast_months"][0]
        self.assertEqual(row["stressed_inflows"], 99000)
        self.assertEqual(row["stressed_outflows"], 82500)
        self.assertEqual(row["planning_headroom"], 16500)

    def test_requires_two_months(self):
        with self.assertRaises(ValueError):
            build_cash_flow_outlook(self.months[:1])

    def test_rejects_duplicate_months(self):
        with self.assertRaises(ValueError):
            build_cash_flow_outlook([self.months[0], self.months[0]])

    def test_rejects_invalid_stress(self):
        with self.assertRaises(ValueError):
            build_cash_flow_outlook(self.months, receipt_shock_pct=101)


if __name__ == "__main__":
    unittest.main()
