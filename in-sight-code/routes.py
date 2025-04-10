from flask import Blueprint, render_template, request, jsonify, url_for
from database import store_video, query_video
from user import add_user_to_db, login_user_from_db

routes = Blueprint('routes', __name__, static_folder='static', template_folder='templates')


@routes.route('/index')
@routes.route('/')
def home():
    currentPage = "homepage"
    return render_template('index.html', currentPage=currentPage)


@routes.route('/howItWorks')
def how_it_works():
    currentPage = "howitworks"
    return render_template('howItWorks.html', currentPage=currentPage)


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
    return render_template('login.html', currentPage=currentPage, registrationSuccessful=False)


@routes.route('/loginPage/successfulRegistration')
def login_sucessful_registration():
    currentPage = "login"
    return render_template('login.html', currentPage=currentPage, registrationSuccessful=True)


@routes.route('/registrationPage')
def registration():
    currentPage = "registration"
    return render_template('registration.html', currentPage=currentPage)


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

    # Call your function to add the user to the database
    response, status_code = add_user_to_db(email, password, confirm_password)
    return jsonify(response), status_code


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

    return response
