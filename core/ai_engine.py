"""Groq-backed explanation layer for recorded financial information.

The model must distinguish recorded facts, calculations, assumptions and missing data.
It must never invent financial metrics or present output as a credit decision.
"""
import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def get_groq_client():
    """Return a Groq client when a non-placeholder API key is configured."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or not api_key.strip() or api_key.strip().lower().startswith("your_"):
        return None
    try:
        return Groq(api_key=api_key.strip())
    except Exception:
        return None


def _format_value(value):
    return "Not recorded" if value is None else str(value)


def build_financial_system_prompt(financial_data):
    """Build an evidence-bounded prompt from supplied application data."""
    loan_fields = (
        "loan_amount", "interest_rate", "tenure", "monthly_income",
        "monthly_emi", "total_interest", "total_payment", "risk_level",
        "credit_score", "financial_health", "approval_status",
    )
    recorded_loan = {
        field: _format_value(financial_data.get(field))
        for field in loan_fields
    }
    msme_context = financial_data.get("msme_context")
    context_json = json.dumps(msme_context, ensure_ascii=False, default=str) if msme_context else "No business profile context supplied."

    return f"""
You are an evidence-bounded MSME financial planning assistant.

STRICT RULES:
- Use only the facts and figures in the supplied application context and the user's current question.
- Never invent revenue, expenses, balances, credit scores, ratios, forecasts, approvals, dates or transaction details.
- If a figure is missing, say "not recorded" and state what input is needed.
- Distinguish recorded values from calculations, assumptions and general suggestions.
- When explaining a calculation, show the formula and the supplied inputs.
- Do not call a rule-based indicator a credit score, default probability, bank rating or lender decision.
- Do not claim a loan is approved or guaranteed. This application is not a lender.
- Do not treat bank credits as automatically being sales or bank debits as automatically being expenses.
- Give practical, specific answers. Avoid generic motivational language, filler, exaggerated claims and fabricated insights.
- If the question cannot be answered from available data, explain the limitation instead of guessing.
- Keep the response concise and use clear Markdown.

LATEST SAVED LOAN CALCULATION (missing fields are not recorded):
{json.dumps(recorded_loan, ensure_ascii=False)}

BUSINESS PROFILE AND LATEST THREE SAVED MONTHS:
{context_json}
"""


def ask_ai_advisor(financial_data, user_message, chat_history=None):
    """Generate an explanation grounded in the supplied financial context."""
    client = get_groq_client()
    if not client:
        return "Groq API key is not configured. Add GROQ_API_KEY to your local .env file to enable the assistant."

    chat_history = chat_history or []
    messages = [{
        "role": "system",
        "content": build_financial_system_prompt(financial_data),
    }]
    for message in chat_history[-8:]:
        role = message.get("role")
        content = message.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            messages.append({"role": role, "content": content[:4000]})
    messages.append({"role": "user", "content": str(user_message)[:4000]})

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.2,
            max_tokens=800,
        )
        return response.choices[0].message.content or "The assistant returned an empty response. Please try again."
    except Exception:
        return "The AI service is temporarily unavailable. Please try again later."
