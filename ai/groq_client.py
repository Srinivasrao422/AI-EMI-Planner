"""
====================================================
Groq AI Client (Safe Wrapper)
Project : AI Powered EMI Planner
====================================================
"""

import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Safely initialize client to avoid import-time crashes
api_key = os.getenv("GROQ_API_KEY")
client = None
if api_key and not api_key.startswith("your_") and api_key.strip() != "":
    try:
        client = Groq(api_key=api_key)
    except Exception:
        pass

def ask_groq(prompt):
    if not client:
        return "⚠️ Warning: Groq API Key is missing or invalid. Please configure GROQ_API_KEY in your .env file."
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional AI financial advisor.\n\n"
                        "Provide practical, safe and clear financial guidance.\n\n"
                        "Focus on:\n"
                        "- EMI affordability\n"
                        "- Loan planning\n"
                        "- Risk reduction\n"
                        "- Savings improvement\n\n"
                        "Never guarantee loan approval."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,
            max_tokens=700
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI service unavailable. Error: {e}"