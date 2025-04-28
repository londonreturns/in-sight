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
        showToast(`Preparing to upload: ${file.name}`, "processing");
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
            // Perform logout action
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

function getAssistantMessage(input) {
    const parts = input.split("ASSISTANT:");
    return parts.length > 1 ? parts[1].trim() : "";
}