"""Tests for deterministic bank-statement helpers."""
import unittest
import pandas as pd
from core.bank_statement import (\n    build_monthly_reconciliation, categorise_description, normalise_transactions,\n)


class BankStatementTests(unittest.TestCase):
    def test_keyword_category_is_deterministic(self):
        self.assertEqual("Loan / EMI", categorise_description("Monthly EMI debit"))
        self.assertEqual("Uncategorised", categorise_description("XYZ"))

    def test_normalises_and_sorts_transactions(self):
        frame = pd.DataFrame({
            "Txn Date": ["02/11/2026", "01/11/2026"],
            "Narration": ["Monthly EMI", "Customer payment received"],
            "Withdrawal": ["2,000", "0"],
            "Deposit": ["0", "5,000"],
            "Closing Balance": ["8,000", "10,000"],
        })
        result = normalise_transactions(frame, {
            "date": "Txn Date", "description": "Narration",
            "debit": "Withdrawal", "credit": "Deposit", "balance": "Closing Balance",
        })
        self.assertEqual("2026-11-01", result.iloc[0]["Date"])
        self.assertEqual(5000, result.iloc[0]["Credit (INR)"])
        self.assertEqual("Sales / customer receipts", result.iloc[0]["Category"])

    def test_rejects_missing_mapping(self):
        with self.assertRaises(ValueError):
            normalise_transactions(pd.DataFrame({"x": [1]}), {})

    def test_rejects_both_debit_and_credit(self):
        frame = pd.DataFrame({"date": ["01/11/2026"], "desc": ["test"], "d": [10], "c": [5]})
        with self.assertRaises(ValueError):
            normalise_transactions(frame, {"date": "date", "description": "desc", "debit": "d", "credit": "c"})



    def test_monthly_reconciliation_maps_reviewed_categories(self):
        frame = pd.DataFrame({
            "Date": ["2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05", "2026-10-06"],
            "Description": ["sales", "supplier", "rent", "emi", "owner", "unknown"],
            "Debit (INR)": [0, 4000, 3000, 1500, 500, 0],
            "Credit (INR)": [10000, 0, 0, 0, 0, 200],
            "Category": [
                "Sales / customer receipts", "Supplier / inventory", "Rent",
                "Loan / EMI", "Owner drawings", "Uncategorised"
            ],
        })
        draft = build_monthly_reconciliation(frame, "2026-10")
        self.assertEqual(10000, draft["revenue"])
        self.assertEqual(4000, draft["cost_of_goods_sold"])
        self.assertEqual(3000, draft["operating_expenses"])
        self.assertEqual(500, draft["owner_drawings"])
        self.assertEqual(1500, draft["existing_debt_service"])
        self.assertEqual(1, draft["uncategorised_count"])

    def test_monthly_reconciliation_rejects_month_without_transactions(self):
        frame = pd.DataFrame({
            "Date": ["2026-10-01"], "Debit (INR)": [0], "Credit (INR)": [10],
            "Category": ["Sales / customer receipts"],
        })
        with self.assertRaises(ValueError):
            build_monthly_reconciliation(frame, "2026-11")

if __name__ == "__main__":
    unittest.main()
