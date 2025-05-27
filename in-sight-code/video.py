from flask import make_response, jsonify, request, session, render_template
from user import check_if_user_exists
from datetime import datetime
from gridfs import GridFS
from database import open_connection, close_connection
from bson import ObjectId
from helper import generate_thumbnail, is_logged_in
from io import BytesIO
from image_captioning import summarize_video_path
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

    filename_parts = video.filename.rsplit('.', 1)
    file_type = filename_parts[1].lower() if len(filename_parts) > 1 else ""

    video_document = {
        "_id": video_id,
        "filename": video.filename,
        "content_type": video.content_type,
        "file_type": file_type,
        "user_id": user_id,
        "date_added": date_added,
        "file_size": file_size,
        "summarized_text": {},
        "is_summarized": False
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


def delete_gridfs_file_and_chunks(db, file_id):
    """Delete a file and its chunks from GridFS."""
    db.fs.files.delete_one({"_id": ObjectId(file_id)})
    db.fs.chunks.delete_many({"files_id": ObjectId(file_id)})


def delete_video_from_db(session, video_id):
    db, client = open_connection()
    fs = GridFS(db)
    try:
        video = db.videos.find_one({"_id": ObjectId(video_id), "user_id": ObjectId(session["_id"])})
        if not video:
            return {"error": "Video not found or unauthorized"}, 404

        # Delete audio transcript
        db.audio_transcripts.delete_many({"video_id": ObjectId(video_id)})

        # Delete summarized video and its chunks if present
        if "summarized_video_id" in video:
            try:
                delete_gridfs_file_and_chunks(db, video["summarized_video_id"])
            except Exception as e:
                print(f"Error deleting summarized video: {e}")

            # Delete summarized text for this summarized video
            try:
                db.summarized_texts.delete_many({"summarized_video_id": video["summarized_video_id"]})
            except Exception as e:
                print(f"Error deleting summarized text: {e}")

        # Delete thumbnail and its chunks if present
        if "thumbnail_id" in video:
            try:
                delete_gridfs_file_and_chunks(db, video["thumbnail_id"])
            except Exception as e:
                print(f"Error deleting thumbnail: {e}")

        if "summarized_text" in video:
            # Delete summarized text for this video
            try:
                db.summarized_texts.delete_many({"video_id": video["_id"]})
            except Exception as e:
                print(f"Error deleting summarized text: {e}")

        # Delete the video file and its chunks
        try:
            delete_gridfs_file_and_chunks(db, video_id)
        except Exception as e:
            print(f"Error deleting video file: {e}")

        # Delete the video document from the database
        db.videos.delete_one({"_id": ObjectId(video_id)})

        close_connection(client)
        return {"message": "Video and all associated data deleted successfully"}, 200
    except Exception as e:
        close_connection(client)
        return {"error": "An error occurred while deleting the video"}, 500


def store_summarized_video(video_id, summary_file, timecodes=None):
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

        # Update the video document with the summarized video ID and timecodes
        update_fields = {"summarized_video_id": summarized_video_id}
        if timecodes is not None:
            update_fields["timecodes"] = timecodes

        db.videos.update_one(
            {"_id": ObjectId(video_id)},
            {"$set": update_fields}
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


def get_summarized_video_text(video_id, keyframe_threshold=80):
    db, client = open_connection()
    fs = GridFS(db)

    try:
        # Try to get the summarized video by id directly
        try:
            summarized_video_file = fs.get(ObjectId(video_id))
            summarized_video_id = ObjectId(video_id)
        except Exception:
            # Fallback: treat video_id as original video, get summarized_video_id
            video_doc = db.videos.find_one({"_id": ObjectId(video_id)})
            if not video_doc or "summarized_video_id" not in video_doc:
                close_connection(client)
                return {"error": "Summarized video not found for given video ID."}
            summarized_video_id = video_doc["summarized_video_id"]
            summarized_video_file = fs.get(ObjectId(summarized_video_id))

        # Check if summary text is already stored in the DB for this summarized video and threshold
        summary_doc = db.summarized_texts.find_one({
            "summarized_video_id": summarized_video_id,
            "keyframe_threshold": keyframe_threshold
        })
        if summary_doc and "summary" in summary_doc:
            close_connection(client)
            return summary_doc["summary"]

        # Save video to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(summarized_video_file.read())
            tmp_path = tmp.name

        close_connection(client)

        # Summarize the summarized video with the given keyframe threshold
        result = summarize_video_path(tmp_path, keyframe_threshold=keyframe_threshold)

        # Store the summary in the DB for future use
        db, client = open_connection()
        db.summarized_texts.update_one(
            {"summarized_video_id": summarized_video_id, "keyframe_threshold": keyframe_threshold},
            {"$set": {"summary": result}},
            upsert=True
        )
        close_connection(client)

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


def get_summarized_text_from_db(video_id):
    db, client = open_connection()

    try:
        # Get the video document
        video_doc = db.videos.find_one({"_id": ObjectId(video_id)})

        # Check if the video document exists and has a summarized_video_id field
        if not video_doc or "summarized_video_id" not in video_doc:
            close_connection(client)
            return None

        # Get the summarized text from the database
        summary_doc = db.summarized_texts.find_one({"summarized_video_id": video_doc["summarized_video_id"]})

        close_connection(client)
        return summary_doc["summary"] if summary_doc else None
    except Exception as e:
        print(f"Error getting summarized text: {e}")
        close_connection(client)
        return None


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


def get_timecodes_from_db(video_id):
    db, client = open_connection()
    try:
        video_doc = db.videos.find_one({"_id": ObjectId(video_id)})
        if not video_doc or "timecodes" not in video_doc:
            close_connection(client)
            return []
        timecodes = video_doc["timecodes"]
        close_connection(client)
        return timecodes
    except Exception as e:
        close_connection(client)
        return []


def store_audio_transcript(video_id, transcript_text):
    """Store audio transcript in the database."""
    db, client = open_connection()
    try:
        transcript_doc = {
            "video_id": ObjectId(video_id),
            "text": transcript_text,
            "timestamp": datetime.now()
        }
        db.audio_transcripts.insert_one(transcript_doc)
        return True
    except Exception as e:
        print(f"Error storing audio transcript: {e}")
        return False
    finally:
        close_connection(client)


def get_summarized_text_from_db_route(video_id):
    db, client = open_connection()
    try:
        transcript = db.audio_transcripts.find_one({"video_id": ObjectId(video_id)})
        if not transcript:
            return jsonify({"error": "Audio transcript not found"}), 404

        return jsonify({
            "success": True,
            "transcript": transcript.get("text", ""),
            "timestamp": transcript.get("timestamp", "")
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve audio transcript: {str(e)}"}), 500
    finally:
        close_connection(client)


def render_video_details():
    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({"error": "Video ID is required"}), 400

    db, client = open_connection()
    try:
        video = db.videos.find_one({"_id": ObjectId(video_id), "user_id": ObjectId(session["_id"])})
        if not video:
            return jsonify({"error": "Video not found or unauthorized"}), 404

        # Format the date
        if isinstance(video.get("date_added"), datetime):
            video["date_added"] = video["date_added"].strftime("%Y-%m-%d")
        else:
            video["date_added"] = "Unknown date"

        # Format file size
        file_size_bytes = video.get("file_size", 0)
        file_size_mb = (file_size_bytes / (1024 * 1024)) if file_size_bytes else 0
        video["file_size"] = f"{file_size_mb:.2f} MB"

        return render_template('video_details.html',
                               video=video,
                               isLoggedIn=is_logged_in(session),
                               currentPage="videoDetails")
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    finally:
        close_connection(client)