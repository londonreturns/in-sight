from flask import Blueprint, render_template, request, jsonify, url_for, session
from database import store_video, query_video
from user import add_user_to_db, login_user_from_db
from helper import is_logged_in, otp_generator, send_user_otp, compare_passwords, clear_session

routes = Blueprint('routes', __name__, static_folder='static', template_folder='templates')


@routes.route('/index')
@routes.route('/')
def home():
    if "user_type" in session:
        currentPage = "homepage"
        return render_template('index.html', currentPage=currentPage, isLoggedIn=is_logged_in(session))
    else:
        currentPage = "login"
        temp = is_logged_in(session)
        return render_template('login.html', currentPage=currentPage, registrationSuccessful=False,
                               isLoggedIn=temp)


@routes.route('/howItWorks')
def how_it_works():
    currentPage = "howitworks"
    return render_template('howItWorks.html', currentPage=currentPage, isLoggedIn=is_logged_in(session))


@routes.route('/uploadVideo', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        error_message = 'No video file uploaded'
        return jsonify({"error": error_message}), 400

    video = request.files['video']

    if video.filename == '':
        error_message = 'No selected file'
        return jsonify({"error": error_message}), 400

    video_id = store_video(video)
    video_url = url_for('routes.get_video', video_id=str(video_id))
    return jsonify({"video_id": str(video_id), "video_url": video_url}), 200


@routes.route('/video/<video_id>')
def get_video(video_id):
    return query_video(video_id)


@routes.route('/loginPage')
def login():
    currentPage = "login"
    return render_template('login.html', currentPage=currentPage, registrationSuccessful=False,
                           isLoggedIn=is_logged_in(session))


@routes.route('/loginPage/successfulRegistration')
def login_sucessful_registration():
    currentPage = "login"
    return render_template('login.html', currentPage=currentPage, registrationSuccessful=True,
                           isLoggedIn=is_logged_in(session))


@routes.route('/registrationPage')
def registration():
    currentPage = "registration"
    return render_template('registration.html', currentPage=currentPage, isLoggedIn=is_logged_in(session))


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

    add_user_to_db(session['user_credentials']['email'], session['user_credentials']['password'],
                   session['user_credentials']['confirm_password'])
    return jsonify({"success": "Verified otp successfully."}), 200


@routes.route('/loginUser', methods=['POST'])
def login_user():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    response = login_user_from_db(email, password)

    if response is None:
        return jsonify({"error": "User not found. Please check your credentials."}), 404

    session["user_type"] = "user"

    return response


@routes.route('/logout', methods=['GET', 'POST'])
def logout():
    if "user_type" in session:
        session.pop('user_type', None)
        return login()
    currentPage = "login"
    return render_template('login.html', currentPage=currentPage, registrationSuccessful=False,
                           isLoggedIn=is_logged_in(session))
