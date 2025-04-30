import showToast from "./toast.js";
import showModal from "./modal.js";

async function sendVideo(file) {
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
            await updateVideoList();
            document.getElementById('videoFile').value = '';

        } else {
            showToast(result.error || "Error uploading video.", "error");
        }

    } catch (error) {
        showToast("An error occurred.", "error");
    }
}

document.querySelector("#uploadButton").addEventListener("click", async function () {
    let fileInput = document.querySelector("#videoFile");
    let file = fileInput.files[0];

    if (!file) {
        showToast("No file selected.", "error");
    } else if (!file.type.startsWith("video/")) {
        showToast("Please upload a valid video file.", "error");
    } else {
        showToast(`Preparing to upload: ${file.name}`, "processing", 999999);
        await sendVideo(file);
    }
});

document.querySelector("#logoutButton").addEventListener("click", function (event) {
    event.preventDefault();

    showModal(
        "Confirm Logout",
        "Are you sure you want to log out?",
        "Logout",
        () => {
            fetch("/logout", {method: "POST"})
                .then(response => {
                    if (response.ok) {
                        window.location.href = "/loginPage";
                    } else {
                        console.error("Logout failed");
                    }
                })
                .catch(error => console.error("An error occurred:", error));
        }
    );
});

async function updateVideoList() {
    try {
        const response = await fetch("/getUpdatedVideoList");

        if (response.ok) {
            document.querySelector("#videoList").innerHTML = await response.text();
        } else {
            showToast("Failed to fetch updated videos", "error");
        }
    } catch (err) {
        console.error(err);
        showToast("Error updating video list", "error");
    }
}

document.addEventListener("click", async (event) => {
    if (event.target.closest(".delete-video-btn")) {
        const button = event.target.closest(".delete-video-btn");
        const videoId = button.getAttribute("data-id");

        showModal(
            "Confirm Deletion",
            "Are you sure you want to delete this video?",
            "Delete",
            async () => {

                try {
                    const response = await fetch(`/deleteVideo/${videoId}`, {
                        method: "DELETE",
                    });


                    showToast("Deleting video.", "processing", 999999);

                    if (response.ok) {
                        showToast("Video deleted successfully.", "success");
                        await updateVideoList();
                    } else {
                        const result = await response.json();
                        showToast(result.error || "Error deleting video.", "error");
                    }
                } catch (error) {
                    showToast("An error occurred while deleting the video.", "error");
                }
            }
        );
    }
});

document.getElementById('dynamicModal').addEventListener('hidden.bs.modal', () => {
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach((backdrop) => backdrop.remove());
});

document.addEventListener("click", (event) => {
    const videoCard = event.target.closest(".video-card");
    if (videoCard) {
        const videoId = videoCard.getAttribute("data-id");

        const modalTitle = document.getElementById("dynamicModalLabel");
        const modalBody = document.querySelector("#dynamicModal .modal-body");

        modalTitle.textContent = "Video Details";
        modalBody.innerHTML = `
            <p>Video ID: ${videoId}</p>
            <p>Additional video details can go here.</p>
        `;

        const modal = new bootstrap.Modal(document.getElementById("dynamicModal"));
        modal.show();
    }
});

document.addEventListener("DOMContentLoaded", async function () {
    const videoListContainer = document.getElementById('videoList');
    const loadingSpinner = document.getElementById('loadingSpinner');

    loadingSpinner.style.display = 'block';

    try {
        const response = await fetch('/getVideosOfUser', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            showToast(response.error || "Error deleting video.", "error");
        }

        const data = await response.json();

        loadingSpinner.style.display = 'none';
        videoListContainer.innerHTML = '';

        data.forEach(video => {
            const videoCard = `
            <div class="col-12 col-md-6 col-lg-4">
                <div class="card mb-3 d-flex flex-row align-items-center justify-content-between video-card" data-id="${video.id}">
                    <div class="w-100">
                        <img src="/getThumbnail/${video.id}" alt="Video Thumbnail"
                             loading="lazy" style="width: 100%; height: 210px; border-radius: 10px; object-fit: cover;">
                        <div class="p-3">
                            <h5 class="mb-1">
                                ${video.filename.length > 30 ? video.filename.substring(0, 30) + '...' : video.filename}
                            </h5>
                            <small>Date: ${video.date_added}</small>
                        </div>
                    </div>
                    <div class="card-actions">
                        <button class="btn delete-video-btn" data-id="${video.id}">
                            <img class="delete-svg" src="static/images/ic_baseline-delete.svg" alt="">
                        </button>
                    </div>
                </div>
            </div>
        `;
            videoListContainer.insertAdjacentHTML('beforeend', videoCard);
        });
    } catch (error) {
        console.error('Error fetching videos:', error);
        loadingSpinner.style.display = 'none';
        videoListContainer.innerHTML = '<div class="alert alert-danger text-center">Failed to load videos.</div>';
    }
});

function getAssistantMessage(input) {
    const parts = input.split("ASSISTANT:");
    return parts.length > 1 ? parts[1].trim() : "";
}