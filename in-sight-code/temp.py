import cv2
from ultralytics import YOLO


def detect_scene_changes(video_path, threshold=0.6):
    cap = cv2.VideoCapture(video_path)
    success, prev_frame = cap.read()
    if not success:
        raise ValueError("Error reading video")

    frames = []
    original_frame_id = 0

    while True:
        success, frame = cap.read()
        if not success:
            break

        diff = compare_histograms(prev_frame, frame)
        if diff > threshold:
            frames.append((original_frame_id, frame))
            prev_frame = frame
        original_frame_id += 1

    cap.release()
    return frames


def compare_histograms(f1, f2):
    f1 = cv2.cvtColor(f1, cv2.COLOR_BGR2HSV)
    f2 = cv2.cvtColor(f2, cv2.COLOR_BGR2HSV)
    h1 = cv2.calcHist([f1], [0, 1], None, [50, 60], [0, 180, 0, 256])
    h2 = cv2.calcHist([f2], [0, 1], None, [50, 60], [0, 180, 0, 256])
    cv2.normalize(h1, h1)
    cv2.normalize(h2, h2)
    return cv2.compareHist(h1, h2, cv2.HISTCMP_CHISQR)


def filter_frames_by_objects(frames, object_names={"person"}):
    model = YOLO("yolov8n.pt")
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
    print(f"Summary video saved to {output_path}")


def format_timestamp(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hrs:02}:{mins:02}:{secs:02}"


def summarize_video(video_path, output_path="summary_video.mp4", threshold=1.4, object_names=None):
    if object_names is None:
        object_names = {"person", "dog", "cat"}
    print("Detecting scene changes...")
    scene_frames = detect_scene_changes(video_path, threshold)

    print(f"Scene changes found: {len(scene_frames)}")
    print("Running object detection...")
    important_frames = filter_frames_by_objects(scene_frames, object_names)

    print(f"Important frames with target objects: {len(important_frames)}")
    print("Saving summarized video as...")
    save_frames_as_video(important_frames, output_path)


if __name__ == "__main__":
    input_video = "1.mp4"
    summarize_video(input_video)