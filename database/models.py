"""
=====================================================
Database Models
Project : AI Powered EMI Planner
Purpose:
Create required tables using non-destructive SQLite migrations.
=====================================================
"""

import sqlite3

from database.connection import get_connection


def _table_columns(cursor, table_name):
    """Return the column names for an existing SQLite table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def _migrate_users_table(cursor):
    """
    Bring the users table to the current naming convention without
    dropping existing users or related loan-history records.
    """
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        ("users",),
    )
    users_table_exists = cursor.fetchone() is not None

    if not users_table_exists:
        cursor.execute(
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
        return

    columns = _table_columns(cursor, "users")

    # Older versions used the name column; rename it in place.
    if "full_name" not in columns and "name" in columns:
        cursor.execute("ALTER TABLE users RENAME COLUMN name TO full_name")
        columns.remove("name")
        columns.add("full_name")

    required_columns = {"id", "full_name", "email", "password_hash"}
    missing_columns = required_columns - columns
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise RuntimeError(
            "The existing users table is missing required columns: "
            f"{missing}. No tables were dropped. Create a verified backup "
            "and define an explicit migration before continuing."
        )


def create_tables():
    """
    Create application tables and apply safe, additive schema migrations.

    This function deliberately never drops users, loans, or loan_history.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")

        with conn:
            _migrate_users_table(cursor)

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS business_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    business_name TEXT NOT NULL,
                    business_type TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    registration_type TEXT,
                    registration_number TEXT,
                    city TEXT NOT NULL,
                    state TEXT NOT NULL,
                    country TEXT NOT NULL DEFAULT 'India',
                    started_year INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id)
                        REFERENCES users (id) ON DELETE CASCADE
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_business_profiles_user_id
                ON business_profiles(user_id)
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS financial_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    business_id INTEGER NOT NULL,
                    period_month TEXT NOT NULL,
                    revenue REAL NOT NULL DEFAULT 0 CHECK (revenue >= 0),
                    other_income REAL NOT NULL DEFAULT 0 CHECK (other_income >= 0),
                    cost_of_goods_sold REAL NOT NULL DEFAULT 0 CHECK (cost_of_goods_sold >= 0),
                    operating_expenses REAL NOT NULL DEFAULT 0 CHECK (operating_expenses >= 0),
                    owner_drawings REAL NOT NULL DEFAULT 0 CHECK (owner_drawings >= 0),
                    existing_debt_service REAL NOT NULL DEFAULT 0 CHECK (existing_debt_service >= 0),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (business_id, period_month),
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (business_id) REFERENCES business_profiles (id) ON DELETE CASCADE
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_financial_records_user_business
                ON financial_records(user_id, business_id, period_month)
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS loan_history (
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
                    FOREIGN KEY (user_id)
                        REFERENCES users (id) ON DELETE CASCADE
                )
                """
            )
    finally:
        conn.close()
