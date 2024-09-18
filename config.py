import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    MYSQL_PASSWORD = os.environ.get('mysql_password')
    SQLALCHEMY_DATABASE_URI = f'mysql+mysqldb://TT:{MYSQL_PASSWORD}@localhost/TTRequests'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Twilio configuration
    TWILIO_ACCOUNT_SID = os.environ.get('twilio_account_sid')
    TWILIO_AUTH_TOKEN = os.environ.get('twilio_auth_token')
    TWILIO_WHATSAPP_FROM = 'whatsapp:+12172861211'

    # Google OAuth configuration
    GOOGLE_CLIENT_ID = os.environ.get('google_client_id')
    GOOGLE_CLIENT_SECRET = os.environ.get('google_client_secret')
    GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'
