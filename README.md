# AI Powered EMI Planner

A Streamlit-based FinTech dashboard for EMI calculation, repayment planning,
loan comparison, affordability review, and AI-style financial guidance.

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
