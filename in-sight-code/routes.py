import os.path
from datetime import timedelta
from flask import Blueprint, render_template, request, jsonify, url_for, session
from video import store_video, query_video, query_all_videos, get_thumbnail_from_db, get_updated_video_list_from_db, \
    delete_video_from_db, store_summarized_video, update_video_filename, get_summarized_video, \
    get_summarized_video_text, get_summarized_text_from_db, get_timecodes_from_db, render_video_details
from user import add_user_to_db, login_user_from_db, check_if_user_exists, get_user_from_db
from helper import is_logged_in, otp_generator, send_user_otp, compare_passwords, validate_email, validate_password, \
    clear_user_credentials, object_id_to_str, is_session_expired, convert_video_to_audio
import whisper
from helper import open_connection, close_connection
from bson.objectid import ObjectId


routes = Blueprint('routes', __name__, static_folder='static', template_folder='templates')


@routes.route('/index')
@routes.route('/')
def home():
    if "user_type" in session:
        current_page = "homepage"
        return render_template('index.html', currentPage=current_page, isLoggedIn=is_logged_in(session), videos=[])
    else:
        current_page = "login"
        temp = is_logged_in(session)
        return render_template('login.html', currentPage=current_page, isLoggedIn=temp)


@routes.route('/howItWorks')
def how_it_works():
    is_session_expired(session)

    current_page = "howitworks"
    return render_template('howItWorks.html', currentPage=current_page, isLoggedIn=is_logged_in(session))


@routes.route('/uploadVideo', methods=['POST'])
def upload_video():
    is_session_expired(session)

    if 'video' not in request.files:
        return jsonify({"error": "No video file uploaded"}), 400

    video = request.files['video']

    if video.filename == '':
        return jsonify({"error": "No selected file"}), 400

    video.stream.seek(0)

    video_id = store_video(video, session)
    video_url = url_for('routes.get_video', video_id=str(video_id))

    return jsonify({
        "video_id": str(video_id),
        "video_url": video_url
    }), 200


@routes.route('/generateSummary/<video_id>', methods=['POST'])
def generate_summary(video_id):
    is_session_expired(session)

    try:
        # Get the video from the database
        video_file = query_video(video_id, return_file=True)

        if not video_file:
            return jsonify({"error": "Video not found"}), 404

        # Read the video file content
        video_file.seek(0)
        video_bytes = video_file.read()

        # Get the threshold value from the request
        data = request.get_json()
        threshold = data.get('threshold', 1.4) if data else 1.4

        # Generate the summary video in memory
        from video_shortener import summarize_video_in_memory
        result = summarize_video_in_memory(video_bytes, threshold=threshold)
        summary_buffer = result["video"]
        timecodes = result["timecodes"]

        if not summary_buffer:
            return jsonify({"error": "Failed to generate summary video"}), 500

        # Store the summarized video in the database, save timecodes
        summary_buffer.seek(0)
        summarized_video_id = store_summarized_video(video_id, summary_buffer, timecodes=timecodes)

        return jsonify({
            "success": True,
            "message": "Summary generated successfully",
            "summarized_video_id": str(summarized_video_id),
            "timecodes": timecodes
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to generate summary: {str(e)}"}), 500


@routes.route('/getVideoTimecodes/<video_id>', methods=['GET'])
def get_video_timecodes(video_id):
    is_session_expired(session)

    timecodes = get_timecodes_from_db(video_id)
    return jsonify({
        "success": True,
        "timecodes": timecodes
    }), 200


@routes.route('/deleteVideo/<video_id>', methods=['DELETE'])
def delete_video(video_id):
    is_session_expired(session)

    if "_id" not in session:
        logout()

    db, client = open_connection()
    try:
        # Delete all associated data
        video = db.videos.find_one({"_id": ObjectId(video_id), "user_id": ObjectId(session["_id"])})
        if not video:
            return jsonify({"error": "Video not found or unauthorized"}), 404

        # Delete audio transcript
        db.audio_transcripts.delete_many({"video_id": ObjectId(video_id)})
        
        # Delete video chunks and metadata
        response, status = delete_video_from_db(session, video_id)
        
        return jsonify(response), status
    except Exception as e:
        return jsonify({"error": f"An error occurred while deleting the video: {str(e)}"}), 500
    finally:
        close_connection(client)


@routes.route('/getVideo/<video_id>')
@routes.route('/video/<video_id>')
def get_video(video_id):
    is_session_expired(session)

    print(f"hit http://127.0.0.1:5000/getVideo/{video_id}")
    response = query_video(video_id)
    print(f"original video response: {response}")
    return response


@routes.route('/getSummarizedVideo/<video_id>')
def get_summarized_video_route(video_id):
    is_session_expired(session)

    print(f"hit http://127.0.0.1:5000/getSummarizedVideo/{video_id}")
    response = get_summarized_video(video_id)
    print(f"summary video response: {response}")
    if response is None:
        return jsonify({"error": "Summarized video not found"}), 404
    return response


@routes.route('/getSummarizedVideoText/<video_id>')
def get_summarized_video_text_route(video_id):
    is_session_expired(session)

    keyframe_threshold = request.args.get("keyframe_threshold", default=80, type=int)
    print(f"hit http://127.0.0.1:5000/getSummarizedVideoText/{video_id}?keyframe_threshold={keyframe_threshold}")
    response = get_summarized_video_text(video_id, keyframe_threshold=keyframe_threshold)
    print(f"text summary response: {response}")
    if response is None:
        return jsonify({"error": "Summarized video text not found"}), 404
    return jsonify(response)


@routes.route('/checkSummaryExists/<video_id>')
def check_summary_exists_route(video_id):
    is_session_expired(session)

    from video import check_summary_exists
    has_summary = check_summary_exists(video_id)
    return jsonify({"has_summary": has_summary})


@routes.route('/getSummarizedTextFromDB/<video_id>')
def get_summarized_text_from_db_route(video_id):
    is_session_expired(session)

    response = get_summarized_text_from_db(video_id)
    if response is None:
        return jsonify({"error": "Summarized text not found"}), 404
    return jsonify(response)


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


@routes.route('/getVideosOfUser', methods=['GET'])
def get_videos_of_user():
    is_session_expired(session)

    user_id = session["_id"]
    videos = query_all_videos(user_id)
    return jsonify(videos), 200


@routes.route('/getThumbnail/<video_id>', methods=['GET'])
def get_thumbnail(video_id):
    is_session_expired(session)

    return get_thumbnail_from_db(video_id)


@routes.route('/updateVideoFilename/<video_id>', methods=['POST'])
def update_video_filename_route(video_id):
    is_session_expired(session)

    try:
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify({"error": "Filename is required"}), 400

        if data['filename'] == '':
            return jsonify({"error": "Filename cannot be empty"}), 400

        new_filename = data['filename']

        # Check if the filename has an extension, if not add .mp4 as default
        if '.' not in new_filename:
            new_filename += '.mp4'

        response, status_code = update_video_filename(video_id, new_filename)
        return jsonify(response), status_code
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@routes.route('/getUpdatedVideoList')
def get_updated_video_list():
    is_session_expired(session)

    if "_id" not in session:
        logout()

    videos = get_updated_video_list_from_db(user_id=session['_id'])
    return render_template('partials/video_list.html', videos=videos)


@routes.route('/getAudioSummarized/<video_id>', methods=['GET'])
def get_audio_summarized(video_id):
    is_session_expired(session)

    print(f"hit http://127.0.0.1:5000/getAudioSummarized/{video_id}")
    video = query_video(video_id, return_file=True)
    audio_path = convert_video_to_audio(video)

    if not os.path.exists(audio_path):
        return jsonify({"error": "Audio file not found"}), 404

    # Load the Whisper model (you can use "base", "small", "medium", or "large")
    model = whisper.load_model("base")

    # Transcribe the audio file with timestamps
    result = model.transcribe(audio_path, verbose=False)

    time_codes = []
    transcript = []

    for segment in result["segments"]:
        start_time = str(timedelta(seconds=int(segment["start"])))
        end_time = str(timedelta(seconds=int(segment["end"])))
        text = segment["text"].strip()
        time_codes.append({
            "start_time": start_time,
            "end_time": end_time,
            "transcript": text
        })
        transcript.append(text)

    # Clean up the audio file after processing
    if os.path.exists(audio_path):
        os.remove(audio_path)

    response = {
        "transcript": transcript,
        "time_codes": time_codes
    }

    print(response)

    return jsonify(response)


@routes.route('/getAudioSummarizedFromDB/<video_id>')


@routes.route('/getAudioTranscript/<video_id>', methods=['GET'])
def get_audio_transcript(video_id):
    is_session_expired(session)
    
    return get_summarized_text_from_db_route(video_id)


@routes.route('/videodetails')
def video_details_page():
    is_session_expired(session)
    return render_video_details()