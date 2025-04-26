import requests
from flask import Blueprint, render_template, request, jsonify, url_for, session
from video import store_video, query_video, query_all_videos
from user import add_user_to_db, login_user_from_db, check_if_user_exists, get_user_from_db
from helper import is_logged_in, otp_generator, send_user_otp, compare_passwords, validate_email, validate_password, \
    clear_user_credentials, object_id_to_str, mock_data

routes = Blueprint('routes', __name__, static_folder='static', template_folder='templates')


@routes.route('/index')
@routes.route('/')
def home():
    if "user_type" in session:
        current_page = "homepage"
        return render_template('index.html', currentPage=current_page, isLoggedIn=is_logged_in(session), videos=query_all_videos(user_id=session['_id']))
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
        return jsonify({"error": "No video file uploaded"}), 400

    video = request.files['video']

    if video.filename == '':
        return jsonify({"error": "No selected file"}), 400

    video.stream.seek(0)

    video_id = store_video(video, session)
    video_url = url_for('routes.get_video', video_id=str(video_id))

    choose = "mock"
    # choose = "summary"

    if choose == "mock":
        response = mock_data()
    else:
        video.stream.seek(0)

        response = requests.post(
            'http://127.0.0.1:5001/summarize',
            files={'video': (video.filename or "uploaded_video.mp4", video.stream, video.mimetype or "video/mp4")}
        )

        if response.status_code == 200:
            response = response.json()
        else:
            response = {"error": "Failed to summarize video"}

    return jsonify({
        "video_id": str(video_id),
        "video_url": video_url,
        "data": response
    }), 200


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

    if check_if_user_exists(email):
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
    clear_user_credentials(session)

    return jsonify({"success": "Verified otp successfully."}), 200


@routes.route('/loginUser', methods=['POST'])
def login_user():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    response, status_code = login_user_from_db(email, password)

    if "error" in response.keys():
        return jsonify({"error": response["error"]}), 400

    _id = object_id_to_str(get_user_from_db(email)['_id'])

    if status_code % 200 == 0:
        session["user_type"] = "user"
        session["email"] = email
        session["_id"] = _id

    return jsonify(response), status_code


@routes.route('/logout', methods=['GET', 'POST'])
def logout():
    clear_user_credentials(session)
    current_page = "login"
    return render_template('login.html', currentPage=current_page, registrationSuccessful=False,
                           isLoggedIn=is_logged_in(session))


@routes.route('/getVideosOfUser/', methods=['GET'])
def get_videos_of_user():
    data = request.get_json()

    user_id = data.get('user_id')

    return query_all_videos(user_id)
