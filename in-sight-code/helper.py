import os
import re
from os import getenv
from smtplib import SMTP_SSL
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from hashlib import sha256
from random import randint

from bson import ObjectId
from dotenv import load_dotenv
from random import choice


def sha_256(string):
    return sha256(string.encode('utf-8')).hexdigest()


def is_logged_in(session):
    return session.get("user_type", None)


def otp_generator():
    otp = ""
    for i in range(6):
        otp += str(randint(0, 9))
    return otp


def send_user_otp(receiver_email, otp_code):
    sender_email, sender_password, host, port = load_smtp_credentials().values()

    subject = "In-Sight OTP Verification"

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(BASE_DIR, 'html_templates', 'otp_template.html')

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
    return re.fullmatch(email_regex, email)


def validate_password(password):
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{9,}$'
    return re.fullmatch(password_regex, password)


def object_id_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, list):
        return [str(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: object_id_to_str(value) for key, value in obj.items()}
    else:
        return obj

def mock_data():
    mock_responses = [
        "The video covers the basics of quantum computing, explaining qubits, superposition, and entanglement in simple terms.",
        "In the video, the speaker discusses the impact of social media on mental health, with expert interviews and recent studies.",
        "This video is a beginner’s guide to investing, covering stocks, bonds, and how to build a diversified portfolio.",
        "The video explores the history of the Roman Empire, from its rise with Julius Caesar to its fall in the 5th century.",
        "It’s a documentary-style video about space exploration, highlighting major NASA missions and the future of Mars colonization.",
        "The video is a tutorial on how to cook a classic Italian lasagna, with step-by-step instructions and cooking tips.",
        "It’s a motivational talk about building discipline, featuring personal anecdotes and practical strategies for self-improvement.",
        "The video gives an overview of AI in healthcare, including applications in diagnostics, treatment planning, and patient care.",
        "This is a tech review video comparing the latest smartphones, covering performance, battery life, and camera quality.",
        "The video explains the science behind black holes, including how they form, their properties, and what happens near the event horizon."
    ]

    selected_response = choice(mock_responses)

    formatted_output = f'USER: Summarize the video\nASSISTANT: {selected_response}'
    return formatted_output