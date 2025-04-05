from flask import Blueprint, render_template, request, jsonify, make_response, url_for
from database import store_video, query_video

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