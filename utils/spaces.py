import boto3
from botocore.client import Config
import streamlit as st
from config import SPACES_KEY, SPACES_SECRET, SPACES_REGION, SPACES_BUCKET, SPACES_ENDPOINT
from PIL import Image
import io
import uuid
import logging

logging.basicConfig(filename='app.log', level=logging.ERROR)

@st.cache_resource
def get_spaces_client():
    return boto3.client(
        's3',
        aws_access_key_id=SPACES_KEY,
        aws_secret_access_key=SPACES_SECRET,
        endpoint_url=SPACES_ENDPOINT,
        config=Config(signature_version='s3v4')
    )

def upload_image(image_bytes, folder='images'):
    try:
        client = get_spaces_client()
        key = f"{folder}/{uuid.uuid4()}.jpg"
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert RGBA to RGB if necessary
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Resize for efficiency (optional: adjust max size as needed)
        img.thumbnail((1024, 1024))
        
        # Save to buffer as JPEG
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)  # Reduce quality to optimize size
        buffer.seek(0)
        
        # Upload to Digital Ocean Spaces
        client.put_object(Bucket=SPACES_BUCKET, Key=key, Body=buffer.getvalue(), ACL='public-read')
        return key
    except Exception as e:
        logging.error(f"Image upload failed: {e}")
        st.error(f"Failed to upload image: {e}")
        return None