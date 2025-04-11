from hashlib import sha256

def sha_256(string):
    return sha256(string.encode('utf-8')).hexdigest()

def is_logged_in(session):
    return session.get("user_type", None)