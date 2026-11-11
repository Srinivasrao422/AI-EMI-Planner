"""Application entry point.

Unauthenticated visitors see the login/register screen.
Authenticated users are sent directly to the MSME dashboard.
"""

import streamlit as st

from components.theme import load_theme
from database.models import create_tables
from utils.auth_helper import require_login
from utils.state_manager import init_state


st.set_page_config(
    page_title="MSME Credit & Financial Risk Platform",
    layout="wide",
)

init_state()
create_tables()
load_theme()

if require_login():
    # The dashboard is the authenticated landing page.
    # Avoid showing a redundant welcome/intermediate screen after login.
    st.switch_page("pages/1_Home.py")
