from . import db

class Round(db.Model):
    __tablename__ = 'rounds'

    roundID = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.courseID'), nullable=False)
    date_played = db.Column(db.Date, nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="rounds")
    course = db.relationship("Course", back_populates="rounds")
