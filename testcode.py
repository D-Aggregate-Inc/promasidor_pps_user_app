from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
import streamlit as st
import logging
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logging.basicConfig(filename='app.log', level=logging.ERROR)

@st.cache_resource
def init_connection_pool():
    return SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode='require'
    )

@st.cache_data(ttl=300)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10), retry=retry_if_exception_type(psycopg2.OperationalError))
def execute_query(query, params=None, fetch='all'):
    pool = init_connection_pool()
    conn = None
    try:
        conn = pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute(query, params)
            except TypeError as e:
                logging.error(f"Query parameter error: {query}, params: {params}, error: {e}")
                st.error(f"Invalid query parameters: {e}")
                raise
            if fetch == 'all':
                return cur.fetchall()
            elif fetch == 'one':
                return cur.fetchone()
            conn.commit()
    except psycopg2.OperationalError as e:
        logging.error(f"Database connection error: {e}")
        st.error(f"Database connection error: {e}")
        if conn:
            pool.putconn(conn, close=True)
        raise
    except Exception as e:
        logging.error(f"Query failed: {query}, error: {e}")
        st.error(f"Query failed: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            pool.putconn(conn)
#----------------------------------------------------------------------------------------------------------
import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from db.db_utils import execute_query, add_posm_deployment, get_posms
from utils.spaces import upload_image

st.title("Builder: Deploy POSM")

user_id = st.session_state['user']['id']
outlets = execute_query("SELECT * FROM outlets")
outlet_dict = {f"{o['name']} ({o['outlet_type']})": o['id'] for o in outlets}
outlet_name = st.selectbox("Select Outlet", list(outlet_dict.keys()))
outlet_id = outlet_dict[outlet_name]

posms = get_posms()
posm_dict = {p['name']: p['id'] for p in posms}
selected_posms = st.multiselect("Select POSMs Deployed", list(posm_dict.keys()))

# Collect quantities for selected POSMs
deployed_posms = []
if selected_posms:
    st.subheader("Specify Quantities")
    for posm_name in selected_posms:
        quantity = st.number_input(
            f"Quantity of {posm_name}",
            min_value=0,
            value=0,
            step=1,
            key=f"qty_{posm_name}"
        )
        if quantity > 0:
            deployed_posms.append({"posm_id": posm_dict[posm_name], "quantity": quantity})

before_img = st.camera_input("Before Deployment Image")
after_img = st.camera_input("After Deployment Image")

location = streamlit_geolocation()
if location and location['latitude'] is not None:
    gps_lat = location['latitude']
    gps_long = location['longitude']
else:
    st.warning("Waiting for GPS location...")
    gps_lat, gps_long = None, None

if st.button("Deploy") and gps_lat and before_img and after_img and deployed_posms:
    before_key = upload_image(before_img.getvalue(), folder='posm_before')
    after_key = upload_image(after_img.getvalue(), folder='posm_after')
    if before_key and after_key:
        add_posm_deployment(outlet_id, user_id, deployed_posms, before_key, after_key, gps_lat, gps_long)
        st.success("POSM Deployed!")
    else:
        st.error("Image upload failed. Please try again.")
else:
    if not deployed_posms and selected_posms:
        st.warning("Please specify quantities for selected POSMs.")
#---------------------------------------------------------------------------------------
import streamlit as st
from streamlit_geolocation import streamlit_geolocation
from db.db_utils import execute_query, add_msl_sos_track, get_skus_grouped, get_user_outlets, save_draft, get_drafts, sync_drafts
from utils.spaces import upload_image
import base64
import logging

logging.basicConfig(filename='app.log', level=logging.ERROR)

st.title("Merchandiser: Track MSL/SOS")

user_id = st.session_state['user']['id']

# Offline detection
is_online = st.components.v1.html("""
    <script>
        function updateConnectivity() {
            const isOnline = navigator.onLine;
            window.Streamlit.setComponentValue(isOnline);
        }
        window.addEventListener('online', updateConnectivity);
        window.addEventListener('offline', updateConnectivity);
        updateConnectivity();
    </script>
""", height=0)

# Sync drafts if online
if is_online:
    sync_drafts()

# Display drafts
with st.expander("View Drafts"):
    drafts = get_drafts()
    for i, draft in enumerate(drafts):
        if draft['form_type'] == 'msl_sos':
            st.write(f"Draft {i+1}: Outlet ID {draft['data']['outlet_id']}")
            if st.button("Sync Now", key=f"sync_draft_{i}"):
                sync_drafts()
                st.rerun()

outlets = get_user_outlets(user_id)
outlet_dict = {
    f"{o['name']} ({o['state_name']} - {o['location_name']}, {o['address'] or 'No Address'}, {o['phone_contact'] or 'No Phone'}, {o['outlet_type']}, {o['classification']})": o['id']
    for o in outlets
}
outlet_name = st.selectbox("Select Outlet", list(outlet_dict.keys()))
outlet_id = outlet_dict[outlet_name]

skus_grouped = get_skus_grouped()
sos_data = {"your_skus": {}, "competitor_facings": {}}
for category, skus in skus_grouped.items():
    with st.expander(category):
        # Your SKUs
        for sku in skus:
            facings = st.number_input(f"{sku['name']} Facings", min_value=0, value=0, key=f"facing_{sku['id']}")
            if facings > 0:
                sos_data["your_skus"][str(sku['id'])] = facings
        # Competitor facings
        competitor_facings[category] = st.number_input(f"Competitor Facings for {category}", min_value=0, value=0, key=f"comp_facing_{category}")
        if competitor_facings[category] > 0:
            sos_data["competitor_facings"][category] = competitor_facings[category]

msl_count = len(sos_data["your_skus"])
image = st.camera_input("Capture Shelf/Tray Image")

location = streamlit_geolocation()
if location and location['latitude'] is not None:
    gps_lat = location['latitude']
    gps_long = location['longitude']
else:
    st.warning("Waiting for GPS location...")
    gps_lat, gps_long = None, None

if st.button("Submit MSL/SOS") and gps_lat and image:
    image_base64 = base64.b64encode(image.getvalue()).decode('utf-8')
    draft_data = {
        'outlet_id': outlet_id, 'user_id': user_id, 'sos_data': sos_data,
        'msl_count': msl_count, 'image_base64': image_base64,
        'gps_lat': gps_lat, 'gps_long': gps_long
    }
    if is_online:
        image_key = upload_image(image.getvalue(), folder='shelves')
        if image_key:
            add_msl_sos_track(outlet_id, user_id, sos_data, msl_count, image_key, gps_lat, gps_long)
            st.success("MSL/SOS Tracked!")
        else:
            st.error("Image upload failed. Saving as draft.")
            save_draft('msl_sos', draft_data)
    else:
        st.warning("Offline. Saving as draft.")
        save_draft('msl_sos', draft_data)