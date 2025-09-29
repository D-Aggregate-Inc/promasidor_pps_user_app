import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from db.db_utils import execute_query, add_oos_track, get_skus_grouped,get_seasoning_skus_grouped,get_diary_general_skus_grouped,get_diary_kiosk_skus_grouped,get_diary_tabletop_skus_grouped

st.write(":material/local_convenience_store:**:blue[Track Out-of-Stock]**")

user_id = st.session_state['user']['id']
st.info("Please click on GPS button to get your location GPS")
location = streamlit_geolocation()
if location and location['latitude'] is not None:
    gps_lat = location['latitude']
    gps_long = location['longitude']
    st.info(f"📍GPS Captured: Lat {gps_lat}, Long {gps_long}")
else:
    st.warning("Waiting for GPS location...")
    gps_lat, gps_long = None, None

outlets = execute_query("""
    SELECT o.id, o.name, o.outlet_address, o.phone_contact, o.location_id, o.outlet_type, o.classification,o.contact_person,
           l.name AS location_name, r.name AS region_name
    FROM outlets o
    JOIN locations_by_region l ON o.location_id = l.id
    JOIN region r ON l.region_id = r.id
    WHERE o.onboarded_by_user_id = %s
""", (user_id,))
outlet_dict = {
    f"{o['name']} ({o['phone_contact']})": o['id']
    for o in outlets
}
outlet_info = st.selectbox("Select Outlet", list(outlet_dict.keys()))
if outlets:
    outlet_id = outlet_dict[outlet_info]
else:
    st.warning("No outlets found. Please onboard an outlet first.")
    st.stop()
selected_outlet = next(o for o in outlets if outlet_dict[outlet_info] == o['id'])
st.caption(f":orange[🏪This outlet is {selected_outlet['outlet_type']}]")
if selected_outlet['outlet_type']=='Lock-Up Shop(Seasoning)' or selected_outlet['outlet_type']=='Kiosk-(Seasoning)' or selected_outlet['outlet_type']=='Table-Top(Seasoning)' or selected_outlet['outlet_type']=='Table Top-OSC':
    skus_grouped = get_seasoning_skus_grouped()
    oos_data = []
    for category, skus in skus_grouped.items():
        with st.expander(category):
            for sku in skus:
                if st.checkbox(f"OOS: {sku['name']}", key=f"oos_{sku['id']}"):
                    # reason = st.text_input(f"Reason for {sku['name']}", key=f"reason_{sku['id']}", help="Owing Distributor, Dont Have Money To Stock, Low Demand, Others")
                    oos_data.append({"sku_id": sku['name'], "reason": None})

elif selected_outlet['outlet_type']=='Lock-Up Shop(Dairy/Beverages)':
    skus_grouped = get_diary_general_skus_grouped()
    oos_data = []
    for category, skus in skus_grouped.items():
        with st.expander(category):
            for sku in skus:
                if st.checkbox(f"OOS: {sku['name']}", key=f"oos_{sku['id']}"):
                    # reason = st.text_input(f"Reason for {sku['name']}", key=f"reason_{sku['id']}", help="Owing Distributor, Dont Have Money To Stock, Low Demand, Others")
                    oos_data.append({"sku_id": sku['name'], "reason": None})

elif selected_outlet['outlet_type']=='Kiosk(Dairy/Beverages)':
    skus_grouped = get_diary_kiosk_skus_grouped()
    oos_data = []
    for category, skus in skus_grouped.items():
        with st.expander(category):
            for sku in skus:
                if st.checkbox(f"OOS: {sku['name']}", key=f"oos_{sku['id']}"):
                    # reason = st.text_input(f"Reason for {sku['name']}", key=f"reason_{sku['id']}", help="Owing Distributor, Dont Have Money To Stock, Low Demand, Others")
                    oos_data.append({"sku_id": sku['name'], "reason": None})

elif selected_outlet['outlet_type']=='Table-Top(Dairy/Beverages)':
    skus_grouped = get_diary_tabletop_skus_grouped()
    oos_data = []
    for category, skus in skus_grouped.items():
        with st.expander(category):
            for sku in skus:
                if st.checkbox(f"OOS: {sku['name']}", key=f"oos_{sku['id']}"):
                    # reason = st.text_input(f"Reason for {sku['name']}", key=f"reason_{sku['id']}", help="Owing Distributor, Dont Have Money To Stock, Low Demand, Others")
                    oos_data.append({"sku_id": sku['name'], "reason": None})

elif selected_outlet['outlet_type']=='GSM-Groceries' or selected_outlet['outlet_type']=='Kiosks' or selected_outlet['outlet_type']=='Table Tops':
    skus_grouped = get_skus_grouped()
    oos_data = []
    for category, skus in skus_grouped.items():
        with st.expander(category):
            for sku in skus:
                if st.checkbox(f"OOS: {sku['name']}", key=f"oos_{sku['id']}"):
                    # reason = st.text_input(f"Reason for {sku['name']}", key=f"reason_{sku['id']}", help="Owing Distributor, Dont Have Money To Stock, Low Demand, Others")
                    oos_data.append({"sku_id": sku['name'], "reason": None})
# location = streamlit_geolocation()
# skus_grouped = get_skus_grouped()
# oos_data = []
# for category, skus in skus_grouped.items():
#     with st.expander(category):
#         for sku in skus:
#             if st.checkbox(f"OOS: {sku['name']}", key=f"oos_{sku['id']}"):
#                 # reason = st.text_input(f"Reason for {sku['name']}", key=f"reason_{sku['id']}", help="Owing Distributor, Dont Have Money To Stock, Low Demand, Others")
#                 oos_data.append({"sku_id": sku['name'], "reason": None})

# location = streamlit_geolocation()

if st.button("Submit OOS") and gps_lat and oos_data:
    add_oos_track(outlet_id, user_id, oos_data, gps_lat, gps_long, outlet_info)
    st.success("OOS Tracked!")
else:
    st.error("fill your OOS SKUs")
st.stop()