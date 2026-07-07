"""
====================================================
AI Prompt Engine
Project : AI Powered EMI Planner
Author  : Srinivas Rao
====================================================
"""


def create_financial_prompt(data):


    prompt = f"""

Analyze this user's financial profile.


Loan Details:

Loan Amount:
₹{data['loan_amount']}


Monthly EMI:
₹{data['monthly_emi']}


Interest Rate:
{data['interest_rate']}%


Loan Tenure:
{data['tenure']} years


Monthly Income:
₹{data['monthly_income']}


Risk Level:
{data['risk_level']}


Credit Score:
{data['credit_score']}



Give:

1. EMI affordability analysis

2. Risk explanation

3. Loan improvement suggestions

4. Saving advice

5. Final recommendation


Answer like a professional financial advisor.

Keep response simple.

"""


    return prompt