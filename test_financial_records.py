"""Tests for monthly MSME financial records."""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from database import business_profiles, financial_records, models


class FinancialRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "records.db"

        def connect():
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            return conn

        self.connect = connect
        with patch.object(models, "get_connection", self.connect):
            models.create_tables()
        self.patcher = patch.object(business_profiles, "get_connection", self.connect)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.patcher2 = patch.object(financial_records, "get_connection", self.connect)
        self.patcher2.start()
        self.addCleanup(self.patcher2.stop)

        conn = self.connect()
        with conn:
            conn.execute(
                "INSERT INTO users (id, full_name, email, password_hash) VALUES (1, 'Owner', 'owner@test.com', 'hash')"
            )
            conn.execute(
                "INSERT INTO users (id, full_name, email, password_hash) VALUES (2, 'Other', 'other@test.com', 'hash')"
            )
        conn.close()
        self.business_id = business_profiles.save_business_profile(
            1,
            {
                "business_name": "Test MSME",
                "business_type": "Proprietorship",
                "industry": "Retail",
                "city": "Hyderabad",
                "state": "Telangana",
            },
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def data(self, **overrides):
        values = {
            "period_month": "2026-10",
            "revenue": 200000,
            "other_income": 5000,
            "cost_of_goods_sold": 90000,
            "operating_expenses": 40000,
            "owner_drawings": 15000,
            "existing_debt_service": 10000,
            "notes": "Test month",
        }
        values.update(overrides)
        return values

    def test_save_and_read_monthly_record(self):
        financial_records.save_business_financial_record(1, self.business_id, self.data())
        rows = financial_records.get_business_financial_records(1, self.business_id)
        self.assertEqual(1, len(rows))
        self.assertEqual("2026-10", rows[0]["period_month"])

    def test_same_month_updates_instead_of_duplicate(self):
        first_id = financial_records.save_business_financial_record(1, self.business_id, self.data())
        second_id = financial_records.save_business_financial_record(
            1, self.business_id, self.data(revenue=220000)
        )
        rows = financial_records.get_business_financial_records(1, self.business_id)
        self.assertEqual(first_id, second_id)
        self.assertEqual(1, len(rows))
        self.assertEqual(220000, rows[0]["revenue"])

    def test_other_user_cannot_access_or_write_business_records(self):
        self.assertEqual([], financial_records.get_business_financial_records(2, self.business_id))
        with self.assertRaises(ValueError):
            financial_records.save_business_financial_record(2, self.business_id, self.data())

    def test_negative_values_and_invalid_month_are_rejected(self):
        with self.assertRaises(ValueError):
            financial_records.save_business_financial_record(1, self.business_id, self.data(revenue=-1))
        with self.assertRaises(ValueError):
            financial_records.save_business_financial_record(1, self.business_id, self.data(period_month="2026-13"))

    def test_cash_headroom_calculation(self):
        record = self.data()
        summary = financial_records.calculate_monthly_summary(record)
        self.assertEqual(205000, summary["total_income"])
        self.assertEqual(75000, summary["operating_surplus"])
        self.assertEqual(50000, summary["cash_headroom"])


if __turn__ == "__main__":
    unittest.main()
