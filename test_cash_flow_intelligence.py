import unittest

from core.cash_flow_intelligence import analyze_transactions, categorize_transaction


class CashFlowIntelligenceTests(unittest.TestCase):
    def test_categories_are_transparent_keyword_rules(self):
        self.assertEqual(categorize_transaction("UPI CUSTOMER RECEIPT")[0], "customer_receipts")
        self.assertEqual(categorize_transaction("NEFT WHOLESALE SUPPLIER")[0], "supplier_payments")
        self.assertEqual(categorize_transaction("mystery transfer")[0], "unclassified")

    def test_totals_and_monthly_summary(self):
        result = analyze_transactions([
            {"date": "01-10-2026", "description": "UPI CUSTOMER PAYMENT", "debit": 0, "credit": 1000},
            {"date": "02-10-2026", "description": "SUPPLIER PAYMENT", "debit": 300, "credit": 0},
            {"date": "01/11/2026", "description": "UNRECOGNISED TRANSFER", "debit": 0, "credit": 200},
        ])
        self.assertEqual(result["transaction_count"], 3)
        self.assertEqual(result["total_inflows"], 1200)
        self.assertEqual(result["total_outflows"], 300)
        self.assertEqual(result["net_cash_movement"], 900)
        self.assertEqual(result["monthly"]["2026-10"]["net"], 700)
        self.assertEqual(len(result["unclassified"]), 1)

    def test_rejects_negative_amounts(self):
        with self.assertRaises(ValueError):
            analyze_transactions([{"description": "x", "debit": -1, "credit": 0}])

    def test_rejects_both_debit_and_credit(self):
        with self.assertRaises(ValueError):
            analyze_transactions([{"description": "x", "debit": 10, "credit": 20}])

    def test_rejects_unsupported_dates(self):
        with self.assertRaises(ValueError):
            analyze_transactions([{"date": "not-a-date", "description": "x", "debit": 1, "credit": 0}])


if __name__ == "__main__":
    unittest.main()
