from flask import Blueprint, render_template, request, jsonify

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

    # Save the video or process it as needed
    # video.save(os.path.join('path_to_save', video.filename))

    success_message = 'Video uploaded successfully'
    return jsonify({"success": success_message}), 200
