import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from db.db_utils import execute_query, add_msl_sos_track, get_skus_grouped
from utils.spaces import upload_image

st.write(":material/local_convenience_store:**:blue[Track MSL/Share of Shelf]**")

user_id = st.session_state['user']['id']
st.info("Please click on GPS button to get your location GPS")
location = streamlit_geolocation()
outlets = execute_query("""
    SELECT o.id, o.name, o.outlet_address, o.phone_contact, o.outlet_type, o.classification,o.contact_person,
           l.name AS location_name, s.name AS state_name
    FROM outlets o
    JOIN locations l ON o.location_id = l.id
    JOIN states s ON l.state_id = s.id
    WHERE o.onboarded_by_user_id = %s
""", (user_id,))
outlet_dict = {
    f"{o['name']} ({o['state_name']} - {o['location_name']} | {o['outlet_address']} | {o['contact_person']} | {o['phone_contact']} | {o['outlet_type']} | {o['classification']})": o['id']
    for o in outlets
}
outlet_name = st.selectbox("Select Outlet", list(outlet_dict.keys()))
if outlets:
    outlet_id = outlet_dict[outlet_name]
else:
    st.warning("No outlets found. Please onboard an outlet first.")
    st.stop()

skus_grouped = get_skus_grouped()
sos_data = {}
for category, skus in skus_grouped.items():
    with st.expander(category):
        for sku in skus:
            facings = st.number_input(f"{sku['name']} Facings", min_value=0, value=0, key=f"facing_{sku['id']}")
            competition_facing=st.number_input("Input Competition Facing",min_value=0,value=0,key=f"Competion_Facing_{category['id']}")
            if facings > 0:
                sos_data[sku['id']] = facings
msl_count = len(sos_data)

image = st.camera_input("Capture Shelf/Tray Image", help="Image is required")

# location = streamlit_geolocation()
if location and location['latitude'] is not None:
    gps_lat = location['latitude']
    gps_long = location['longitude']
else:
    st.warning("Waiting for GPS location...")
    gps_lat, gps_long = None, None

if st.button("Submit MSL/SOS") and gps_lat and image:
    image_key = upload_image(image.getvalue(), folder='shelves')
    if image_key:
        add_msl_sos_track(outlet_id, user_id, sos_data, msl_count, image_key, gps_lat, gps_long)
        st.success("MSL/SOS Tracked!")