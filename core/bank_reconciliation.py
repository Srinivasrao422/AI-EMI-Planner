"""Review-first reconciliation of bank transactions into monthly MSME figures."""
import pandas as pd

BUCKETS = (
    "Revenue", "Other income", "Direct costs", "Operating expenses",
    "Owner drawings", "Existing debt service", "Exclude / transfer",
)
CATEGORY_BUCKETS = {
    "Sales / customer receipts": "Revenue",
    "Supplier / inventory": "Direct costs",
    "Rent": "Operating expenses",
    "Utilities": "Operating expenses",
    "Loan / EMI": "Existing debt service",
    "Bank charges": "Operating expenses",
    "Taxes": "Operating expenses",
    "Cash withdrawal": "Owner drawings",
    "Uncategorised": "Exclude / transfer",
    "Other": "Exclude / transfer",
}


def suggest_financial_bucket(category):
    return CATEGORY_BUCKETS.get(str(category), "Exclude / transfer")


def build_monthly_reconciliation(transactions, period_month):
    """Aggregate a reviewed transaction frame into existing monthly-record fields.

    Credits feed income buckets; debits feed cost/expense buckets.
    Transfers are excluded. This is a bank-cash reconciliation aid, not accrual accounting.
    """
    required = {"Date", "Debit (INR)", "Credit (INR)", "Financial bucket"}
    missing = required - set(transactions.columns)
    if missing:
        raise ValueError("Missing required transaction columns: " + ", ".join(sorted(missing)))

    try:
        parsed_month = pd.Period(str(period_month), freq="M")
    except Exception as exc:
        raise ValueError("Select a valid reporting month.") from exc

    frame = transactions.copy()
    dates = pd.to_datetime(frame["Date"], errors="coerce")
    if dates.isna().any():
        raise ValueError("Every transaction must have a valid date.")
    frame = frame.loc[dates.dt.to_period("M") == parsed_month].copy()
    if frame.empty:
        raise ValueError("No transactions exist for the selected reporting month.")

    debit = pd.to_numeric(frame["Debit (INR)"], errors="coerce").fillna(0)
    credit = pd.to_numeric(frame["Credit (INR)"], errors="coerce").fillna(0)
    if (debit < 0).any() or (credit < 0).any():
        raise ValueError("Debit and credit values cannot be negative.")
    if ((debit > 0) & (credit > 0)).any():
        raise ValueError("A transaction cannot have both a debit and a credit.")

    totals = {
        "revenue": 0.0, "other_income": 0.0, "cost_of_goods_sold": 0.0,
        "operating_expenses": 0.0, "owner_drawings": 0.0,
        "existing_debt_service": 0.0,
    }
    mapping = {
        "Revenue": ("revenue", credit),
        "Other income": ("other_income", credit),
        "Direct costs": ("cost_of_goods_sold", debit),
        "Operating expenses": ("operating_expenses", debit),
        "Owner drawings": ("owner_drawings", debit),
        "Existing debt service": ("existing_debt_service", debit),
    }
    for bucket, (field, amounts) in mapping.items():
        totals[field] = round(float(amounts[frame["Financial bucket"] == bucket].sum()), 2)
    totals["period_month"] = str(parsed_month)
    totals["notes"] = "Prepared from reviewed bank statement transactions; verify classification and cash/accrual treatment."
    return totals
