"""
=====================================================
Loan History Manager
Project : AI Powered EMI Planner
Purpose:
Save, fetch and manage user-specific loan records in SQLite
=====================================================
"""

import pandas as pd
from database.connection import get_connection

def save_loan(user_id, data):
    """Automatically save loan calculation attached to user_id."""
    if not user_id:
        return False
        
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO loan_history (
                user_id,
                loan_amount,
                interest_rate,
                tenure,
                monthly_income,
                monthly_emi,
                total_interest,
                total_payment,
                risk_level
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                float(data["loan_amount"]),
                float(data["interest_rate"]),
                int(data["tenure"]),
                float(data.get("monthly_income", 0.0)),
                float(data.get("monthly_emi", 0.0)),
                float(data.get("total_interest", 0.0)),
                float(data.get("total_payment", 0.0)),
                data.get("risk_level", "Pending")
            )
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving loan: {e}")
        return False
    finally:
        conn.close()


def get_user_loans(user_id):
    """Fetch all history records specifically for the logged-in user."""
    if not user_id:
        return pd.DataFrame()
        
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            """
            SELECT *
            FROM loan_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            conn,
            params=(int(user_id),)
        )
    except Exception as e:
        print(f"Error fetching user loans: {e}")
        df = pd.read_sql_query("SELECT * FROM loan_history WHERE 1=0", conn)
    finally:
        conn.close()
    return df


def delete_loan(loan_id):
    """Delete a specific loan calculation record."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM loan_history WHERE id = ?", (int(loan_id),))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting loan: {e}")
        return False
    finally:
        conn.close()


def get_latest_loan(user_id):
    """Retrieve user's most recent EMI calculation as a dictionary or None."""
    if not user_id:
        return None
        
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT loan_amount, interest_rate, tenure, monthly_income, 
                   monthly_emi, total_interest, total_payment, risk_level, created_at
            FROM loan_history
            WHERE user_id = ?
            ORDER BY created_at DESC LIMIT 1
            """,
            (int(user_id),)
        )
        row = cursor.fetchone()
        if row:
            return {
                "loan_amount": row[0],
                "interest_rate": row[1],
                "tenure": row[2],
                "monthly_income": row[3],
                "monthly_emi": row[4],
                "total_interest": row[5],
                "total_payment": row[6],
                "risk_level": row[7],
                "created_at": row[8]
            }
    except Exception as e:
        print(f"Error fetching latest loan: {e}")
    finally:
        conn.close()
    return None