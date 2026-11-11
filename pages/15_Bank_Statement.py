from pathlib import Path
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.theme import load_theme
from core.bank_statement import extract_pdf_text, normalise_transactions, read_csv_statement
from database.business_profiles import get_user_business_profiles
from utils.auth_helper import require_login


st.set_page_config(page_title="Bank Statement Intelligence | MSME Financial Platform", layout="wide")
load_theme()

if require_login():
    st.title("Bank Statement Intelligence")
    st.caption(
        "Review bank transactions, categorise cash movements and reconcile totals. "
        "All processing happens in this session; uploaded statement files are not saved."
    )

    profiles = get_user_business_profiles(st.session_state.user_id)
    if not profiles:
        st.warning("Create a business profile before analysing a statement.")
        st.page_link("pages/9_Business_Profile.py", label="Create business profile")
        st.stop()

    business_options = {
        f"{p['business_name']} — {p['city']}, {p['state']}": p["id"] for p in profiles
    }
    selected_business = st.selectbox("Business profile", list(business_options))
    st.caption(f"Selected business: {selected_business}")

    uploaded = st.file_uploader(
        "Upload bank statement",
        type=["csv", "pdf"],
        help="CSV is recommended for accurate transaction mapping. PDF support extracts selectable text for inspection.",
    )

    if uploaded is not None:
        file_bytes = uploaded.getvalue()
        if uploaded.name.lower().endswith(".pdf"):
            try:
                extracted = extract_pdf_text(file_bytes)
                st.success("Selectable PDF text extracted.")
                st.info(
                    "PDF layouts vary by bank. To avoid guessing debit/credit columns, "
                    "review the extracted text below and export the statement as CSV for transaction analysis."
                )
                st.text_area("Extracted PDF text (not saved)", extracted, height=280)
                st.download_button(
                    "Download extracted text",
                    extracted,
                    file_name="bank_statement_extracted.txt",
                    mime="text/plain",
                )
            except ValueError as exc:
                st.error(str(exc))
        else:
            try:
                raw = read_csv_statement(file_bytes)
                st.subheader("Step 1 · Map statement columns")
                columns = list(raw.columns)

                def guess(candidates):
                    for column in columns:
                        label = str(column).lower().replace("_", " ")
                        if any(token in label for token in candidates):
                            return column
                    return columns[0]

                date_col = st.selectbox("Transaction date", columns, index=columns.index(guess(["date", "txn date", "value date"])))
                desc_col = st.selectbox("Description / narration", columns, index=columns.index(guess(["description", "narration", "particular", "details", "remarks"])))
                debit_options = ["(Not present)"] + columns
                credit_options = ["(Not present)"] + columns
                balance_options = ["(Not present)"] + columns
                debit_guess = guess(["debit", "withdrawal", "paid out", "dr"])
                credit_guess = guess(["credit", "deposit", "paid in", "cr"])
                balance_guess = guess(["balance", "closing"])
                debit_default = debit_options.index(debit_guess) if debit_guess != date_col and debit_guess in debit_options else 0
                credit_default = credit_options.index(credit_guess) if credit_guess != date_col and credit_guess in credit_options else 0
                balance_default = balance_options.index(balance_guess) if balance_guess != date_col and balance_guess in balance_options else 0
                c1, c2, c3 = st.columns(3)
                with c1:
                    debit_col = st.selectbox("Debit / withdrawal", debit_options, index=debit_default)
                with c2:
                    credit_col = st.selectbox("Credit / deposit", credit_options, index=credit_default)
                with c3:
                    balance_col = st.selectbox("Balance (optional)", balance_options, index=balance_default)

                mapping = {
                    "date": date_col,
                    "description": desc_col,
                    "debit": None if debit_col == "(Not present)" else debit_col,
                    "credit": None if credit_col == "(Not present)" else credit_col,
                    "balance": None if balance_col == "(Not present)" else balance_col,
                }
                if st.button("Analyse transactions", type="primary", use_container_width=True):
                    try:
                        st.session_state["bank_statement_preview"] = normalise_transactions(raw, mapping)
                        st.session_state["bank_statement_business"] = business_options[selected_business]
                        st.success("Transactions extracted. Review categories before downloading.")
                    except ValueError as exc:
                        st.error(str(exc))

                preview = st.session_state.get("bank_statement_preview")
                if preview is not None and st.session_state.get("bank_statement_business") == business_options[selected_business]:
                    st.subheader("Step 2 · Review extracted transactions")
                    edited = st.data_editor(
                        preview,
                        use_container_width=True,
                        hide_index=True,
                        num_rows="dynamic",
                        column_config={
                            "Debit (INR)": st.column_config.NumberColumn(format="₹%.2f"),
                            "Credit (INR)": st.column_config.NumberColumn(format="₹%.2f"),
                            "Balance (INR)": st.column_config.NumberColumn(format="₹%.2f"),
                            "Category": st.column_config.SelectboxColumn(options=[
                                "Sales / customer receipts", "Supplier / inventory", "Rent",
                                "Utilities", "Loan / EMI", "Bank charges", "Taxes",
                                "Cash withdrawal", "Uncategorised", "Other",
                            ]),
                        },
                        key="bank_statement_editor",
                    )
                    total_debit = float(pd.to_numeric(edited["Debit (INR)"], errors="coerce").fillna(0).sum())
                    total_credit = float(pd.to_numeric(edited["Credit (INR)"], errors="coerce").fillna(0).sum())
                    net = total_credit - total_debit
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total credits", f"₹{total_credit:,.2f}")
                    m2.metric("Total debits", f"₹{total_debit:,.2f}")
                    m3.metric("Net movement", f"₹{net:,.2f}")
                    st.caption(
                        "Categories are keyword-based suggestions, not verified accounting classifications. "
                        "Review and edit every row. Transfers between own accounts can distort totals."
                    )
                    st.download_button(
                        "Download reviewed transactions (CSV)",
                        edited.to_csv(index=False).encode("utf-8"),
                        file_name="reviewed_bank_transactions.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                    st.info(
                        "This first release does not write bank transactions into your financial records. "
                        "Use the reviewed CSV as a reconciliation aid; manually confirm monthly figures before saving them."
                    )
            except ValueError as exc:
                st.error(str(exc))

    st.divider()
    st.subheader("Privacy and accuracy")
    st.write(
        "- Uploaded files are processed in memory and are not stored in the application database.\n"
        "- CSV transaction columns must be mapped and reviewed by you.\n"
        "- Text-based PDFs can be inspected; scanned PDFs and bank-specific PDF table parsing are not yet supported.\n"
        "- No AI model, credit score, default probability or lending decision is generated here."
    )
