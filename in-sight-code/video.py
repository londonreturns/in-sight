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
    # Check if user exists
    user_id = check_if_user_exists(session['email'])['_id']

    if user_id is None:
        return {"error": "User not found"}, 404

    # Open MongoDB connection
    db, client = open_connection()
    fs = gridfs.GridFS(db)

    # Store the video into GridFS
    video_id = fs.put(video, filename=video.filename)

    # Date the video was added
    date_added = datetime.now()

    # Insert the video metadata into the 'videos' collection
    video_document = {
        "_id": video_id,
        "filename": video.filename,
        "content_type": video.content_type,
        "user_id": user_id,
        "date_added": date_added,
        "summarized_text": {}  # This can be populated later if needed
    }

    db.videos.insert_one(video_document)

    generate_thumbnail(video_id)

    # Close the connection to the database
    close_connection(client)

    return {"video_id": str(video_id)}


def get_thumbnail_from_db(video_id):
    db, client = open_connection()
    fs = GridFS(db)

    try:
        # Ensure the video_id is a valid ObjectId
        video_id = ObjectId(video_id)
    except Exception as e:
        return {"error": "Invalid video ID"}, 400

    # Fetch the video document to get the thumbnail_id
    video_doc = db.videos.find_one({"_id": video_id})
    if not video_doc:
        return {"error": "Video not found."}, 404

    thumbnail_id = video_doc.get("thumbnail_id")

    if not thumbnail_id:
        return {"error": "Thumbnail not found for this video."}, 404

    # Retrieve the thumbnail from GridFS using the thumbnail_id
    thumbnail_file = fs.get(ObjectId(thumbnail_id))

    # Optionally, send the thumbnail image as a response
    thumbnail_data = thumbnail_file.read()
    response = make_response(thumbnail_data)
    response.headers['Content-Type'] = 'image/png'
    response.headers['Content-Disposition'] = f'inline; filename={video_id}_thumbnail.png'

    # Close the connection
    close_connection(client)

    return response


def generate_thumbnail(video_id):
    # Get the video file from GridFS
    db, client = open_connection()
    fs = GridFS(db)
    video_file = fs.get(ObjectId(video_id))

    # Read the video from GridFS as bytes
    video_bytes = video_file.read()

    # Create a temporary file to store the video content
    with tempfile.NamedTemporaryFile(delete=False) as temp_video_file:
        temp_video_file.write(video_bytes)
        temp_video_path = temp_video_file.name  # Store the path of the temporary video file

    # Open the video file using OpenCV
    video = cv2.VideoCapture(temp_video_path)

    # Check if the video opened successfully
    if not video.isOpened():
        return {"error": "Failed to open video."}, 500

    # Read the first frame from the video
    ret, frame = video.read()
    if not ret:
        return {"error": "Failed to read the video frame."}, 500

    # Resize the frame to create a thumbnail (you can adjust the size as needed)
    thumbnail = cv2.resize(frame, (200, 200))  # Resize to 200x200 for the thumbnail

    # Convert the BGR frame (OpenCV format) to RGB (PIL format)
    thumbnail_rgb = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)

    # Convert the frame to an image object for further manipulation or saving
    pil_image = Image.fromarray(thumbnail_rgb)

    # Save the thumbnail image as bytes (in-memory)
    thumbnail_io = io.BytesIO()
    pil_image.save(thumbnail_io, format="PNG")
    thumbnail_io.seek(0)

    # Store the thumbnail in GridFS or save it in the database as metadata
    thumbnail_id = fs.put(thumbnail_io, filename=f"{video_id}_thumbnail.png")

    # Update the video document with the thumbnail ID (or store URL if you prefer)
    db.videos.update_one(
        {"_id": ObjectId(video_id)},
        {"$set": {"thumbnail_id": thumbnail_id}}
    )

    # Close the video capture and delete the temporary video file
    video.release()
    os.remove(temp_video_path)  # Clean up the temporary video file

    # Close the database connection
    close_connection(client)

    return {"message": "Thumbnail generated successfully", "thumbnail_id": str(thumbnail_id)}


# Query the video from MongoDB
def query_video(video_id):
    # Open MongoDB connection
    db, client = open_connection()
    fs = gridfs.GridFS(db)

    # Retrieve the video from GridFS by its ObjectId
    video_file = fs.get(ObjectId(video_id))

    # Prepare the video file content for the response
    response = make_response(video_file.read())
    response.headers['Content-Type'] = video_file.content_type
    response.headers['Content-Disposition'] = f'attachment; filename={video_file.filename}'

    # Close the connection
    close_connection(client)

    return video_file  # Return the video file object for thumbnail generation


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
                "title": video.get("title", "Untitled"),  # Assuming there's a title field
                "date": video.get("date", "Unknown date")  # Assuming there's a date field
            }
            video_list.append(video_info)
        return video_list
    except Exception as e:
        print(f"An error occurred while querying videos: {e}")
        return []
    finally:
        close_connection(client)
