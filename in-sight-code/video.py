from flask import make_response
from user import check_if_user_exists
from datetime import datetime
from gridfs import GridFS
from database import open_connection, close_connection
from bson import ObjectId
from helper import generate_thumbnail
from io import BytesIO
from image_summary import summarize_video_path
import tempfile


def store_video(video, session):
    user_id = check_if_user_exists(session['email'])['_id']

    if user_id is None:
        return {"error": "User not found"}, 404

    db, client = open_connection()
    fs = GridFS(db)

    video.seek(0, 2)
    file_size = video.tell()
    video.seek(0)

    video_id = fs.put(video, filename=video.filename)

    date_added = datetime.now()

    video_document = {
        "_id": video_id,
        "filename": video.filename,
        "content_type": video.content_type,
        "user_id": user_id,
        "date_added": date_added,
        "file_size": file_size,
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


def query_video(video_id, return_file=False):
    db, client = open_connection()
    fs = GridFS(db)

    try:
        video_file = fs.get(ObjectId(video_id))

        if return_file:
            # Read the file content into memory before closing the connection
            file_content = video_file.read()
            content_type = video_file.content_type
            filename = video_file.filename
            close_connection(client)

            # Create a file-like object from the content
            file_obj = BytesIO(file_content)
            file_obj.filename = filename
            file_obj.content_type = content_type
            return file_obj

        response = make_response(video_file.read())
        response.headers['Content-Type'] = video_file.content_type
        response.headers['Content-Disposition'] = f'attachment; filename={video_file.filename}'

        close_connection(client)
        return response
    except Exception as e:
        close_connection(client)
        return None


def query_all_videos(user_id):
    db, client = open_connection()
    try:
        videos_collection = db['videos']
        videos = videos_collection.find({"user_id": ObjectId(user_id)})
        video_list = []
        for video in videos:
            file_size_bytes = video.get("file_size", 0)
            file_size_mb = (file_size_bytes / (1024 * 1024)) if file_size_bytes else 0
            file_size_formatted = f"{file_size_mb:.2f} MB"

            video_info = {
                "id": str(video["_id"]),
                "filename": video["filename"],
                "content_type": video["content_type"],
                "title": video.get("title", "Untitled"),
                "file_size": file_size_formatted,
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
    fs = GridFS(db)
    try:
        video = db.videos.find_one({"_id": ObjectId(video_id), "user_id": ObjectId(session["_id"])})
        if not video:
            return {"error": "Video not found or unauthorized"}, 404

        # Check if the video has a summarized video
        if "summarized_video_id" in video:
            # Delete the summarized video from GridFS
            try:
                fs.delete(ObjectId(video["summarized_video_id"]))
            except Exception as e:
                print(f"Error deleting summarized video: {e}")
                # Continue with deleting the video even if deleting the summary fails

        # Delete the video document from the database
        db.videos.delete_one({"_id": ObjectId(video_id)})

        close_connection(client)
        return {"message": "Video deleted successfully"}, 200
    except Exception as e:
        close_connection(client)
        return {"error": "An error occurred while deleting the video"}, 500


def store_summarized_video(video_id, summary_file):
    db, client = open_connection()
    fs = GridFS(db)

    try:
        # Get the original video document
        video_doc = db.videos.find_one({"_id": ObjectId(video_id)})
        if not video_doc:
            close_connection(client)
            return None

        # Store the summarized video in GridFS
        summarized_video_id = fs.put(
            summary_file, 
            filename=f"summary_{video_doc['filename']}",
            content_type=video_doc['content_type']
        )

        # Update the video document with the summarized video ID
        db.videos.update_one(
            {"_id": ObjectId(video_id)},
            {"$set": {"summarized_video_id": summarized_video_id}}
        )

        close_connection(client)
        return summarized_video_id
    except Exception as e:
        print(f"Error storing summarized video: {e}")
        close_connection(client)
        return None


def get_summarized_video(video_id):
    db, client = open_connection()
    fs = GridFS(db)

    try:
        # Get the video document
        video_doc = db.videos.find_one({"_id": ObjectId(video_id)})
        if not video_doc or "summarized_video_id" not in video_doc:
            close_connection(client)
            return None

        # Get the summarized video from GridFS
        summarized_video_file = fs.get(ObjectId(video_doc["summarized_video_id"]))

        response = make_response(summarized_video_file.read())
        response.headers['Content-Type'] = summarized_video_file.content_type
        response.headers['Content-Disposition'] = f'attachment; filename={summarized_video_file.filename}'

        close_connection(client)
        return response
    except Exception as e:
        print(f"Error getting summarized video: {e}")
        close_connection(client)
        return None

def get_summarized_video_text(video_id):
    db, client = open_connection()
    fs = GridFS(db)

    try:
        # Get the video document
        video_doc = db.videos.find_one({"_id": ObjectId(video_id)})
        if not video_doc or "summarized_video_id" not in video_doc:
            close_connection(client)
            return {"error": "Summarized video not found for given video ID."}

        # Get summarized video from GridFS
        summarized_video_file = fs.get(ObjectId(video_doc["summarized_video_id"]))

        # Save video to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(summarized_video_file.read())
            tmp_path = tmp.name

        close_connection(client)

        # Summarize the summarized video
        result = summarize_video_path(tmp_path)
        return result

    except Exception as e:
        print(f"Error processing summarized video text: {e}")
        close_connection(client)
        return {"error": str(e)}


def check_summary_exists(video_id):
    db, client = open_connection()

    try:
        # Get the video document
        video_doc = db.videos.find_one({"_id": ObjectId(video_id)})

        # Check if the video document exists and has a summarized_video_id field
        has_summary = video_doc is not None and "summarized_video_id" in video_doc

        close_connection(client)
        return has_summary
    except Exception as e:
        print(f"Error checking if summary exists: {e}")
        close_connection(client)
        return False


def update_video_filename(video_id, new_filename):
    db, client = open_connection()
    fs = GridFS(db)

    try:
        # Get the video document
        video_doc = db.videos.find_one({"_id": ObjectId(video_id)})
        if not video_doc:
            close_connection(client)
            return {"error": "Video not found"}, 404

        # Get the video file from GridFS
        video_file = fs.get(ObjectId(video_id))

        # Update the filename in the video document
        db.videos.update_one(
            {"_id": ObjectId(video_id)},
            {"$set": {"filename": new_filename}}
        )

        # If there's a summarized video, update its filename too
        if "summarized_video_id" in video_doc:
            summarized_video_id = video_doc["summarized_video_id"]
            # Update the summarized video filename
            db.fs.files.update_one(
                {"_id": ObjectId(summarized_video_id)},
                {"$set": {"filename": f"summary_{new_filename}"}}
            )

        # Update the original video filename in GridFS
        db.fs.files.update_one(
            {"_id": ObjectId(video_id)},
            {"$set": {"filename": new_filename}}
        )

        close_connection(client)
        return {"message": "Filename updated successfully"}, 200
    except Exception as e:
        print(f"Error updating video filename: {e}")
        close_connection(client)
        return {"error": f"An error occurred while updating the filename: {str(e)}"}, 500
