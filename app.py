from flask import Flask, render_template, request, session
from models.sg_model import SG_calculator  # Import your SG calculator model
from models.unit_converter import metres_to_yards, metres_to_feet

# Import database modules
from config import Config
from models import db, init_app, User
from flask_migrate import Migrate

# Import login modules
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key_here"
app.config.from_object(Config)

# Initialize the database
init_app(app)
migrate = Migrate(app, db)

# Initialse the flask login 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect users to the login page if not logged in

@login_manager.user_loader
def load_user(userID):
    return User.query.get(int(userID))

# Route for user signup
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user already exists
        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            return "User already exists", 400

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create a new user
        new_user = User(username=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return "User registered successfully!", 200

    return render_template('register.html')

# Route for user login 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Fetch the user from the database
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return "Invalid credentials", 401

        # Log the user in
        login_user(user)
        return "Logged in successfully!", 200

    return render_template('login.html')

# Add a route for user logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return "Logged out successfully!", 200




@app.route('/', methods=['GET', 'POST'])
def home():
    sg = None
    sg_color = None
    errors = {}
    before_distance = None
    before_lie = None
    after_distance = None
    after_lie = None
    penalty = False
    oob = False
    hazard = False

    # Retrieve the last selected unit from the session, default to "yards"
    unit = session.get("unit", "yards")

    if request.method == 'POST':
        # Extract the unit from the toggle value
        unit = request.form.get("unit", "yards")
        session["unit"] = unit  # Save the user's preference in the session

        # Extract data from form
        before_lie = request.form.get('before_lie')
        
        try:
            before_distance = float(request.form.get('before_distance'))
            if (unit == "yards" and before_distance > 600) or (unit == "metres" and before_distance > 548):
                errors['before_distance'] = (
                    "Distance must not exceed 600 yards." if unit == "yards" else "Distance must not exceed 548 metres."
                )
            if (unit == "yards" and before_lie == "Green" and before_distance > 110) or (unit == "metres" and before_lie == "Green" and before_distance > 33.5):
                errors["before_distance"] = (
                    "Strokes Gained on Green can only be calculated to 110 feet." if unit == "yards" else "Strokes Gained on Green can only be calculated to 33.5 metres."
                )
        except ValueError:
            errors['before_distance'] = "Invalid value for distance."

        
        after_lie = request.form.get('after_lie')
        if request.form.get('after_lie') == 'In the Hole':
            after_distance = 0  # Ensure after_distance is 0 if "In the Hole" is selected
        else:
            after_distance = float(after_distance) if after_distance else None
        
        try:
            
            if request.form.get('after_lie') == 'In the Hole':
                after_distance = 0  # Ensure after_distance is 0 if "In the Hole" is selected
            else:
                after_distance = float(request.form.get("after_distance"))
            if (unit == "yards" and after_distance > 600) or (unit == "metres" and after_distance > 548):
                errors['after_distance'] = (
                    "Distance must not exceed 600 yards." if unit == "yards" else "Distance must not exceed 548 metres."
                )
            if (unit == "yards" and after_lie == "Green" and after_distance > 110) or (unit == "metres" and after_lie == "Green" and after_distance > 33.5):
                errors["after_distance"] = (
                    "Strokes Gained on Green can only be calculated to 110 feet." if unit == "yards" else "Strokes Gained on Green can only be calculated to 33.5 metres."
                )
        except ValueError:
            errors['after_distance'] = "Invalid value for distance."

        

        # Convert distances to yards for calculation, keeping original values for display
        if unit == "metres":
            converted_before_distance = metres_to_yards(before_distance) if before_distance else None
            converted_after_distance = metres_to_yards(after_distance) if after_distance else None
        else:
            converted_before_distance = before_distance
            converted_after_distance = after_distance

        # Extract penalty, oob, and hazard values
        penalty = request.form.get("penalty") == '1'  # If checked, 'penalty' will be '1'
        oob = request.form.get("oob") == '1'  # If checked, 'oob' will be '1'
        hazard = request.form.get("hazard") == '1'  # If checked, 'hazard' will be '1'

        # Calculate strokes gained if no errors
        if not errors:
            sg = SG_calculator(converted_before_distance, before_lie, converted_after_distance, after_lie)

            if penalty:
                if oob:
                    sg = -2  # Subtract 2 strokes for OOB / Lost Ball
                elif hazard:
                    sg -= 1  # Subtract 1 stroke for Hazard / Unplayable

           # Determine the background color based on sg value
            # Determine the background color based on sg value
            if sg < 0:
                # Negative values: Dark red to dark grey gradient with enhanced red intensity
                intensity = int((1 + sg) * 200)  # Scale `-1` to `0` into `0` to `200`
                red_intensity = 170  # Keep red component strong
                sg_color = f"rgb({red_intensity}, {intensity // 2}, {intensity // 2})"  # Dark red with fade
            elif sg > 0:
                # Positive values: Dark grey to dark green gradient
                intensity = int(abs(sg) * 150)  # Scale `0` to `1` into `0` to `150`
                sg_color = f"rgb({128 - (intensity // 3)}, {128 + intensity}, {128 - (intensity // 3)})"  # Grey fades to softer green
            else:
                # Neutral value (sg = 0)
                sg_color = "rgb(128, 128, 128)"  # Dark grey

    return render_template('index.html', sg=sg, sg_color=sg_color, errors=errors, 
                           before_distance=before_distance, before_lie=before_lie,
                           after_distance=after_distance, after_lie=after_lie,
                           penalty=penalty, oob=oob, hazard=hazard, unit=unit)

if __name__ == '__main__':
    app.run(debug=True)
