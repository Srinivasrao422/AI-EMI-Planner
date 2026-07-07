"""
==========================================
Groq AI Engine
AI Powered EMI Planner
==========================================
"""

import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

def get_groq_client():
    """Safe retrieval of Groq client. Returns None if API key is missing or invalid."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        # Check for empty or generic placeholder values
        if api_key.strip() == "" or api_key.startswith("your_"):
            return None
        return Groq(api_key=api_key)
    except Exception:
        return None

def ask_ai_advisor(financial_data, user_message, chat_history=None):
    """
    Generate conversational advice based on the user's financial profile.
    """
    client = get_groq_client()
    if not client:
        return "⚠️ Warning: Groq API Key is missing. Please configure GROQ_API_KEY in your .env file to enable the AI Advisor."

    if chat_history is None:
        chat_history = []

    # Format values for readability
    loan_amount = financial_data.get('loan_amount', 0.0)
    interest_rate = financial_data.get('interest_rate', 0.0)
    tenure = financial_data.get('tenure', 0)
    monthly_income = financial_data.get('monthly_income', 0.0)
    monthly_emi = financial_data.get('monthly_emi', 0.0)
    risk_level = financial_data.get('risk_level', 'Pending')
    credit_score = financial_data.get('credit_score', 300)
    financial_health = financial_data.get('financial_health', 0)
    approval_status = financial_data.get('approval_status', 'Pending')

    system_prompt = f"""
You are a professional AI financial advisor. 
Provide practical, safe, and clear financial guidance.
Never guarantee loan approval or make legally binding promises.

Here is the user's current financial profile:
- Loan Amount: INR {loan_amount:,.2f}
- Interest Rate: {interest_rate}%
- Tenure: {tenure} years
- Monthly Income: INR {monthly_income:,.2f}
- Monthly EMI: INR {monthly_emi:,.2f}
- Risk Level: {risk_level}
- Credit Score: {credit_score}
- Financial Health Score: {financial_health}%
- Current Approval Status: {approval_status}

Address the user's queries regarding:
1. EMI suggestions (how to optimize/lower monthly EMI)
2. Loan advice (whether the loan is affordable, loan types)
3. Repayment advice (prepayment strategies, tenure adjustments)
4. Risk explanation (why they got their specific risk level or status)

Provide answers formatted in beautiful, readable Markdown. Keep advice highly personalized to the profile above.
"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.6,
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI service error: {str(e)}"
