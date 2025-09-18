import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from db.db_utils import execute_query, add_order_track, get_skus_grouped, add_pricing_track

st.write(":material/barcode_reader:**:blue[Price Compliance Check]**")

user_id = st.session_state['user']['id']
st.info("Please click on GPS button to get your location GPS")
location = streamlit_geolocation()
outlets = execute_query("""
    SELECT o.id, o.name, o.outlet_address, o.phone_contact, o.location_id, o.outlet_type, o.classification,o.contact_person,
           l.name AS location_name, r.name AS region_name
    FROM outlets o
    JOIN locations_by_region l ON o.location_id = l.id
    JOIN region r ON l.region_id = r.id
    WHERE o.onboarded_by_user_id = %s
""", (user_id,))
outlet_dict = {
    f"{o['name']} ({o['region_name']} - {o['location_name']} | {o['outlet_address']} | {o['contact_person']} | {o['phone_contact']} | {o['outlet_type']} | {o['classification']})": o['id']
    for o in outlets
}
outlet_info = st.selectbox("Select Outlet", list(outlet_dict.keys()))
if outlets:
    outlet_id = outlet_dict[outlet_info]
else:
    st.warning("No outlets found. Please onboard an outlet first.")
    st.stop()
skus_grouped = get_skus_grouped()
price_data = []
for category, skus in skus_grouped.items():
    with st.expander(category):
        for sku in skus:
            price = st.number_input(f"{sku['name']} 🆖Price", min_value=0, value=0, key=f"qty_{sku['id']}")
            if price> 0:
                price_data.append({"sku_id": sku['id'], "price": price})

# location = streamlit_geolocation()
if location and location['latitude'] is not None:
    gps_lat = location['latitude']
    gps_long = location['longitude']
    st.info(f"📍GPS Captured: Lat {gps_lat}, Long {gps_long}")
else:
    st.warning("Waiting for GPS location...")
    gps_lat, gps_long = None, None

if st.button("Submit Prices") and gps_lat:
    add_pricing_track(outlet_id, user_id, price_data, gps_lat, gps_long, outlet_info)
    st.success("Price Compliance Submitted")