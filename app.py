from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash
from models.sg_model import SG_calculator, shot_type_func  # Import your SG calculator model
from models.unit_converter import metres_to_yards, metres_to_feet
from models.gir_fw_tracking import update_gir_fairway
from functools import wraps

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
from collections import defaultdict

import pprint

# Stripe modules
import os 
from dotenv import load_dotenv
import stripe

from config import DevelopmentConfig, ProductionConfig  # or ProductionConfig for production

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config.from_object(ProductionConfig)  # Use ProductionConfig in production

# Initialize your database and migrations after configuration is set.
init_app(app)
migrate = Migrate(app, db)


# Initialse the flask login 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect users to the login page if not logged in

# Stripe api keys
# stripe_keys = {
#     "secret_key": os.environ["STRIPE_SECRET_KEY"],
#     "publishable_key": os.environ["STRIPE_PUBLISHABLE_KEY"],
#     "endpoint_secret": os.environ["STRIPE_ENDPOINT_SECRET"],
#     "price_id": os.environ["STRIPE_MONTHLY_PRICE_ID"],
#     "annual_price_id": os.environ["STRIPE_ANNUAL_PRICE_ID"],
#     "daily_price_id": os.environ["STRIPE_DAILY_PRICE_ID"],
# }

#stripe.api_key = stripe_keys["secret_key"]

@login_manager.user_loader
def load_user(userID):
    return User.query.get(int(userID))

# Custom wrapper function to make sure that a user is subscribed
def subscription_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the user is logged in and has an active subscription
        if not current_user.is_authenticated or not current_user.subscription_active:
            flash("You need an active subscription to access this page.", "warning")
            return redirect(url_for('recurring_payment_demo'))  # 'subscribe' is the route for subscription info
        return f(*args, **kwargs)
    return decorated_function


# # Recurring Payment Demo Page
# @app.route("/recurring_payment_demo")
# def recurring_payment_demo():
#     return render_template("recurring_payment_demo.html")

# # Recurring Payment Demo Page
# @app.route("/recurring_payment_demo_success")
# def recurring_payment_demo_success():
#     return render_template("recurring_payment_demo_success.html")

# # Recurring Payment Demo Page
# @app.route("/recurring_payment_demo_cancelled")
# def recurring_payment_demo_cancelled():
#     return render_template("recurring_payment_demo_cancelled.html")


# @app.route("/config")
# def get_publishable_key():
#     stripe_config = {"publicKey": stripe_keys["publishable_key"]}
#     return jsonify(stripe_config)

# @app.route("/create-checkout-session")
# def create_checkout_session():

    

#     # Get the product type from the query string; default to "monthly"
#     product_type = request.args.get("product_type", "monthly")
    
#     # Choose the price ID based on the product type
#     if product_type == "annual":
#         price_id = stripe_keys["annual_price_id"]
#     if product_type == "daily":
#         price_id = stripe_keys["daily_price_id"]
#     else: # This is monthly
#         price_id = stripe_keys["price_id"]

#     domain_url = "http://127.0.0.1:5000/recurring_payment_demo"
#     stripe.api_key = stripe_keys["secret_key"]

#     try:
#         checkout_session = stripe.checkout.Session.create(
#             # you should get the user id here and pass it along as 'client_reference_id'
#             #
#             # this will allow you to associate the Stripe session with
#             # the user saved in your database
#             #
#             # example: client_reference_id=user.id,
#             client_reference_id=current_user.get_id(),
#             success_url=domain_url + "_success?session_id={CHECKOUT_SESSION_ID}",
#             cancel_url=domain_url + "_cancel",
#             payment_method_types=["card"],
#             mode="subscription",
#             line_items=[
#                 {
#                     "price": price_id,
#                     "quantity": 1,
#                 }
#             ]
#         )
#         return jsonify({"sessionId": checkout_session["id"]})
#     except Exception as e:
#         return jsonify(error=str(e)), 403



# @app.route("/stripe-webhook", methods=["POST"])
# def stripe_webhook():
#     payload = request.get_data(as_text=True)
#     sig_header = request.headers.get("Stripe-Signature")

#     try:
#         event = stripe.Webhook.construct_event(
#             payload, sig_header, stripe_keys["endpoint_secret"]
#         )
#         data = event['data']

#     except ValueError as e:
#         # Invalid payload
#         return "Invalid payload", 400
#     except stripe.error.SignatureVerificationError as e:
#         # Invalid signature
#         return "Invalid signature", 400

#     # Handle the checkout.session.completed event
#     if event["type"] == "checkout.session.completed":
#         session = event["data"]["object"]

#         # Fulfill the purchase...
#         handle_checkout_session(session)

#     elif event["type"] == "invoice.paid":
#         invoice = event["data"]["object"]
#         # Retrieve the customer ID from the invoice.
#         customer_id = invoice.get("customer")
#         # Look up the user by their Stripe customer ID.
#         user = User.query.filter_by(stripe_customer_id=customer_id).first()
#         if user:
#             # Mark the subscription as active (1).
#             user.subscription_active = True
#             db.session.commit()
#             print("Invoice paid: Subscription active for user", user.get_id())
#         else:
#             print("Invoice paid: No user found for customer", customer_id)


#     elif event["type"] == "invoice.payment_failed":
#         invoice = event["data"]["object"]
#         customer_id = invoice.get("customer")
#         # Look up the user by their Stripe customer ID.
#         user = User.query.filter_by(stripe_customer_id=customer_id).first()
#         if user:
#             # Mark the subscription as inactive (0).
#             user.subscription_active = False
#             db.session.commit()
#             print("Invoice payment failed: Subscription inactive for user", user.get_id())
#         else:
#             print("Invoice payment failed: No user found for customer", customer_id)

#     elif event["type"] == "customer.subscription.deleted":
#         subscription = event["data"]["object"]
#         customer_id = subscription.get("customer")
#         # Look up the user by their Stripe customer ID.
#         user = User.query.filter_by(stripe_customer_id=customer_id).first()
#         if user:
#             # Mark the subscription as inactive and remove the subscription plan.
#             user.subscription_active = False
#             user.subscription_plan = None
#             db.session.commit()
#             print("Subscription deleted: Updated user", user.get_id())
#         else:
#             print("Subscription deleted: No user found for customer", customer_id)

#     else:
#         print("Unhandled event type {}".format(event["type"]))

#     return "Success", 200


# def handle_checkout_session(session):
#     # Retrieve the user ID from the checkout session.
#     # Ensure you pass the client_reference_id when creating the checkout session.
#     user_id = session.get("client_reference_id")
#     if not user_id:
#         print("No client_reference_id found in session.")
#         return

#     # Fetch the user from your database.
#     user = User.query.get(int(user_id))
#     if not user:
#         print(f"User with id {user_id} not found.")
#         return

#     # Update the user's subscription details using data from the Stripe session.
#     # The 'customer' field holds the Stripe customer ID.
#     # The 'subscription' field holds the subscription ID (or plan details if needed).
#     user.stripe_customer_id = session.get("customer")
#     user.subscription_active = True
#     user.subscription_plan = session.get("subscription")  # Optionally, retrieve more details via Stripe API if needed

#     # Commit the changes to the database.
#     db.session.commit()
#     print("User subscription details updated successfully.")



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')


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

        return redirect('/login')

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
        return redirect('/dashboard')

    return render_template('login.html')

# Add a route for user logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')
    


# Add a route to display a list of courses in the database
@app.route('/courses')
@login_required
def courses():
    query = request.args.get('search', '')  # Grab the query from ?search= in URL
    if query:
        # Filter courses whose name matches the query
        courses = Course.query.filter(Course.name.ilike(f"%{query}%")).all()
    else:
        # If no search query, display all courses
        courses = Course.query.all()

    return render_template('courses.html', courses=courses)

# Add a route to add a course
@app.route('/add_course', methods=['GET', 'POST'])
@login_required
def add_course():
    if request.method == 'POST':
        course_name = request.form.get('name').strip()
        location = request.form.get('location').strip()

        # 1. Check if a course with the same name & location already exists
        existing_course = Course.query.filter_by(name=course_name, location=location).first()

        if existing_course:
            # 2. Flash an error and re-render the form
            flash('A course with that name and location already exists!', 'danger')
            return redirect(url_for('add_course'))
        else:
            # 3. Create a new course if it doesn't exist
            new_course = Course(name=course_name, location=location)
            db.session.add(new_course)
            db.session.commit()

            return redirect(url_for('add_tee', course_id=new_course.courseID))

    # GET request: just render the blank form
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

@app.route('/add_holes/<int:tee_id>', methods=['GET', 'POST'])
@login_required
def add_holes(tee_id):
    tee = Tee.query.get_or_404(tee_id)
    if request.method == 'POST':
        # 1) Get the total number of holes from the slider
        num_holes = int(request.form.get('num_holes', 18))

        # 2) Get the list of distances. 
        #    This works because your <input> for hole distance has name="distances"
        distances_data = request.form.getlist('distances')

        # Remove any references to request.form.getlist('pars') or request.form.getlist('holes')

        # 3) For each hole index, retrieve distance from distances_data
        #    and the par from request.form.get(f"par_{i+1}")
        for i in range(num_holes):
            distance_str = distances_data[i]  # e.g. "385"
            distance = int(distance_str) if distance_str else 0

            # Get the par using the hole-specific name "par_1", "par_2", etc.
            par_value = request.form.get(f"par_{i+1}", "4")  # default to "4" if not found
            par = int(par_value)

            # Create the Hole object
            hole = Hole(
                courseID = tee.courseID,
                teeID    = tee.teeID,
                number   = i + 1,
                par      = par,
                distance = distance
            )
            db.session.add(hole)

        # 4) Commit the newly added holes
        db.session.commit()

        # 5) Recalculate the tee’s total_distance
        tee.total_distance = sum(h.distance or 0 for h in tee.holes)
        db.session.commit()

        # 6) Redirect to wherever you’d like after saving
        return redirect('/add_round')

    # If GET, just render the add_holes form
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
        round_type = request.form.get('round_type')

        # Validate form data
        if not course_id or not tee_id or not date_played_str or not round_type:
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
            round_type = round_type,
            date_played=date_played
        )
        db.session.add(new_round)
        db.session.commit()

        # Redirect to the next page for shot entry
        return redirect(url_for('add_shots', roundID=new_round.roundID))

    # Retrieve course data for the form
    courses = Course.query.all()
    return render_template('add_round.html', courses=courses)


# Add a route to put the shots in
@app.route('/add_shots/<int:roundID>', methods=['GET', 'POST'])
@login_required
def add_shots(roundID):
    round_data = Round.query.get_or_404(roundID)
    course = Course.query.get_or_404(round_data.course_id)
    tee_id = round_data.tee_id
    holes = Hole.query.filter_by(courseID=course.courseID, teeID=tee_id).order_by(Hole.number).all()

    if request.method == 'POST':
        round_score = 0

        # We'll store all new shots here temporarily before adding to DB
        all_new_shots = []

        for hole in holes:
            num_shots = 1
            hole_penalty_shots = 0

            # We'll keep track of the "real" shots in this hole
            hole_shots_list = []

            while True:
                distance_str = request.form.get(f"hole_{hole.number}_shot_{num_shots}_distance")
                lie = request.form.get(f"hole_{hole.number}_shot_{num_shots}_lie")
                if not distance_str or not lie:
                    # If these fields are missing, we're done with this hole
                    break

                distance = float(distance_str)
                out_of_bounds = (request.form.get(f"hole_{hole.number}_shot_{num_shots}_out_of_bounds") == "1")
                hazard = (request.form.get(f"hole_{hole.number}_shot_{num_shots}_hazard") == "1")
                miss_direction = request.form.get(
                    f"hole_{hole.number}_shot_{num_shots}_miss_direction", "None"
                )
                club = request.form.get(f"hole_{hole.number}_shot_{num_shots}_club", None)

                # Check if short_sided was checked in the form
                short_sided = (request.form.get(f"hole_{hole.number}_shot_{num_shots}_short_sided") == "1")

                # figure out distance_after/lie_after
                distance_after = 0.0
                lie_after = "In the Hole"
                if request.form.get(f"hole_{hole.number}_shot_{num_shots + 1}_distance"):
                    distance_after = float(request.form.get(f"hole_{hole.number}_shot_{num_shots + 1}_distance"))
                if request.form.get(f"hole_{hole.number}_shot_{num_shots + 1}_lie"):
                    lie_after = request.form.get(f"hole_{hole.number}_shot_{num_shots + 1}_lie")

                # Calculate strokes gained
                if out_of_bounds:
                    sg = SG_calculator(distance, lie, distance_after, "OOB")
                    hole_penalty_shots += 1
                else:
                    sg = SG_calculator(distance, lie, distance_after, lie_after)

                if hazard:
                    sg -= 1
                    hole_penalty_shots += 1

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
                    club=club,
                    short_sided=short_sided  # <-- store the user’s checkbox
                )

                # Add to our hole-local list
                hole_shots_list.append(new_shot)
                num_shots += 1

            # Now that we have the hole’s shots in hole_shots_list, 
            #  check if any shot has short_sided=1. If so, 
            #  set the preceding shot's short_sided=1 if that preceding shot is Approach.
            for i, s in enumerate(hole_shots_list):
                if s.short_sided:
                    # If this shot is short_sided, mark the previous shot if it is approach
                    if i > 0:  # there is a previous shot
                        prev_shot = hole_shots_list[i - 1]
                        if prev_shot.shot_type == "Approach":
                            prev_shot.short_sided = True

            # Now we can add them all to the DB and compute the hole’s score
            # note: hole_score = (# of real shots) + penaltyShots
            hole_score = len(hole_shots_list) + hole_penalty_shots
            round_score += hole_score

            # Add to the master list
            all_new_shots.extend(hole_shots_list)

            # If hole_score > 0, update the holeStats
            if hole_score > 0:
                hole_stat = HoleStats.query.filter_by(roundID=roundID, holeID=hole.holeID).first()
                if not hole_stat:
                    hole_stat = HoleStats(roundID=roundID, holeID=hole.holeID)
                    db.session.add(hole_stat)
                hole_stat.hole_score = hole_score

        # Once all holes are processed, insert the new shots
        for shot in all_new_shots:
            db.session.add(shot)

        db.session.commit()

        # Then do any post-processing updates, e.g. GIR/fairway, aggregated strokes gained, etc.
        update_gir_fairway(roundID, holes)
        sg_off_tee = db.session.query(func.sum(Shot.strokes_gained)).filter(
            Shot.roundID == roundID, Shot.shot_type == "Off the Tee"
        ).scalar() or 0.0
        sg_approach = db.session.query(func.sum(Shot.strokes_gained)).filter(
            Shot.roundID == roundID, Shot.shot_type == "Approach"
        ).scalar() or 0.0
        sg_around_green = db.session.query(func.sum(Shot.strokes_gained)).filter(
            Shot.roundID == roundID, Shot.shot_type == "Around the Green"
        ).scalar() or 0.0
        sg_putting = db.session.query(func.sum(Shot.strokes_gained)).filter(
            Shot.roundID == roundID, Shot.shot_type == "Putting"
        ).scalar() or 0.0

        round_data.sg_off_tee = sg_off_tee
        round_data.sg_approach = sg_approach
        round_data.sg_around_green = sg_around_green
        round_data.sg_putting = sg_putting
        round_data.score = round_score

        # Compute round score to par
        this_tee = Tee.query.get_or_404(tee_id)
        round_data.score_to_par = round_score - this_tee.course_par

        db.session.commit()
        return redirect('/dashboard')

    # GET request - just render the template
    return render_template('add_shots.html', round_data=round_data, course=course, tee_id=tee_id, holes=holes)

# Route where the user's rounds are stored
@app.route('/my_rounds', methods=['GET', 'POST'])
@login_required
def my_rounds():
    if request.method == 'POST':
        # Get the round ID from the submitted form
        round_id = request.form.get('round_id')
        if round_id:
            # Verify the round belongs to the current user
            round_to_delete = Round.query.filter_by(roundID=round_id, userID=current_user.userID).first()
            if round_to_delete:
                # Delete the round.
                # With cascade="all, delete-orphan" in your relationships,
                # all related Shots and HoleStats will be deleted automatically.
                db.session.delete(round_to_delete)
                db.session.commit()
                flash("Round and all associated shots and hole stats deleted successfully.", "success")
            else:
                flash("Round not found or not authorized.", "danger")
        return redirect(url_for('my_rounds'))

    # For GET requests, fetch all rounds for the current user (newest first)
    rounds = Round.query.filter_by(userID=current_user.userID).order_by(Round.date_played.desc()).all()
    return render_template('my_rounds.html', rounds=rounds)




@app.route('/dashboard')
@login_required
@subscription_required
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
    round_type = request.args.get('round_type')
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
    if round_type:
        q = q.filter(Round.round_type == round_type)
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

@app.route('/api/last50_approach', methods=['GET'])
@login_required
def last50_approach():
    rounds = (Round.query.filter_by(userID=current_user.userID)
              .order_by(Round.date_played.desc())
              .limit(50)
              .all())
    rounds = sorted(rounds, key=lambda r: r.date_played)
    data = [
        {
            "roundID": r.roundID,
            "date_played": r.date_played.strftime('%Y-%m-%d'),
            "sg_approach": float(r.sg_approach or 0),
            "course_name": r.course.name
        }
        for r in rounds
    ]
    return jsonify(data)

@app.route('/api/last50_offtee', methods=['GET'])
@login_required
def last50_offtee():
    rounds = (Round.query.filter_by(userID=current_user.userID)
              .order_by(Round.date_played.desc())
              .limit(50)
              .all())
    rounds = sorted(rounds, key=lambda r: r.date_played)
    data = [
        {
            "roundID": r.roundID,
            "date_played": r.date_played.strftime('%Y-%m-%d'),
            "sg_off_tee": float(r.sg_off_tee or 0),
            "course_name": r.course.name
        }
        for r in rounds
    ]
    return jsonify(data)

@app.route('/api/last50_around_green', methods=['GET'])
@login_required
def last50_around_green():
    rounds = (Round.query.filter_by(userID=current_user.userID)
              .order_by(Round.date_played.desc())
              .limit(50)
              .all())
    rounds = sorted(rounds, key=lambda r: r.date_played)
    data = [
        {
            "roundID": r.roundID,
            "date_played": r.date_played.strftime('%Y-%m-%d'),
            "sg_around_green": float(r.sg_around_green or 0),
            "course_name": r.course.name
        }
        for r in rounds
    ]
    return jsonify(data)

@app.route('/api/last50_putting', methods=['GET'])
@login_required
def last50_putting():
    rounds = (Round.query.filter_by(userID=current_user.userID)
              .order_by(Round.date_played.desc())
              .limit(50)
              .all())
    rounds = sorted(rounds, key=lambda r: r.date_played)
    data = [
        {
            "roundID": r.roundID,
            "date_played": r.date_played.strftime('%Y-%m-%d'),
            "sg_putting": float(r.sg_putting or 0),
            "course_name": r.course.name
        }
        for r in rounds
    ]
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
    round_type = request.args.get('round_type')
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
    if round_type:
        round_query = round_query.filter(Round.round_type == round_type)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        round_query = round_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        round_query = round_query.filter(Round.date_played <= end_date)

    # Obtain the total number of rounds
    round_result = round_query.one()
    total_rounds = int(round_result.num_rounds or 0)

    # Add in a condition for when the total rounds is 0
    # The front end will need adapting to display a value such as --
    if total_rounds == 0:
        data = {
            "scoring_avg": None,
            "scoring_avg_to_par": None,
            "total_rounds": 0,
            "par3_avg": None,
            "par4_avg": None,
            "par5_avg": None
        }
        return jsonify(data)

    # Calculate the scoring averages
    avg_score = float(round_result.avg_score)
    avg_score_to_par = float(round_result.avg_score_to_par)
     
    # 2) Hole-level stats for Par 3, 4, 5
    hs_query = (db.session.query(HoleStats.hole_score, Hole.par)
                .join(Round, HoleStats.roundID == Round.roundID)
                .join(Hole, HoleStats.holeID == Hole.holeID)
                .filter(Round.userID == current_user.userID))

    if course_id:
        hs_query = hs_query.filter(Round.course_id == course_id)
    if round_id:
        hs_query = hs_query.filter(Round.roundID == round_id)
    if round_type:
        hs_query = hs_query.filter(Round.round_type == round_type)
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

@app.route('/api/rounds', methods=['GET'])
@login_required
def get_rounds():
    """
    Fetch rounds for the current user filtered by course, round, and date range.
    Returns:
      - roundID
      - course_name
      - date_played
      - score_to_par
    """
    # Get query parameters
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    round_type = request.args.get('round_type')
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # Build query
    query = Round.query.join(Course).filter(Round.userID == current_user.userID)

    if course_id:
        query = query.filter(Round.course_id == course_id)
    if round_id:
        query = query.filter(Round.roundID == round_id)
    if round_type:
        query = query.filter(Round.round_type == round_type)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        query = query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        query = query.filter(Round.date_played <= end_date)

    # Order rounds by date_played
    query = query.order_by(Round.date_played.asc())

    # Execute query and format results
    rounds = query.all()
    data = [
        {
            "roundID": r.roundID,
            "course_name": r.course.name,
            "date_played": r.date_played.strftime('%Y-%m-%d'),
            "score_to_par": r.score_to_par
        }
        for r in rounds
    ]

    return jsonify(data)


@app.route('/api/tee_stats', methods=['GET'])
@login_required
def tee_stats():
    """
    Returns data specific to 'Off the Tee':
      1) avg_off_tee_sg      (AVG of Round.sg_off_tee)
      2) avg_tee_distance    (AVG of distance_before - distance_after for Off the Tee shots)
      3) distribution of miss_direction for Off the Tee shots
      4) cumulative percentage of Off the Tee shots finishing in "Fairway", "Bunker", "Rough", "Green", or "In the Hole"
         (all other lies are excluded from this cumulative %).
    """
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    round_type = request.args.get('round_type')
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # -----------------------------
    # 1) AVG Off-The-Tee SG (Round)
    # -----------------------------
    sg_query = db.session.query(
        func.avg(Round.sg_off_tee).label('avg_off_tee_sg')
    ).filter(Round.userID == current_user.userID)

    if course_id:
        sg_query = sg_query.filter(Round.course_id == course_id)
    if round_id:
        sg_query = sg_query.filter(Round.roundID == round_id)
    if round_type:
        sg_query = sg_query.filter(Round.round_type == round_type)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        sg_query = sg_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        sg_query = sg_query.filter(Round.date_played <= end_date)

    sg_result = sg_query.one()
    avg_off_tee_sg = float(sg_result.avg_off_tee_sg or 0)

    # -------------------------------------------------
    # 2) Average Tee Shot Distance (Off the Tee)
    # -------------------------------------------------
    dist_query = db.session.query(
        func.avg(Shot.distance_before - Shot.distance_after).label('avg_tee_distance')
    ).join(Round, Shot.roundID == Round.roundID)\
     .filter(Round.userID == current_user.userID, Shot.shot_type == "Off the Tee")

    if course_id:
        dist_query = dist_query.filter(Round.course_id == course_id)
    if round_id:
        dist_query = dist_query.filter(Round.roundID == round_id)
    if round_type:
        dist_query = dist_query.filter(Round.round_type == round_type)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        dist_query = dist_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        dist_query = dist_query.filter(Round.date_played <= end_date)

    dist_result = dist_query.one()
    avg_tee_distance = float(dist_result.avg_tee_distance or 0)

    # ------------------------------------------------------------
    # 2B) Average Driver Tee Shot Distance (non-Par 3, club = "Driver")
    # ------------------------------------------------------------
    driver_query = db.session.query(
         func.avg(Shot.distance_before - Shot.distance_after).label('avg_driver_distance')
    ).join(Round, Shot.roundID == Round.roundID)\
     .join(Hole, Shot.holeID == Hole.holeID)\
     .filter(
         Round.userID == current_user.userID,
         Shot.shot_type == "Off the Tee",
         Hole.par != 3,
         Shot.club == "Dr"
     )
    driver_result = driver_query.one()
    print(driver_result)
    avg_driver_distance = float(driver_result.avg_driver_distance or 0)

    # -------------------------------------------------
    # 3) Miss Direction Distribution (Off the Tee)
    # -------------------------------------------------
    miss_query = db.session.query(
        Shot.miss_direction,
        func.count(Shot.shotID).label("count_dir")
    ).join(Round, Shot.roundID == Round.roundID)\
     .filter(Round.userID == current_user.userID, Shot.shot_type == "Off the Tee")

    if course_id:
        miss_query = miss_query.filter(Round.course_id == course_id)
    if round_id:
        miss_query = miss_query.filter(Round.roundID == round_id)
    if round_type:
        miss_query = miss_query.filter(Round.round_type == round_type)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        miss_query = miss_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        miss_query = miss_query.filter(Round.date_played <= end_date)

    miss_query = miss_query.group_by(Shot.miss_direction)
    miss_results = miss_query.all()

    directions = []
    direction_counts = []
    total_shots_dir = 0

    for row in miss_results:
        directions.append(row.miss_direction)      
        direction_counts.append(row.count_dir)     
        total_shots_dir += row.count_dir

    # -------------------------------------------------
    # 4) Cumulative Percentage of Final Lies of Interest
    # -------------------------------------------------
    # We only care about: "Fairway", "Bunker", "Rough", "Green", "In the Hole"
    # For Off the Tee shots
    lie_query = db.session.query(
        Shot.lie_after,
        func.count(Shot.shotID).label("count_lie")
    ).join(Round, Shot.roundID == Round.roundID)\
     .filter(Round.userID == current_user.userID, Shot.shot_type == "Off the Tee")

    if course_id:
        lie_query = lie_query.filter(Round.course_id == course_id)
    if round_id:
        lie_query = lie_query.filter(Round.roundID == round_id)
    if round_type:
        lie_query = lie_query.filter(Round.round_type == round_type)
    if start_date_str:
        lie_query = lie_query.filter(Round.date_played >= start_date)
    if end_date_str:
        lie_query = lie_query.filter(Round.date_played <= end_date)

    lie_query = lie_query.group_by(Shot.lie_after)
    lie_results = lie_query.all()

    # Put results into a dictionary like {"Fairway": x, "Bunker": y, ...}
    final_lie_counts = {}
    total_shots_lie = 0
    for row in lie_results:
        final_lie = row.lie_after
        count_lie = row.count_lie
        final_lie_counts[final_lie] = count_lie
        total_shots_lie += count_lie

    # We only want the sum of these categories
    relevant_lies = ["Fairway", "Bunker", "Rough", "Green", "In the Hole"] # Hazard, OOB and Recovery omitted
    relevant_shot_sum = 0

    for lie_key, count_val in final_lie_counts.items():
        if lie_key in relevant_lies:
            relevant_shot_sum += count_val

    # Compute the cumulative % for these relevant lies
    if total_shots_lie > 0:
        cumulative_pct = round((relevant_shot_sum / total_shots_lie) * 100, 1)
    else:
        cumulative_pct = 0.0

    data = {
        "avg_off_tee_sg": round(avg_off_tee_sg, 2),
        "avg_tee_distance": round(avg_tee_distance, 2),
        "avg_driver_distance": round(avg_driver_distance, 2),
        "miss_directions": directions,       # e.g. ["Left", "Right", "None", etc.]
        "miss_counts": direction_counts,     # e.g. [10, 5, 2, ...]
        "total_shots": int(total_shots_dir), # total from the miss direction perspective
        "cumulativeLiePct": cumulative_pct   # single number for card
    }
    return jsonify(data)

@app.route('/api/tee_miss_direction_dr', methods=['GET'])
@login_required
def tee_miss_direction_dr():
    """
    Returns the miss direction counts for tee shots (shot_type == "Off the Tee")
    but only for shots with the club value "Dr".
    """
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    round_type = request.args.get('round_type')
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    dr_miss_query = db.session.query(
        Shot.miss_direction,
        func.count(Shot.shotID).label("count_dir")
    ).join(Round, Shot.roundID == Round.roundID)\
     .filter(
         Round.userID == current_user.userID,
         Shot.shot_type == "Off the Tee",
         Shot.club == "Dr"
     )
    
    if course_id:
        dr_miss_query = dr_miss_query.filter(Round.course_id == course_id)
    if round_id:
        dr_miss_query = dr_miss_query.filter(Round.roundID == round_id)
    if round_type:
        dr_miss_query = dr_miss_query.filter(Round.round_type == round_type)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        dr_miss_query = dr_miss_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        dr_miss_query = dr_miss_query.filter(Round.date_played <= end_date)

    dr_miss_query = dr_miss_query.group_by(Shot.miss_direction)
    dr_miss_results = dr_miss_query.all()

    # Calculate breakdown: for simplicity, use the same algorithm as before:
    leftCount = 0
    rightCount = 0
    centerCount = 0
    totalShots = 0

    for row in dr_miss_results:
        direction = row.miss_direction.lower() if row.miss_direction else ""
        count = row.count_dir
        totalShots += count
        if "left" in direction:
            leftCount += count
        elif "right" in direction:
            rightCount += count
        else:
            centerCount += count

    # Return the counts (and percentages if desired)
    data = {
        "left": leftCount,
        "right": rightCount,
        "center": centerCount,
        "total": totalShots
    }
    return jsonify(data)

@app.route('/api/tee_miss_direction_non_dr', methods=['GET'])
@login_required
def tee_miss_direction_non_dr():
    """
    Returns the miss direction counts for tee shots that are:
     - Off the Tee,
     - Played on non-par-3 holes (Hole.par != 3),
     - With a club value NOT equal to "Dr".
    """
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    round_type = request.args.get('round_type')
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    non_dr_miss_query = db.session.query(
        Shot.miss_direction,
        func.count(Shot.shotID).label("count_dir")
    ).join(Round, Shot.roundID == Round.roundID)\
     .join(Hole, Shot.holeID == Hole.holeID)\
     .filter(
         Round.userID == current_user.userID,
         Shot.shot_type == "Off the Tee",
         Hole.par != 3,
         Shot.club != "Dr"
     )
    
    if course_id:
        non_dr_miss_query = non_dr_miss_query.filter(Round.course_id == course_id)
    if round_id:
        non_dr_miss_query = non_dr_miss_query.filter(Round.roundID == round_id)
    if round_type:
        non_dr_miss_query = non_dr_miss_query.filter(Round.round_type == round_type)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        non_dr_miss_query = non_dr_miss_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        non_dr_miss_query = non_dr_miss_query.filter(Round.date_played <= end_date)

    non_dr_miss_query = non_dr_miss_query.group_by(Shot.miss_direction)
    non_dr_results = non_dr_miss_query.all()

    # Aggregate the counts.
    leftCount = 0
    rightCount = 0
    centerCount = 0
    total_count = 0

    for row in non_dr_results:
        direction = (row.miss_direction or "").lower()
        count = row.count_dir
        total_count += count
        if "left" in direction:
            leftCount += count
        elif "right" in direction:
            rightCount += count
        else:
            centerCount += count

    data = {
        "left": leftCount,
        "right": rightCount,
        "center": centerCount,
        "total": total_count
    }
    return jsonify(data)


@app.route('/api/approach_stats', methods=['GET'])
@login_required
def approach_stats():
    """
    Returns data specific to Approach:
      1) avg_approach_sg (AVG of Round.sg_approach)
      2) greens_hit (Shots-based %: Approach shots that ended on Green / total approach shots)
      3) gir_percent (HoleStats-based %: #holes with gir=True / total holes)
      4) distribution of approach shot miss_direction (excluding 'None')
    """
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    round_type = request.args.get('round_type')
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # Add in the option to filter the api request to certain distances
    min_distance = request.args.get('min_distance', type=float)
    max_distance = request.args.get('max_distance', type=float)

    # ---------------------------
    # 1) Average Approach SG
    # ---------------------------
    sg_query = db.session.query(
        func.avg(Round.sg_approach).label('avg_approach_sg')
    ).filter(Round.userID == current_user.userID)

    if course_id:
        sg_query = sg_query.filter(Round.course_id == course_id)
    if round_id:
        sg_query = sg_query.filter(Round.roundID == round_id)
    if round_type:
        sg_query = sg_query.filter(Round.round_type == round_type)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        sg_query = sg_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        sg_query = sg_query.filter(Round.date_played <= end_date)

    sg_result = sg_query.one()
    avg_approach_sg = float(sg_result.avg_approach_sg or 0)

    # --------------------------------------------------------
    # 2) "greens_hit" - The *original method* from Approach shots
    #    (Shots that ended on Green / total Approach shots * 100)
    # --------------------------------------------------------
    shot_query = db.session.query(
        Shot.miss_direction,
        Shot.lie_after
    ).join(Round, Shot.roundID == Round.roundID)\
      .filter(Round.userID == current_user.userID, Shot.shot_type == "Approach", Shot.lie_before != "Recovery")

    # Apply distance filters if they are provided:
    if min_distance is not None:
        shot_query = shot_query.filter(Shot.distance_before >= min_distance)
    if max_distance is not None:
        shot_query = shot_query.filter(Shot.distance_before <= max_distance)


    if course_id:
        shot_query = shot_query.filter(Round.course_id == course_id)
    if round_id:
        shot_query = shot_query.filter(Round.roundID == round_id)
    if round_type:
        shot_query = shot_query.filter(Round.round_type == round_type)
    if start_date_str:
        shot_query = shot_query.filter(Round.date_played >= start_date)
    if end_date_str:
        shot_query = shot_query.filter(Round.date_played <= end_date)

    approach_shots = shot_query.all()
    total_approach_shots = len(approach_shots)
    green_hits = sum(1 for s in approach_shots if s.lie_after == "Green")
    # "greens_hit" => percentage of approach shots that ended on Green
    greens_hit = (green_hits / total_approach_shots * 100) if total_approach_shots > 0 else 0.0

    # -------------------------------------------------------
    # 3) "gir_percent" - The *new method* from HoleStats
    #    (#holes with gir=True / total holes * 100)
    # -------------------------------------------------------
    hole_stats_query = db.session.query(HoleStats).join(Round, HoleStats.roundID == Round.roundID)\
        .filter(Round.userID == current_user.userID)

    if course_id:
        hole_stats_query = hole_stats_query.filter(Round.course_id == course_id)
    if round_id:
        hole_stats_query = hole_stats_query.filter(Round.roundID == round_id)
    if round_type:
        hole_stats_query = hole_stats_query.filter(Round.round_type == round_type)
    if start_date_str:
        hole_stats_query = hole_stats_query.filter(Round.date_played >= start_date)
    if end_date_str:
        hole_stats_query = hole_stats_query.filter(Round.date_played <= end_date)

    hole_stats = hole_stats_query.all()
    total_holes = len(hole_stats)
    gir_count = sum(1 for hs in hole_stats if hs.gir)
    gir_percent = (gir_count / total_holes * 100) if total_holes > 0 else 0.0

    # -------------------------------------------------------
    # 4) Distribution of approach shot miss_direction
    # -------------------------------------------------------
    miss_counter = defaultdict(int)
    for shot in approach_shots:
        if shot.lie_after != "Green":
            direction = shot.miss_direction or "Unknown"
            miss_counter[direction] += 1

    # 8 fixed directions
    fixed_directions = [
        "Long Right", "Right", "Short Right", "Short",
        "Short Left", "Left", "Long Left", "Long"
    ]
    miss_directions = []
    miss_counts = []
    for direction in fixed_directions:
        miss_directions.append(direction)
        miss_counts.append(miss_counter.get(direction, 0))

    data = {
        "avg_approach_sg": round(avg_approach_sg, 2),
        # The old Shot-based method:
        "greens_hit": round(greens_hit, 1),
        # The new HoleStats-based method:
        "gir_percent": round(gir_percent, 1),
        "miss_directions": miss_directions,
        "miss_counts": miss_counts,
        "total_approach_shots": total_approach_shots
    }
    return jsonify(data)


from collections import defaultdict
from datetime import datetime
from flask import jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func

@app.route('/api/approach_table', methods=['GET'])
@login_required
def approach_table():
    """
    Returns a JSON object containing an array of Approach Shots stats:
      - distanceRange : e.g. "50-75", "75-100", ...
      - sgPerShot     : strokes gained average per shot in this range
      - avgProximity  : average final proximity (distance_after, *3 if lie_after != "Green")
      - greenHitPct   : percentage of shots where lie_after is "Green" or "In the Hole"
    """

    # 1) Parse filters
    course_id = request.args.get('course', type=int)
    round_id  = request.args.get('round', type=int)
    round_type  = request.args.get('round_type')
    start_date_str = request.args.get('startDate')
    end_date_str   = request.args.get('endDate')

    # 2) Query Shots joined with Round
    shots_query = (db.session.query(Shot)
                   .join(Round, Shot.roundID == Round.roundID)
                   .filter(Round.userID == current_user.userID,
                           Shot.shot_type == "Approach", Shot.lie_before != "Recovery"))

    # Apply filters
    if course_id:
        shots_query = shots_query.filter(Round.course_id == course_id)
    if round_id:
        shots_query = shots_query.filter(Round.roundID == round_id)
    if round_type:
        shots_query = shots_query.filter(Round.round_type == round_type)
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            shots_query = shots_query.filter(Round.date_played >= start_date)
        except ValueError:
            return jsonify({"error": "Invalid startDate format. Use YYYY-MM-DD."}), 400
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            shots_query = shots_query.filter(Round.date_played <= end_date)
        except ValueError:
            return jsonify({"error": "Invalid endDate format. Use YYYY-MM-DD."}), 400

    all_approach_shots = shots_query.all()

    # 3) Define Approach Distance Bins
    approach_bins = {
        "50-75 yds":   {"countShots": 0, "sumSG": 0.0, "sumProximity": 0.0, "countGreenHits": 0},
        "75-100 yds":  {"countShots": 0, "sumSG": 0.0, "sumProximity": 0.0, "countGreenHits": 0},
        "100-125 yds": {"countShots": 0, "sumSG": 0.0, "sumProximity": 0.0, "countGreenHits": 0},
        "125-150 yds": {"countShots": 0, "sumSG": 0.0, "sumProximity": 0.0, "countGreenHits": 0},
        "150-175 yds": {"countShots": 0, "sumSG": 0.0, "sumProximity": 0.0, "countGreenHits": 0},
        "175-200 yds": {"countShots": 0, "sumSG": 0.0, "sumProximity": 0.0, "countGreenHits": 0},
        "200-225 yds": {"countShots": 0, "sumSG": 0.0, "sumProximity": 0.0, "countGreenHits": 0},
        "225-250 yds": {"countShots": 0, "sumSG": 0.0, "sumProximity": 0.0, "countGreenHits": 0},
        "250-275 yds": {"countShots": 0, "sumSG": 0.0, "sumProximity": 0.0, "countGreenHits": 0},
        "275+ yds":    {"countShots": 0, "sumSG": 0.0, "sumProximity": 0.0, "countGreenHits": 0},
    }

    def get_approach_bin(d):
        """
        Return the bin label based on distance_before.
        For distances < 50, skip or handle differently if desired.
        """
        if 50 <= d < 75:
            return "50-75 yds"
        elif 75 <= d < 100:
            return "75-100 yds"
        elif 100 <= d < 125:
            return "100-125 yds"
        elif 125 <= d < 150:
            return "125-150 yds"
        elif 150 <= d < 175:
            return "150-175 yds"
        elif 175 <= d < 200:
            return "175-200 yds"
        elif 200 <= d < 225:
            return "200-225 yds"
        elif 225 <= d < 250:
            return "225-250 yds"
        elif 250 <= d < 275:
            return "250-275 yds"
        else:
            # d >= 275
            return "275+ yds"

    # 4) Populate Bin Stats
    for shot in all_approach_shots:
        dist_before = shot.distance_before
        if dist_before < 50:
            # If you want to skip approach shots < 50 yds:
            continue
            # Or handle them in a separate bin if you wish

        bin_label = get_approach_bin(dist_before)
        approach_bins[bin_label]["countShots"] += 1
        approach_bins[bin_label]["sumSG"]      += shot.strokes_gained

        # 4a) Count "Green Hits"
        # "Green Hit" if lie_after is "Green" or "In the Hole"
        if shot.lie_after in ("Green", "In the Hole"):
            approach_bins[bin_label]["countGreenHits"] += 1

        # 4b) Calculate proximity
        final_dist = shot.distance_after
        if shot.lie_after != "Green":
            final_dist *= 3
        approach_bins[bin_label]["sumProximity"] += final_dist

    # 5) Build Output
    approachData = []
    for bin_label, stats in approach_bins.items():
        cShots    = stats["countShots"]
        totalSG   = stats["sumSG"]
        totalProx = stats["sumProximity"]
        greenHits = stats["countGreenHits"]

        if cShots > 0:
            sgPerShot  = totalSG / cShots
            avgProx    = totalProx / cShots
            greenHitPct = (greenHits / cShots) * 100.0
        else:
            sgPerShot   = 0.0
            avgProx     = 0.0
            greenHitPct = 0.0

        row = {
            "distanceRange": bin_label,
            "sgPerShot": round(sgPerShot, 3),     # e.g., 3 decimal places
            "avgProximity": round(avgProx, 1),   # e.g., 1 decimal place
            "greenHitPct": round(greenHitPct, 1) # e.g., 1 decimal place
        }
        approachData.append(row)

    # 6) Return JSON
    return jsonify({"approachData": approachData})


from collections import defaultdict
import pprint  # For better formatting

from collections import defaultdict
import pprint  # For better formatting

@app.route('/api/short_game_stats', methods=['GET'])
@login_required
def short_game_stats():
    """
    Returns:
      - avg_around_green_sg (float)
      - up_down_percent (float, based on "Around the Green" shots)
      - bunkerData (list of dicts for each distance bracket)
      - nonBunkerData (list of dicts for each distance bracket)
    """
    # --------------- Query Parameters ---------------
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    round_type = request.args.get('round_type')
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # --------------- 1) Calculate Average SG Around Green ---------------
    sg_query = db.session.query(
        func.avg(Round.sg_around_green).label('avg_around_green_sg')
    ).filter(Round.userID == current_user.userID)

    if course_id:
        sg_query = sg_query.filter(Round.course_id == course_id)
    if round_id:
        sg_query = sg_query.filter(Round.roundID == round_id)
    if round_type:
        sg_query = sg_query.filter(Round.round_type == round_type)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        sg_query = sg_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        sg_query = sg_query.filter(Round.date_played <= end_date)

    sg_result = sg_query.one()
    avg_around_green_sg = float(sg_result.avg_around_green_sg or 0)

    # --------------- 2) Remove Existing Up & Down % Calculation ---------------
    # The previous calculation based on HoleStats is removed.
    # Up & Down % will now be calculated based on Shot records.

    # --------------- 3) Fetch All Shots for Accurate Up & Down % ---------------
    # Fetch all shots (not just "Around the Green") to accurately find the next shot
    shots_query = (
        db.session.query(Shot)
        .join(Round, Shot.roundID == Round.roundID)
        .filter(Round.userID == current_user.userID)
    )

    if course_id:
        shots_query = shots_query.filter(Round.course_id == course_id)
    if round_id:
        shots_query = shots_query.filter(Round.roundID == round_id)
    if round_type:
        shots_query = shots_query.filter(Round.round_type == round_type)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        shots_query = shots_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        shots_query = shots_query.filter(Round.date_played <= end_date)

    # Fetch all relevant shots
    all_shots = shots_query.all()

    # Group shots by (roundID, holeID) to maintain shot sequence per hole
    shots_by_round_hole = defaultdict(list)
    for s in all_shots:
        shots_by_round_hole[(s.roundID, s.holeID)].append(s)

    # Sort each list by shotID (assuming shotID is chronological)
    for key in shots_by_round_hole:
        shots_by_round_hole[key].sort(key=lambda x: x.shotID)

    # ----- Debugging Section Start -----
    for (round_id, hole_id), shots in shots_by_round_hole.items():
        shot_list = []
        for shot in shots:
            shot_info = {
                "Shot ID": shot.shotID,
                "Distance Before": shot.distance_before,
                "Lie Before": shot.lie_before,
                "Distance After": shot.distance_after,
                "Lie After": shot.lie_after,
                "Shot Type": shot.shot_type  # Added for clarity
            }
            shot_list.append(shot_info)
    
    # ----- Debugging Section End -----

    # --------------- 4) Prepare Structures for Bunker vs. Non-Bunker ---------------
    # We'll track stats in 4 distance "bins": <10, 10–20, 20–30, 30+
    # Each bin tracks totalShots, sumProximity, upDownSuccessShots

    bunker_bins = {
        "<10 yds": {"count": 0, "sumProximity": 0.0, "upDownSuccess": 0},
        "10-20 yds": {"count": 0, "sumProximity": 0.0, "upDownSuccess": 0},
        "20-30 yds": {"count": 0, "sumProximity": 0.0, "upDownSuccess": 0},
        "30+ yds": {"count": 0, "sumProximity": 0.0, "upDownSuccess": 0},
    }
    non_bunker_bins = {
        "<10 yds": {"count": 0, "sumProximity": 0.0, "upDownSuccess": 0},
        "10-20 yds": {"count": 0, "sumProximity": 0.0, "upDownSuccess": 0},
        "20-30 yds": {"count": 0, "sumProximity": 0.0, "upDownSuccess": 0},
        "30+ yds": {"count": 0, "sumProximity": 0.0, "upDownSuccess": 0},
    }

    # Global counters for Up & Down %
    total_arounds = 0
    total_up_down_success = 0

    def get_distance_bin(dist_before):
        if dist_before < 10:
            return "<10 yds"
        elif dist_before < 20:
            return "10-20 yds"
        elif dist_before < 30:
            return "20-30 yds"
        else:
            return "30+ yds"

    # Helper to check if a shot is "up & down" success
    #  - If the shot.lie_after == "In the Hole", success = True
    #  - Else if next shot in same hole is "In the Hole", success = True
    #  - Otherwise = False
    def shot_up_and_down_success(shot, next_shot):
        # If this shot itself finishes in the hole
        if shot.lie_after == "In the Hole":
            return True
        # Or the subsequent shot is in the hole
        if next_shot and next_shot.lie_after == "In the Hole":
            return True
        return False

    # --------------- 5) Iterate All Shots and Fill Data ---------------
    for (round_hole_key, shot_list) in shots_by_round_hole.items():

        for i, shot in enumerate(shot_list):
            # Only process "Around the Green" shots
            if shot.shot_type != "Around the Green":
                continue  # Skip non-Around the Green shots

            # Determine if bunker or non-bunker
            is_bunker = (shot.lie_before == "Bunker")

            # Find the next shot (any shot type)
            next_shot = shot_list[i+1] if (i+1 < len(shot_list)) else None


            # Bucket by distance_before
            dist_bin = get_distance_bin(shot.distance_before)

            # Check up & down success
            up_down_success = 1 if shot_up_and_down_success(shot, next_shot) else 0

            # Update global counters
            total_arounds += 1
            total_up_down_success += up_down_success

            # Add to the appropriate bin
            if is_bunker:
                bunker_bins[dist_bin]["count"] += 1
                bunker_bins[dist_bin]["sumProximity"] += shot.distance_after
                bunker_bins[dist_bin]["upDownSuccess"] += up_down_success
            else:
                non_bunker_bins[dist_bin]["count"] += 1
                non_bunker_bins[dist_bin]["sumProximity"] += shot.distance_after
                non_bunker_bins[dist_bin]["upDownSuccess"] += up_down_success

    # --------------- 6) Convert Bins to Lists for JSON ---------------
    def convert_bins_to_list(bins_dict):
        results = []
        for distance_range in ["<10 yds", "10-20 yds", "20-30 yds", "30+ yds"]:
            count = bins_dict[distance_range]["count"]
            sum_prox = bins_dict[distance_range]["sumProximity"]
            ud_success = bins_dict[distance_range]["upDownSuccess"]

            avg_prox = (sum_prox / count) if count > 0 else 0.0
            up_down_pct = (ud_success / count * 100) if count > 0 else 0.0

            results.append({
                "distanceRange": distance_range,
                "avgProximity": round(avg_prox, 1),
                "upDownPercent": round(up_down_pct, 1)
            })
        return results

    bunker_data = convert_bins_to_list(bunker_bins)
    non_bunker_data = convert_bins_to_list(non_bunker_bins)

    # --------------- 7) Calculate Up & Down % Based on Shots ---------------
    up_down_percent = (total_up_down_success / total_arounds * 100) if total_arounds > 0 else 0.0

    # --------------- 8) Return the Complete Data ---------------
    data = {
        "avg_around_green_sg": round(avg_around_green_sg, 2),
        "up_down_percent": round(up_down_percent, 1),  # Updated Up & Down %
        "bunkerData": bunker_data,
        "nonBunkerData": non_bunker_data
    }
    return jsonify(data)



@app.route('/api/putting_stats', methods=['GET'])
@login_required
def putting_stats():
    """
    Returns a JSON object containing:
      - avg_putting_sg (float): Average Strokes Gained for Putting
      - puttingData (list of dicts): Stats for each distance bin
    """
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    round_type = request.args.get('round_type')
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # 1) Calculate Average SG Putting
    # Assuming 'sg_putting' is a field in the Round model
    sg_query = db.session.query(
        func.avg(Round.sg_putting).label('avg_putting_sg')
    ).filter(Round.userID == current_user.userID)

    # Apply filters
    if course_id:
        sg_query = sg_query.filter(Round.course_id == course_id)
    if round_id:
        sg_query = sg_query.filter(Round.roundID == round_id)
    if round_type:
        sg_query = sg_query.filter(Round.round_type == round_type)
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            sg_query = sg_query.filter(Round.date_played >= start_date)
        except ValueError:
            return jsonify({"error": "Invalid startDate format. Use YYYY-MM-DD."}), 400
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            sg_query = sg_query.filter(Round.date_played <= end_date)
        except ValueError:
            return jsonify({"error": "Invalid endDate format. Use YYYY-MM-DD."}), 400

    sg_result = sg_query.one()
    avg_putting_sg = round(float(sg_result.avg_putting_sg or 0), 2)

    # 2) Query all Shots (not just 'Putting'), so we have the full hole sequence
    shots_query = (db.session.query(Shot)
                   .join(Round, Shot.roundID == Round.roundID)
                   .filter(Round.userID == current_user.userID))

    # Apply filters
    if course_id:
        shots_query = shots_query.filter(Round.course_id == course_id)
    if round_id:
        shots_query = shots_query.filter(Round.roundID == round_id)
    if round_type:
        shots_query = shots_query.filter(Round.round_type == round_type)
    if start_date_str:
        shots_query = shots_query.filter(Round.date_played >= start_date)
    if end_date_str:
        shots_query = shots_query.filter(Round.date_played <= end_date)

    all_shots = shots_query.all()

    # 3) Group shots by (roundID, holeID) to maintain shot sequence per hole
    shots_by_round_hole = defaultdict(list)
    for s in all_shots:
        shots_by_round_hole[(s.roundID, s.holeID)].append(s)

    # Sort each list by shotID (assuming shotID is chronological)
    for key in shots_by_round_hole:
        shots_by_round_hole[key].sort(key=lambda x: x.shotID)

    # 4) Prepare Structures for Putting Bins
    putting_bins = {
        "0-3 ft":    {"countShots": 0, "countMakes": 0, "count3PuttAvoid": 0, "sumNextDist": 0.0},
        "3-6 ft":    {"countShots": 0, "countMakes": 0, "count3PuttAvoid": 0, "sumNextDist": 0.0},
        "6-9 ft":    {"countShots": 0, "countMakes": 0, "count3PuttAvoid": 0, "sumNextDist": 0.0},
        "9-12 ft":   {"countShots": 0, "countMakes": 0, "count3PuttAvoid": 0, "sumNextDist": 0.0},
        "12-15 ft":  {"countShots": 0, "countMakes": 0, "count3PuttAvoid": 0, "sumNextDist": 0.0},
        "15-20 ft":  {"countShots": 0, "countMakes": 0, "count3PuttAvoid": 0, "sumNextDist": 0.0},
        "20-25 ft":  {"countShots": 0, "countMakes": 0, "count3PuttAvoid": 0, "sumNextDist": 0.0},
        "25-30 ft":  {"countShots": 0, "countMakes": 0, "count3PuttAvoid": 0, "sumNextDist": 0.0},
        "30-40 ft":  {"countShots": 0, "countMakes": 0, "count3PuttAvoid": 0, "sumNextDist": 0.0},
        "40-50 ft":  {"countShots": 0, "countMakes": 0, "count3PuttAvoid": 0, "sumNextDist": 0.0},
        "50-60 ft":  {"countShots": 0, "countMakes": 0, "count3PuttAvoid": 0, "sumNextDist": 0.0},
        "60+ ft":    {"countShots": 0, "countMakes": 0, "count3PuttAvoid": 0, "sumNextDist": 0.0},
    }

    def get_putting_bin(d):
        if d < 3:
            return "0-3 ft"
        elif d < 6:
            return "3-6 ft"
        elif d < 9:
            return "6-9 ft"
        elif d < 12:
            return "9-12 ft"
        elif d < 15:
            return "12-15 ft"
        elif d < 20:
            return "15-20 ft"
        elif d < 25:
            return "20-25 ft"
        elif d < 30:
            return "25-30 ft"
        elif d < 40:
            return "30-40 ft"
        elif d < 50:
            return "40-50 ft"
        elif d < 60:
            return "50-60 ft"
        else:
            return "60+ ft"

    def is_three_putt_avoided(shot_list, i):
        """
        Returns True if from shot_list[i], we complete the hole in <= 2 putts.
        Specifically:
          - If this shot.lie_after == 'In the Hole', then 1 putt => avoid 3 putt
          - Else if next shot (i+1) is in the same hole & also finishes 'In the Hole', => 2 putts => avoid 3 putt
          - Otherwise => it's at least a 3-putt from here => return False.
        """
        curr_shot = shot_list[i]
        # If this putt itself goes in:
        if curr_shot.lie_after == "In the Hole":
            return True
        
        # Otherwise, check the next shot
        if (i + 1) < len(shot_list):
            next_shot = shot_list[i+1]
            # Ensure it's the same hole
            if next_shot.holeID == curr_shot.holeID and next_shot.lie_after == "In the Hole":
                return True  # 2 total putts
        return False  # 3+ putts

    # 5) Iterate over each hole's shot list
    for (round_id, hole_id), shot_list in shots_by_round_hole.items():
        for i, shot in enumerate(shot_list):
            # We only care about Putting shots
            if shot.shot_type != "Putting":
                continue

            # Determine which bin this shot belongs to
            bin_label = get_putting_bin(shot.distance_before)

            # Update the counters
            putting_bins[bin_label]["countShots"] += 1

            # Make rate: is the putt holed right now?
            if shot.lie_after == "In the Hole":
                putting_bins[bin_label]["countMakes"] += 1

            # 3-Putt Avoidance
            if is_three_putt_avoided(shot_list, i):
                putting_bins[bin_label]["count3PuttAvoid"] += 1

            # Sum next putt distance (i.e., distance_after)
            # If the ball goes in, distance_after is 0
            putting_bins[bin_label]["sumNextDist"] += shot.distance_after

    # 6) Convert the data into a list of rows for JSON
    puttingData = []
    for bin_label, stats in putting_bins.items():
        cShots   = stats["countShots"]
        cMakes   = stats["countMakes"]
        cAvoid   = stats["count3PuttAvoid"]
        sumDist  = stats["sumNextDist"]

        makeRate         = (cMakes / cShots * 100) if cShots > 0 else 0.0
        threePuttAvoid   = (cAvoid / cShots * 100) if cShots > 0 else 0.0
        avgNextPuttDist  = (sumDist / cShots)       if cShots > 0 else 0.0

        row = {
            "distanceRange":     bin_label,
            "makeRate":          round(makeRate, 1),
            "threePuttAvoid":    round(threePuttAvoid, 1),
            "avgNextPuttDist":   round(avgNextPuttDist, 1)
        }
        puttingData.append(row)

    # 7) Return as JSON including avg_putting_sg
    data = {
        "avg_putting_sg": avg_putting_sg,
        "puttingData": puttingData
    }
    return jsonify(data)

@app.route('/api/distance_histogram', methods=['GET'])
@login_required
def distance_histogram():
    """
    Returns histogram data of distance_before (converted to yards if lie_before='Green') 
    using custom bins:
      - First bin: 1–3 yards,
      - Second bin: 3–5 yards,
      - Then 5-yard bins from 5 up to 600 yards.
    Each bin includes the average strokes gained (sg) for shots in that range.
    Only shots > 1 yard are considered.
    Applies the same filters (course, round, date range) as the rest of the dashboard.
    """
    # 1) Parse request args (filters)
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    round_type = request.args.get('round_type')
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # 2) Query Shots joined with Round so we can filter by user & the same dashboard filters
    shot_query = (db.session.query(Shot.distance_before, Shot.lie_before, Shot.strokes_gained)
                  .join(Round, Shot.roundID == Round.roundID)
                  .filter(Round.userID == current_user.userID))

    if course_id:
        shot_query = shot_query.filter(Round.course_id == course_id)
    if round_id:
        shot_query = shot_query.filter(Round.roundID == round_id)
    if round_type:
        shot_query = shot_query.filter(Round.round_type == round_type)
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        shot_query = shot_query.filter(Round.date_played >= start_date)
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        shot_query = shot_query.filter(Round.date_played <= end_date)

    shots = shot_query.all()

    # 3) Process distances and strokes gained.
    distances_yards = []
    strokes_gained_list = []
    for (dist_before, lie_before, sg) in shots:
        if lie_before == "Green":
            # Convert from feet to yards.
            dist_yards = dist_before / 3.0
        else:
            dist_yards = dist_before
        # Clip distances to be within 0 and 600 yards.
        if dist_yards < 0:
            dist_yards = 0
        elif dist_yards > 600:
            dist_yards = 600
        distances_yards.append(dist_yards)
        strokes_gained_list.append(sg)

    # 4) Define custom bins.
    # First bin: 1 to 3 yards, second bin: 3 to 5 yards.
    custom_bins = [(1, 3), (3, 5)]
    # Then, add 5-yard bins from 5 up to 600.
    for lower in range(5, 600, 5):
        custom_bins.append((lower, lower + 5))
    num_bins = len(custom_bins)
    bin_labels = [f"{lb}-{ub}" for (lb, ub) in custom_bins]
    bin_counts = [0] * num_bins
    bin_total_sg = [0.0] * num_bins

    # 5) Increment counts and accumulate strokes gained for each shot.
    for dist_y, sg in zip(distances_yards, strokes_gained_list):
        # Only consider shots > 1 yard.
        if dist_y <= 1:
            continue
        assigned = False
        for i, (lb, ub) in enumerate(custom_bins):
            # For all bins except the last, include shot if lb <= dist < ub.
            # For the last bin, include shot if lb <= dist <= ub.
            if i == num_bins - 1:
                if lb <= dist_y <= ub:
                    bin_counts[i] += 1
                    bin_total_sg[i] += sg
                    assigned = True
                    break
            else:
                if lb <= dist_y < ub:
                    bin_counts[i] += 1
                    bin_total_sg[i] += sg
                    assigned = True
                    break
        # (If not assigned, the shot is skipped.)
        if not assigned:
            continue

    # 6) Compute average strokes gained per bin.
    bin_avg_sg = []
    for i in range(num_bins):
        if bin_counts[i] > 0:
            avg_sg = bin_total_sg[i] / bin_counts[i]
        else:
            avg_sg = 0.0
        bin_avg_sg.append(avg_sg)

    # 7) Return JSON with bin labels, counts, and average strokes gained.
    data = {
        "bin_labels": bin_labels,
        "bin_counts": bin_counts,
        "bin_avg_sg": bin_avg_sg
    }
    return jsonify(data)

@app.route('/api/putts_1to15_make_rate', methods=['GET'])
@login_required
def putts_1to15_make_rate():
    """
    Returns an array of length 15, where each entry has:
      {
        "distance": i,               # i = 1..15
        "makeRate": float,           # in percent
        "avgStrokesGained": float    # average SG for putts at this distance
      }
    Only includes shots with lie_before='Green' (i.e. on the green) 
    and shot_type='Putting', ignoring distances outside 1..15 feet.
    Respects the same filters as the main dashboard (course, round, etc.).
    """
    import math

    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    round_type = request.args.get('round_type')
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    # Build query of Shots joined with Round.
    # We want putting shots on the green, ignoring distance <1 or >15 feet.
    query = (
        db.session.query(Shot)
        .join(Round, Shot.roundID == Round.roundID)
        .filter(
            Round.userID == current_user.userID,
            Shot.lie_before == "Green",    # On green before putt
            Shot.shot_type == "Putting"    # Marked as putting shots
        )
    )

    # Apply filters
    if course_id:
        query = query.filter(Round.course_id == course_id)
    if round_id:
        query = query.filter(Round.roundID == round_id)
    if round_type:
        query = query.filter(Round.round_type == round_type)
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            query = query.filter(Round.date_played >= start_date)
        except ValueError:
            return jsonify({"error": "Invalid startDate format. Use YYYY-MM-DD."}), 400
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            query = query.filter(Round.date_played <= end_date)
        except ValueError:
            return jsonify({"error": "Invalid endDate format. Use YYYY-MM-DD."}), 400

    # Fetch all relevant shots
    shots = query.all()

    # Prepare bins for distances 1..15 feet
    # Each bin: { totalShots, totalMakes, sumSG }
    bins = []
    for i in range(1, 16):
        bins.append({
            "distance": i,
            "countShots": 0,
            "countMakes": 0,
            "sumSG": 0.0
        })

    # Populate bins
    for s in shots:
        # distance_before is in feet already if lie_before == "Green"
        dist_foot = int(math.floor(s.distance_before or 0))
        if dist_foot < 1 or dist_foot > 15:
            continue  # skip anything outside 1..15

        index = dist_foot - 1  # 0-based index in the bins array
        bins[index]["countShots"] += 1
        bins[index]["sumSG"] += (s.strokes_gained or 0.0)

        # If putt ended in hole, that’s a make
        if s.lie_after == "In the Hole":
            bins[index]["countMakes"] += 1

    # Compute final makeRate% and avgStrokesGained for each bin
    output = []
    for b in bins:
        cShots = b["countShots"]
        if cShots > 0:
            makeRate = (b["countMakes"] / cShots) * 100.0
            avgSG = b["sumSG"] / cShots
        else:
            makeRate = 0.0
            avgSG = 0.0

        output.append({
            "distance": b["distance"],
            "makeRate": round(makeRate, 1),
            "avgStrokesGained": round(avgSG, 2)
        })

    return jsonify(output)


@app.route('/api/three_putt_percent', methods=['GET'])
@login_required
def three_putt_percent():
    """
    Returns JSON array of objects like:
      [
        {
          "bracket": "15-20",
          "threePuttPercent":  (float),
          "boxStats": {
            "min":    (float),
            "q1":     (float),
            "median": (float),
            "q3":     (float),
            "max":    (float)
          }
        },
        ...
      ]
    """
    course_id = request.args.get('course', type=int)
    round_id = request.args.get('round', type=int)
    round_type = request.args.get('round_type')
    start_date_str = request.args.get('startDate')
    end_date_str = request.args.get('endDate')

    shot_query = (db.session.query(Shot)
                  .join(Round, Shot.roundID == Round.roundID)
                  .filter(Round.userID == current_user.userID,
                          Shot.shot_type == "Putting",
                          Shot.lie_before == "Green"))

    if course_id:
        shot_query = shot_query.filter(Round.course_id == course_id)
    if round_id:
        shot_query = shot_query.filter(Round.roundID == round_id)
    if round_type:
        shot_query = shot_query.filter(Round.round_type == round_type)
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            shot_query = shot_query.filter(Round.date_played >= start_date)
        except ValueError:
            return jsonify({"error": "Invalid startDate format"}), 400
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            shot_query = shot_query.filter(Round.date_played <= end_date)
        except ValueError:
            return jsonify({"error": "Invalid endDate format"}), 400

    all_putts = shot_query.all()

    # Group shots by (roundID, holeID) to see how many putts per hole
    from collections import defaultdict
    shots_by_hole = defaultdict(list)
    for s in all_putts:
        shots_by_hole[(s.roundID, s.holeID)].append(s)

    # Sort each hole's shots by shotID
    for key in shots_by_hole:
        shots_by_hole[key].sort(key=lambda x: x.shotID)

    # Distance brackets
    bracket_edges = [
        (15, 20), (20, 25), (25, 30), (30, 35),
        (35, 40), (40, 45), (45, 50), (50, 55), (55, 60)
    ]
    brackets = []
    for (low, high) in bracket_edges:
        bracket_label = f"{low}-{high}"
        brackets.append({
            "label": bracket_label,
            "attempts": 0,
            "threePutts": 0,
            "distAfters": []   # store all distance_after values
        })

    def get_bracket_label(d_ft):
        for (low, high) in bracket_edges:
            if low <= d_ft < high:
                return f"{low}-{high}"
        return None

    for _, shot_list in shots_by_hole.items():
        n = len(shot_list)
        for i, shot in enumerate(shot_list):
            dist_ft = shot.distance_before
            bracket_label = get_bracket_label(dist_ft)
            if bracket_label is None:
                continue  # not in 15..60 range

            # Count how many putts from this shot forward until the ball is holed
            putt_count = 1
            if shot.lie_after != "In the Hole":
                for j in range(i+1, n):
                    nxt = shot_list[j]
                    if nxt.shot_type == "Putting":
                        putt_count += 1
                    if nxt.lie_after == "In the Hole":
                        break

            # Find bracket record and update
            for b in brackets:
                if b["label"] == bracket_label:
                    b["attempts"] += 1
                    if putt_count >= 3:
                        b["threePutts"] += 1
                    # Collect distance_after for the *first* putt in that bracket
                    b["distAfters"].append(shot.distance_after or 0.0)
                    break

    # Helper to compute five-number summary
    def five_number_summary(values):
        # Return (min, q1, median, q3, max)
        # We'll do a simple approach. Sort, then pick the quartiles by .25, .5, .75
        if not values:
            return (0, 0, 0, 0, 0)
        sorted_vals = sorted(values)
        mn = sorted_vals[0]
        mx = sorted_vals[-1]

        def percentile(sorted_list, p):
            # p in [0..1], e.g. 0.25 for Q1
            idx = (len(sorted_list) - 1) * p
            lower = int(idx)
            upper = min(lower + 1, len(sorted_list) - 1)
            frac = idx - lower
            return sorted_list[lower] + (sorted_list[upper] - sorted_list[lower]) * frac

        q1 = percentile(sorted_vals, 0.25)
        med = percentile(sorted_vals, 0.50)
        q3 = percentile(sorted_vals, 0.75)
        return (mn, q1, med, q3, mx)

    # Build final output
    output = []
    for b in brackets:
        attempts = b["attempts"]
        if attempts > 0:
            rate = (b["threePutts"] / attempts) * 100.0
        else:
            rate = 0.0

        (mn, q1, med, q3, mx) = five_number_summary(b["distAfters"])
        stats = {
            "min":    round(mn, 1),
            "q1":     round(q1, 1),
            "median": round(med, 1),
            "q3":     round(q3, 1),
            "max":    round(mx, 1),
        }

        output.append({
            "bracket": b["label"],
            "threePuttPercent": round(rate, 1),
            "boxStats": stats
        })

    return jsonify(output)

@app.route('/api/round_analysis', methods=['GET'])
@login_required
def round_analysis():
    """
    Returns JSON with analysis of a round:
      - If the query string includes a "round" parameter, that round is used.
        Otherwise, the most recent round for the user is returned.
      - The response includes "round_info" (e.g. roundID and date_played),
        "best_shots" (the top 3 shots by strokes gained, highest first) and 
        "worst_shots" (the bottom 3 shots by strokes gained).
      
      Each shot is serialized to include:
          - shotID
          - hole (using shot.holeID)
          - shot_number (its order number in the round based on shotID)
          - distance_before, lie_before, distance_after, lie_after
          - strokes_gained
    """
    # Get the round parameter from the query, if provided.
    round_id = request.args.get('round', type=int)
    
    if round_id:
        # Use the specified round, ensuring it belongs to the current user.
        selected_round = Round.query.filter_by(roundID=round_id, userID=current_user.userID).first()
    else:
        # If no round specified, default to the most recent round.
        selected_round = (
            Round.query.filter_by(userID=current_user.userID)
                 .order_by(Round.date_played.desc())
                 .first()
        )
    
    if not selected_round:
        # Return an empty result if no round is found.
        return jsonify({
            'round_info': None,
            'best_shots': [],
            'worst_shots': []
        })

    # Retrieve all shots associated with the selected round.
    shots = selected_round.shots
    if not shots:
        return jsonify({
            'round_info': {'roundID': selected_round.roundID,
                           'date_played': selected_round.date_played.strftime('%Y-%m-%d')},
            'best_shots': [],
            'worst_shots': []
        })

    # Sort shots by strokes gained.
    sorted_shots = sorted(shots, key=lambda s: s.strokes_gained)
    # The worst shots are the three with the lowest strokes gained.
    worst_shots = sorted_shots[:3]
    # The best shots are the three with the highest strokes gained.
    best_shots = sorted_shots[-3:]
    best_shots.reverse()  # Reverse so the highest strokes gained is first.

    # To provide a shot number (e.g. "Shot 3") we sort all shots
    # by shotID (assumed to be in chronological order).
    ordered_shots = sorted(shots, key=lambda s: s.shotID)

    def get_shot_number(shot):
        """Return the 1-indexed position of this shot within the ordered shots list."""
        for idx, s in enumerate(ordered_shots, start=1):
            if s.shotID == shot.shotID:
                return idx
        return 0

    def serialize_shot(s):
        """Serialize a shot for JSON output."""
        return {
            'shotID': s.shotID,
            'hole': s.holeID,  # Alternatively, you might extract a more user-friendly hole name if available.
            'shot_number': get_shot_number(s),
            'distance_before': s.distance_before,
            'lie_before': s.lie_before,
            'distance_after': s.distance_after,
            'lie_after': s.lie_after,
            'strokes_gained': s.strokes_gained
        }

    best_serialized = [serialize_shot(s) for s in best_shots]
    worst_serialized = [serialize_shot(s) for s in worst_shots]

    round_info = {
        'roundID': selected_round.roundID,
        'date_played': selected_round.date_played.strftime('%Y-%m-%d')
        # You can add more round-related details if desired.
    }

    return jsonify({
        'round_info': round_info,
        'best_shots': best_serialized,
        'worst_shots': worst_serialized
    })



@app.route('/get_tees/<int:course_id>')
def get_tees(course_id):
    """
    Fetches the tees associated with a specific course.
    Returns a JSON object containing the tee names and IDs.
    """
    tees = Tee.query.filter_by(courseID=course_id).all()
    return jsonify([{"teeID": tee.teeID, "name": tee.name} for tee in tees])


@app.route('/sg_calc', methods=['GET', 'POST'])
def sg_calculator():
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

    return render_template('sg_calc.html', sg=sg, sg_color=sg_color, errors=errors, 
                           before_distance=before_distance, before_lie=before_lie,
                           after_distance=after_distance, after_lie=after_lie,
                           penalty=penalty, oob=oob, hazard=hazard, unit=unit)

if __name__ == '__main__':
    app.run(debug=True)
