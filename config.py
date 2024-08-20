import os


class Config:
    MYSQL_PASSWORD = os.getenv('mysql_password')
    SQLALCHEMY_DATABASE_URI = f'mysql://TT:{MYSQL_PASSWORD}@localhost/TTRequests'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
