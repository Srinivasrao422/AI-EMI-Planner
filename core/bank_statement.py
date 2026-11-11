"""Deterministic bank-statement parsing and categorisation helpers.

No statement data is persisted by this module. Parsing is intentionally
review-first: callers must map columns and confirm extracted transactions.
"""
from __future__ import annotations

import re
from io import BytesIO
from typing import Mapping

import pandas as pd


DATE_FORMATS = ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %b %Y", "%d-%b-%Y")
CATEGORY_RULES = {
    "Sales / customer receipts": ("upi", "neft", "imps", "rtgs", "payment received", "customer", "settlement", "pos credit"),
    "Supplier / inventory": ("supplier", "purchase", "inventory", "wholesale", "vendor", "raw material"),
    "Rent": ("rent", "lease"),
    "Utilities": ("electricity", "water bill", "internet", "broadband", "mobile bill"),
    "Loan / EMI": ("emi", "loan repayment", "term loan", "interest debit"),
    "Bank charges": ("bank charge", "service charge", "sms charge", "gst on charge"),
    "Taxes": ("gst", "income tax", "tds", "tax payment"),
    "Cash withdrawal": ("atm", "cash withdrawal", "self transfer"),
}


def categorise_description(description: str) -> str:
    """Assign a transparent keyword category; unmatched items stay uncategorised."""
    value = str(description or "").lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in value for keyword in keywords):
            return category
    return "Uncategorised"


def _amount(value):
    if pd.isna(value) or str(value).strip() == "":
        return 0.0
    text = str(value).strip().replace(",", "").replace("₹", "").replace("INR", "")
    text = text.replace("(", "-").replace(")", "")
    text = re.sub(r"[^0-9.\\-]", "", text)
    try:
        result = float(text or 0)
    except ValueError as exc:
        raise ValueError(f"Cannot interpret amount: {value}") from exc
    if result < 0:
        raise ValueError("Map debit and credit columns as positive amounts.")
    return round(result, 2)


def normalise_transactions(frame: pd.DataFrame, mapping: Mapping[str, str]) -> pd.DataFrame:
    """Convert user-mapped statement columns into a consistent transaction table."""
    required = ("date", "description")
    for field in required:
        column = mapping.get(field)
        if not column or column not in frame.columns:
            raise ValueError(f"Select a valid {field} column.")

    rows = []
    for _, row in frame.iterrows():
        raw_date = str(row[mapping["date"]]).strip()
        parsed = pd.to_datetime(raw_date, dayfirst=True, errors="coerce")
        if pd.isna(parsed):
            continue
        debit = _amount(row[mapping["debit"]]) if mapping.get("debit") in frame.columns else 0.0
        credit = _amount(row[mapping["credit"]]) if mapping.get("credit") in frame.columns else 0.0
        if debit and credit:
            raise ValueError("A transaction cannot have both debit and credit amounts. Review the column mapping.")
        description = str(row[mapping["description"]]).strip()
        if not description or description.lower() == "nan":
            continue
        balance = None
        if mapping.get("balance") in frame.columns:
            balance = _amount(row[mapping["balance"]])
        rows.append({
            "Date": parsed.date().isoformat(),
            "Description": description,
            "Debit (INR)": debit,
            "Credit (INR)": credit,
            "Balance (INR)": balance,
            "Category": categorise_description(description),
        })

    result = pd.DataFrame(rows, columns=[
        "Date", "Description", "Debit (INR)", "Credit (INR)", "Balance (INR)", "Category"
    ])
    if result.empty:
        raise ValueError("No transactions could be read. Check the date column and file format.")
    return result.sort_values("Date", kind="stable").reset_index(drop=True)


def read_csv_statement(file_bytes: bytes) -> pd.DataFrame:
    """Read a CSV statement without retaining the uploaded file."""
    try:
        frame = pd.read_csv(BytesIO(file_bytes))
    except Exception as exc:
        raise ValueError("Could not read this CSV. Export it again as a standard comma-separated file.") from exc
    if frame.empty or len(frame.columns) < 2:
        raise ValueError("The CSV does not contain a usable transaction table.")
    return frame


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract selectable text from a PDF; scanned image PDFs need OCR first."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(file_bytes))
        text = "\\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise ValueError("Could not read this PDF. Check that it is a valid, unencrypted PDF.") from exc
    if not text.strip():
        raise ValueError("No selectable text found. This may be a scanned PDF; export it as CSV or OCR it first.")
    return text


def build_monthly_reconciliation(transactions: pd.DataFrame, period_month: str) -> dict:
    """Aggregate reviewed transactions into a draft monthly record.

    Uncategorised transactions are deliberately excluded. The caller must
    review category assignments and explicitly confirm before saving.
    """
    import re
    from datetime import date

    try:
        parsed_month = date.fromisoformat(str(period_month).strip() + "-01")
    except ValueError as exc:
        raise ValueError("Reporting month must use YYYY-MM format.") from exc
    month = parsed_month.strftime("%Y-%m")
    if month != str(period_month).strip():
        raise ValueError("Reporting month must use YYYY-MM format.")

    required = {"Date", "Debit (INR)", "Credit (INR)", "Category"}
    missing = required - set(transactions.columns)
    if missing:
        raise ValueError("Transaction table is missing: " + ", ".join(sorted(missing)))

    dates = pd.to_datetime(transactions["Date"], errors="coerce")
    selected = transactions.loc[dates.dt.strftime("%Y-%m") == month].copy()
    if selected.empty:
        raise ValueError("No reviewed transactions were found for the selected month.")

    debit = pd.to_numeric(selected["Debit (INR)"], errors="coerce").fillna(0)
    credit = pd.to_numeric(selected["Credit (INR)"], errors="coerce").fillna(0)
    if (debit < 0).any() or (credit < 0).any():
        raise ValueError("Debit and credit values must be non-negative.")

    category = selected["Category"].astype(str)
    sums = lambda mask, values: round(float(values[mask].sum()), 2)
    sales = sums(category.eq("Sales / customer receipts"), credit)
    other_income = sums(category.eq("Other income"), credit)
    supplier = sums(category.eq("Supplier / inventory"), debit)
    rent = sums(category.eq("Rent"), debit)
    utilities = sums(category.eq("Utilities"), debit)
    bank_charges = sums(category.eq("Bank charges"), debit)
    taxes = sums(category.eq("Taxes"), debit)
    other_expenses = sums(category.eq("Other operating expense"), debit)
    owner_drawings = sums(category.eq("Owner drawings"), debit)
    debt = sums(category.eq("Loan / EMI"), debit)

    included_categories = {
        "Sales / customer receipts", "Other income", "Supplier / inventory",
        "Rent", "Utilities", "Bank charges", "Taxes",
        "Other operating expense", "Owner drawings", "Loan / EMI",
    }
    ignored = int((~category.isin(included_categories)).sum())
    return {
        "period_month": month,
        "revenue": sales,
        "other_income": other_income,
        "cost_of_goods_sold": supplier,
        "operating_expenses": round(rent + utilities + bank_charges + taxes + other_expenses, 2),
        "owner_drawings": owner_drawings,
        "existing_debt_service": debt,
        "notes": "Drafted from user-reviewed bank statement transactions. Verify cash, non-bank transactions and classifications.",
        "transaction_count": int(len(selected)),
        "uncategorised_count": ignored,
        "included_debits": round(supplier + rent + utilities + bank_charges + taxes + other_expenses + owner_drawings + debt, 2),
        "included_credits": round(sales + other_income, 2),
    }
