from database import open_connection, close_connection
from helper import sha_256, compare_passwords


def add_user_to_db(email, password):
    db, client = open_connection()
    users_collection = db['users']

    existing_user = users_collection.find_one({"username": email})
    if existing_user:
        return {"error": "Email already exists"}, 400

    user_data = {
        "email": email,
        "password": sha_256(password),
        "user_type": "user",
        "verified": True
    }
    users_collection.insert_one(user_data)
    close_connection(client)
    return {"message": "User registered successfully"}, 200


def login_user_from_db(email, password):
    check_user = check_if_user_exists(email)
    if check_user is not None and compare_passwords(check_user['password'], sha_256(password)):
        return {"message": "Login successful"}, 200
    elif check_user is None:
        return {"error": "User not found. Please check your credentials."}, 404
    elif not check_user['verified']:
        return {"error": "User not verified"}, 401
    else:
        return {"error": "Please try again. Some error occurred"}, 401


def check_if_user_exists(email):
    db, client = open_connection()
    users_collection = db['users']
    existing_user = users_collection.find_one({"email": email})
    close_connection(client)
    if existing_user:
        return existing_user
    else:
        return None


def get_user_from_db(email):
    db, client = open_connection()
    users_collection = db['users']
    existing_user = users_collection.find_one({"email": email})
    close_connection(client)
    if existing_user:
        return existing_user
    else:
        return None