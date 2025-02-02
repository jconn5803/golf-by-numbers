from flask_sqlalchemy import SQLAlchemy

# Create the SQLAlchemy instance
db = SQLAlchemy()

from .user import User
from .course import Course
from .round import Round

def init_app(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)
