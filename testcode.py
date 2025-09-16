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
#------------------------------------------------------------------------------
import boto3
import uuid
import io
import logging
from PIL import Image
from config import SPACES_KEY, SPACES_SECRET, SPACES_REGION, SPACES_BUCKET, SPACES_ENDPOINT
from exif import Image as ExifImage
from datetime import datetime

logging.basicConfig(filename='app.log', level=logging.ERROR)

def get_spaces_client():
    try:
        session = boto3.session.Session()
        return session.client(
            's3',
            region_name=SPACES_REGION,
            endpoint_url=SPACES_ENDPOINT,
            aws_access_key_id=SPACES_KEY,
            aws_secret_access_key=SPACES_SECRET
        )
    except Exception as e:
        logging.error(f"Failed to create Spaces client: {e}")
        raise

def dms_to_decimal(degrees, minutes, seconds, direction):
    """Convert degrees, minutes, seconds to decimal degrees."""
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal

def upload_image(image_bytes, folder='images', gps_lat=None, gps_long=None):
    try:
        client = get_spaces_client()
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img.thumbnail((1024, 1024))  # Optimize size
        buffer = io.BytesIO()
        
        # Add EXIF metadata
        exif_img = ExifImage(io.BytesIO(image_bytes))
        exif_dict = exif_img.get_all() if hasattr(exif_img, '_exif_ifd') else {}
        
        # Set datetime
        current_time = datetime.now().strftime('%Y:%m:%d %H:%M:%S')
        exif_dict['datetime'] = current_time
        
        # Set GPS data if provided
        if gps_lat is not None and gps_long is not None:
            # Convert to degrees, minutes, seconds
            lat_deg = int(abs(gps_lat))
            lat_min = int((abs(gps_lat) - lat_deg) * 60)
            lat_sec = ((abs(gps_lat) - lat_deg - lat_min / 60) * 3600)
            lon_deg = int(abs(gps_long))
            lon_min = int((abs(gps_long) - lon_deg) * 60)
            lon_sec = ((abs(gps_long) - lon_deg - lon_min / 60) * 3600)
            
            exif_dict['gps_latitude'] = (lat_deg, lat_min, lat_sec)
            exif_dict['gps_latitude_ref'] = 'N' if gps_lat >= 0 else 'S'
            exif_dict['gps_longitude'] = (lon_deg, lon_min, lon_sec)
            exif_dict['gps_longitude_ref'] = 'E' if gps_long >= 0 else 'W'
        
        # Save image with EXIF data
        img.save(buffer, format="JPEG", quality=85, exif=exif_img.get_exif_bytes() if hasattr(exif_img, '_exif_ifd') else None)
        buffer.seek(0)
        
        key = f"{folder}/{uuid.uuid4()}.jpg"
        client.put_object(Bucket=SPACES_BUCKET, Key=key, Body=buffer.getvalue(), ACL='public-read')
        return key
    except Exception as e:
        logging.error(f"Image upload failed: {e}")
        return None
#----------------------------------------------------------------------------------------------------------------------
import boto3
import uuid
import io
import logging
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from config import SPACES_KEY, SPACES_SECRET, SPACES_REGION, SPACES_BUCKET, SPACES_ENDPOINT

logging.basicConfig(filename='app.log', level=logging.ERROR)

def get_spaces_client():
    try:
        session = boto3.session.Session()
        return session.client(
            's3',
            region_name=SPACES_REGION,
            endpoint_url=SPACES_ENDPOINT,
            aws_access_key_id=SPACES_KEY,
            aws_secret_access_key=SPACES_SECRET
        )
    except Exception as e:
        logging.error(f"Failed to create Spaces client: {e}")
        raise

def upload_image(image_bytes, folder='images', gps_lat=None, gps_long=None):
    try:
        client = get_spaces_client()
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img.thumbnail((1024, 1024))  # Optimize size

        # Add watermark with GPS and datetime
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)  # Default font, size 20
        except IOError:
            font = ImageFont.load_default()  # Fallback if arial.ttf unavailable
        current_time = datetime.now().strftime('%Y:%m:%d %H:%M:%S')
        gps_text = f"Lat: {gps_lat:.6f}, Lon: {gps_long:.6f}" if gps_lat is not None and gps_long is not None else "No GPS"
        watermark_text = f"{current_time}\n{gps_text}"
        draw.text((10, 10), watermark_text, fill="white", font=font, stroke_width=2, stroke_fill="black")

        # Save image to buffer
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)

        key = f"{folder}/{uuid.uuid4()}.jpg"
        client.put_object(Bucket=SPACES_BUCKET, Key=key, Body=buffer.getvalue(), ACL='public-read')
        return key
    except Exception as e:
        logging.error(f"Image upload failed: {e}")
        return None
#--------------------------------------------------------------------------------------------------------------------------------------------
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import streamlit as st
import logging
import json
import base64
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logging.basicConfig(filename='app.log', level=logging.ERROR)

@st.cache_resource
def init_connection_pool():
    return SimpleConnectionPool(
        minconn=5, maxconn=50,  # Increased for ~150 users
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD, sslmode='require'
    )

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=10), 
       retry=retry_if_exception_type((psycopg2.OperationalError, psycopg2.DatabaseError)))
def execute_query(query, params=None, fetch='all'):
    pool = init_connection_pool()
    conn = None
    try:
        conn = pool.getconn()
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute(query, params)
                if fetch == 'all':
                    return cur.fetchall()
                elif fetch == 'one':
                    return cur.fetchone()
                conn.commit()
            except psycopg2.errors.SerializationFailure as e:
                logging.error(f"Serialization failure: {e}")
                conn.rollback()
                raise
            except psycopg2.errors.UniqueViolation as e:
                logging.error(f"Duplicate entry: {e}")
                conn.rollback()
                st.error("Submission failed: Duplicate entry detected.")
                return None
            except Exception as e:
                logging.error(f"Query failed: {query}, error: {e}")
                conn.rollback()
                st.error(f"Query failed: {e}")
                raise
    except psycopg2.OperationalError as e:
        logging.error(f"Database connection error: {e}")
        st.error(f"Database connection error: {e}")
        if conn:
            pool.putconn(conn, close=True)
        raise
    finally:
        if conn:
            pool.putconn(conn)

def save_draft(form_type, data, user_id):
    if 'drafts' not in st.session_state:
        st.session_state['drafts'] = []
    draft_id = str(uuid.uuid4())  # Unique draft ID
    draft = {'id': draft_id, 'form_type': form_type, 'data': data, 'user_id': user_id}
    st.session_state['drafts'].append(draft)
    js_code = f"""
    <script>
        localStorage.setItem('retail_app_drafts_{user_id}', JSON.stringify({json.dumps(st.session_state['drafts'])}));
    </script>
    """
    st.components.v1.html(js_code, height=0)

def get_drafts(user_id):
    return [draft for draft in st.session_state.get('drafts', []) if draft['user_id'] == user_id]

def clear_draft(draft_id, user_id):
    if 'drafts' in st.session_state:
        st.session_state['drafts'] = [d for d in st.session_state['drafts'] if d['id'] != draft_id]
        js_code = f"""
        <script>
            localStorage.setItem('retail_app_drafts_{user_id}', JSON.stringify({json.dumps(st.session_state['drafts'])}));
        </script>
        """
        st.components.v1.html(js_code, height=0)

def sync_drafts(user_id):
    drafts = get_drafts(user_id)
    if not drafts:
        return
    for draft in drafts[:]:
        try:
            if draft['form_type'] == 'onboard':
                data = draft['data']
                image_bytes = base64.b64decode(data['image_base64']) if data['image_base64'] else None
                image_key = upload_image(image_bytes, folder='outlets', gps_lat=data['gps_lat'], gps_long=data['gps_long']) if image_bytes else None
                if image_key:
                    result = add_outlet(
                        data['name'], data['address'], data['phone_contact'], data['location_id'],
                        data['classification'], data['outlet_type'], data['user_id'],
                        data['gps_lat'], data['gps_long'], image_key
                    )
                    if result is not None:  # Success
                        clear_draft(draft['id'], user_id)
            elif draft['form_type'] == 'posm_deployment':
                data = draft['data']
                before_key = upload_image(base64.b64decode(data['before_image_base64']), folder='posm_before', gps_lat=data['gps_lat'], gps_long=data['gps_long'])
                after_key = upload_image(base64.b64decode(data['after_image_base64']), folder='posm_after', gps_lat=data['gps_lat'], gps_long=data['gps_long'])
                if before_key and after_key:
                    result = add_posm_deployment(
                        data['outlet_id'], data['user_id'], data['deployed_posms'],
                        before_key, after_key, data['gps_lat'], data['gps_long']
                    )
                    if result is not None:
                        clear_draft(draft['id'], user_id)
            elif draft['form_type'] == 'msl_sos':
                data = draft['data']
                image_key = upload_image(base64.b64decode(data['image_base64']), folder='shelves', gps_lat=data['gps_lat'], gps_long=data['gps_long'])
                if image_key:
                    result = add_msl_sos_track(
                        data['outlet_id'], data['user_id'], data['sos_data'],
                        data['msl_count'], image_key, data['gps_lat'], data['gps_long']
                    )
                    if result is not None:
                        clear_draft(draft['id'], user_id)
        except Exception as e:
            logging.error(f"Failed to sync draft {draft['form_type']}: {e}")
            continue

def get_user_by_email(email):
    return execute_query("SELECT * FROM users WHERE email = %s", (email,), fetch='one')

def add_user(email, phone, password_hash, role):
    return execute_query(
        "INSERT INTO users (email, phone, password_hash, role) VALUES (%s, %s, %s, %s) ON CONFLICT (email) DO NOTHING",
        (email, phone, password_hash, role), fetch=None
    )

def add_outlet(name, address, phone_contact, location_id, classification, outlet_type, user_id, gps_lat, gps_long, image_key):
    return execute_query(
        """INSERT INTO outlets (name, address, phone_contact, location_id, classification, outlet_type, onboarded_by_user_id, gps_lat, gps_long, outlet_image_key)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (name, address, location_id) DO NOTHING""",
        (name, address, phone_contact, location_id, classification, outlet_type, user_id, gps_lat, gps_long, image_key), fetch=None
    )

def add_posm_deployment(outlet_id, user_id, deployed_posms, before_key, after_key, gps_lat, gps_long):
    return execute_query(
        """INSERT INTO posm_deployments (outlet_id, deployed_by_user_id, deployed_posms, before_image_key, after_image_key, gps_lat, gps_long, deployed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (outlet_id, deployed_at) DO NOTHING""",
        (outlet_id, user_id, psycopg2.extras.Json(deployed_posms), before_key, after_key, gps_lat, gps_long), fetch=None
    )

def add_msl_sos_track(outlet_id, user_id, sos_data, msl_count, image_key, gps_lat, gps_long):
    return execute_query(
        """INSERT INTO msl_sos (outlet_id, tracked_by_user_id, sos_data, msl_count, shelf_image_key, gps_lat, gps_long, tracked_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (outlet_id, tracked_at) DO NOTHING""",
        (outlet_id, user_id, psycopg2.extras.Json(sos_data), msl_count, image_key, gps_lat, gps_long), fetch=None
    )

def get_user_outlets(user_id):
    return execute_query(
        """SELECT o.id, o.name, o.address, o.phone_contact, o.outlet_type, o.classification, 
                  l.name AS location_name, s.name AS state_name
           FROM outlets o
           JOIN locations l ON o.location_id = l.id
           JOIN states s ON l.state_id = s.id
           WHERE o.onboarded_by_user_id = %s""",
        (user_id,)
    )

def get_posms():
    return execute_query("SELECT * FROM posms")

def get_skus_grouped():
    skus = execute_query("SELECT s.id, s.name, c.name AS category FROM skus s JOIN categories c ON s.category_id = c.id")
    grouped = {}
    for sku in skus:
        category = sku['category']
        if category not in grouped:
            grouped[category] = []
        grouped[category].append({'id': sku['id'], 'name': sku['name']})
    return grouped
#-------------------------------------------------------------------------------------------------------------------------------------------
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import streamlit as st
import logging
import json
import base64
import uuid
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logging.basicConfig(filename='app.log', level=logging.ERROR)

@st.cache_resource
def init_connection_pool():
    return SimpleConnectionPool(
        minconn=5, maxconn=50,
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD, sslmode='require'
    )

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=10), 
       retry=retry_if_exception_type((psycopg2.OperationalError, psycopg2.DatabaseError)))
def execute_query(query, params=None, fetch='all'):
    pool = init_connection_pool()
    conn = None
    try:
        conn = pool.getconn()
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute(query, params)
                if fetch == 'all':
                    return cur.fetchall()
                elif fetch == 'one':
                    return cur.fetchone()
                conn.commit()
            except psycopg2.errors.SerializationFailure as e:
                logging.error(f"Serialization failure: {e}")
                conn.rollback()
                raise
            except psycopg2.errors.UniqueViolation as e:
                logging.error(f"Duplicate entry: {e}")
                conn.rollback()
                st.error("Submission failed: Duplicate entry detected.")
                return None
            except Exception as e:
                logging.error(f"Query failed: {query}, error: {e}")
                conn.rollback()
                st.error(f"Query failed: {e}")
                raise
    except psycopg2.OperationalError as e:
        logging.error(f"Database connection error: {e}")
        st.error(f"Database connection error: {e}")
        if conn:
            pool.putconn(conn, close=True)
        raise
    finally:
        if conn:
            pool.putconn(conn)

def save_draft(form_type, data, user_id):
    if 'drafts' not in st.session_state:
        st.session_state['drafts'] = []
    draft_id = str(uuid.uuid4())
    draft = {'id': draft_id, 'form_type': form_type, 'data': data, 'user_id': user_id}
    st.session_state['drafts'].append(draft)
    js_code = f"""
    <script>
        localStorage.setItem('retail_app_drafts_{user_id}', JSON.stringify({json.dumps(st.session_state['drafts'])}));
    </script>
    """
    st.components.v1.html(js_code, height=0)

def get_drafts(user_id):
    return [draft for draft in st.session_state.get('drafts', []) if draft['user_id'] == user_id]

def clear_draft(draft_id, user_id):
    if 'drafts' in st.session_state:
        st.session_state['drafts'] = [d for d in st.session_state['drafts'] if d['id'] != draft_id]
        js_code = f"""
        <script>
            localStorage.setItem('retail_app_drafts_{user_id}', JSON.stringify({json.dumps(st.session_state['drafts'])}));
        </script>
        """
        st.components.v1.html(js_code, height=0)

def sync_drafts(user_id):
    drafts = get_drafts(user_id)
    if not drafts:
        return
    for draft in drafts[:]:
        try:
            if draft['form_type'] == 'onboard':
                data = draft['data']
                image_bytes = base64.b64decode(data['image_base64']) if data['image_base64'] else None
                image_key = upload_image(image_bytes, folder='outlets', gps_lat=data['gps_lat'], gps_long=data['gps_long']) if image_bytes else None
                if image_key:
                    result = add_outlet(
                        data['name'], data['address'], data['phone_contact'], data['location_id'],
                        data['classification'], data['outlet_type'], data['user_id'],
                        data['gps_lat'], data['gps_long'], image_key
                    )
                    if result is not None:
                        clear_draft(draft['id'], user_id)
            elif draft['form_type'] == 'posm_deployment':
                data = draft['data']
                before_key = upload_image(base64.b64decode(data['before_image_base64']), folder='posm_before', gps_lat=data['gps_lat'], gps_long=data['gps_long'])
                after_key = upload_image(base64.b64decode(data['after_image_base64']), folder='posm_after', gps_lat=data['gps_lat'], gps_long=data['gps_long'])
                if before_key and after_key:
                    result = add_posm_deployment(
                        data['outlet_id'], data['user_id'], data['deployed_posms'],
                        before_key, after_key, data['gps_lat'], data['gps_long']
                    )
                    if result is not None:
                        clear_draft(draft['id'], user_id)
            elif draft['form_type'] == 'msl_sos':
                data = draft['data']
                image_key = upload_image(base64.b64decode(data['image_base64']), folder='shelves', gps_lat=data['gps_lat'], gps_long=data['gps_long'])
                if image_key:
                    result = add_msl_sos_track(
                        data['outlet_id'], data['user_id'], data['sos_data'],
                        data['msl_count'], image_key, data['gps_lat'], data['gps_long']
                    )
                    if result is not None:
                        clear_draft(draft['id'], user_id)
        except Exception as e:
            logging.error(f"Failed to sync draft {draft['form_type']}: {e}")
            continue

def get_user_by_email(email):
    return execute_query("SELECT * FROM users WHERE email = %s", (email,), fetch='one')

def add_user(email, phone, password_hash, role, region):
    return execute_query(
        "INSERT INTO users (email, phone, password_hash, role, region) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (email) DO NOTHING",
        (email, phone, password_hash, role, region), fetch=None
    )

def get_regions():
    return execute_query("SELECT id, name FROM regions", fetch='all')

def get_locations_by_user_region(user_id):
    user = execute_query("SELECT region FROM users WHERE id = %s", (user_id,), fetch='one')
    if not user or not user['region']:
        return []
    return execute_query(
        """SELECT l.id, l.name, r.name AS region_name
           FROM locations l
           JOIN regions r ON l.region_id = r.id
           WHERE r.name = %s""",
        (user['region'],), fetch='all'
    )

def add_outlet(name, address, phone_contact, location_id, classification, outlet_type, user_id, gps_lat, gps_long, image_key):
    return execute_query(
        """INSERT INTO outlets (name, address, phone_contact, location_id, classification, outlet_type, onboarded_by_user_id, gps_lat, gps_long, outlet_image_key)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (name, address, location_id) DO NOTHING""",
        (name, address, phone_contact, location_id, classification, outlet_type, user_id, gps_lat, gps_long, image_key), fetch=None
    )

def add_posm_deployment(outlet_id, user_id, deployed_posms, before_key, after_key, gps_lat, gps_long):
    return execute_query(
        """INSERT INTO posm_deployments (outlet_id, deployed_by_user_id, deployed_posms, before_image_key, after_image_key, gps_lat, gps_long, deployed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (outlet_id, deployed_at) DO NOTHING""",
        (outlet_id, user_id, psycopg2.extras.Json(deployed_posms), before_key, after_key, gps_lat, gps_long), fetch=None
    )

def add_msl_sos_track(outlet_id, user_id, sos_data, msl_count, image_key, gps_lat, gps_long):
    return execute_query(
        """INSERT INTO msl_sos (outlet_id, tracked_by_user_id, sos_data, msl_count, shelf_image_key, gps_lat, gps_long, tracked_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (outlet_id, tracked_at) DO NOTHING""",
        (outlet_id, user_id, psycopg2.extras.Json(sos_data), msl_count, image_key, gps_lat, gps_long), fetch=None
    )

def get_user_outlets(user_id):
    return execute_query(
        """SELECT o.id, o.name, o.address, o.phone_contact, o.outlet_type, o.classification, 
                  l.name AS location_name, r.name AS region_name
           FROM outlets o
           JOIN locations l ON o.location_id = l.id
           JOIN regions r ON l.region_id = r.id
           WHERE o.onboarded_by_user_id = %s""",
        (user_id,)
    )

def get_posms():
    return execute_query("SELECT * FROM posms")

def get_skus_grouped():
    skus = execute_query("SELECT s.id, s.name, c.name AS category FROM skus s JOIN categories c ON s.category_id = c.id")
    grouped = {}
    for sku in skus:
        category = sku['category']
        if category not in grouped:
            grouped[category] = []
        grouped[category].append({'id': sku['id'], 'name': sku['name']})
    return grouped
#-------------------------------------------------------------------------------
import streamlit as st
from passlib.hash import bcrypt
from db.db_utils import add_user, get_regions

st.title("Merchandiser/Recruiter Signup")

with st.form("signup_form"):
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["merchandiser", "recruiter"])
    regions = get_regions()
    region_options = [r['name'] for r in regions]
    selected_regions = st.multiselect("Select Regions of Work", region_options)
    submit_button = st.form_submit_button("Sign Up")

    if submit_button:
        if not (email and phone and password and selected_regions):
            st.error("Please fill all fields and select at least one region.")
        else:
            password_hash = bcrypt.hash(password)
            result = add_user(email, phone, password_hash, role, selected_regions)
            if result is not None:
                st.success("Signup successful! Please log in.")
            else:
                st.error("Signup failed: Email already exists.")