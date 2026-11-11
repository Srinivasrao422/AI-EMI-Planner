# AI-Powered MSME Credit Assessment & Financial Risk Analysis Platform

A Streamlit-based MSME financial decision-support platform. Current capabilities include multi-business profile management, EMI and repayment planning, loan comparison, affordability review, risk indicators, and AI-assisted financial guidance.

The MSME Financial Resilience Twin, detailed cash-flow timing records, and advanced credit assessment workflows are planned additions; they are not yet implemented.

## Current scope

- MSME business profiles: multiple profiles per user, with ownership checks.
- Monthly financial records: one record per business per month, with revenue, other income, direct costs, operating expenses, owner drawings and existing debt service.
- Transparent monthly operating-surplus and cash-headroom calculations.
- EMI calculator and repayment schedule.
- Loan comparison and rule-based affordability/risk review.
- AI-assisted financial guidance.
- Existing loan history.

Risk outputs are decision-support indicators, not a bank credit decision or loan approval.

## Architecture

- `app.py` provides the root Streamlit entry point.
- `pages/` contains Streamlit pages with one workflow per file.
- `components/` contains reusable UI components only.
- `core/` contains business calculations and should remain UI-free.
- `utils/` contains shared utility helpers.
- `assets/style.css` contains the global Streamlit theme.

## Run Locally

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

## Verify

```powershell
python -m compileall app.py components pages core utils
.\.venv\Scripts\python.exe test_repayment.py
.\.venv\Scripts\python.exe test_emi.py
.\.venv\Scripts\python.exe test_dataframe.py
.\.venv\Scripts\python.exe test_comparison.py
.\.venv\Scripts\python.exe test_affordability.py
.\.venv\Scripts\python.exe test_risk.py
```

## Notes

The `core` package owns financial business logic. UI refactors should not
change formulas, thresholds, or return contracts without a dedicated business
logic review.
