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
