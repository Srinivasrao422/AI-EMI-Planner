import unittest

from core.loan_optimizer import (
    analyze_repayment_capacity,
    compare_loan_scenarios,
    maximum_principal_for_emi,
)


def record():
    return {
        "period_month": "2026-11",
        "revenue": 200000,
        "other_income": 5000,
        "cost_of_goods_sold": 90000,
        "operating_expenses": 40000,
        "owner_drawings": 15000,
        "existing_debt_service": 10000,
    }


class LoanOptimizerTests(unittest.TestCase):
    def test_repayment_capacity_uses_cash_headroom_and_reserve(self):
        result = analyze_repayment_capacity(record(), 30)
        self.assertEqual(result["cash_headroom"], 50000)
        self.assertEqual(result["reserve_amount"], 15000)
        self.assertEqual(result["estimated_monthly_emi_capacity"], 35000)

    def test_negative_headroom_means_zero_additional_capacity(self):
        data = record()
        data["operating_expenses"] = 100000
        result = analyze_repayment_capacity(data, 30)
        self.assertLess(result["cash_headroom"], 0)
        self.assertEqual(result["estimated_monthly_emi_capacity"], 0)

    def test_zero_interest_reverse_principal(self):
        self.assertEqual(360000, maximum_principal_for_emi(10000, 0, 3))

    def test_reverse_principal_round_trips_to_emi_capacity(self):
        principal = maximum_principal_for_emi(15000, 12, 5)
        from core.emi import calculate_emi
        self.assertLessEqual(calculate_emi(principal, 12, 5), 15000.01)

    def test_comparison_marks_capacity_and_interest(self):
        results = compare_loan_scenarios(500000, 12, [3, 5, 7], 12000)
        self.assertEqual(3, len(results))
        self.assertTrue(all("within_estimated_capacity" in item for item in results))
        self.assertLess(results[2]["monthly_emi"], results[0]["monthly_emi"])
        self.assertGreater(results[2]["total_interest"], results[0]["total_interest"])

    def test_rejects_invalid_inputs(self):
        with self.assertRaises(ValueError):
            analyze_repayment_capacity(record(), 95)
        with self.assertRaises(ValueError):
            maximum_principal_for_emi(-1, 12, 5)
        with self.assertRaises(ValueError):
            compare_loan_scenarios(0, 12, [5], 10000)
        with self.assertRaises(ValueError):
            compare_loan_scenarios(500000, 12, [], 10000)


if __name__ == "__main__":
    unittest.main()
