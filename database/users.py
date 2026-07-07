"""
=====================================================
User Authentication Manager
Project : AI Powered EMI Planner
Purpose:
Manage user records, registration, and logins using SQLite
=====================================================
"""

import hashlib
import os
import streamlit as st
from database.connection import get_connection

# -----------------------------
# PASSWORD SECURITY
# -----------------------------

def hash_password(password: str) -> str:
    """Hash password using PBKDF2 with a random salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}:{key.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against stored salt and key."""
    if not hashed:
        return False
    try:
        salt_hex, key_hex = hashed.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        actual_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return expected_key == actual_key
    except Exception:
        return False


# -----------------------------
# USER ACTIONS
# -----------------------------

def create_user(full_name, email, password, confirm_password):
    """Register a new user after verifying fields, password match and email uniqueness."""
    full_name = full_name.strip()
    email = email.strip().lower()
    
    # Empty fields check
    if not full_name or not email or not password or not confirm_password:
        raise ValueError("All fields are required. Please fill in all text inputs.")
        
    # Password confirmation check
    if password != confirm_password:
        raise ValueError("Password confirmation does not match the entered password.")
        
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Duplicate email check
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            raise ValueError("An account with this email address already exists.")
            
        hashed = hash_password(password)
        cursor.execute(
            "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
            (full_name, email, hashed)
        )
        conn.commit()
        user_id = cursor.lastrowid
    finally:
        conn.close()
        
    return user_id


def login_user(email, password):
    """Verify login credentials and establish streamlit session state variables."""
    email = email.strip().lower()
    
    if not email or not password:
        return False
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, email, password_hash FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        user_id, full_name, user_email, hashed = row
        if verify_password(password, hashed):
            # Save required session variables
            st.session_state["authenticated"] = True
            st.session_state["user_id"] = user_id
            st.session_state["username"] = full_name
            st.session_state["email"] = user_email
            return True
            
    return False


def logout_user():
    """Clear all authentication state variables from st.session_state."""
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = None
    st.session_state["username"] = None
    st.session_state["email"] = None
    st.session_state["state_synced"] = False
    # Reset chat history on logout
    if "messages" in st.session_state:
        del st.session_state.messages
