from tkinter import N
import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from db.db_utils import execute_query, add_oos_track, get_skus_grouped

st.write(":material/local_convenience_store:**:blue[Track Out-of-Stock]**")

user_id = st.session_state['user']['id']
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
oos_data = []
for category, skus in skus_grouped.items():
    with st.expander(category):
        for sku in skus:
            if st.checkbox(f"OOS: {sku['name']}", key=f"oos_{sku['id']}"):
                # reason = st.text_input(f"Reason for {sku['name']}", key=f"reason_{sku['id']}", help="Owing Distributor, Dont Have Money To Stock, Low Demand, Others")
                oos_data.append({"sku_id": sku['name'], "reason": None})

location = streamlit_geolocation()
if location and location['latitude'] is not None:
    gps_lat = location['latitude']
    gps_long = location['longitude']
else:
    st.warning("Waiting for GPS location...")
    gps_lat, gps_long = None, None

if st.button("Submit OOS") and gps_lat:
    add_oos_track(outlet_id, user_id, oos_data, gps_lat, gps_long)
    st.success("OOS Tracked!")