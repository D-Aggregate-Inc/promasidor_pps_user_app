import streamlit as st
from datetime import date
from utils.auth import logout
import warnings
from components.common import signup_form, login_form, reset_form
import logging

logging.basicConfig(filename='app.log', level=logging.ERROR)

warnings.filterwarnings('ignore')

st.set_page_config(
page_title="Promassidor Perfect Store®️",
page_icon="🏬",
layout="wide",
initial_sidebar_state="expanded",
menu_items={
'Get Help': 'https://d-aggregate.com/',
'Report a bug': None,
'About':None
}
)
st.html("""<head>
<meta name="viewport" content="width=device-width,initial-scale=1,shrink-to-fit=no">
</head>""")

# st.context.cookies
# st.markdown("""<script>
#     async src = "https://platform.twitter.com/widgets.js"
#     charset = "utf-8" >
# </script>""",unsafe_allow_html=True)
#set the css styling sheet 
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

coy_logo="data:image/png;base64,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"
coy_logo2="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSYV4MC8OOMiWO5VLq4c2ad8RHZryFF_pV4Eg&s"
st.logo(coy_logo,link=None,icon_image=coy_logo2,size="large")

st.subheader(f""":orange[RetailScope®️] :blue[Promasidor Perfect Store Management System]""")

# if 'logout' not in st.session_state:
#     st.session_state['logout'] = False
# def logout():
#     st.session_state['user'] = None
#     st.session_state['logout'] = True
#     st.rerun()
# --- PAGE SETUP ---
admin= st.Page(
    "views/admin.py",
    title="Admin Panel",
    icon=":material/manage_accounts:",
    default=True,
)
builders = st.Page(
    "views/builders_deploy.py",
    title="Builders Deployment",
    icon=":material/deployed_code_account:",
)
msl_sos = st.Page(
    "views/merchandiser_msl_sos.py",
    title="MSL/Share of Shelf Tracking",
    icon=":material/shelves:",
)
outlet_onboarding = st.Page(
    "views/merchandiser_onboard.py",
    title="Outlet Onboarding",
    icon=":material/add_business:",
)
oos = st.Page(
    "views/merchandiser_oos.py",
    title="OOS Tracking",
    icon=":material/production_quantity_limits:",
)

order = st.Page(
    "views/merchandiser_order.py",
    title="Order Generation",
    icon=":material/orders:",
)

pricing = st.Page(
    "views/merchandiser_expiry.py",
    title="Price Complaince Tracking",
    icon=":material/timer_off:",
)

# CURRENT_MONTH = date.today().month  # Based on Aug 25, 2025, month=8; adjust logic as needed (e.g., if project starts in month 1)

if 'user' not in st.session_state:
    tab1, tab2, tab3 = st.tabs(["Login", "Signup", "Reset Password"])
    with tab1:
        login_form()
    with tab2:
        role = st.selectbox("Role", ["Merchandiser", "Builder"])  # Admin manual
        signup_form(role)
    with tab3:
        reset_form()
else:
    user = st.session_state['user']
    st.sidebar.button("🔐Logout", on_click=logout)
    # st.sidebar.title("Navigation")
    
    if user['role'] == 'admin':
        pg1=st.navigation(
            {"Admin Panel": [admin]}
                            )
        pg1.run()
        # st.page_link("pages/admin.py", label="Admin Panel")
    elif user['role'] == 'builder':
        pg2=st.navigation(
            {"Builders Deployment": [builders]}
                            )
        pg2.run()
        # st.page_link("pages/builder_deploy.py", label="Deploy POSM")
    elif user['role'] == 'merchandiser':
        pg3=st.navigation(
            {"🏪Merchandiser Tasks": [outlet_onboarding],
            "👨👨Merchandiser Visits":
            [msl_sos, oos, order, pricing]
            }
                            )
        pg3.run()
        st.sidebar.image('assets/OM Lockup Dairy and Beverage 2.png', caption="A look of success for OM Perfect Store®️", width=200)
        st.sidebar.image('assets/OM Lockup Seasoning.png', caption="A look of success for OM Perfect Store®️", width=200)
        st.sidebar.image('assets/OM Lockup Stores Dairy and Beverages.png', caption="A look of success for OM Perfect Store®️", width=200)
        st.sidebar.caption("### :blue[Developed by D-Aggregate®️]")
        st.sidebar.caption("#### :orange[www.d-aggregate.com]")



# st.sidebar.button("📌Logout", on_click=logout)
        # # if CURRENT_MONTH == 1:
        #     st.page_link("pages/merchandiser_onboard.py", label="Onboard Outlets")
        # else:
        #     st.page_link("pages/merchandiser_onboard.py", label="Onboard Outlets")  # Allow ongoing if needed
        #     st.page_link("pages/merchandiser_msl_sos.py", label="Track MSL/SOS")
        #     st.page_link("pages/merchandiser_oos.py", label="Track OOS")
        #     st.page_link("pages/merchandiser_order.py", label="Generate Orders")
        #     st.page_link("pages/merchandiser_expiry.py", label="Track Expiry")
st.markdown("""<br>""",unsafe_allow_html=True)
st.markdown("""<br>""",unsafe_allow_html=True)
st.markdown("""<br>""",unsafe_allow_html=True)
st.markdown("""<p style="font-size:16px; text-align:center; color:darkred;"> Copyright©️ RetailScope(2025) -All right reserved</p>""",unsafe_allow_html=True)
st.markdown("""<br>""",unsafe_allow_html=True)
