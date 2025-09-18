from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
import streamlit as st
import warnings
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
import logging

logging.basicConfig(filename='app.log', level=logging.ERROR)

warnings.filterwarnings('ignore')
# Initialize connection pool
@st.cache_resource
def init_connection_pool():
    return SimpleConnectionPool(
        minconn=1,  # Minimum connections
        maxconn=10,  # Maximum connections (adjust based on DB plan)
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode='require'  # Ensure SSL for Digital Ocean
    )

# @st.cache_resource
# def init_connection_pool():
#     return SimpleConnectionPool(
#         minconn=1,
#         maxconn=10,
#         host=DB_HOST,
#         port=DB_PORT,
#         dbname=DB_NAME,
#         user=DB_USER,
#         password=DB_PASSWORD,
#         sslmode='require'
#     )

# @st.cache_data(ttl=300)
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

# User functions
def get_regions():
    return execute_query("SELECT id, name FROM region", fetch='all')

def get_locations_by_user_region(user_id):
    user = execute_query("SELECT merchandiser_region FROM users WHERE id = %s", (user_id,), fetch='one')
    if not user or not user['merchandiser_region']:
        return []
    return execute_query(
        """SELECT l.id, l.name, r.name AS region_name
           FROM locations_by_region l
           JOIN region r ON l.region_id = r.id
           WHERE r.name = %s""",
        (user['merchandiser_region'],), fetch='all'
    )
def get_user_by_email(email):
    return execute_query("SELECT * FROM users WHERE email = %s", (email,), fetch='one')

def get_outlet_by_phone_contact(phone_contact):
    return execute_query("SELECT * FROM outlets WHERE phone_contact = %s", (phone_contact,), fetch='one')

def disable_user(user_id):
    execute_query("UPDATE users SET is_active = FALSE WHERE id = %s", (user_id,), fetch=None)

def add_user(email, phone, password_hash, role, merchandiser_region):
    return execute_query(
        "INSERT INTO users (email, phone, password_hash, role, merchandiser_region) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (email) DO NOTHING",
        (email, phone, password_hash, role,merchandiser_region), fetch=None
    )
def add_location_by_region(region_id,name):
    execute_query("INSERT INTO locations_by_region(region_id,name) VALUES (%s, %s)",(region_id,name), fetch=None)
# Other functions (add_state, add_location, etc.) remain similar
def add_region(name):
    execute_query("INSERT INTO region (name) VALUES (%s)", (name,), fetch=None)

def add_state(name):
    execute_query("INSERT INTO states (name) VALUES (%s)", (name,), fetch=None)

def add_bank(name):
    execute_query("INSERT INTO banks (name) VALUES (%s)", (name,), fetch=None)

def add_location(state_id, name):
    execute_query("INSERT INTO locations (state_id, name) VALUES (%s, %s)", (state_id, name), fetch=None)



def add_sku(category, name, description, expiry_tracking):
    execute_query(
        "INSERT INTO skus (category, name, description, expiry_tracking) VALUES (%s, %s, %s, %s)",
        (category, name, description, expiry_tracking), fetch=None
    )

def add_posm(name):
    execute_query("INSERT INTO posms (name) VALUES (%s)", (name,), fetch=None)

def add_outlet(name, location_id, classification,outlet_type, user_id, gps_lat, gps_long, image_key,phone_contact, outlet_number, outlet_address,  
                   outlet_landmark,contact_person,region,account_no, bank_name,account_name):
    execute_query(
        """INSERT INTO outlets (name,location_id, classification, outlet_type, onboarded_by_user_id, gps_lat, gps_long, outlet_image_key,phone_contact, outlet_number, outlet_address,  
                   outlet_landmark,contact_person,region,account_no,bank_name,account_name)
        VALUES (%s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s, %s,%s)""",
        (name, location_id, classification,outlet_type, user_id, gps_lat, gps_long, image_key,phone_contact, outlet_number, outlet_address,  
                   outlet_landmark,contact_person,region,account_no,bank_name,account_name), fetch=None
    )

def add_posm_deployment(outlet_id, user_id, deployed_posms, before_key, after_key, gps_lat, gps_long):
    execute_query(
        """INSERT INTO posm_deployments (outlet_id, deployed_by_user_id, deployed_posms, before_image_key, after_image_key, gps_lat, gps_long)
        VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (outlet_id, user_id, psycopg2.extras.Json(deployed_posms), before_key, after_key, gps_lat, gps_long), fetch=None
    )

def add_msl_sos_track(outlet_id, user_id, sos_data, msl_count, image_key, gps_lat, gps_long,outlet_info):
    execute_query(
        """INSERT INTO msl_sos_tracks (outlet_id, tracked_by_user_id, sos_data, msl_count, shelf_image_key, gps_lat, gps_long,outlet_info)
        VALUES (%s, %s, %s, %s, %s, %s, %s,%s)""",
        (outlet_id, user_id, psycopg2.extras.Json(sos_data), msl_count, image_key, gps_lat, gps_long,outlet_info), fetch=None
    )

def add_oos_track(outlet_id, user_id, oos_data, gps_lat, gps_long,outlet_info):
    execute_query(
        """INSERT INTO oos_tracks (outlet_id, tracked_by_user_id, oos_data, gps_lat, gps_long,outlet_info)
        VALUES (%s, %s, %s, %s, %s,%s)""",
        (outlet_id, user_id, psycopg2.extras.Json(oos_data), gps_lat, gps_long,outlet_info), fetch=None
    )

def add_order_track(outlet_id, user_id, order_data, gps_lat, gps_long, outlet_info):
    execute_query(
        """INSERT INTO order_tracks (outlet_id, tracked_by_user_id, order_data, gps_lat, gps_long, outlet_info)
        VALUES (%s, %s, %s, %s, %s, %s)""",
        (outlet_id, user_id, psycopg2.extras.Json(order_data), gps_lat, gps_long, outlet_info), fetch=None
    )

def add_pricing_track(outlet_id, user_id,price_data, gps_lat, gps_long, outlet_info):
    execute_query(
        """INSERT INTO price_tracks (outlet_id, tracked_by_user_id, price_data, gps_lat, gps_long, outlet_info)
        VALUES (%s, %s, %s, %s, %s,%s)""",
        (outlet_id, user_id, psycopg2.extras.Json(price_data), gps_lat, gps_long, outlet_info), fetch=None
    )


# def add_expiry_track(outlet_id, user_id, expiry_data, gps_lat, gps_long):
#     execute_query(
#         """INSERT INTO expiry_tracks (outlet_id, tracked_by_user_id, expiry_data, gps_lat, gps_long)
#         VALUES (%s, %s, %s, %s, %s)""",
#         (outlet_id, user_id, psycopg2.extras.Json(expiry_data), gps_lat, gps_long), fetch=None
#     )


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

def get_skus_grouped():
    skus = execute_query("SELECT * FROM skus ORDER BY category, name")
    grouped = {}
    for sku in skus:
        cat = sku['category']
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(sku)
    return grouped

def get_posms():
    return execute_query("SELECT * FROM posms")