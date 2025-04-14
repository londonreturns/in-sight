from flask import Blueprint, render_template, request, jsonify, url_for, session
from video import store_video, query_video
from user import add_user_to_db, login_user_from_db, checkIfUserExists
from helper import is_logged_in, otp_generator, send_user_otp, compare_passwords, validate_email, validate_password, \
    clear_session, clear_user_credentials

routes = Blueprint('routes', __name__, static_folder='static', template_folder='templates')


@routes.route('/index')
@routes.route('/')
def home():
    print(session)
    if "user_type" in session:
        current_page = "homepage"
        return render_template('index.html', currentPage=current_page, isLoggedIn=is_logged_in(session))
    else:
        current_page = "login"
        temp = is_logged_in(session)
        return render_template('login.html', currentPage=current_page, isLoggedIn=temp)


@routes.route('/howItWorks')
def how_it_works():
    current_page = "howitworks"
    return render_template('howItWorks.html', currentPage=current_page, isLoggedIn=is_logged_in(session))


@routes.route('/uploadVideo', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        error_message = 'No video file uploaded'
        return jsonify({"error": error_message}), 400

    video = request.files['video']
    user_email = session.get('email')

    if video.filename == '':
        error_message = 'No selected file'
        return jsonify({"error": error_message}), 400

    video_id = store_video(video, user_email)
    video_url = url_for('routes.get_video', video_id=str(video_id))
    return jsonify({"video_id": str(video_id), "video_url": video_url}), 200


@routes.route('/video/<video_id>')
def get_video(video_id):
    return query_video(video_id)


@routes.route('/loginPage')
def login():
    current_page = "login"
    return render_template('login.html', currentPage=current_page, isLoggedIn=is_logged_in(session))


@routes.route('/loginPage/successfulRegistration')
def login_successful_registration():
    current_page = "login"
    return render_template('login.html', currentPage=current_page, isLoggedIn=is_logged_in(session))


@routes.route('/registrationPage')
def registration():
    current_page = "registration"
    return render_template('registration.html', currentPage=current_page, isLoggedIn=is_logged_in(session))


@routes.route('/registerUser', methods=['POST'])
def register_user():
    if request.content_type != 'application/json':
        return jsonify({"error": "Unsupported Media Type"}), 415

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirmPassword')

    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    if not validate_password(password):
        return jsonify({"error": "Invalid password format"}), 400

    if checkIfUserExists(email):
        return jsonify({"error": "Email already exists"}), 400

    if not compare_passwords(password, confirm_password):
        return jsonify({"error": "Passwords do not match"}), 400

    otp = otp_generator()
    send_user_otp(email, otp)

    session['otp'] = otp
    session['user_credentials'] = {'email': email, 'password': password, 'confirm_password': confirm_password}

    return jsonify({"success": "Credentials received successfully."}), 200


@routes.route('/accountVerification', methods=['POST', 'GET'])
def account_verification():
    return render_template('accountVerification.html', isLoggedIn=is_logged_in(session))


@routes.route('/verifyOtp', methods=['POST'])
def verify_otp():
    if session.get('otp') is None:
        return jsonify({"error": "No OTP generated"}), 400

    if session['otp'] != request.json.get('otp'):
        return jsonify({"error": "Invalid OTP"}), 400

    add_user_to_db(session['user_credentials']['email'], session['user_credentials']['password'])
    clear_session(session)

    return jsonify({"success": "Verified otp successfully."}), 200


@routes.route('/loginUser', methods=['POST'])
def login_user():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    response, status_code = login_user_from_db(email, password)

    if status_code % 200 == 0:
        session["user_type"] = "user"
        session["email"] = email

    return jsonify(response), status_code


@routes.route('/logout', methods=['GET', 'POST'])
def logout():
    clear_user_credentials(session)
    current_page = "login"
    return render_template('login.html', currentPage=current_page, registrationSuccessful=False,
                           isLoggedIn=is_logged_in(session))
