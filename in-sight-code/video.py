from bson import ObjectId
from flask import make_response
import gridfs
from database import open_connection, close_connection
from user import checkIfUserExists


def store_video(video, email=None):
    user = checkIfUserExists(email)

    if user is None:
        return {"error": "User not found"}, 404

    db, client = open_connection()
    fs = gridfs.GridFS(db)
    video_id = fs.put(video, filename=video.filename)
    video_document = {
        "_id": video_id,
        "filename": video.filename,
        "content_type": video.content_type,
        "user_id": user['_id']
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
