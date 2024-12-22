from . import db
from sqlalchemy.orm import relationship

class User(db.Model):
    __tablename__ = 'users'

    userID = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # One-to-many relationship with rounds
    rounds = relationship("Round", back_populates="user")
