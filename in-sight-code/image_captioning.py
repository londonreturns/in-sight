import os
import cv2
import numpy as np
from PIL import Image
import torch
import tempfile
import json
from transformers import InstructBlipProcessor, InstructBlipForConditionalGeneration
from concurrent.futures import ThreadPoolExecutor

device = torch.device("cpu")
print(f"\n🔧 Using device: {device}\n")

torch.set_num_threads(os.cpu_count())
torch.backends.cudnn.benchmark = True

executor = ThreadPoolExecutor(max_workers=os.cpu_count())

import threading

_model_loaded = False
_cached_processor = None
_cached_model = None
_model_lock = threading.Lock()

def load_model():
    global _model_loaded, _cached_processor, _cached_model
    with _model_lock:
        if not _model_loaded:
            print("📦 Loading model... (this may take a while)")
            _cached_processor = InstructBlipProcessor.from_pretrained("Salesforce/instructblip-flan-t5-xl")
            _cached_model = InstructBlipForConditionalGeneration.from_pretrained(
                "Salesforce/instructblip-flan-t5-xl"
            ).to(device)
            _cached_model.eval()
            _model_loaded = True
            print("✅ Model loaded!")
    return _cached_processor, _cached_model


def unload_model(model):
    # No-op: model is kept in memory for reuse
    pass

def get_keyframes(video_path, threshold=80):
    cap = cv2.VideoCapture(video_path)
    keyframes = []
    last_frame = None
    frame_id = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if last_frame is not None:
            diff = cv2.absdiff(gray, last_frame)
            non_zero_count = np.count_nonzero(diff)
            if non_zero_count > threshold * gray.size / 100:
                keyframes.append((frame_id, frame))

        last_frame = gray
        frame_id += 1

    cap.release()
    return keyframes


def caption_image(img: Image.Image, prompt: str):
    processor, model = load_model()  # Load model when needed
    try:
        inputs = processor(images=img, text=prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=100)
        result = processor.tokenizer.decode(out[0], skip_special_tokens=True)

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw": result}
    finally:
        unload_model(model)  # No-op now


def summarize_video_file(video_file) -> dict:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        video_path = tmp.name
        video_file.save(video_path)

    return summarize_video_path(video_path)


def summarize_video_path(video_path: str, keyframe_threshold: int = 80) -> dict:
    frames = get_keyframes(video_path, threshold=keyframe_threshold)

    if not frames:
        return {"error": "No keyframes could be extracted from the video."}

    prompt = """For each image, provide a detailed summary with the following structure in a single JSON object:
    {
        "frame_description": "Describe the content of the image, including any notable actions, settings, or context.",
        "people": ["List all people visible in this image as a JSON array with descriptions of each person."],
        "objects": ["List all objects visible in this image as a JSON array with descriptions of each object."]
    }
    """

    frame_summaries = []

    print(f"🖼 Extracted {len(frames)} keyframes.")

    future_to_frame = {
        frame_id: executor.submit(caption_image, Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), prompt)
        for frame_id, frame in frames
    }

    for frame_id, future in future_to_frame.items():
        frame_summaries.append(future.result())

    mid_index = len(frames) // 2 if len(frames) > 1 else 0
    mid_frame = frames[mid_index][1]
    overall_summary = caption_image(
        Image.fromarray(cv2.cvtColor(mid_frame, cv2.COLOR_BGR2RGB)),
        "Provide a complete JSON summary of the video with keys: 'frame_description', 'people', 'animals', 'background'."
    )

    response = {
        "frame_summaries": frame_summaries,
        "overall_summary": overall_summary
    }

    print(response)

    # Ensure the temporary file is deleted only after the summary is generated
    try:
        os.remove(video_path)
    except OSError as e:
        print(f"Error deleting temporary file: {e}")

    return response
