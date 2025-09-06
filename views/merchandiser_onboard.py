from numpy import place
import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from db.db_utils import execute_query, add_outlet, get_outlet_by_phone_contact
from utils.spaces import upload_image
import warnings
import logging

logging.basicConfig(level=logging.INFO)

warnings.filterwarnings('ignore')

st.write(":material/local_convenience_store:**:orange[Outlet Onboarding]**")


user_id = st.session_state['user']['id']

st.markdown("""<hr class="line">""",unsafe_allow_html=True)
st.write(f'Welcome, **:blue[{st.session_state["user"]["email"]}]**! Use the form below to onboard a new outlet.')

with st.form("Onboard Outlet"):
    name = st.text_input("Outlet Name", max_chars=50, help="E.g DM Ventures",placeholder="Enter outlet name")
    phone_contact = st.text_input("Contact Phone", max_chars=11, help="11-digit phone number",placeholder="08012345678")
    outlet_number = st.text_input("Outlet Number", max_chars=20, help="E.g No. 12, Shop 34B")
    outlet_address = st.text_area("Address", max_chars=200, help="E.g 12, Shop 34B, Tipper Garage Road")
    outlet_landmark = st.text_input("Landmark ", max_chars=50, help="E.g Opposite Tipper Garage, Near Shoprite Mall")
    region= execute_query("SELECT * FROM region")
    region_dict = {r['name']: r['id'] for r in region}  
    region_name = st.selectbox("Region", list(region_dict.keys()))
    state=execute_query("SELECT * FROM state")
    locations = execute_query("SELECT l.id, l.name, s.name as state FROM locations l JOIN states s ON l.state_id = s.id")
    loc_dict = {f"{loc['state']} - {loc['name']}": loc['id'] for loc in locations}
    loc_selection = st.selectbox("Location", list(loc_dict.keys()))
    location_id = loc_dict[loc_selection]
    contact_person=st.text_input("Contact Person", max_chars=50, help="E.g John Doe",placeholder="Enter contact person name")
    classification = st.selectbox("Channel", ['Neighborhood','Open market'])
    outlet_type = st.selectbox("Outlet Type", ['Wholesaler', 'GSM-Groceries', 'Lock-Up Shop', 'Kiosks', 'Table Tops'])
    image = st.camera_input("Capture Outlet Image", help="Image is required")
    location = streamlit_geolocation()
    if location and location['latitude'] is not None:
        gps_lat = location['latitude']
        gps_long = location['longitude']
        st.info(f"📍GPS Captured: Lat {gps_lat}, Long {gps_long}")
    else:
        st.warning("Waiting for GPS location...")
        gps_lat, gps_long = None, None
    if st.form_submit_button("Submit Outlet Onboarded",type='primary') and gps_lat and image:
        image_key = upload_image(image.getvalue(), folder='outlets')
        if image_key:
            if get_outlet_by_phone_contact(phone_contact):
                st.warning("An outlet with this contact phone already exists.")
            add_outlet(name, location_id, classification,outlet_type, user_id, gps_lat, gps_long, image_key,
                   phone_contact, outlet_number, outlet_address,outlet_landmark, contact_person)
            
            st.success("Outlet Onboarded Successfully!")
        else:
            st.error("Image upload failed. Please try again.")
    # elif  not gps_lat:
    #     st.warning("GPS location is required to onboard an outlet.")
    # elif not image:
    #     st.error("Outlet image is required to onboard an outlet.")
