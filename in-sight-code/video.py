from flask import make_response, url_for
from user import check_if_user_exists
from datetime import datetime
import gridfs
from database import open_connection, close_connection
import cv2
import io
from PIL import Image
from gridfs import GridFS
from bson import ObjectId
import os
import tempfile


def store_video(video, session):
    user_id = check_if_user_exists(session['email'])['_id']

    if user_id is None:
        return {"error": "User not found"}, 404

    db, client = open_connection()
    fs = gridfs.GridFS(db)

    video_id = fs.put(video, filename=video.filename)

    date_added = datetime.now()

    video_document = {
        "_id": video_id,
        "filename": video.filename,
        "content_type": video.content_type,
        "user_id": user_id,
        "date_added": date_added,
        "summarized_text": {}
    }

    db.videos.insert_one(video_document)

    generate_thumbnail(video_id)

    close_connection(client)

    return {"video_id": str(video_id)}


def get_thumbnail_from_db(video_id):
    db, client = open_connection()
    fs = GridFS(db)

    try:
        video_id = ObjectId(video_id)
    except Exception as e:
        return {"error": "Invalid video ID"}, 400

    video_doc = db.videos.find_one({"_id": video_id})
    if not video_doc:
        return {"error": "Video not found."}, 404

    thumbnail_id = video_doc.get("thumbnail_id")

    if not thumbnail_id:
        return {"error": "Thumbnail not found for this video."}, 404

    thumbnail_file = fs.get(ObjectId(thumbnail_id))

    thumbnail_data = thumbnail_file.read()
    response = make_response(thumbnail_data)
    response.headers['Content-Type'] = 'image/png'
    response.headers['Content-Disposition'] = f'inline; filename={video_id}_thumbnail.png'

    close_connection(client)

    return response


def generate_thumbnail(video_id):
    db, client = open_connection()
    fs = GridFS(db)
    video_file = fs.get(ObjectId(video_id))

    video_bytes = video_file.read()

    with tempfile.NamedTemporaryFile(delete=False) as temp_video_file:
        temp_video_file.write(video_bytes)
        temp_video_path = temp_video_file.name

    video = cv2.VideoCapture(temp_video_path)

    if not video.isOpened():
        return {"error": "Failed to open video."}, 500

    ret, frame = video.read()
    if not ret:
        return {"error": "Failed to read the video frame."}, 500

    thumbnail = cv2.resize(frame, (410, 200))

    thumbnail_rgb = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)

    pil_image = Image.fromarray(thumbnail_rgb)

    thumbnail_io = io.BytesIO()
    pil_image.save(thumbnail_io, format="PNG")
    thumbnail_io.seek(0)

    thumbnail_id = fs.put(thumbnail_io, filename=f"{video_id}_thumbnail.png")

    db.videos.update_one(
        {"_id": ObjectId(video_id)},
        {"$set": {"thumbnail_id": thumbnail_id}}
    )

    video.release()
    os.remove(temp_video_path)

    close_connection(client)

    return {"message": "Thumbnail generated successfully", "thumbnail_id": str(thumbnail_id)}


def query_video(video_id):
    db, client = open_connection()
    fs = gridfs.GridFS(db)

    video_file = fs.get(ObjectId(video_id))

    response = make_response(video_file.read())
    response.headers['Content-Type'] = video_file.content_type
    response.headers['Content-Disposition'] = f'attachment; filename={video_file.filename}'

    close_connection(client)

    return video_file


def query_all_videos(user_id):
    db, client = open_connection()
    try:
        videos_collection = db['videos']
        videos = videos_collection.find({"user_id": ObjectId(user_id)})
        video_list = []
        for video in videos:
            video_info = {
                "id": str(video["_id"]),
                "filename": video["filename"],
                "content_type": video["content_type"],
                "title": video.get("title", "Untitled"),
                "date": video.get("date", "Unknown date")
            }
            video_list.append(video_info)
        return video_list
    except Exception as e:
        print(f"An error occurred while querying videos: {e}")
        return []
    finally:
        close_connection(client)


def get_updated_video_list_from_db(user_id):
    return query_all_videos(user_id)