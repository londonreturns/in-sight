import { setupUploadListener } from "./features/upload/uploadHandler.js";
import { setupLogoutListener } from "./features/auth/logoutHandler.js";
import { updateVideoList } from "./features/video/videoList.js";
import { setupVideoCardClickListener } from "./features/video/videoDetailsModal.js";

// Run everything after DOM is ready
document.addEventListener("DOMContentLoaded", async () => {
    // Hide loading spinner
    const loadingSpinner = document.getElementById("loadingSpinner");
    if (loadingSpinner) loadingSpinner.style.display = "none";

    // Set up video upload
    setupUploadListener();

    // Set up logout button
    setupLogoutListener();

    // Load and render user videos
    await updateVideoList();

    // Handle video card click -> show modal
    setupVideoCardClickListener();

;
});
