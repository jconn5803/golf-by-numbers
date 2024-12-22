from . import db
from sqlalchemy.orm import relationship

class Course(db.Model):
    __tablename__ = 'courses'

    courseID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    location = db.Column(db.String(200))

    # Relationships
    tees = relationship("Tee", back_populates="course", cascade="all, delete-orphan")
    holes = relationship("Hole", back_populates="course", cascade="all, delete-orphan")
    rounds = db.relationship("Round", back_populates="course")

class Tee(db.Model):
    __tablename__ = 'tees'

    teeID = db.Column(db.Integer, primary_key=True)
    courseID = db.Column(db.Integer, db.ForeignKey('courses.courseID'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    total_distance = db.Column(db.Integer)
    course_par = db.Column(db.Integer, nullable = False)


    # Relationships
    course = relationship("Course", back_populates="tees")

class Hole(db.Model):
    __tablename__ = 'holes'

    holeID = db.Column(db.Integer, primary_key=True)
    courseID = db.Column(db.Integer, db.ForeignKey('courses.courseID'), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    par = db.Column(db.Integer, nullable=False)
    distance = db.Column(db.Integer)

    # Relationships
    course = relationship("Course", back_populates="holes")
