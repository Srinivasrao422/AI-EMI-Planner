"""Deterministic cash-flow analysis helpers for reviewed bank transactions.

This module does not use an AI model. It applies transparent keyword rules and
keeps ambiguous transactions in an "unclassified" bucket for human review.
"""
from collections import defaultdict
from datetime import datetime


CATEGORY_RULES = (
    ("customer_receipts", ("customer", "sales settlement", "counter sales", "upi receipt", "cash deposit")),
    ("supplier_payments", ("supplier", "wholesale", "inventory", "stock purchase", "vendor")),
    ("rent_and_utilities", ("rent", "electricity", "water bill", "broadband", "internet")),
    ("staff_costs", ("salary", "staff wages", "payroll", "employee")),
    ("debt_service", ("loan emi", "loan repayment", "term loan", "interest payment")),
    ("owner_drawings", ("owner drawing", "owner withdrawal", "cash withdrawal by owner")),
    ("tax_and_compliance", ("gst", "tax payment", "professional tax", "tds")),
    ("bank_charges", ("bank charge", "service charge", "sms charge", "processing fee")),
    ("delivery_and_travel", ("fuel", "delivery", "transport", "courier")),
)


def categorize_transaction(description):
    """Return (category, confidence); confidence is a rule-match indicator."""
    text = str(description or "").strip().lower()
    if not text:
        return "unclassified", 0.0
    for category, keywords in CATEGORY_RULES:
        if any(keyword in text for keyword in keywords):
            return category, 1.0
    return "unclassified", 0.0


def _to_amount(value):
    if value in (None, ""):
        return 0.0
    amount = float(value)
    if amount < 0:
        raise ValueError("Transaction amounts must be non-negative.")
    return amount


def analyze_transactions(transactions):
    """Summarise normalized transaction mappings.

    Required keys: description, debit, credit. Optional key: date.
    A row with both debit and credit > 0 is rejected to avoid double counting.
    """
    totals = defaultdict(float)
    monthly = defaultdict(lambda: {"inflows": 0.0, "outflows": 0.0, "count": 0})
    unclassified = []
    total_inflows = total_outflows = 0.0
    count = 0

    for index, row in enumerate(transactions):
        debit = _to_amount(row.get("debit", 0))
        credit = _to_amount(row.get("credit", 0))
        if debit and credit:
            raise ValueError(f"Transaction {index + 1} has both debit and credit.")
        description = row.get("description", "")
        category, confidence = categorize_transaction(description)
        if credit:
            total_inflows += credit
            totals[category] += credit
        elif debit:
            total_outflows += debit
            totals[category] += debit
        else:
            continue

        date_value = row.get("date")
        month = None
        if date_value:
            parsed = None
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    parsed = datetime.strptime(str(date_value), fmt)
                    break
                except ValueError:
                    continue
            if parsed is None:
                raise ValueError(f"Unsupported transaction date: {date_value}")
            month = parsed.strftime("%Y-%m")
            monthly[month]["inflows"] += credit
            monthly[month]["outflows"] += debit
            monthly[month]["count"] += 1

        if category == "unclassified":
            unclassified.append({
                "row_number": index + 1,
                "description": str(description),
                "debit": debit,
                "credit": credit,
                "date": date_value,
                "confidence": confidence,
            })
        count += 1

    return {
        "transaction_count": count,
        "total_inflows": round(total_inflows, 2),
        "total_outflows": round(total_outflows, 2),
        "net_cash_movement": round(total_inflows - total_outflows, 2),
        "category_totals": {key: round(value, 2) for key, value in sorted(totals.items())},
        "monthly": {
            key: {
                "inflows": round(value["inflows"], 2),
                "outflows": round(value["outflows"], 2),
                "net": round(value["inflows"] - value["outflows"], 2),
                "transaction_count": value["count"],
            }
            for key, value in sorted(monthly.items())
        },
        "unclassified": unclassified,
        "limitations": [
            "Keyword categories are suggestions and require human review.",
            "A bank credit is not necessarily business revenue.",
            "A bank debit is not necessarily an operating expense.",
            "Transfers between own accounts may distort totals unless identified.",
            "This statement-level summary is not a cash-flow forecast or credit decision.",
        ],
    }
