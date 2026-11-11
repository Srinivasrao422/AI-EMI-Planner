import unittest

from core.financial_intelligence import analyze_business_trends


def sample_records():
    return [
        {"period_month": "2026-11", "revenue": 75000, "other_income": 0, "cost_of_goods_sold": 20000, "operating_expenses": 10000, "owner_drawings": 7000, "existing_debt_service": 20000},
        {"period_month": "2026-10", "revenue": 60000, "other_income": 0, "cost_of_goods_sold": 18000, "operating_expenses": 8000, "owner_drawings": 7000, "existing_debt_service": 24000},
    ]


class FinancialIntelligenceTests(unittest.TestCase):
    def test_compares_saved_months_and_calculates_actual_headroom(self):
        result = analyze_business_trends(sample_records())
        self.assertEqual("2026-11", result["latest_month"])
        self.assertEqual(2, result["records_compared"])
        self.assertEqual(18000, result["latest_summary"]["cash_headroom"])
        self.assertEqual(15000, result["changes"][0]["change_amount"])

    def test_flags_increased_costs_and_revenue_change_with_month_evidence(self):
        result = analyze_business_trends(sample_records())
        evidence_text = " ".join(item["text"] for item in result["findings"])
        self.assertIn("2026-10", evidence_text)
        self.assertIn("2026-11", evidence_text)
        self.assertTrue(any(item["field"] == "operating_expenses" for item in result["changes"]))

    def test_single_month_does_not_claim_a_trend(self):
        result = analyze_business_trends(sample_records()[:1])
        self.assertEqual(1, result["records_compared"])
        self.assertEqual([], result["changes"])
        self.assertIn("Only one month", result["findings"][0]["text"])

    def test_negative_headroom_gets_high_attention(self):
        rows = sample_records()
        rows[0]["owner_drawings"] = 50000
        result = analyze_business_trends(rows)
        self.assertLess(result["latest_summary"]["cash_headroom"], 0)
        self.assertTrue(any(item["severity"] == "high" for item in result["findings"]))

    def test_rejects_negative_values(self):
        rows = sample_records()
        rows[0]["revenue"] = -1
        with self.assertRaises(ValueError):
            analyze_business_trends(rows)


if __name__ == "__main__":
    unittest.main()
