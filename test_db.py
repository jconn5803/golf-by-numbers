from models import db  # Adjust import paths as necessary
from models.user import User
from models.course import Course
from models.round import Round
from app import app  # Ensure this points to your Flask app instance


from sqlalchemy.sql import text  # Import the `text` function for raw SQL queries


# Start an application context
with app.app_context():
    # Step 1: Test database connection
    print("Testing database connection...")
    try:
        db.session.execute(text("SELECT 1"))  # Explicitly use `text` for raw SQL
        print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {e}")
        exit(1)

    # Step 2: Test adding a user
    print("Testing User table...")
    try:
        test_user = User(username="testuser", email="testuser@example.com", password_hash="hashedpassword")
        db.session.add(test_user)
        db.session.commit()
        print("User added successfully!")

        # Query the user
        queried_user = User.query.filter_by(username="testuser").first()
        assert queried_user is not None, "User not found in database!"
        print(f"Queried User: {queried_user.username}, {queried_user.email}")

    except Exception as e:
        print(f"Error testing User table: {e}")
        db.session.rollback()

    # Step 3: Test adding a course
    print("Testing Course table...")
    try:
        test_course = Course(name="Test Course", location="Test Location")
        db.session.add(test_course)
        db.session.commit()
        print("Course added successfully!")

        # Query the course
        queried_course = Course.query.filter_by(name="Test Course").first()
        assert queried_course is not None, "Course not found in database!"
        print(f"Queried Course: {queried_course.name}, {queried_course.location}")

    except Exception as e:
        print(f"Error testing Course table: {e}")
        db.session.rollback()

    # Step 4: Cleanup
    print("Cleaning up test data...")
    try:
        if queried_user:
            db.session.delete(queried_user)
        if queried_course:
            db.session.delete(queried_course)
        db.session.commit()
        print("Test data cleaned up successfully!")
    except Exception as e:
        print(f"Error during cleanup: {e}")
        db.session.rollback()

print("Database test complete!")
