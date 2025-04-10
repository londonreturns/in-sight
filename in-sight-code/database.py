from bson import ObjectId
from flask import make_response
from pymongo import MongoClient
from os import getenv
import gridfs


def open_connection():
    client = MongoClient(getenv('DATABASE_CONNECTION_STRING'))
    db = client['in-sight']
    return db, client


def close_connection(client):
    client.close()


def store_video(video):
    db, client = open_connection()
    fs = gridfs.GridFS(db)
    video_id = fs.put(video, filename=video.filename)
    video_document = {
        "_id": video_id,
        "filename": video.filename,
        "content_type": video.content_type
    }
    db.videos.insert_one(video_document)
    close_connection(client)
    return video_id


def query_video(video_id):
    db, client = open_connection()
    fs = gridfs.GridFS(db)
    video_file = fs.get(ObjectId(video_id))
    response = make_response(video_file.read())
    response.headers['Content-Type'] = video_file.content_type
    response.headers['Content-Disposition'] = f'attachment; filename={video_file.filename}'
    close_connection(client)
    return response
