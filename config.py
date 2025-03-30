import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Use SQLite in development
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'instance/app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoid overhead of modification tracking
    SECRET_KEY = os.getenv("SECRET_KEY", "your-default-secret-key")
