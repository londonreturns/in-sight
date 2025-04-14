from pymongo import MongoClient
from os import getenv


def open_connection():
    client = MongoClient(getenv('DATABASE_CONNECTION_STRING'))
    db = client[getenv('CLIENT_NAME')]
    return db, client


def close_connection(client):
    client.close()
