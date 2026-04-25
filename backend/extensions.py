"""
extensions.py — Single source of truth for Flask extensions.

All extensions are instantiated here (not in app.py) so that
route files can import directly from this module without
creating a second instance, avoiding the "app not registered"
RuntimeError in the Flask application factory pattern.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
