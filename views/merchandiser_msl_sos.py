import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from db.db_utils import execute_query, add_msl_sos_track, get_skus_grouped, get_seasoning_skus_grouped,get_diary_general_skus_grouped, get_diary_kiosk_skus_grouped, get_diary_tabletop_skus_grouped
from utils.spaces import upload_image

st.write(":material/local_convenience_store:**:blue[Track MSL/Share of Shelf]**")

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
    f"{o['name']} ({o['region_name']} - {o['location_name']} | {o['outlet_address']} | {o['contact_person']} | {o['phone_contact']} | {o['outlet_type']} | {o['classification']})": o['id']
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
    sos_data = {"your_skus": {}, "competitor_facings": {}}
    competitor_facings={}
    for category, skus in skus_grouped.items():
        with st.expander(category):
            # Your SKUs
            for sku in skus:
                facings = st.number_input(f"{sku['name']} Facings", min_value=0, value=0, key=f"facing_{sku['id']}")
                if facings >= 0:
                    sos_data["your_skus"][str(sku['id'])] = facings
            # Competitor facings
            competitor_facings[category] = st.number_input(f":orange[**Competitor Facings for {category}**]", min_value=0, value=0, key=f"comp_facing_{category}")
            if competitor_facings[category] > 0:
                sos_data["competitor_facings"][category] = competitor_facings[category]

    msl_count = len(sos_data)
elif selected_outlet['outlet_type']=='Lock-Up Shop(Dairy/Beverages)':
    skus_grouped = get_diary_general_skus_grouped()
    sos_data = {"your_skus": {}, "competitor_facings": {}}
    competitor_facings={}
    for category, skus in skus_grouped.items():
        with st.expander(category):
            # Your SKUs
            for sku in skus:
                facings = st.number_input(f"{sku['name']} Facings", min_value=0, value=0, key=f"facing_{sku['id']}")
                if facings >= 0:
                    sos_data["your_skus"][str(sku['id'])] = facings
            # Competitor facings
            competitor_facings[category] = st.number_input(f":orange[**Competitor Facings for {category}**]", min_value=0, value=0, key=f"comp_facing_{category}")
            if competitor_facings[category] > 0:
                sos_data["competitor_facings"][category] = competitor_facings[category]

    msl_count = len(sos_data)
elif selected_outlet['outlet_type']=='Kiosk(Dairy/Beverages)':
    skus_grouped = get_diary_kiosk_skus_grouped()
    sos_data = {"your_skus": {}, "competitor_facings": {}}
    competitor_facings={}
    for category, skus in skus_grouped.items():
        with st.expander(category):
            # Your SKUs
            for sku in skus:
                facings = st.number_input(f"{sku['name']} Facings", min_value=0, value=0, key=f"facing_{sku['id']}")
                if facings >= 0:
                    sos_data["your_skus"][str(sku['id'])] = facings
            # Competitor facings
            competitor_facings[category] = st.number_input(f":orange[**Competitor Facings for {category}**]", min_value=0, value=0, key=f"comp_facing_{category}")
            if competitor_facings[category] > 0:
                sos_data["competitor_facings"][category] = competitor_facings[category]

    msl_count = len(sos_data)
elif selected_outlet['outlet_type']=='Table-Top(Dairy/Beverages)':
    skus_grouped = get_diary_tabletop_skus_grouped()
    sos_data = {"your_skus": {}, "competitor_facings": {}}
    competitor_facings={}
    for category, skus in skus_grouped.items():
        with st.expander(category):
            # Your SKUs
            for sku in skus:
                facings = st.number_input(f"{sku['name']} Facings", min_value=0, value=0, key=f"facing_{sku['id']}")
                if facings >= 0:
                    sos_data["your_skus"][str(sku['id'])] = facings
            # Competitor facings
            competitor_facings[category] = st.number_input(f":orange[**Competitor Facings for {category}**]", min_value=0, value=0, key=f"comp_facing_{category}")
            if competitor_facings[category] > 0:
                sos_data["competitor_facings"][category] = competitor_facings[category]

    msl_count = len(sos_data)
elif selected_outlet['outlet_type']=='GSM-Groceries' or selected_outlet['outlet_type']=='Kiosks' or selected_outlet['outlet_type']=='Table Tops':
    skus_grouped = get_skus_grouped()
    sos_data = {"your_skus": {}, "competitor_facings": {}}
    competitor_facings={}
    for category, skus in skus_grouped.items():
        with st.expander(category):
            # Your SKUs
            for sku in skus:
                facings = st.number_input(f"{sku['name']} Facings", min_value=0, value=0, key=f"facing_{sku['id']}")
                if facings >= 0:
                    sos_data["your_skus"][str(sku['id'])] = facings
            # Competitor facings
            competitor_facings[category] = st.number_input(f":orange[**Competitor Facings for {category}**]", min_value=0, value=0, key=f"comp_facing_{category}")
            if competitor_facings[category] > 0:
                sos_data["competitor_facings"][category] = competitor_facings[category]

    msl_count = len(sos_data)
# location = streamlit_geolocation()


image = st.camera_input("Capture Shelf/Tray Image", help="Image is required",key=f'{outlet_id}_shelf_image_{gps_long}')
image2= st.camera_input("Outside Store Image", help="Image is required",key=f'{msl_count}_outside_store_image_{gps_lat}')

if st.button("Submit MSL/SOS") and gps_lat and sos_data and outlet_info and msl_count):
    if image:
        image_key = upload_image(image.getvalue(), folder='NB_shelves',gps_lat=gps_lat, gps_long=gps_long)
    else:
        image_key=[]
    if image2:
        image_key2 = upload_image(image2.getvalue(), folder='outside_NB_OM',gps_lat=gps_lat, gps_long=gps_long)
    else:
        image_key2=[]
    if image_key or image_key2 :
        add_msl_sos_track(outlet_id, user_id, sos_data, msl_count, image_key, gps_lat, gps_long,outlet_info,image_key2)
        st.success("MSL/SOS Tracked Submitted!")
    else:
        st.error("Image Not Uploaded")
else:
    st.warning(f"Please ensure all field are correctly filled")