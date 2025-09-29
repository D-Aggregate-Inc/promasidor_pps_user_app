import boto3
import uuid
import io
import logging
from PIL import Image, ImageDraw, ImageFont
import pytz
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
        max_size=(2048, 2048))
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)  # Optimize size

        # Add watermark with GPS and datetime
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)  # Default font, size 20
        except IOError:
            font = ImageFont.load_default()  # Fallback if arial.ttf unavailable
        current_time = datetime.now(pytz.timezone('Africa/Lagos')).strftime('%Y:%m:%d %H:%M:%S')
        gps_text = f"Lat: {gps_lat:.6f}, Lon: {gps_long:.6f}" if gps_lat is not None and gps_long is not None else "No GPS"
        watermark_text = f"{current_time}\n{gps_text}"
        draw.text((10, 10), watermark_text, fill="white", font=font, stroke_width=1, stroke_fill="black")

        # Save image to buffer
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=95, optimize=True, progressive=True)
        buffer.seek(0)

        key = f"{folder}/{uuid.uuid4()}.jpg"
        client.put_object(Bucket=SPACES_BUCKET, Key=key, Body=buffer.getvalue(), ACL='public-read')
        return key
    except Exception as e:
        logging.error(f"Image upload failed: {e}")
        return None