from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config

# Initialize extensions (but do not bind to an app yet)
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()  # Initialize the migrate object but don't bind it yet

def create_app():
    app = Flask(__name__)

    # Load configuration from Config class
    app.config.from_object(Config)

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)  # Bind Flask-Migrate to the app and SQLAlchemy instance

    # Import routes and models *after* app and db are initialized
    with app.app_context():
        from app import routes, models  # Avoid circular imports

    return app

