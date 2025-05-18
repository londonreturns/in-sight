from os import path, remove
from re import fullmatch
from os import getenv
from smtplib import SMTP_SSL
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from hashlib import sha256
from random import randint
from bson import ObjectId
from dotenv import load_dotenv
from database import open_connection, close_connection
from tempfile import NamedTemporaryFile
from io import BytesIO
from cv2 import VideoCapture, CAP_PROP_FPS, CAP_PROP_FRAME_COUNT, CAP_PROP_POS_MSEC, CAP_PROP_POS_FRAMES, cvtColor, \
    COLOR_BGR2RGB, resize
from PIL import Image
from gridfs import GridFS
from flask import render_template
from moviepy import VideoFileClip
import tempfile
import os


def sha_256(string):
    return sha256(string.encode('utf-8')).hexdigest()


def is_logged_in(session):
    return session.get("user_type", None)


def is_session_expired(session):
    if not session.get("_id") or not session.get("user_type"):
        current_page = "login"
        return render_template('login.html', currentPage=current_page, isLoggedIn=False)
    return None


def otp_generator():
    otp = ""
    for i in range(6):
        otp += str(randint(0, 9))
    return otp


def send_user_otp(receiver_email, otp_code):
    sender_email, sender_password, host, port = load_smtp_credentials().values()

    subject = "In-Sight OTP Verification"

    BASE_DIR = path.dirname(path.abspath(__file__))
    template_dir = path.join(BASE_DIR, 'html_templates', 'otp_template.html')

    with open(template_dir, "r") as file:
        html_content = file.read().replace("{{ otp_code }}", otp_code)

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    mime_html = MIMEText(html_content, "html")
    message.attach(mime_html)

    with SMTP_SSL(host, port) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())


def compare_passwords(password, confirm_password):
    if password != confirm_password:
        return False
    return True


def clear_user_credentials(session):
    session.pop('user_credentials', None)
    session.pop('email', None)
    session.pop('password', None)
    session.pop('confirm_password', None)
    session.pop('otp_code', None)
    session.pop('user_type', None)
    session.pop('id', None)
    session.clear()


def load_smtp_credentials():
    load_dotenv()
    return {
        "email": getenv('SMTP_EMAIL'),
        "password": getenv('SMTP_PASSWORD'),
        "host": getenv('SMTP_HOST'),
        "port": int(getenv('SMTP_PORT'))
    }


def validate_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return fullmatch(email_regex, email)


def validate_password(password):
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{9,}$'
    return fullmatch(password_regex, password)


def object_id_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, list):
        return [str(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: object_id_to_str(value) for key, value in obj.items()}
    else:
        return obj


def generate_thumbnail(video_id):
    db, client = open_connection()
    fs = GridFS(db)
    video_file = fs.get(ObjectId(video_id))

    video_bytes = video_file.read()

    with NamedTemporaryFile(delete=False) as temp_video_file:
        temp_video_file.write(video_bytes)
        temp_video_path = temp_video_file.name

    video = VideoCapture(temp_video_path)

    if not video.isOpened():
        return {"error": "Failed to open video."}, 500

    fps = video.get(CAP_PROP_FPS)
    frame_count = int(video.get(CAP_PROP_FRAME_COUNT))
    video_length = frame_count / fps if fps > 0 else 0

    if video_length > 1:
        video.set(CAP_PROP_POS_MSEC, 1000)
    else:
        video.set(CAP_PROP_POS_FRAMES, 0)

    ret, frame = video.read()
    if not ret:
        return {"error": "Failed to read the video frame."}, 500

    thumbnail = resize(frame, (410, 200))

    thumbnail_rgb = cvtColor(thumbnail, COLOR_BGR2RGB)

    pil_image = Image.fromarray(thumbnail_rgb)

    thumbnail_io = BytesIO()
    pil_image.save(thumbnail_io, format="PNG")
    thumbnail_io.seek(0)

    thumbnail_id = fs.put(thumbnail_io, filename=f"{video_id}_thumbnail.png")

    db.videos.update_one(
        {"_id": ObjectId(video_id)},
        {"$set": {"thumbnail_id": thumbnail_id}}
    )

    video.release()
    remove(temp_video_path)

    close_connection(client)

    return {"message": "Thumbnail generated successfully", "thumbnail_id": str(thumbnail_id)}


def convert_video_to_audio(video):
    # If video is in memory as a BytesIO object, save it to a temporary file
    if isinstance(video, BytesIO):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video_file:
            video_path = temp_video_file.name
            temp_video_file.write(video.read())
    else:
        # If video is already a file path, just use it
        video_path = video

    try:
        # Open the video file using MoviePy
        with VideoFileClip(video_path) as video_clip:
            # Check if the video has an audio track
            audio = video_clip.audio
            if audio is None:
                raise ValueError("Video does not contain an audio track.")

            # Write audio to a temporary .wav file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio_file:
                audio_path = temp_audio_file.name
                audio.write_audiofile(audio_path, codec='pcm_s16le')

        # Cleanup: remove the temporary video file if it was created
        if isinstance(video, BytesIO):
            os.remove(video_path)

        return audio_path

    except Exception as e:
        # Handle errors and log them
        print(f"Error during audio extraction: {e}")
        return str(e)

