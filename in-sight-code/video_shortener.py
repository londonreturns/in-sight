import cv2
import os
import subprocess
import tempfile
from io import BytesIO
from concurrent.futures import ProcessPoolExecutor, as_completed


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
    fps = cap.get(cv2.CAP_PROP_FPS)
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
    return frames, fps


def detect_objects_in_frame(model_path, frame_data, object_names):
    from ultralytics import YOLO
    import cv2
    import numpy as np

    frame_id, frame_bytes = frame_data
    frame = cv2.imdecode(np.frombuffer(frame_bytes, np.uint8), cv2.IMREAD_COLOR)
    model = YOLO(model_path)

    results = model.predict(frame, verbose=False)
    if not results or not results[0].boxes:
        return None

    labels = results[0].names
    detected = set([labels[int(cls)] for cls in results[0].boxes.cls])

    if object_names & detected:
        return (frame_id, frame)
    return None


def filter_frames_by_objects(frames, object_names={"person"}):
    import cv2
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, 'models', 'yolov8n.pt')

    # Serialize frames to bytes
    frame_data_list = []
    for frame_id, frame in frames:
        _, frame_bytes = cv2.imencode('.jpg', frame)
        frame_data_list.append((frame_id, frame_bytes.tobytes()))

    selected_frames = []
    with ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(detect_objects_in_frame, model_path, frame_data, object_names)
            for frame_data in frame_data_list
        ]

        for future in as_completed(futures):
            result = future.result()
            if result:
                selected_frames.append(result)

    return sorted(selected_frames, key=lambda x: x[0])


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
    FFMPEG_PATH = r"C:\ffmpeg-2025-05-07-git-1b643e3f65-essentials_build\bin\ffmpeg.exe"  # Adjust this path

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
    if object_names is None:
        object_names = {"person", "dog", "cat"}

    fd_in, tmp_in_path = tempfile.mkstemp(suffix='.mp4')
    fd_raw, tmp_raw_summary = tempfile.mkstemp(suffix='.mp4')
    fd_out, tmp_browser_compatible = tempfile.mkstemp(suffix='.mp4')

    try:
        with os.fdopen(fd_in, 'wb') as f_in:
            f_in.write(video_bytes)

        # Step 1: Detect scene changes and get FPS
        scene_frames, fps = detect_scene_changes(tmp_in_path, threshold)

        # Step 2: Fallback if no scene changes
        if not scene_frames:
            cap = cv2.VideoCapture(tmp_in_path)
            success, frame = cap.read()
            cap.release()
            if success:
                scene_frames = [(0, frame)]
            fps = fps or 30

        # Step 3: Filter frames by objects (in parallel)
        important_frames = filter_frames_by_objects(scene_frames, object_names)

        # Step 4: Fallback if no important frames
        if not important_frames:
            important_frames = [scene_frames[0]]

        # Step 5: Generate timecodes
        timecodes = []
        for frame_id, _ in important_frames:
            seconds = frame_id / fps
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            timecodes.append(f"{h:02}:{m:02}:{s:02}.{ms:03}")

        # Step 6: Save and convert video
        save_frames_as_video(important_frames, tmp_raw_summary)
        convert_to_browser_compatible(tmp_raw_summary, tmp_browser_compatible)

        # Step 7: Return video and timecodes
        with open(tmp_browser_compatible, "rb") as f_out:
            final_video = f_out.read()
            return {
                "video": BytesIO(final_video),
                "timecodes": timecodes
            }

    finally:
        for path in [tmp_in_path, tmp_raw_summary, tmp_browser_compatible]:
            try:
                os.remove(path)
            except OSError:
                pass
