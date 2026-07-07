"""
====================================================
Financial Advisor Engine (Wrapper)
Project : AI Powered EMI Planner
====================================================
"""

from core.ai_engine import ask_ai_advisor

def generate_ai_advice(financial_data):
    # Backward compatibility helper that delegates to core/ai_engine.py
    return ask_ai_advisor(financial_data, "Provide comprehensive loan advice and suggestions based on my profile.")