from hashlib import sha256

def sha_256(string):
    return sha256(string.encode('utf-8')).hexdigest()