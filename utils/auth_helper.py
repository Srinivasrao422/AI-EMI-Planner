"""
=====================================================
Authentication Helper & Sidebar Navigation
Project : AI Powered EMI Planner
Purpose:
Manage login/register screens, sidebar navigation and page protection
=====================================================
"""

import streamlit as st
from database.users import login_user, create_user, logout_user
from utils.state_manager import init_state

def render_auth_pages():
    """Render the classic banking login/register forms centered."""
    init_state()
    
    if "auth_page" not in st.session_state:
        st.session_state["auth_page"] = "login"

    # Main centered card layout
    st.markdown(
        """
        <div style="max-width: 440px; margin: 3rem auto; padding: 2.5rem; background-color: var(--card); border-radius: 12px; box-shadow: var(--shadow); border: 1px solid var(--border);">
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1 style="color: var(--text); font-size: 2rem; font-weight: 700; margin: 0; font-family: 'Outfit', sans-serif;">AI EMI Planner</h1>
                <p style="color: var(--muted); font-size: 0.9rem; margin-top: 0.25rem;">Secure Financial Dashboard Portal</p>
            </div>
        """,
        unsafe_allow_html=True
    )

    if st.session_state["auth_page"] == "login":
        st.subheader("Login")
        email = st.text_input("Email", placeholder="name@domain.com", key="login_email")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
        
        st.write("")
        if st.button("Login", type="primary", use_container_width=True):
            if not email or not password:
                st.error("Please fill in both email and password fields.")
            else:
                success = login_user(email, password)
                if success:
                    st.success("Successfully logged in!")
                    st.rerun()
                else:
                    st.error("Invalid email or password.")
        
        st.write("")
        if st.button("Create Account", use_container_width=True, key="switch_to_register"):
            st.session_state["auth_page"] = "register"
            st.rerun()

    else:  # register page
        st.subheader("Register")
        full_name = st.text_input("Full Name", placeholder="John Doe", key="reg_fullname")
        email = st.text_input("Email", placeholder="john@example.com", key="reg_email")
        password = st.text_input("Password", type="password", placeholder="At least 6 characters", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="reg_confirm")
        
        st.write("")
        if st.button("Register Now", type="primary", use_container_width=True):
            try:
                create_user(full_name, email, password, confirm_password)
                st.success("Registration successful! You can now log in.")
                st.session_state["auth_page"] = "login"
                st.rerun()
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Error during registration: {e}")
                
        st.write("")
        if st.button("Already have an account? Sign In", use_container_width=True, key="switch_to_login"):
            st.session_state["auth_page"] = "login"
            st.rerun()

    # Close card div
    st.markdown("</div>", unsafe_allow_html=True)


def render_custom_sidebar():
    """Render the sidebar profile details and page links in the sidebar."""
    with st.sidebar:
        # Title of the application in sidebar
        st.markdown(
            """
            <div style="padding: 0.5rem 0; margin-bottom: 1.5rem; text-align: left;">
                <h2 style="color: var(--text); font-size: 1.4rem; font-weight: 700; margin: 0; font-family: 'Outfit', sans-serif;">AI EMI Planner</h2>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.session_state.get("authenticated", False):
            # User profile card
            full_name = st.session_state.get("username", "User")
            email = st.session_state.get("email", "")
            
            st.markdown(
                f"""
                <div style="background-color: var(--card); border-radius: 8px; padding: 1rem; color: var(--text); margin-bottom: 1.5rem; text-align: left; border: 1px solid var(--border); box-shadow: var(--shadow);">
                    <div style="font-weight: 600; font-size: 1.05rem; font-family: 'Outfit', sans-serif; color: var(--text);">{full_name}</div>
                    <div style="font-size: 0.85rem; color: var(--muted); margin-top: 0.2rem; word-break: break-all;">{email}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            st.markdown("<p style='font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: var(--muted); margin-bottom: 0.5rem;'>Navigation</p>", unsafe_allow_html=True)
            
            # Pages list - Emojis removed
            st.page_link("pages/1_Home.py", label="Dashboard")
            st.page_link("pages/2_EMI_Calculator.py", label="EMI Calculator")
            st.page_link("pages/3_Repayment.py", label="Repayment")
            st.page_link("pages/4_Comparison.py", label="Comparison")
            st.page_link("pages/5_Risk_Analysis.py", label="Risk Analysis")
            st.page_link("pages/6_AI_Assistant.py", label="AI Assistant")
            st.page_link("pages/8_History.py", label="History")
            
            st.divider()
            
            # Logout
            if st.button("Logout", use_container_width=True, key="logout_button"):
                logout_user()
                st.rerun()
        else:
            # Before login: Only show: Login/Register
            st.markdown(
                """
                <div style="background-color: var(--card); border-radius: 8px; padding: 1rem; color: var(--text); margin-bottom: 1.5rem; text-align: center; border: 1px solid var(--border);">
                    <div style="font-size: 1rem; font-weight: 600; font-family: 'Outfit', sans-serif;">Login/Register</div>
                </div>
                """,
                unsafe_allow_html=True
            )


def require_login():
    """Enforce login requirement on pages."""
    init_state()
    
    # Render sidebar before checking login, to handle unauthenticated sidebar contents
    render_custom_sidebar()
    
    if not st.session_state.get("authenticated", False):
        render_auth_pages()
        st.stop()
        return False
        
    # Sync session state with SQLite latest record if not done in this session
    if not st.session_state.get("state_synced", False):
        try:
            from database.loan_history import get_latest_loan
            from utils.state_manager import save_emi_data
            latest = get_latest_loan(st.session_state.user_id)
            if latest:
                save_emi_data(
                    loan_amount=latest["loan_amount"],
                    interest_rate=latest["interest_rate"],
                    tenure=latest["tenure"],
                    income=latest["monthly_income"],
                    emi=latest["monthly_emi"],
                    interest=latest["total_interest"],
                    payment=latest["total_payment"]
                )
                st.session_state.risk_level = latest["risk_level"]
        except Exception as e:
            print(f"Error syncing session state: {e}")
        finally:
            st.session_state["state_synced"] = True
        
    return True
