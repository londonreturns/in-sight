from os import getenv
from smtplib import SMTP_SSL
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from hashlib import sha256
from random import randint
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

    with open("html_templates/otp_template.html", "r") as file:
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


def clear_session(session):
    session.pop('user_credentials', None)
    session.pop('otp', None)
    session.pop('user_type', None)


def load_smtp_credentials():
    load_dotenv()
    return {
        "email": getenv('SMTP_EMAIL'),
        "password": getenv('SMTP_PASSWORD'),
        "host": getenv('SMTP_HOST'),
        "port": int(getenv('SMTP_PORT'))
    }
