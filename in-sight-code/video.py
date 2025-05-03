from flask import make_response
from user import check_if_user_exists
from datetime import datetime
from gridfs import GridFS
from database import open_connection, close_connection
from bson import ObjectId
from helper import generate_thumbnail


def store_video(video, session):
    user_id = check_if_user_exists(session['email'])['_id']

    if user_id is None:
        return {"error": "User not found"}, 404

    db, client = open_connection()
    fs = GridFS(db)

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


def query_video(video_id):
    db, client = open_connection()
    fs = GridFS(db)

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
                "date_added": video.get("date_added", "Unknown date").strftime("%Y-%m-%d") if isinstance(
                    video.get("date_added"), datetime) else "Unknown date"
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


def delete_video_from_db(session, video_id):
    db, client = open_connection()
    try:
        video = db.videos.find_one({"_id": ObjectId(video_id), "user_id": ObjectId(session["_id"])})
        if not video:
            return {"error": "Video not found or unauthorized"}, 404

        db.videos.delete_one({"_id": ObjectId(video_id)})
        close_connection(client)
        return {"message": "Video deleted successfully"}, 200
    except Exception as e:
        close_connection(client)
        return {"error": "An error occurred while deleting the video"}, 500
