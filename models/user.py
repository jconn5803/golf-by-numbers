from . import db
from sqlalchemy.orm import relationship
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    userID = db.Column(db.Integer, primary_key=True, unique=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(128), nullable = False)
    last_name = db.Column(db.String(128), nullable = False)

    # Subscription plan
    stripe_customer_id = db.Column(db.String(120), nullable=True)
    subscription_active = db.Column(db.Boolean, default=False)
    subscription_plan = db.Column(db.String(50), nullable=True)

    



    # One-to-many relationship with rounds
    rounds = relationship("Round", back_populates="user")

    def get_id(self):
        """Return the unique ID for the user as a string."""
        return str(self.userID)
    
