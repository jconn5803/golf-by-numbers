from . import db

class Round(db.Model):
    __tablename__ = 'rounds'

    roundID = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.courseID'), nullable=False)
    tee_id = db.Column(db.Integer, db.ForeignKey('tees.teeID'), nullable=False)
    date_played = db.Column(db.Date, nullable=False)
    round_type = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable = True)
    score_to_par = db.Column(db.Integer, nullable = True)

    # -- NEW: store aggregated SG by shot type
    sg_off_tee = db.Column(db.Float, default=0.0)
    sg_approach = db.Column(db.Float, default=0.0)
    sg_around_green = db.Column(db.Float, default=0.0)
    sg_putting = db.Column(db.Float, default=0.0)

    # Relationships
    user = db.relationship("User", back_populates="rounds")
    course = db.relationship("Course", back_populates="rounds")
    shots = db.relationship("Shot", back_populates="round", cascade="all, delete-orphan")
    tee = db.relationship("Tee", back_populates="rounds")
    hole_stats = db.relationship("HoleStats", back_populates="round", cascade="all, delete-orphan")

class HoleStats(db.Model):
    __tablename__ = "hole_stats"

    holeStatsID = db.Column(db.Integer, primary_key=True)
    roundID = db.Column(db.Integer, db.ForeignKey('rounds.roundID'), nullable=False)
    holeID = db.Column(db.Integer, db.ForeignKey('holes.holeID'), nullable=False)
    
    # True if the user hit the green in regulation
    gir = db.Column(db.Boolean, default=False, nullable = False) 
    
    # True if user’s tee shot ended on the fairway (for par 4, par 5)
    fairway_hit = db.Column(db.Boolean, default=False, nullable = True)

    # Up and down (1 = yes, 0 = no, Null = not applicable)
    up_and_down = db.Column(db.Boolean, default = False, nullable = True)

    # Hole score
    hole_score = db.Column(db.Integer, nullable = False)

    # Relationship
    round = db.relationship("Round", back_populates="hole_stats")
    hole = db.relationship("Hole", back_populates="hole_stats")