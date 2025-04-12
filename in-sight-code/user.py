from database import open_connection, close_connection
from helper import sha_256, compare_passwords


def add_user_to_db(email, password, confirm_password):
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
    db, client = open_connection()
    users_collection = db['users']

    check_user = users_collection.find_one({"email": email})
    close_connection(client)

    if check_user and compare_passwords(check_user['password'], sha_256(password)):
        return {"message": "Login successful"}, 200
    elif not check_user['verified']:
        return {"error": "User not verified"}, 401
    else:
        return {"error": "Invalid credentials"}, 401


def checkIfUserExists(email):
    db, client = open_connection()
    users_collection = db['users']
    existing_user = users_collection.find_one({"username": email})
    close_connection(client)
    return existing_user is not None
