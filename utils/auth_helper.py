"""
Authentication helpers and sidebar navigation for the MSME platform.
"""

import streamlit as st

from database.users import login_user, create_user, logout_user
from utils.state_manager import init_state


def render_auth_pages():
    """Render a clean, responsive login and registration experience."""
    init_state()

    if "auth_page" not in st.session_state:
        st.session_state["auth_page"] = "login"

    st.markdown(
        """
        <style>
        .auth-intro {
            min-height: 420px;
            padding: 2.4rem;
            border-radius: 18px;
            color: #F8FAFC;
            background: linear-gradient(145deg, #101B35 0%, #1E3A70 100%);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 16px 36px rgba(15, 23, 42, .12);
        }
        .auth-eyebrow {
            color: #BFDBFE;
            font-size: .72rem;
            font-weight: 700;
            letter-spacing: .16em;
            text-transform: uppercase;
        }
        .auth-intro h1 {
            color: #FFFFFF !important;
            font-size: clamp(2rem, 3vw, 2.8rem) !important;
            line-height: 1.12;
            margin: 1.2rem 0 .9rem 0;
        }
        .auth-intro p { color: #DCE7F7; line-height: 1.7; }
        .auth-feature {
            border-top: 1px solid rgba(255,255,255,.18);
            padding: .8rem 0;
            color: #F8FAFC;
            font-size: .92rem;
        }
        .auth-footnote {
            color: #64748B;
            font-size: .78rem;
            line-height: 1.6;
            margin-top: 1rem;
        }
        @media (max-width: 800px) {
            .auth-intro { min-height: 260px; padding: 1.5rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        st.markdown(
            """
            <section class="auth-intro">
                <div>
                    <div class="auth-eyebrow">MSME FINANCIAL WORKSPACE</div>
                    <h1>Make business finances easier to understand.</h1>
                    <p>
                        Keep your business records, review repayment capacity
                        and test how changing conditions affect monthly cash headroom.
                    </p>
                </div>
                <div>
                    <div class="auth-feature">01&nbsp;&nbsp; Business profiles and monthly records</div>
                    <div class="auth-feature">02&nbsp;&nbsp; EMI planning and repayment schedules</div>
                    <div class="auth-feature">03&nbsp;&nbsp; Financial health and resilience scenarios</div>
                </div>
            </section>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.write("")
        st.write("")
        if st.session_state["auth_page"] == "login":
            st.markdown("### Sign in")
            st.caption("Access your MSME financial workspace.")

            with st.form("msme_login_form"):
                email = st.text_input(
                    "Email address",
                    placeholder="name@business.com",
                    key="login_email",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password",
                )
                submitted = st.form_submit_button(
                    "Sign in",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                if not email.strip() or not password:
                    st.error("Enter both your email address and password.")
                elif login_user(email, password):
                    st.rerun()
                else:
                    st.error("Email or password is incorrect.")

            st.markdown(
                '<div class="auth-footnote">Your existing account and saved records remain unchanged.</div>',
                unsafe_allow_html=True,
            )
            if st.button("Create a new account", use_container_width=True):
                st.session_state["auth_page"] = "register"
                st.rerun()

        else:
            st.markdown("### Create your account")
            st.caption("Set up secure access to your financial workspace.")

            with st.form("msme_register_form"):
                full_name = st.text_input(
                    "Full name",
                    placeholder="Your name",
                    key="reg_fullname",
                )
                email = st.text_input(
                    "Email address",
                    placeholder="name@business.com",
                    key="reg_email",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="At least 6 characters",
                    key="reg_password",
                )
                confirm_password = st.text_input(
                    "Confirm password",
                    type="password",
                    placeholder="Re-enter your password",
                    key="reg_confirm",
                )
                submitted = st.form_submit_button(
                    "Create account",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                try:
                    create_user(full_name, email, password, confirm_password)
                    st.success("Account created. You can now sign in.")
                    st.session_state["auth_page"] = "login"
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
                except Exception:
                    st.error("Account creation failed. Please try again.")

            st.markdown(
                '<div class="auth-footnote">Already registered?</div>',
                unsafe_allow_html=True,
            )
            if st.button("Back to sign in", use_container_width=True):
                st.session_state["auth_page"] = "login"
                st.rerun()


def render_custom_sidebar():
    """Render the application sidebar and authenticated navigation."""
    with st.sidebar:
        st.markdown(
            """
            <div style="padding:.5rem 0 1.5rem 0;">
                <h2 style="font-size:1.35rem;line-height:1.2;margin:0;">
                    MSME Financial Platform
                </h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.get("authenticated", False):
            full_name = st.session_state.get("username", "User")
            email = st.session_state.get("email", "")

            st.markdown(
                f"""
                <div style="background:var(--card);border:1px solid var(--border);
                    border-radius:10px;padding:1rem;margin-bottom:1.25rem;">
                    <div style="font-weight:700;">{full_name}</div>
                    <div style="font-size:.78rem;color:var(--muted);overflow-wrap:anywhere;">
                        {email}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption("NAVIGATION")
            st.page_link("pages/1_Home.py", label="Dashboard")
            st.page_link("pages/2_EMI_Calculator.py", label="EMI Calculator")
            st.page_link("pages/3_Repayment.py", label="Repayment")
            st.page_link("pages/4_Comparison.py", label="Comparison")
            st.page_link("pages/5_Risk_Analysis.py", label="Risk Analysis")
            st.page_link("pages/6_AI_Assistant.py", label="AI Assistant")
            st.page_link("pages/8_History.py", label="Loan History")
            st.page_link("pages/9_Business_Profile.py", label="MSME Business Profiles")
            st.page_link("pages/10_Financial_Records.py", label="Monthly Financial Records")
            st.page_link("pages/11_Financial_Health.py", label="MSME Financial Health")
            st.page_link("pages/12_Resilience_Twin.py", label="Financial Resilience Twin")
            st.divider()

            if st.button("Logout", use_container_width=True, key="logout_button"):
                logout_user()
                st.rerun()
        else:
            st.caption("BUSINESS CREDIT & FINANCIAL RISK WORKSPACE")


def require_login():
    """Enforce authentication and synchronize the latest saved loan once."""
    init_state()
    render_custom_sidebar()

    if not st.session_state.get("authenticated", False):
        render_auth_pages()
        st.stop()
        return False

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
                    payment=latest["total_payment"],
                )
                st.session_state.risk_level = latest["risk_level"]
        except Exception as error:
            print(f"Error syncing session state: {error}")
        finally:
            st.session_state["state_synced"] = True

    return True
