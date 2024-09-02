import os


class Config:
    MYSQL_PASSWORD = os.getenv('mysql_password')
    SQLALCHEMY_DATABASE_URI = f'mysql://TT:{MYSQL_PASSWORD}@localhost/TTRequests'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Twilio configuration
    TWILIO_ACCOUNT_SID = os.getenv('twilio_account_sid')
    TWILIO_AUTH_TOKEN = os.getenv('twilio_auth_token')
    TWILIO_WHATSAPP_FROM = 'whatsapp:+12172861211'

    # Google OAuth configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or 'your_google_client_id'
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or 'your_google_client_secret'
    GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'
