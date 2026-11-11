import unittest

from core.msme_credit_assessment import assess_credit_readiness


def records():
    return [
        {"period_month": "2026-11", "revenue": 100000, "other_income": 1000, "cost_of_goods_sold": 40000, "operating_expenses": 25000, "owner_drawings": 5000, "existing_debt_service": 10000},
        {"period_month": "2026-10", "revenue": 95000, "other_income": 1000, "cost_of_goods_sold": 38000, "operating_expenses": 25000, "owner_drawings": 5000, "existing_debt_service": 10000},
        {"period_month": "2026-09", "revenue": 90000, "other_income": 1000, "cost_of_goods_sold": 36000, "operating_expenses": 24000, "owner_drawings": 5000, "existing_debt_service": 10000},
    ]


class MSMECreditReadinessTests(unittest.TestCase):
    def test_supportive_cash_flow(self):
        result = assess_credit_readiness(records(), proposed_monthly_emi=5000)
        self.assertEqual("Cash-flow indicators are supportive", result["status"])
        self.assertEqual(3, result["positive_headroom_months"])
        self.assertGreater(result["headroom_after_proposed_emi"], 0)

    def test_proposed_emi_negative_headroom_is_flagged(self):
        result = assess_credit_readiness(records(), proposed_monthly_emi=50000)
        self.assertEqual("High attention required", result["status"])
        self.assertLess(result["headroom_after_proposed_emi"], 0)
        self.assertTrue(any("proposed EMI" in item for item in result["findings"]))

    def test_requires_three_consecutive_months(self):
        with self.assertRaises(ValueError):
            assess_credit_readiness(records()[:2])
        broken = records()
        broken[1]["period_month"] = "2026-08"
        with self.assertRaises(ValueError):
            assess_credit_readiness(broken)

    def test_rejects_negative_amounts(self):
        broken = records()
        broken[0]["revenue"] = -1
        with self.assertRaises(ValueError):
            assess_credit_readiness(broken)

    def test_explains_missing_evidence(self):
        result = assess_credit_readiness(records())
        self.assertTrue(result["evidence_gaps"])
        self.assertIn("not a credit score", result["limitations"])


if __name__ == "__main__":
    unittest.main()
