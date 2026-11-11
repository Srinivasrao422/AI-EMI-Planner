"""Regression tests for safe SQLite schema initialization."""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database.models as models


class DatabaseMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def initialize(self):
        with patch.object(models, "get_connection", self.connect):
            models.create_tables()

    def table_columns(self, table):
        with self.connect() as conn:
            return {
                row[1]
                for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
            }

    def test_creates_fresh_schema(self):
        self.initialize()

        self.assertTrue(
            {"id", "full_name", "email", "password_hash"}
            .issubset(self.table_columns("users"))
        )
        self.assertTrue(
            {"id", "user_id", "loan_amount", "monthly_emi"}
            .issubset(self.table_columns("loan_history"))
        )

    def test_preserves_current_users_and_loan_history(self):
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE loan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    loan_amount REAL NOT NULL,
                    interest_rate REAL NOT NULL,
                    tenure INTEGER NOT NULL,
                    monthly_income REAL,
                    monthly_emi REAL,
                    total_interest REAL,
                    total_payment REAL,
                    risk_level TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                ("Test User", "test@example.com", "test-hash"),
            )
            conn.execute(
                """
                INSERT INTO loan_history
                (user_id, loan_amount, interest_rate, tenure)
                VALUES (1, 100000, 9.5, 3)
                """
            )

        self.initialize()

        with self.connect() as conn:
            user = conn.execute(
                "SELECT id, full_name, email FROM users WHERE id = 1"
            ).fetchone()
            loan = conn.execute(
                "SELECT user_id, loan_amount FROM loan_history WHERE id = 1"
            ).fetchone()

        self.assertEqual(user, (1, "Test User", "test@example.com"))
        self.assertEqual(loan, (1, 100000.0))

    def test_renames_legacy_name_column_without_data_loss(self):
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Legacy User", "legacy@example.com", "legacy-hash"),
            )

        self.initialize()

        self.assertIn("full_name", self.table_columns("users"))
        self.assertNotIn("name", self.table_columns("users"))
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id, full_name, email FROM users WHERE id = 1"
            ).fetchone()
        self.assertEqual(row, (1, "Legacy User", "legacy@example.com"))

    def test_unexpected_users_schema_fails_without_dropping_data(self):
        with self.connect() as conn:
            conn.execute(
                "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)"
            )
            conn.execute(
                "INSERT INTO users (id, email) VALUES (1, 'keep@example.com')"
            )

        with patch.object(models, "get_connection", self.connect):
            with self.assertRaisesRegex(RuntimeError, "No tables were dropped"):
                models.create_tables()

        with self.connect() as conn:
            row = conn.execute(
                "SELECT id, email FROM users WHERE id = 1"
            ).fetchone()
            tables = {
                result[0]
                for result in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }

        self.assertEqual(row, (1, "keep@example.com"))
        self.assertIn("users", tables)


if __name__ == "__main__":
    unittest.main()
