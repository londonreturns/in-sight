import cv2
import os
import tempfile
import subprocess
from ultralytics import YOLO
from io import BytesIO


def compare_histograms(f1, f2):
    f1 = cv2.cvtColor(f1, cv2.COLOR_BGR2HSV)
    f2 = cv2.cvtColor(f2, cv2.COLOR_BGR2HSV)
    h1 = cv2.calcHist([f1], [0, 1], None, [50, 60], [0, 180, 0, 256])
    h2 = cv2.calcHist([f2], [0, 1], None, [50, 60], [0, 180, 0, 256])
    cv2.normalize(h1, h1)
    cv2.normalize(h2, h2)
    return cv2.compareHist(h1, h2, cv2.HISTCMP_CHISQR)


def detect_scene_changes(video_path, threshold=0.6):
    cap = cv2.VideoCapture(video_path)
    success, prev_frame = cap.read()
    if not success:
        raise ValueError("Error reading video")

    frames = []
    frame_id = 0

    while True:
        success, frame = cap.read()
        if not success:
            break

        diff = compare_histograms(prev_frame, frame)
        if diff > threshold:
            frames.append((frame_id, frame))
            prev_frame = frame
        frame_id += 1

    cap.release()
    return frames


def filter_frames_by_objects(frames, object_names={"person"}):
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, 'models', 'yolov8n.pt')

    model = YOLO(model_path)
    selected_frames = []

    for frame_id, frame in frames:
        results = model.predict(frame, verbose=False)
        if not results or not results[0].boxes:
            continue

        labels = results[0].names
        detected = set([labels[int(cls)] for cls in results[0].boxes.cls])

        if object_names & detected:
            selected_frames.append((frame_id, frame))

    return selected_frames


def save_frames_as_video(frames, output_path, fps=30):
    if not frames:
        print("No frames to save.")
        return

    height, width, _ = frames[0][1].shape
    out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    for _, frame in frames:
        out.write(frame)

    out.release()
    print(f"Raw summary video saved to {output_path}")


def convert_to_browser_compatible(input_path, output_path):
    FFMPEG_PATH = r"C:\ffmpeg-2025-05-07-git-1b643e3f65-essentials_build\bin\ffmpeg.exe"  # Adjust the path if it's different

    subprocess.run([
        FFMPEG_PATH,
        "-y",
        "-i", input_path,
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path
    ], check=True)

    print(f"Browser-compatible video saved to {output_path}")


def summarize_video_in_memory(video_bytes, threshold=1.4, object_names=None):
    import tempfile

    if object_names is None:
        object_names = {"person", "dog", "cat"}

    fd_in, tmp_in_path = tempfile.mkstemp(suffix='.mp4')
    fd_raw, tmp_raw_summary = tempfile.mkstemp(suffix='.mp4')
    fd_out, tmp_browser_compatible = tempfile.mkstemp(suffix='.mp4')

    try:
        with os.fdopen(fd_in, 'wb') as f_in:
            f_in.write(video_bytes)

        # Step 1: Detect scene changes
        scene_frames = detect_scene_changes(tmp_in_path, threshold)

        # Step 2: Fallback if no scene changes
        if not scene_frames:
            cap = cv2.VideoCapture(tmp_in_path)
            success, frame = cap.read()
            cap.release()
            if success:
                scene_frames = [(0, frame)]

        # Step 3: Filter frames by objects
        important_frames = filter_frames_by_objects(scene_frames, object_names)

        # Step 4: Fallback if no important frames
        if not important_frames:
            important_frames = [scene_frames[0]]

        # Step 5: Save and convert video
        save_frames_as_video(important_frames, tmp_raw_summary)
        convert_to_browser_compatible(tmp_raw_summary, tmp_browser_compatible)

        # Step 6: Load final video
        with open(tmp_browser_compatible, "rb") as f_out:
            return BytesIO(f_out.read())

    finally:
        for path in [tmp_in_path, tmp_raw_summary, tmp_browser_compatible]:
            try:
                os.remove(path)
            except OSError:
                pass
