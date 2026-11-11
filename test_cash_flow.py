import unittest

from core.cash_flow import build_cash_flow_projection


def sample_records():
    return [
        {
            "period_month": "2026-11",
            "revenue": 100000,
            "other_income": 5000,
            "cost_of_goods_sold": 40000,
            "operating_expenses": 25000,
            "owner_drawings": 5000,
            "existing_debt_service": 10000,
        },
        {
            "period_month": "2026-10",
            "revenue": 90000,
            "other_income": 5000,
            "cost_of_goods_sold": 36000,
            "operating_expenses": 24000,
            "owner_drawings": 5000,
            "existing_debt_service": 10000,
        },
        {
            "period_month": "2026-09",
            "revenue": 80000,
            "other_income": 5000,
            "cost_of_goods_sold": 32000,
            "operating_expenses": 23000,
            "owner_drawings": 5000,
            "existing_debt_service": 10000,
        },
    ]


class CashFlowProjectionTests(unittest.TestCase):
    def test_three_month_average_baseline(self):
        result = build_cash_flow_projection(sample_records(), months=3)
        self.assertEqual(result["baseline_months"], ["2026-11", "2026-10", "2026-09"])
        self.assertEqual(result["baseline_averages"]["revenue"], 90000)
        self.assertEqual(len(result["projections"]), 3)

    def test_flat_scenario_headroom_is_consistent(self):
        result = build_cash_flow_projection(sample_records(), months=1)
        row = result["projections"][0]
        expected = (
            row["sales_collected"] + row["other_income"]
            - row["direct_costs"] - row["operating_expenses"]
            - row["owner_drawings"] - row["existing_debt"]
        )
        self.assertEqual(row["cash_headroom"], round(expected, 2))

    def test_cost_increase_and_additional_emi_reduce_headroom(self):
        base = build_cash_flow_projection(sample_records(), months=1)
        stressed = build_cash_flow_projection(
            sample_records(),
            months=1,
            monthly_cost_increase_percent=10,
            additional_monthly_emi=5000,
        )
        self.assertLess(
            stressed["projections"][0]["cash_headroom"],
            base["projections"][0]["cash_headroom"],
        )

    def test_revenue_drop_and_delayed_receipts_reduce_collections(self):
        base = build_cash_flow_projection(sample_records(), months=1)
        stressed = build_cash_flow_projection(
            sample_records(),
            months=1,
            monthly_revenue_change_percent=-10,
            delayed_sales_percent=20,
        )
        self.assertLess(
            stressed["projections"][0]["sales_collected"],
            base["projections"][0]["sales_collected"],
        )

    def test_requires_three_months(self):
        with self.assertRaises(ValueError):
            build_cash_flow_projection(sample_records()[:2])

    def test_rejects_invalid_horizon_and_assumptions(self):
        with self.assertRaises(ValueError):
            build_cash_flow_projection(sample_records(), months=7)
        with self.assertRaises(ValueError):
            build_cash_flow_projection(
                sample_records(), delayed_sales_percent=101
            )
        with self.assertRaises(ValueError):
            build_cash_flow_projection(
                sample_records(), additional_monthly_emi=-1
            )

    def test_rejects_negative_recorded_amount(self):
        records = sample_records()
        records[0]["revenue"] = -1
        with self.assertRaises(ValueError):
            build_cash_flow_projection(records)


if __name__ == "__main__":
    unittest.main()
