from pathlib import Path
import sys

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.theme import load_theme
from database.models import create_tables
from database.business_profiles import (
    delete_business_profile,
    get_user_business_profiles,
    save_business_profile,
)
from utils.auth_helper import require_login


st.set_page_config(page_title="Business Profile | MSME Financial Platform", layout="wide")
load_theme()
create_tables()

if require_login():
    user_id = st.session_state.user_id

    st.title("MSME Business Profile")
    st.caption(
        "Create and manage business profiles. You can maintain more than one "
        "business under the same account."
    )

    with st.form("business_profile_form", clear_on_submit=True):
        st.subheader("Business details")
        business_name = st.text_input("Business name *")
        col1, col2 = st.columns(2)
        with col1:
            business_type = st.selectbox(
                "Business type *",
                ["Proprietorship", "Partnership", "LLP", "Private Limited",
                 "Public Limited", "Self Help Group", "Other"],
            )
            industry = st.selectbox(
                "Industry *",
                ["Agriculture", "Manufacturing", "Retail", "Wholesale / Distribution",
                 "Food Processing", "Services", "Transport / Logistics",
                 "Technology", "Construction", "Other"],
            )
            registration_type = st.selectbox(
                "Registration type",
                ["Not registered / Not specified", "Udyam", "GST", "Company / LLP",
                 "Other"],
            )
            registration_number = st.text_input(
                "Registration number (optional)",
                help="Avoid entering sensitive personal identity numbers.",
            )
        with col2:
            city = st.text_input("City / Town *")
            state = st.text_input("State *")
            country = st.text_input("Country", value="India")
            started_year = st.number_input(
                "Business start year (optional)",
                min_value=1800,
                max_value=2100,
                value=2020,
                step=1,
            )
            year_unknown = st.checkbox("I don't know the start year")

        submitted = st.form_submit_button("Save Business Profile", use_container_width=True)
        if submitted:
            profile_data = {
                "business_name": business_name,
                "business_type": business_type,
                "industry": industry,
                "registration_type": (
                    "" if registration_type == "Not registered / Not specified"
                    else registration_type
                ),
                "registration_number": registration_number,
                "city": city,
                "state": state,
                "country": country,
                "started_year": None if year_unknown else int(started_year),
            }
            try:
                save_business_profile(user_id, profile_data)
                st.success("Business profile saved successfully.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.divider()
    st.subheader("Your businesses")
    profiles = get_user_business_profiles(user_id)

    if not profiles:
        st.info("No business profiles yet. Add your first business using the form above.")
    else:
        for profile in profiles:
            with st.container(border=True):
                col_info, col_action = st.columns([5, 1])
                with col_info:
                    st.markdown(f"**{profile['business_name']}**")
                    st.caption(
                        f"{profile['business_type']} · {profile['industry']} · "
                        f"{profile['city']}, {profile['state']}, {profile['country']}"
                    )
                    if profile["registration_type"]:
                        st.write(f"Registration: {profile['registration_type']}")
                    if profile["started_year"]:
                        st.write(f"Started: {profile['started_year']}")
                with col_action:
                    confirm_key = f"confirm_delete_business_{profile['id']}"
                    if st.button("Delete", key=f"delete_business_{profile['id']}"):
                        st.session_state[confirm_key] = True
                    if st.session_state.get(confirm_key):
                        st.warning("Delete this business profile?")
                        yes_col, no_col = st.columns(2)
                        with yes_col:
                            if st.button("Confirm", key=f"confirm_{profile['id']}"):
                                if delete_business_profile(user_id, profile["id"]):
                                    st.success("Profile deleted.")
                                st.session_state.pop(confirm_key, None)
                                st.rerun()
                        with no_col:
                            if st.button("Cancel", key=f"cancel_{profile['id']}"):
                                st.session_state.pop(confirm_key, None)
                                st.rerun()
