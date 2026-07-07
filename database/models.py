"""
=====================================================
Database Models
Project : AI Powered EMI Planner
Purpose:
Create required database tables with migration support
=====================================================
"""

import sqlite3
from database.connection import get_connection

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Schema migration check: drop old tables if 'full_name' is missing in 'users' table
    try:
        # Check if table exists
        cursor.execute("SELECT id FROM users LIMIT 1")
        # Check if full_name column exists
        cursor.execute("SELECT full_name FROM users LIMIT 1")
    except sqlite3.OperationalError:
        # Table is missing or has the old schema (name instead of full_name)
        # Drop old tables to migrate to new layout
        cursor.execute("DROP TABLE IF EXISTS loan_history;")
        cursor.execute("DROP TABLE IF EXISTS loans;")
        cursor.execute("DROP TABLE IF EXISTS users;")

    # Create users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Create loan_history table
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
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
    )

    conn.commit()
    conn.close()