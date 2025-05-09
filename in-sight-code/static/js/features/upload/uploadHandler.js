import showToast from "../../modules/toast.js";
import { updateVideoList, appendVideoCard } from "../video/videoList.js";

export async function sendVideo(file) {
    const formData = new FormData();
    formData.append('video', file);

    try {
        const response = await fetch("/uploadVideo", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            showToast("Video uploaded successfully.", 'success');
            const videoListContainer = document.getElementById('videoList');
            if (videoListContainer) {
                // Remove "No videos found" message if present
                const noVideosCol = videoListContainer.querySelector('.col-12 .alert-info')?.parentElement;
                if (noVideosCol && noVideosCol.classList.contains('col-12')) {
                    noVideosCol.remove();
                } else {
                    const noVideosMsg = videoListContainer.querySelector('.alert-info');
                    if (noVideosMsg) noVideosMsg.remove();
                }
                // If the container is now empty (e.g. only spinner or alert was present), clear it
                if (videoListContainer.children.length === 0) {
                    videoListContainer.innerHTML = '';
                }
            }
            updateVideoList();
            document.getElementById('videoFile').value = '';
        } else {
            showToast(result.error || "Error uploading video.", "error");
        }
    } catch (error) {
        showToast("An error occurred.", "error");
    }
}

export function setupUploadListener() {
    document.querySelector("#uploadButton").addEventListener("click", async function () {
        const uploadButton = this;

        let fileInput = document.querySelector("#videoFile");
        let file = fileInput.files[0];

        if (!file) {
            showToast("No file selected.", "error");
        } else if (!file.type.startsWith("video/")) {
            showToast("Please upload a valid video file.", "error");
        } else {
            uploadButton.disabled = true;
            uploadButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Uploading...';

            showToast(`Preparing to upload: ${file.name}`, "processing", 999999);

            try {
                await sendVideo(file);
            } catch (error) {
                console.error("Upload error:", error);
            } finally {
                uploadButton.disabled = false;
                uploadButton.textContent = "Upload Video";
            }
        }
    });
}
