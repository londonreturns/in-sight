from hashlib import sha256
from random import randint

def sha_256(string):
    return sha256(string.encode('utf-8')).hexdigest()

def is_logged_in(session):
    return session.get("user_type", None)

def otp_generator():
    # otp = ""
    # for i in range(6):
    #     otp += str(randint(0, 9))
    # return otp
    return "000000"

def send_user_otp(user_email, otp):
    print(f"Sending OTP {otp} to {user_email}")

def compare_passwords(password, confirm_password):
    if password != confirm_password:
        return False
    return True

def clear_session(session):
    session.pop('user_credentials', None)
    session.pop('otp', None)
    session.pop('user_type', None)