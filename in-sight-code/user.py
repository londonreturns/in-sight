from database import open_connection, close_connection
from helper import sha_256


def add_user_to_db(email, password, confirm_password):
    if password != confirm_password:
        return {"error": "Passwords do not match"}, 400

    db, client = open_connection()
    users_collection = db['users']

    existing_user = users_collection.find_one({"username": email})
    if existing_user:
        return {"error": "Email already exists"}, 400

    user_data = {
        "email": email,
        "password": sha_256(password)
    }
    users_collection.insert_one(user_data)
    close_connection(client)
    return {"message": "User registered successfully"}, 200


def login_user_from_db(email, password):
    db, client = open_connection()
    users_collection = db['users']

    check_user = users_collection.find_one({"email": email})
    close_connection(client)

    pas1 = check_user['password']
    pas2 = sha_256(password)

    if check_user and pas1 == pas2:
        return {"message": "Login successful"}, 200
    else:
        return {"error": "Invalid credentials"}, 401


def checkIfUserExists(email):
    db, client = open_connection()
    users_collection = db['users']
    existing_user = users_collection.find_one({"username": email})
    close_connection(client)
    return existing_user is not None
