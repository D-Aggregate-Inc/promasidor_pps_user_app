import streamlit as st
import logging
from streamlit_geolocation import streamlit_geolocation
from db.db_utils import execute_query, add_posm_deployment, get_posms
from utils.spaces import upload_image
from config import SPACES_ENDPOINT, SPACES_BUCKET
import requests
from PIL import Image


logging.basicConfig(filename='app.log', level=logging.ERROR)

st.write(":material/local_convenience_store:**:orange[Deploy POSMs and Track]**")

# # Offline detection
# is_online = st.components.v1.html("""
#     <script>
#         function updateConnectivity() {
#             const isOnline = navigator.onLine;
#             window.Streamlit.setComponentValue(isOnline);
#         }
#         window.addEventListener('online', updateConnectivity);
#         window.addEventListener('offline', updateConnectivity);
#         updateConnectivity();
#     </script>
# """, height=0)

# # Sync drafts if online
# if is_online:
#     sync_drafts()

# # Display drafts
# with st.expander("View Drafts"):
#     drafts = get_drafts()
#     for i, draft in enumerate(drafts):
#         if draft['form_type'] == 'posm_deployment':
#             st.write(f"Draft {i+1}: Outlet ID {draft['data']['outlet_id']}")
#             if st.button("Sync Now", key=f"sync_draft_{i}"):
#                 sync_drafts()
#                 st.rerun()

user_id = st.session_state['user']['id']
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
outlet_name = st.selectbox("Select Outlet", list(outlet_dict.keys()))
outlet_id = outlet_dict[outlet_name]
try:
    selected_outlet = next(o for o in outlets if outlet_dict[outlet_name] == o['id'])
    if selected_outlet['outlet_image_key']:
        image_url = f"{SPACES_ENDPOINT}/{SPACES_BUCKET}/{selected_outlet['outlet_image_key']}"
        st.sidebar.write("### :blue[Outlet Image]")
        st.sidebar.write(f"**:orange[{selected_outlet['name']}]**")
        st.sidebar.write(f"**Address:** {selected_outlet['outlet_address']}")
        st.sidebar.write(f"**Contact:** {selected_outlet['contact_person']} | {selected_outlet['phone_contact']}")
        st.sidebar.write(f"**Type:** {selected_outlet['outlet_type']} | {selected_outlet['classification']}")
        st.sidebar.write(f"**Location:** {selected_outlet['location_name']}, {selected_outlet['state_name']}")
        st.sidebar.write("---")
        st.sidebar.write(Image.open(requests.get(image_url, stream=True).raw))
        st.sidebar.image(image_url, caption="Outlet Image (Captured by Recruiter/Merchandiser)", width=200)
    else:
        st.sidebar.write("No image available for this outlet.")
except Exception as e:
    logging.error(f"Failed to load outlet image: {e}")
    st.sidebar.error("Error loading outlet image.")


posms = get_posms()
posm_dict = {p['name']: p['id'] for p in posms}
selected_posms = st.multiselect("**:green[Select POSMs Deployed]**", list(posm_dict.keys()))

# Collect quantities for selected POSMs
deployed_posms = []
if selected_posms:
    st.write("🔢:red[**Pls Specify Quantities**]")
    for posm_name in selected_posms:
        quantity = st.number_input(
            f"Quantity of {posm_name}",
            min_value=0,
            value=0,
            step=1,
            key=f"qty_{posm_name}"
        )
        if quantity > 1:
            st.warning(f'{posm_name} must be 1 per outlet')
        elif quantity == 1:
             deployed_posms.append({"posm_id": posm_dict[posm_name], "quantity": quantity})

before_img = st.camera_input(":orange[**Before Deployment Image**]", help="Image is required")
after_img = st.camera_input(":blue[**After Deployment Image**]", help="Image is required")

location = streamlit_geolocation()
if location and location['latitude'] is not None:
    gps_lat = location['latitude']
    gps_long = location['longitude']
    st.info(f"📍GPS Captured: Lat {gps_lat}, Long {gps_long}")
else:
    st.warning("Waiting for GPS location...")
    gps_lat, gps_long = None, None

if st.button("Deploy") and gps_lat and before_img and after_img:
    before_key = upload_image(before_img.getvalue(), folder='posm_before',gps_lat=gps_lat,gps_long=gps_long)
    after_key = upload_image(after_img.getvalue(), folder='posm_after',gps_lat=gps_lat,gps_long=gps_long)
    if before_key and after_key:
        add_posm_deployment(outlet_id, user_id, deployed_posms, before_key, after_key, gps_lat, gps_long)
        st.success("POSM Deployed!")
    else:
        st.error("Image upload failed. Please try again.")
else:
    if not deployed_posms and selected_posms:
        st.warning("Please specify quantities for selected POSMs.")