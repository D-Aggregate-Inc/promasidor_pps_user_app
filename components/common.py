import streamlit as st
import warnings
from utils.auth import signup, login, reset_password
import logging
from db.db_utils import add_user, get_regions

logging.basicConfig(level=logging.INFO)

warnings.filterwarnings('ignore')


def signup_form(role):
    with st.form("signup"):
        email = st.text_input("Email")
        phone = st.text_input("Phone Number", max_chars=11, help="11-digit phone number",placeholder="8012345678")
        password = st.text_input("Password", type="password")
        regions = get_regions()
        region_options = [r['name'] for r in regions]
        merchandiser_region = st.selectbox("Select Regions of Work", region_options)
        if st.form_submit_button("🔏Sign Up"):
            if signup(email, phone, password, role,merchandiser_region):
                st.success("Signed up! Please log in.")

def login_form():
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("🔑Log In"):
            if login(email, password):
                st.rerun()  # Refresh for role-based redirect

def reset_form():
    with st.form("reset"):
        email = st.text_input("Email")
        new_pass = st.text_input("New Password", type="password")
        if st.form_submit_button("🛠Reset"):
            if reset_password(email, new_pass):
                st.success("Password reset!")