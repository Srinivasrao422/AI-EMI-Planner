"""Monthly financial records for MSME business profiles."""

from datetime import date
from database.connection import get_connection


def _validate_record(data):
    month = str(data.get("period_month", "")).strip()
    try:
        parsed = date.fromisoformat(month + "-01")
    except ValueError as exc:
        raise ValueError("Select a valid reporting month.") from exc
    if parsed.strftime("%Y-%m") != month:
        raise ValueError("Reporting month must use YYYY-MM format.")

    fields = (
        "revenue",
        "other_income",
        "cost_of_goods_sold",
        "operating_expenses",
        "owner_drawings",
        "existing_debt_service",
    )
    values = {}
    for field in fields:
        try:
            amount = float(data.get(field, 0) or 0)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field.replace('_', ' ').title()} must be numeric.") from exc
        if amount < 0:
            raise ValueError(f"{field.replace('_', ' ').title()} cannot be negative.")
        values[field] = round(amount, 2)
    values["period_month"] = month
    values["notes"] = str(data.get("notes", "") or "").strip()
    return values


def get_business_financial_records(user_id, business_id):
    """Return monthly records only when the business belongs to this user."""
    conn = get_connection()
    try:
        conn.row_factory = __import__("sqlite3").Row
        rows = conn.execute(
            """
            SELECT fr.*
            FROM financial_records AS fr
            JOIN business_profiles AS bp ON bp.id = fr.business_id
            WHERE fr.user_id = ? AND fr.business_id = ?
              AND bp.user_id = ?
            ORDER BY fr.period_month DESC
            """,
            (user_id, business_id, user_id),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def save_business_financial_record(user_id, business_id, data, record_id=None):
    """Insert or update a monthly record, scoped to the owning user."""
    if not user_id:
        raise ValueError("A signed-in user is required.")
    values = _validate_record(data)
    conn = get_connection()
    try:
        with conn:
            owned = conn.execute(
                "SELECT 1 FROM business_profiles WHERE id = ? AND user_id = ?",
                (business_id, user_id),
            ).fetchone()
            if not owned:
                raise ValueError("Business profile was not found for this user.")

            if record_id is None:
                conn.execute(
                    """
                    INSERT INTO financial_records (
                        user_id, business_id, period_month, revenue, other_income,
                        cost_of_goods_sold, operating_expenses, owner_drawings,
                        existing_debt_service, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(business_id, period_month) DO UPDATE SET
                        revenue = excluded.revenue,
                        other_income = excluded.other_income,
                        cost_of_goods_sold = excluded.cost_of_goods_sold,
                        operating_expenses = excluded.operating_expenses,
                        owner_drawings = excluded.owner_drawings,
                        existing_debt_service = excluded.existing_debt_service,
                        notes = excluded.notes,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE financial_records.user_id = excluded.user_id
                    """,
                    (
                        user_id, business_id, values["period_month"],
                        values["revenue"], values["other_income"],
                        values["cost_of_goods_sold"], values["operating_expenses"],
                        values["owner_drawings"], values["existing_debt_service"],
                        values["notes"],
                    ),
                )
                row = conn.execute(
                    "SELECT id FROM financial_records WHERE business_id = ? AND period_month = ? AND user_id = ?",
                    (business_id, values["period_month"], user_id),
                ).fetchone()
                if not row:
                    raise ValueError("Could not save this financial record.")
                return row[0]

            cursor = conn.execute(
                """
                UPDATE financial_records
                SET period_month = ?, revenue = ?, other_income = ?,
                    cost_of_goods_sold = ?, operating_expenses = ?,
                    owner_drawings = ?, existing_debt_service = ?,
                    notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND business_id = ? AND user_id = ?
                """,
                (
                    values["period_month"], values["revenue"], values["other_income"],
                    values["cost_of_goods_sold"], values["operating_expenses"],
                    values["owner_drawings"], values["existing_debt_service"],
                    values["notes"], record_id, business_id, user_id,
                ),
            )
            if cursor.rowcount != 1:
                raise ValueError("Financial record was not found for this business.")
            return record_id
    finally:
        conn.close()


def calculate_monthly_summary(record):
    """Calculate transparent monthly cash headroom from entered figures."""
    operating_surplus = (
        record["revenue"] + record["other_income"]
        - record["cost_of_goods_sold"] - record["operating_expenses"]
    )
    cash_headroom = (
        operating_surplus - record["owner_drawings"]
        - record["existing_debt_service"]
    )
    return {
        "total_income": round(record["revenue"] + record["other_income"], 2),
        "operating_surplus": round(operating_surplus, 2),
        "cash_headroom": round(cash_headroom, 2),
    }
