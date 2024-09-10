from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config


# Initialize extensions (but do not bind to an app yet)
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    # Load configuration from Config class
    app.config.from_object(Config)

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)

    # Import routes and models *after* app and db are initialized
    with app.app_context():
        from app import routes, models  # Moved import here to avoid circular imports

        # Create the database tables (after the app is fully initialized)
        db.create_all()

    return app

