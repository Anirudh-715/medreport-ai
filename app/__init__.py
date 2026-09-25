"""
Flask application factory.
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize SQLAlchemy
db = SQLAlchemy()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configuration
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

    # Database configuration
    base_dir = os.path.abspath(os.path.dirname(__file__))
    instance_dir = os.path.join(os.path.dirname(base_dir), "instance")
    os.makedirs(instance_dir, exist_ok=True)
    db_file = os.path.join(instance_dir, "reports.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", f"sqlite:///{db_file}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Upload folder
    upload_folder = os.path.join(os.path.dirname(base_dir), "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder

    # Initialize extensions
    db.init_app(app)

    # Register routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Create database tables
    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    return app
