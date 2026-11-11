"""Tests for the MSME Financial Resilience Twin calculations."""

import unittest

from core.resilience_twin import simulate_resilience


class ResilienceTwinTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            "period_month": "2026-11",
            "revenue": 200000,
            "other_income": 5000,
            "cost_of_goods_sold": 90000,
            "operating_expenses": 40000,
            "owner_drawings": 15000,
            "existing_debt_service": 10000,
        }

    def test_zero_stress_matches_recorded_cash_headroom(self):
        result = simulate_resilience(self.record)
        self.assertEqual(50000, result["base_cash_headroom"])
        self.assertEqual(50000, result["stressed_headroom"])

    def test_combined_stress_calculation(self):
        result = simulate_resilience(
            self.record,
            revenue_drop_percent=10,
            cost_increase_percent=10,
            delayed_receipts_percent=20,
            proposed_new_emi=5000,
        )
        self.assertEqual(144000, result["stressed_sales_collected"])
        self.assertEqual(143000, result["stressed_costs"])
        self.assertEqual(-19000, result["stressed_headroom"])
        self.assertTrue(result["is_stressed_headroom_negative"])

    def test_new_emi_reduces_headroom_rupee_for_rupee(self):
        result = simulate_resilience(self.record, proposed_new_emi=12000)
        self.assertEqual(38000, result["stressed_headroom"])
        self.assertEqual(50000, result["additional_emi_headroom"])

    def test_break_even_threshold(self):
        result = simulate_resilience(self.record)
        self.assertEqual(75.0, result["revenue_break_even_drop_percent"])

    def test_rejects_invalid_percentages_and_negative_emi(self):
        with self.assertRaises(ValueError):
            simulate_resilience(self.record, revenue_drop_percent=101)
        with self.assertRaises(ValueError):
            simulate_resilience(self.record, proposed_new_emi=-1)

    def test_zero_sales_has_no_revenue_threshold(self):
        record = dict(self.record, revenue=0)
        result = simulate_resilience(record)
        self.assertIsNone(result["revenue_break_even_drop_percent"])


if __name__ == "__main__":
    unittest.main()
