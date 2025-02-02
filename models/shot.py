from . import db
from sqlalchemy.orm import relationship

# Set up the Shot table
class Shot(db.Model):
    __tablename__ = 'shots'

    shotID = db.Column(db.Integer, primary_key=True)
    roundID = db.Column(db.Integer, db.ForeignKey('rounds.roundID'), nullable=False)
    holeID = db.Column(db.Integer, db.ForeignKey('holes.holeID'), nullable=False)  
    distance_before = db.Column(db.Float, nullable=False)
    lie_before = db.Column(db.String(50), nullable=False)
    distance_after = db.Column(db.Float, nullable= False)
    lie_after = db.Column(db.String(50), nullable=False)
    shot_type = db.Column(db.String(50), nullable=False)
    strokes_gained = db.Column(db.Float, nullable=False)
    miss_direction = db.Column(db.String, default = "None")

    # Relationships
    round = relationship("Round", back_populates="shots")
    holes = relationship("Hole", back_populates="shots")  