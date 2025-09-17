from altair import SampleTransform
from passlib.hash import bcrypt
import streamlit as st
# import bcrypt
import logging
from db.db_utils import get_user_by_email, execute_query, add_user

logging.basicConfig(filename='app.log', level=logging.ERROR)

def hash_password(password):
    try:
        # Ensure password is a string, then encode to bytes
        if not isinstance(password, str):
            password = str(password)
        hashed = bcrypt.hash(password)
        # Return as string for database storage
        return hashed.decode('utf-8') if isinstance(hashed, bytes) else hashed
    except Exception as e:
        logging.error(f"Password hashing failed: {e}")
        st.error(f"Failed to hash password: {e}")
        return None



def verify_password(stored_hash, provided_password):
    try:
        # Ensure inputs are bytes
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        if isinstance(provided_password, str):
            provided_password = provided_password.encode('utf-8')
        return bcrypt.verify(provided_password, stored_hash)
    except ValueError as e:
        logging.error(f"Invalid password hash: {e}")
        st.error(f"Invalid password hash: {e}")
        return False
    except Exception as e:
        logging.error(f"Password verification failed: {e}")
        st.error(f"Password verification failed: {e}")
        return False

# def signup(email, phone, password, role='merchandiser'):  
#     if get_user_by_email(email):
#         st.error("Email already exists")
#         return False
#     password_hash = hash_password(password)
#     add_user(email, phone, password_hash, role)
#     return True

def signup(email, phone, password,merchandiser_region, role='merchandiser', ):   # Default to merchandiser; admin sets builders
    if get_user_by_email(email):
        st.error("Email already exists")
        return False
    password_hash = hash_password(password)
    if not password_hash:
        return False
    add_user(email, phone, password_hash, merchandiser_region,role)
    return True

def login(email, password):
    user = get_user_by_email(email)
    print(user)
    if user and user['is_active'] and verify_password(user['password_hash'], password):
        st.session_state['user'] = user
        return True
    st.error("Invalid email or password or account disabled")
    return False

def reset_password(email, new_password):
    user = get_user_by_email(email)
    if user:
        new_hash = hash_password(new_password)
        execute_query("UPDATE users SET password_hash = %s WHERE email = %s", (new_hash, email), fetch=None)
        return True
    return False

def logout():
    if 'user' in st.session_state:
        del st.session_state['user']
