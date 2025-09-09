import boto3
import uuid
import io
import logging
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
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

def dms_to_decimal(degrees, minutes, seconds, direction):
    """Convert degrees, minutes, seconds to decimal degrees."""
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal

def get_exif(img):
    """Extract or create EXIF data for an image."""
    exif_data = img.getexif()
    if not exif_data:
        exif_data = Image.Exif()
    return exif_data

def set_gps_exif(exif_data, gps_lat, gps_long):
    """Set GPS EXIF tags."""
    gps_ifd = {}
    lat_deg = int(abs(gps_lat))
    lat_min = int((abs(gps_lat) - lat_deg) * 60)
    lat_sec = int((abs(gps_lat) - lat_deg - lat_min / 60) * 3600 * 100)
    lon_deg = int(abs(gps_long))
    lon_min = int((abs(gps_long) - lon_deg) * 60)
    lon_sec = int((abs(gps_long) - lon_deg - lon_min / 60) * 3600 * 100)

    gps_ifd[GPSTAGS.get('GPSLatitude')] = [(lat_deg, 1), (lat_min, 1), (lat_sec, 100)]
    gps_ifd[GPSTAGS.get('GPSLatitudeRef')] = 'N' if gps_lat >= 0 else 'S'
    gps_ifd[GPSTAGS.get('GPSLongitude')] = [(lon_deg, 1), (lon_min, 1), (lon_sec, 100)]
    gps_ifd[GPSTAGS.get('GPSLongitudeRef')] = 'E' if gps_long >= 0 else 'W'

    exif_data[0x8825] = gps_ifd  # GPSInfo tag
    return exif_data

def upload_image(image_bytes, folder='images', gps_lat=None, gps_long=None):
    try:
        client = get_spaces_client()
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img.thumbnail((1024, 1024))  # Optimize size
        buffer = io.BytesIO()

        # Add EXIF metadata
        exif_data = get_exif(img)
        
        # Set datetime
        current_time = datetime.now().strftime('%Y:%m:%d %H:%M:%S')
        exif_data[TAGS.get('DateTimeOriginal')] = current_time
        
        # Set GPS data if provided
        if gps_lat is not None and gps_long is not None:
            exif_data = set_gps_exif(exif_data, gps_lat, gps_long)

        # Save image with EXIF data
        img.save(buffer, format="JPEG", quality=85, exif=exif_data)
        buffer.seek(0)

        key = f"{folder}/{uuid.uuid4()}.jpg"
        client.put_object(Bucket=SPACES_BUCKET, Key=key, Body=buffer.getvalue(), ACL='public-read')
        return key
    except Exception as e:
        logging.error(f"Image upload failed: {e}")
        return None