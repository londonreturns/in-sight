import showToast from "../../modules/toast.js";
import { updateVideoList } from "./videoList.js";

import { setupSummarySection } from "./videoSummary.js";


export function setupVideoCardClickListener() {
    document.addEventListener("click", async (event) => {
        const videoCard = event.target.closest(".video-card");
        if (!videoCard) return;

        const videoId = videoCard.getAttribute("data-id");
        const modal = new bootstrap.Modal(document.getElementById("dynamicModal"));
        const modalTitle = document.getElementById("dynamicModalLabel");
        const modalBody = document.querySelector("#dynamicModal .modal-body");
        const modalDialog = document.querySelector("#dynamicModal .modal-dialog");
        const modalFooter = document.querySelector("#dynamicModal .modal-footer");

        modalDialog.classList.add("modal-xl");
        modalFooter.style.display = "none";
        modalTitle.textContent = "Video Details";

        modalBody.innerHTML = `
            <div class="text-center my-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading video details...</p>
            </div>
        `;

        modal.show();

        try {
            const response = await fetch(`/getVideosOfUser`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) throw new Error("Failed to fetch video details");

            const videos = await response.json();
            const video = videos.find(v => v.id === videoId);
            if (!video) throw new Error("Video not found");

            const filenameWithoutExt = video.filename.split('.').slice(0, -1).join('.');
            const formattedType = video.content_type === "video/mp4" ? "MP4" : video.content_type;
            const dateAdded = video.date_added;

            modalBody.innerHTML = `
                <div class="row mb-3">
                    <div class="col-md-8">
                        <h2 class="fw-bold" id="videoTitle">${filenameWithoutExt}</h2>
                    </div>
                    <div class="col-md-4 text-end">
                        <button class="btn btn-primary me-2" id="editVideoBtn">Edit</button>
                        <button class="btn btn-danger" id="deleteVideoBtn">Delete</button>
                    </div>
                </div>
                <div class="row mb-3">
                    <div class="col-md-12">
                        <h5>Original Video</h5>
                        <div class="ratio ratio-16x9 mb-3">
                            <video id="originalVideo" controls>
                                <source src="/getVideo/${videoId}" type="${video.content_type}">
                                Your browser does not support the video tag.
                            </video>
                        </div>
                        <div class="text-muted">
                            <small>${dateAdded} | ${formattedType} | ${video.file_size || "Unknown"}</small>
                        </div>
                    </div>
                </div>
            `;

            setupEditHandler(videoId);
            setupDeleteHandler(videoId, modal);

            setupSummarySection(modalBody, video.id, video.content_type);
        } catch (err) {
            modalBody.innerHTML = `
                <div class="alert alert-danger">
                    Failed to load video details: ${err.message}
                </div>
            `;
        }
    });
}

function setupEditHandler(videoId) {
    const videoTitle = document.querySelector('#videoTitle');
    const editBtn = document.querySelector('#editVideoBtn');

    if (editBtn && videoTitle) {
        editBtn.addEventListener('click', () => {
            const currentTitle = videoTitle.textContent;
            videoTitle.innerHTML = `<input type="text" class="form-control" id="videoTitleInput" value="${currentTitle}">`;

            const input = document.getElementById('videoTitleInput');
            input.focus();

            const updateTitle = async (newTitle) => {
                try {
                    const response = await fetch(`/updateVideoFilename/${videoId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ filename: newTitle })
                    });

                    const result = await response.json();

                    if (response.ok) {
                        showToast("Filename updated successfully", "success");
                        await updateVideoList();
                        videoTitle.textContent = newTitle;
                    } else {
                        showToast(result.error || "Error updating filename", "error");
                        videoTitle.textContent = currentTitle;
                    }
                } catch (error) {
                    console.error("Edit error:", error);
                    showToast("An error occurred while updating the filename", "error");
                    videoTitle.textContent = currentTitle;
                }
            };

            input.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    updateTitle(input.value);
                }
            });

            input.addEventListener("blur", () => {
                updateTitle(input.value);
            });
        });
    }
}

function setupDeleteHandler(videoId, modalInstance) {
    const deleteBtn = document.getElementById("deleteVideoBtn");
    const confirmModal = new bootstrap.Modal(document.getElementById("confirmModal"));
    const confirmActionButton = document.getElementById("confirmActionButton");

    if (deleteBtn) {
        deleteBtn.addEventListener("click", () => {
            confirmModal.show();

            const deleteHandler = async () => {
                try {
                    showToast("Deleting video...", "processing", 999999);

                    const response = await fetch(`/deleteVideo/${videoId}`, { method: "DELETE" });

                    if (response.ok) {
                        confirmModal.hide();
                        modalInstance.hide();
                        showToast("Video deleted successfully.", "success");
                        // Remove only the deleted video card from the DOM
                        const card = document.querySelector(`.video-card[data-id="${videoId}"]`);
                        if (card) {
                            const col = card.closest('.col-12, .col-md-6, .col-lg-4');
                            if (col) col.remove();
                            else card.remove();
                        }
                        // If no more video cards, show "No videos found" message
                        const videoListContainer = document.getElementById('videoList');
                        const remainingCards = videoListContainer.querySelectorAll('.video-card');
                        if (remainingCards.length === 0) {
                            videoListContainer.innerHTML = '<div class="alert alert-info text-center">No videos found. Please upload a video.</div>';
                        }
                    } else {
                        const result = await response.json();
                        showToast(result.error || "Error deleting video.", "error");
                    }
                } catch (error) {
                    showToast("An error occurred while deleting the video.", "error");
                } finally {
                    confirmActionButton.removeEventListener("click", deleteHandler);
                }
            };

            confirmActionButton.addEventListener("click", deleteHandler);
        });
    }
}

