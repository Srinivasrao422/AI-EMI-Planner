import unittest

from core.ai_engine import build_financial_system_prompt


class GroundedAdvisorPromptTests(unittest.TestCase):
    def test_missing_financial_values_are_marked_not_recorded(self):
        prompt = build_financial_system_prompt({})
        self.assertIn('"loan_amount": "Not recorded"', prompt)
        self.assertIn("Never invent revenue", prompt)
        self.assertIn("not a lender", prompt.lower())

    def test_business_context_is_included_without_fabricated_score(self):
        context = {
            "business_name": "Sample Retail",
            "reporting_months": [{
                "period_month": "2026-11",
                "revenue": 100000,
                "operating_expenses": 20000,
            }],
        }
        prompt = build_financial_system_prompt({"msme_context": context})
        self.assertIn("Sample Retail", prompt)
        self.assertIn("100000", prompt)
        self.assertIn("Never invent", prompt)
        self.assertNotIn('"credit_score": 760', prompt)


if __name__ == "__main__":
    unittest.main()
