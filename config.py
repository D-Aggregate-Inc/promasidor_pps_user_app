import os

DB_HOST = os.getenv('DB_HOST', 'postgresqlppspromasidor-do-user-4247704-0.e.db.ondigitalocean.com')
DB_PORT = os.getenv('DB_PORT', '25060')
DB_NAME = os.getenv('DB_NAME', 'defaultdb')
DB_USER = os.getenv('DB_USER', 'doadmin')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'AVNS_DGMA2Iy5H2yDTXoeGrf')
DB_SSLMODE = 'require'

SPACES_KEY = os.getenv('SPACES_KEY', 'DO00NJLZHJZXDV2CWCAU')
SPACES_SECRET = os.getenv('SPACES_SECRET', 'JFFpbO7qKS/vhx4ziUT1wKsV9M92Az44WAzfAeW5/xA')
SPACES_REGION = 'fra1'  # e.g., your region
SPACES_BUCKET = 'promassidorpps_image'
SPACES_ENDPOINT = f'https://alphageekimage.fra1.digitaloceanspaces.com'