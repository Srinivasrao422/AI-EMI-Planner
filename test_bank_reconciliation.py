"""Tests for reviewed bank transaction to monthly record reconciliation."""
import unittest
import pandas as pd
from core.bank_reconciliation import build_monthly_reconciliation, suggest_financial_bucket


class BankReconciliationTests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame({
            "Date": ["2026-10-01","2026-10-02","2026-10-03","2026-11-01"],
            "Debit (INR)": [0, 2000, 500, 0],
            "Credit (INR)": [10000, 0, 0, 8000],
            "Financial bucket": ["Revenue","Direct costs","Operating expenses","Revenue"],
        })

    def test_suggested_buckets(self):
        self.assertEqual("Revenue", suggest_financial_bucket("Sales / customer receipts"))
        self.assertEqual("Exclude / transfer", suggest_financial_bucket("Uncategorised"))

    def test_monthly_reconciliation_filters_month_and_maps_values(self):
        result = build_monthly_reconciliation(self.frame(), "2026-10")
        self.assertEqual(10000, result["revenue"])
        self.assertEqual(2000, result["cost_of_goods_sold"])
        self.assertEqual(500, result["operating_expenses"])
        self.assertEqual("2026-10", result["period_month"])

    def test_rejects_negative_amounts(self):
        frame = self.frame()
        frame.loc[0, "Credit (INR)"] = -1
        with self.assertRaises(ValueError):
            build_monthly_reconciliation(frame, "2026-10")

    def test_rejects_both_debit_and_credit(self):
        frame = self.frame()
        frame.loc[0, "Debit (INR)"] = 5
        with self.assertRaises(ValueError):
            build_monthly_reconciliation(frame, "2026-10")

    def test_requires_transactions_for_month(self):
        with self.assertRaises(ValueError):
            build_monthly_reconciliation(self.frame(), "2026-09")


if __name__ == "__main__":
    unittest.main()
