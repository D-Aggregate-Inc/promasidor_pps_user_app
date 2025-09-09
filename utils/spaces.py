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