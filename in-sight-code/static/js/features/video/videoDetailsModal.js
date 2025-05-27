import showToast from "../../modules/toast.js";
import { updateVideoList } from "./videoList.js";

import { setupSummarySection } from "./videoSummary.js";


export function setupVideoCardClickListener() {
    document.addEventListener("click", async (event) => {
        const videoCard = event.target.closest(".video-card");
        if (!videoCard) return;

        const videoId = videoCard.getAttribute("data-id");
        window.location.href = `/videodetails?video_id=${videoId}`;
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
                    // Disable button and show spinner
                    confirmActionButton.disabled = true;
                    const originalText = confirmActionButton.innerHTML;
                    confirmActionButton.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Deleting...`;

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
                } 
            };

            confirmActionButton.addEventListener("click", deleteHandler);
        });
    }
}
