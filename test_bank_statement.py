"""Tests for deterministic bank-statement helpers."""
import unittest
import pandas as pd
from core.bank_statement import categorise_description, normalise_transactions


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


if __name__ == "__main__":
    unittest.main()
