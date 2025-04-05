import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Common configurations for both development and production
    SECRET_KEY = os.getenv("SECRET_KEY", "your-default-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False  # Default to False

class DevelopmentConfig(Config):
    DEBUG = True  # Enable debug mode for development
    # Use SQLite for development
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'instance/app.db')}"
    # Get the test Stripe keys
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_ENDPOINT_SECRET=os.getenv("STRIPE_ENDPOINT_SECRET")
    STRIPE_MONTHLY_PRICE_ID=os.getenv("STRIPE_MONTHLY_PRICE_ID")
    STRIPE_ANNUAL_PRICE_ID=os.getenv("STRIPE_ANNUAL_PRICE_ID")
    STRIPE_DAILY_PRICE_ID=os.getenv("STRIPE_DAILY_PRICE_ID")

class ProductionConfig(Config):
    DEBUG = False  # Ensure debug is off in production
    # Get the production database URI from an environment variable.
    # For example, for PostgreSQL: "postgresql://user:password@host:port/dbname"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)



   

