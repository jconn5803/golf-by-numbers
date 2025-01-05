from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from models.sg_model import SG_calculator, shot_type_func  # Import your SG calculator model
from models.unit_converter import metres_to_yards, metres_to_feet
from models.gir_fw_tracking import update_gir_fairway

# Import database modules
from config import Config
from models import db, init_app, User
from models.course import Tee, Hole, Course
from models.shot import Shot
from models.round import Round, HoleStats
from flask_migrate import Migrate
from sqlalchemy import func

# Import login modules
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import datetime



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
        # Retrieve form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user already exists by username or email
        user_exists = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if user_exists:
            return "User already exists", 400

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create a new user record
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password_hash=hashed_password
        )

        # Add to database
        db.session.add(new_user)
        db.session.commit()

        return "User registered successfully!", 200

    # If GET request, just show the register template
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


# Add a route to display a list of courses in the database
@app.route('/courses')
def view_courses():
    courses = Course.query.all()
    return render_template('courses.html', courses=courses)

# Add a route to add a course
@app.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    if request.method == 'POST':
        course_name = request.form.get('name')
        location = request.form.get('location')

        new_course = Course(name=course_name, location=location)
        db.session.add(new_course)
        db.session.commit()

        return redirect('/courses')

    return render_template('add_course.html')

# Add a route to populate tees and holes 
@app.route('/add_tee/<int:course_id>', methods=['GET', 'POST'])
@login_required
def add_tee(course_id):
    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        name = request.form.get('name')
        total_distance = request.form.get('total_distance')
        course_par = request.form.get('course_par')

        new_tee = Tee(name=name, total_distance = total_distance, course_par = course_par, courseID=course.courseID)
        db.session.add(new_tee)
        db.session.commit()

        return redirect(f'/add_holes/{new_tee.teeID}')

    return render_template('add_tee.html', course=course)

# Add a route to add in the holes
@app.route('/add_holes/<int:tee_id>', methods=['GET', 'POST'])
@login_required
def add_holes(tee_id):
    tee = Tee.query.get_or_404(tee_id)
    if request.method == 'POST':
        # Get data from the form
        num_holes = int(request.form.get('num_holes', 18))
        holes_data = request.form.getlist('holes')
        pars_data = request.form.getlist('pars')
        distances_data = request.form.getlist('distances')

        # Add holes to the database
        for i in range(num_holes):
            hole = Hole(
                courseID=tee.courseID,
                teeID=tee.teeID,
                number=i + 1,
                par=int(pars_data[i]),
                distance=int(distances_data[i])
            )
            db.session.add(hole)

        db.session.commit()
        return redirect('/courses')  # Replace with the appropriate redirect
    
    return render_template('add_holes.html', tee=tee)

# Add a route to add a round in
from datetime import datetime

@app.route('/add_round', methods=['GET', 'POST'])
@login_required
def add_round():
    if request.method == 'POST':
        # Retrieve form data
        course_id = request.form.get('course')
        tee_id = request.form.get('tee')
        date_played_str = request.form.get('date_played')

        # Validate form data
        if not course_id or not tee_id or not date_played_str:
            return "All fields are required.", 400

        # Convert the date string to a Python date object
        try:
            date_played = datetime.strptime(date_played_str, "%Y-%m-%d").date()
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD.", 400

        # Create a new Round object
        new_round = Round(
            userID=current_user.userID,
            course_id=course_id,
            tee_id = tee_id,
            date_played=date_played
        )
        db.session.add(new_round)
        db.session.commit()

        # Redirect to the next page for shot entry
        return redirect(url_for('add_shots', roundID=new_round.roundID))

    # Retrieve course data for the form
    courses = Course.query.all()
    return render_template('add_round.html', courses=courses)

from flask import jsonify

# Add a route to put the shots in
@app.route('/add_shots/<int:roundID>', methods=['GET', 'POST'])
@login_required
def add_shots(roundID):
    round_data = Round.query.get_or_404(roundID)
    course = Course.query.get_or_404(round_data.course_id)
    tee_id = round_data.tee_id
    holes = Hole.query.filter_by(courseID=course.courseID, teeID=tee_id).order_by(Hole.number).all()

    if request.method == 'POST':
        # Initialise the score for the round
        round_score = 0
        # 1) Insert Shots + Track Shots per Hole
        for hole in holes:
            num_shots = 1
            hole_penalty_shots = 0
            while True:
                distance_str = request.form.get(f"hole_{hole.number}_shot_{num_shots}_distance")
                lie = request.form.get(f"hole_{hole.number}_shot_{num_shots}_lie")
                out_of_bounds = request.form.get(f"hole_{hole.number}_shot_{num_shots}_out_of_bounds") == "1"
                hazard = request.form.get(f"hole_{hole.number}_shot_{num_shots}_hazard") == "1"

                if not distance_str or not lie:
                    # We break if the fields for shot #num_shots are missing.
                    break

                distance = float(distance_str)

                # Code to specify what happens if OOB selected
                if out_of_bounds:
                    lie_after = "OOB" # Condtion already written into SG function 
                    distance_after = distance # Stil the same distance away
                    sg = SG_calculator(distance, lie, distance_after, lie_after)
                    hole_penalty_shots += 1
                else:
                    distance_after = (
                        float(request.form.get(f"hole_{hole.number}_shot_{num_shots + 1}_distance", 0))
                        if request.form.get(f"hole_{hole.number}_shot_{num_shots + 1}_distance")
                        else 0
                    )
                    lie_after = request.form.get(
                        f"hole_{hole.number}_shot_{num_shots + 1}_lie",
                        "In the Hole"
                    )

                    # Calculate the strokes gained normally
                    sg = SG_calculator(distance, lie, distance_after, lie_after)

                if hazard:
                    sg -= 1 # Subtract 1 if end up in a hazard
                    num_shots += 1
                    hole_penalty_shots += 1
                
                miss_direction = request.form.get(
                    f"hole_{hole.number}_shot_{num_shots}_miss_direction",
                    "None"
                )

                shot_type = shot_type_func(lie=lie, distance=distance, par=hole.par)

                new_shot = Shot(
                    roundID=roundID,
                    holeID=hole.holeID,
                    distance_before=distance,
                    lie_before=lie,
                    distance_after=distance_after,
                    lie_after=lie_after,
                    shot_type=shot_type,
                    strokes_gained=sg,
                    miss_direction=miss_direction,
                )
                db.session.add(new_shot)

                # We increment num_shots here,
                # so when we finally break, num_shots is 1 higher than the valid shots.
                num_shots += 1

            # Because the loop breaks when the next shot's fields are missing,
            # num_shots is now "one too many".
            # So the actual hole score = num_shots - 1
            hole_score = num_shots - 1 + hole_penalty_shots
            # Add on the hole_score to the round score
            round_score +=  hole_score


            if hole_score > 0:
                # Find or create HoleStats for this round+hole
                hole_stat = HoleStats.query.filter_by(
                    roundID=roundID, 
                    holeID=hole.holeID
                ).first()
                if not hole_stat:
                    hole_stat = HoleStats(roundID=roundID, holeID=hole.holeID)
                    db.session.add(hole_stat)

                hole_stat.hole_score = hole_score

        db.session.commit()

        # Update the fw hit/ gir hit
        update_gir_fairway(roundID, holes)


        # 2. Once all shots are inserted, compute aggregated SG:
        sg_off_tee = db.session.query(func.sum(Shot.strokes_gained))\
            .filter(Shot.roundID == roundID, Shot.shot_type == "Off the Tee").scalar() or 0.0

        sg_approach = db.session.query(func.sum(Shot.strokes_gained))\
            .filter(Shot.roundID == roundID, Shot.shot_type == "Approach").scalar() or 0.0

        sg_around_green = db.session.query(func.sum(Shot.strokes_gained))\
            .filter(Shot.roundID == roundID, Shot.shot_type == "Around the Green")\
            .scalar() or 0.0

        sg_putting = db.session.query(func.sum(Shot.strokes_gained))\
            .filter(Shot.roundID == roundID, Shot.shot_type == "Putting").scalar() or 0.0

        # 3. Update Round table
        round_data.sg_off_tee = sg_off_tee
        round_data.sg_approach = sg_approach
        round_data.sg_around_green = sg_around_green
        round_data.sg_putting = sg_putting
        round_data.score = round_score

        # Compute the round score to par
        # Retrieve this tee's par (no need to sum holes)
        this_tee = Tee.query.get_or_404(tee_id)
        # e.g., round_score - total par on this tee
        round_data.score_to_par = round_score - this_tee.course_par

        db.session.commit()

        return redirect('/dashboard')

    return render_template('add_shots.html', round_data=round_data, course=course, tee_id=tee_id, holes=holes)



@app.route('/dashboard')
@login_required
def dashboard():
    """
    Renders the main dashboard page with filters and placeholder for charts/cards.
    """
    # 1) Query user courses and rounds for filter dropdowns
    user_courses = (Course.query
                    .join(Round, Course.courseID == Round.course_id)
                    .filter(Round.userID == current_user.userID)
                    .distinct()
                    .all())
    user_rounds = (Round.query
                   .filter_by(userID=current_user.userID)
                   .order_by(Round.date_played.desc())
                   .all())

    return render_template(
        'dashboard.html',
        user_courses=user_courses,
        user_rounds=user_rounds
    )


@app.route('/api/sg_by_shot_type', methods=['GET'])
@login_required
def sg_by_shot_type():
    """
    Returns average strokes gained by shot type (Off Tee, Approach, Around Green, Putting),
    filtered by course, round, date range if specified.
    """
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # Query from Round table, computing the AVG of each SG column
    q = db.session.query(
        func.avg(Round.sg_off_tee).label('avg_off_tee'),
        func.avg(Round.sg_approach).label('avg_approach'),
        func.avg(Round.sg_around_green).label('avg_around_green'),
        func.avg(Round.sg_putting).label('avg_putting')
    ).filter(Round.userID == current_user.userID)

    if course_id:
        q = q.filter(Round.course_id == course_id)
    if round_id:
        q = q.filter(Round.roundID == round_id)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        q = q.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        q = q.filter(Round.date_played <= end_date)

    result = q.one()  # single row
    labels = ["Off the Tee", "Approach", "Around the Green", "Putting"]
    values = [
        float(result.avg_off_tee or 0),
        float(result.avg_approach or 0),
        float(result.avg_around_green or 0),
        float(result.avg_putting or 0)
    ]

    data = {
        "labels": labels,
        "values": values
    }
    return jsonify(data)


@app.route('/api/dashboard_stats', methods=['GET'])
@login_required
def dashboard_stats():
    """
    Returns multiple stats in one payload:
    - scoring_avg (AVG of Round.score)
    - scoring_avg_to_par (AVG of Round.score_to_par)
    - total_rounds (count of distinct rounds)
    - par3_avg, par4_avg, par5_avg (from hole_stats joined with holes)
    """
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # 1) Round-level stats
    round_query = db.session.query(
        func.avg(Round.score).label('avg_score'),
        func.avg(Round.score_to_par).label('avg_score_to_par'),
        func.count(Round.roundID).label('num_rounds')
    ).filter(Round.userID == current_user.userID)

    if course_id:
        round_query = round_query.filter(Round.course_id == course_id)
    if round_id:
        round_query = round_query.filter(Round.roundID == round_id)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        round_query = round_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        round_query = round_query.filter(Round.date_played <= end_date)

    round_result = round_query.one()
    avg_score = float(round_result.avg_score or 0)
    avg_score_to_par = float(round_result.avg_score_to_par or 0)
    total_rounds = int(round_result.num_rounds or 0)

    # 2) Hole-level stats for Par 3, 4, 5
    hs_query = (db.session.query(HoleStats.hole_score, Hole.par)
                .join(Round, HoleStats.roundID == Round.roundID)
                .join(Hole, HoleStats.holeID == Hole.holeID)
                .filter(Round.userID == current_user.userID))

    if course_id:
        hs_query = hs_query.filter(Round.course_id == course_id)
    if round_id:
        hs_query = hs_query.filter(Round.roundID == round_id)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        hs_query = hs_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        hs_query = hs_query.filter(Round.date_played <= end_date)

    results = hs_query.all()
    par3_scores = []
    par4_scores = []
    par5_scores = []

    for row in results:
        if row.par == 3 and row.hole_score:
            par3_scores.append(row.hole_score)
        elif row.par == 4 and row.hole_score:
            par4_scores.append(row.hole_score)
        elif row.par == 5 and row.hole_score:
            par5_scores.append(row.hole_score)

    def safe_avg(scores):
        return round(sum(scores) / len(scores), 2) if scores else 0.0

    par3_avg = safe_avg(par3_scores)
    par4_avg = safe_avg(par4_scores)
    par5_avg = safe_avg(par5_scores)

    data = {
        "scoring_avg": round(avg_score, 2),
        "scoring_avg_to_par": round(avg_score_to_par, 2),
        "total_rounds": total_rounds,
        "par3_avg": par3_avg,
        "par4_avg": par4_avg,
        "par5_avg": par5_avg
    }
    return jsonify(data)

@app.route('/api/tee_stats', methods=['GET'])
@login_required
def tee_stats():
    """
    Returns data specific to 'Off the Tee':
      1) avg_off_tee_sg  (AVG of Round.sg_off_tee)
      2) avg_tee_distance (AVG of distance_after - distance_before for shots of shot_type='Off the Tee')
      3) distribution of miss_direction for tee shots
    """
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # -----------------------------
    # 1) AVG Off-The-Tee SG (Round)
    # -----------------------------
    # Similar to /api/sg_by_shot_type, but focusing on Round.sg_off_tee
    sg_query = db.session.query(
        func.avg(Round.sg_off_tee).label('avg_off_tee_sg')
    ).filter(Round.userID == current_user.userID)

    if course_id:
        sg_query = sg_query.filter(Round.course_id == course_id)
    if round_id:
        sg_query = sg_query.filter(Round.roundID == round_id)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        sg_query = sg_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        sg_query = sg_query.filter(Round.date_played <= end_date)

    sg_result = sg_query.one()
    avg_off_tee_sg = float(sg_result.avg_off_tee_sg or 0)

    # -------------------------------------------------
    # 2) Average Tee Shot Distance (Shot table, shot_type='Off the Tee')
    # -------------------------------------------------
    # We'll compute func.avg(Shot.distance_after - Shot.distance_before)
    # and also join Round so we can apply the same filters (user, date, course, round).
    dist_query = db.session.query(
        func.avg(Shot.distance_before - Shot.distance_after).label('avg_tee_distance')
    ).join(Round, Shot.roundID == Round.roundID)\
     .filter(Round.userID == current_user.userID, Shot.shot_type == "Off the Tee")

    if course_id:
        dist_query = dist_query.filter(Round.course_id == course_id)
    if round_id:
        dist_query = dist_query.filter(Round.roundID == round_id)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        dist_query = dist_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        dist_query = dist_query.filter(Round.date_played <= end_date)

    dist_result = dist_query.one()
    avg_tee_distance = float(dist_result.avg_tee_distance or 0)

    # -------------------------------------------------
    # 3) Miss Direction Distribution (shot_type='Off the Tee')
    # -------------------------------------------------
    # We group by Shot.miss_direction and count how many. 
    # Then we'll compute proportions on the front end or just return counts.
    miss_query = db.session.query(
        Shot.miss_direction,
        func.count(Shot.shotID).label("count_dir")
    ).join(Round, Shot.roundID == Round.roundID)\
     .filter(Round.userID == current_user.userID, Shot.shot_type == "Off the Tee")

    if course_id:
        miss_query = miss_query.filter(Round.course_id == course_id)
    if round_id:
        miss_query = miss_query.filter(Round.roundID == round_id)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        miss_query = miss_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        miss_query = miss_query.filter(Round.date_played <= end_date)

    miss_query = miss_query.group_by(Shot.miss_direction)
    miss_results = miss_query.all()

    # Convert results into arrays for Chart.js (or any chart)
    directions = []
    direction_counts = []
    total_shots = 0

    for row in miss_results:
        directions.append(row.miss_direction)       # e.g. "Left", "Right", "None", etc.
        direction_counts.append(row.count_dir)      # integer count
        total_shots += row.count_dir

    data = {
        "avg_off_tee_sg": round(avg_off_tee_sg, 2),
        "avg_tee_distance": round(avg_tee_distance, 2),
        "miss_directions": directions,
        "miss_counts": direction_counts,
        "total_shots": int(total_shots)
    }
    return jsonify(data)

@app.route('/api/approach_stats', methods=['GET'])
@login_required
def approach_stats():
    """
    Returns data specific to Approach:
      1) avg_approach_sg (AVG of Round.sg_approach)
      2) gir_percent (Approach shots that end on Green / total approach shots * 100)
      3) distribution of approach shot miss_direction (excluding 'None')
    """
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # 1) AVG Approach SG
    sg_query = db.session.query(
        func.avg(Round.sg_approach).label('avg_approach_sg')
    ).filter(Round.userID == current_user.userID)

    if course_id:
        sg_query = sg_query.filter(Round.course_id == course_id)
    if round_id:
        sg_query = sg_query.filter(Round.roundID == round_id)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        sg_query = sg_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        sg_query = sg_query.filter(Round.date_played <= end_date)

    sg_result = sg_query.one()
    avg_approach_sg = float(sg_result.avg_approach_sg or 0)

    # 2) GIR % for Approach Shots
    shot_query = db.session.query(
        Shot.miss_direction,
        Shot.lie_after
    ).join(Round, Shot.roundID == Round.roundID)\
     .filter(Round.userID == current_user.userID, Shot.shot_type == "Approach")

    if course_id:
        shot_query = shot_query.filter(Round.course_id == course_id)
    if round_id:
        shot_query = shot_query.filter(Round.roundID == round_id)
    if start_date_str:
        shot_query = shot_query.filter(Round.date_played >= start_date)
    if end_date_str:
        shot_query = shot_query.filter(Round.date_played <= end_date)

    approach_shots = shot_query.all()
    total_approach_shots = len(approach_shots)
    gir_count = sum(1 for s in approach_shots if s.lie_after == "Green")
    gir_percent = (gir_count / total_approach_shots) * 100 if total_approach_shots > 0 else 0.0

    # 3) Miss Direction Distribution (excluding 'None')
    from collections import defaultdict
    miss_counter = defaultdict(int)

    for shot in approach_shots:
        if shot.lie_after != "Green":
            direction = shot.miss_direction or "Unknown"
            miss_counter[direction] += 1

    # Define the 8 fixed miss directions in the desired order
    fixed_directions = [
        "Long Right",    # 22.5° - 67.5°
        "Right",         # 67.5° - 112.5°
        "Short Right",   # 112.5° - 157.5°
        "Short",         # 157.5° - 202.5°
        "Short Left",    # 202.5° - 247.5°
        "Left",          # 247.5° - 292.5°
        "Long Left",     # 292.5° - 337.5°
        "Long"     # 337.5° - 382.5° (same as 337.5° - 22.5°)
    ]

    # Ensure all fixed directions are present
    miss_directions = []
    miss_counts = []
    for direction in fixed_directions:
        miss_directions.append(direction)
        miss_counts.append(miss_counter.get(direction, 0))

    data = {
        "avg_approach_sg": round(avg_approach_sg, 2),
        "gir_percent": round(gir_percent, 1),
        "miss_directions": miss_directions,
        "miss_counts": miss_counts,
        "total_approach_shots": total_approach_shots
    }
    return jsonify(data)

@app.route('/api/short_game_stats', methods=['GET'])
@login_required
def short_game_stats():
    """
    Returns:
      - up_down_percent (percentage of successful up-and-down)
      - avg_around_green_sg (average Round.sg_around_green across filtered rounds)
    """
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # 1) Average SG Around Green
    sg_query = db.session.query(
        func.avg(Round.sg_around_green).label('avg_around_green_sg')
    ).filter(Round.userID == current_user.userID)

    if course_id:
        sg_query = sg_query.filter(Round.course_id == course_id)
    if round_id:
        sg_query = sg_query.filter(Round.roundID == round_id)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        sg_query = sg_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        sg_query = sg_query.filter(Round.date_played <= end_date)

    sg_result = sg_query.one()
    avg_around_green_sg = float(sg_result.avg_around_green_sg or 0)

    # 2) Up & Down %
    #    Assume HoleStats.up_and_down = True if up/down was successful
    #    We'll join Round -> HoleStats to filter the same way
    ud_query = db.session.query(HoleStats.up_and_down)\
        .join(Round, HoleStats.roundID == Round.roundID)\
        .filter(Round.userID == current_user.userID)

    if course_id:
        ud_query = ud_query.filter(Round.course_id == course_id)
    if round_id:
        ud_query = ud_query.filter(Round.roundID == round_id)
    if start_date_str:
        ud_query = ud_query.filter(Round.date_played >= start_date)
    if end_date_str:
        ud_query = ud_query.filter(Round.date_played <= end_date)

    hole_stats = ud_query.all()
    total_attempts = len(hole_stats)
    successful = sum(1 for (ud,) in hole_stats if ud)

    up_down_percent = 0.0
    if total_attempts > 0:
        up_down_percent = successful / total_attempts * 100

    data = {
        "avg_around_green_sg": round(avg_around_green_sg, 2),
        "up_down_percent": round(up_down_percent, 1)
    }
    return jsonify(data)

@app.route('/api/putting_stats', methods=['GET'])
@login_required
def putting_stats():
    """
    Returns:
      - avg_putting_sg: Average strokes gained for putting.
    """
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # Query for average SG Putting
    q = db.session.query(
        func.avg(Round.sg_putting).label('avg_putting_sg')
    ).filter(Round.userID == current_user.userID)

    # Apply filters
    if course_id:
        q = q.filter(Round.course_id == course_id)
    if round_id:
        q = q.filter(Round.roundID == round_id)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        q = q.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        q = q.filter(Round.date_played <= end_date)

    result = q.one()
    avg_putting_sg = round(float(result.avg_putting_sg or 0), 2)

    return jsonify({"avg_putting_sg": avg_putting_sg})

@app.route('/api/distance_histogram', methods=['GET'])
@login_required
def distance_histogram():
    """
    Returns histogram data of distance_before (converted to yards if lie_before='Green') 
    in 5-yard bins from 0 to 600.
    Applies the same filters (course, round, date range) as the rest of the dashboard.
    """

    # 1) Parse request args (filters)
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # 2) Query Shots joined with Round so we can filter by user & the same dashboard filters
    shot_query = (db.session.query(Shot.distance_before, Shot.lie_before)
                  .join(Round, Shot.roundID == Round.roundID)
                  .filter(Round.userID == current_user.userID))

    # Apply filters
    if course_id:
        shot_query = shot_query.filter(Round.course_id == course_id)
    if round_id:
        shot_query = shot_query.filter(Round.roundID == round_id)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        shot_query = shot_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        shot_query = shot_query.filter(Round.date_played <= end_date)

    shots = shot_query.all()

    # 3) Convert distances to yards if lie_before = 'Green', otherwise assume distance_before is already in yards
    distances_yards = []
    for (dist_before, lie_before) in shots:
        if lie_before == "Green":
            # dist_before is in FEET, so divide by 3 to convert to yards
            dist_yards = dist_before / 3.0
        else:
            dist_yards = dist_before
        # Clip at 600 if you want to ensure no out-of-bounds beyond 600 
        # (or just trust that you won't have any >600)
        if dist_yards < 0:
            dist_yards = 0
        elif dist_yards > 600:
            dist_yards = 600
        distances_yards.append(dist_yards)

    # 4) Bin the distances in 5-yard increments from 0–5, 5–10, ... up to 600
    #    We'll create a list of bin edges (0,5,10,...,600).
    bin_size = 5
    max_yards = 600
    num_bins = max_yards // bin_size  # 600//5=120
    # We'll store counts in each bin index. 
    bin_counts = [0] * num_bins  # 120 bins
    # We'll also build labels like "0-5", "5-10", ...
    bin_labels = []
    for i in range(num_bins):
        left_edge = i * bin_size
        right_edge = left_edge + bin_size
        label = f"{left_edge}-{right_edge}"
        bin_labels.append(label)

    # 5) Increment counts for each shot
    for dist_y in distances_yards:
        # Which bin does this distance fall into?
        bin_index = int(dist_y // bin_size)  # e.g. dist_y=12 => bin_index=2 (for 10–15)
        # Edge case: dist_y=600 => bin_index=120; but our bins go up to index=119
        if bin_index == num_bins: 
            bin_index = num_bins - 1  # Put it into the last bin
        bin_counts[bin_index] += 1

    # 6) Return JSON
    data = {
        "bin_labels": bin_labels,  # e.g. ["0-5", "5-10", ..., "595-600"]
        "bin_counts": bin_counts   # e.g. [12, 42, 18, ...]
    }
    return jsonify(data)


@app.route('/get_tees/<int:course_id>')
def get_tees(course_id):
    """
    Fetches the tees associated with a specific course.
    Returns a JSON object containing the tee names and IDs.
    """
    tees = Tee.query.filter_by(courseID=course_id).all()
    return jsonify([{"teeID": tee.teeID, "name": tee.name} for tee in tees])


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
