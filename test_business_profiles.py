"""Regression tests for MSME business-profile storage."""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from database import business_profiles, models


class BusinessProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"

        def connect():
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            return conn

        self.connect = connect
        with patch.object(models, "get_connection", self.connect):
            models.create_tables()
        self.patch_connection = patch.object(
            business_profiles, "get_connection", self.connect
        )
        self.patch_connection.start()
        self.addCleanup(self.patch_connection.stop)

        conn = self.connect()
        with conn:
            conn.execute(
                """
                INSERT INTO users (id, full_name, email, password_hash)
                VALUES (1, 'Test User', 'test@example.com', 'not-a-real-hash')
                """
            )
            conn.execute(
                """
                INSERT INTO users (id, full_name, email, password_hash)
                VALUES (2, 'Other User', 'other@example.com', 'not-a-real-hash')
                """
            )
        conn.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def profile(self, **overrides):
        data = {
            "business_name": "Sample Foods",
            "business_type": "Proprietorship",
            "industry": "Food Processing",
            "city": "Hyderabad",
            "state": "Telangana",
            "country": "India",
            "started_year": 2020,
        }
        data.update(overrides)
        return data

    def test_create_and_list_multiple_profiles_for_same_user(self):
        first = business_profiles.save_business_profile(1, self.profile())
        second = business_profiles.save_business_profile(
            1, self.profile(business_name="Sample Distribution")
        )
        profiles = business_profiles.get_user_business_profiles(1)
        self.assertEqual({first, second}, {p["id"] for p in profiles})
        self.assertEqual(2, len(profiles))

    def test_profiles_are_isolated_between_users(self):
        business_profiles.save_business_profile(1, self.profile())
        self.assertEqual([], business_profiles.get_user_business_profiles(2))

    def test_update_requires_ownership(self):
        profile_id = business_profiles.save_business_profile(1, self.profile())
        with self.assertRaises(ValueError):
            business_profiles.save_business_profile(
                2, self.profile(business_name="Unauthorized edit"),
                profile_id=profile_id,
            )
        self.assertEqual(
            "Sample Foods",
            business_profiles.get_user_business_profiles(1)[0]["business_name"],
        )

    def test_delete_requires_ownership(self):
        profile_id = business_profiles.save_business_profile(1, self.profile())
        self.assertFalse(business_profiles.delete_business_profile(2, profile_id))
        self.assertEqual(1, len(business_profiles.get_user_business_profiles(1)))
        self.assertTrue(business_profiles.delete_business_profile(1, profile_id))
        self.assertEqual([], business_profiles.get_user_business_profiles(1))

    def test_required_fields_and_year_are_validated(self):
        with self.assertRaises(ValueError):
            business_profiles.save_business_profile(
                1, self.profile(business_name=" ")
            )
        with self.assertRaises(ValueError):
            business_profiles.save_business_profile(
                1, self.profile(started_year=1700)
            )

    def test_existing_loan_history_is_not_modified(self):
        conn = self.connect()
        with conn:
            conn.execute(
                """
                INSERT INTO loan_history (
                    user_id, loan_amount, interest_rate, tenure
                ) VALUES (1, 100000, 9.0, 3)
                """
            )
        conn.close()

        business_profiles.save_business_profile(1, self.profile())
        conn = self.connect()
        count = conn.execute("SELECT COUNT(*) FROM loan_history").fetchone()[0]
        conn.close()
        self.assertEqual(1, count)


if __name__ == "__main__":
    unittest.main()
