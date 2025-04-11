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

        const data = await response.json();

        if (response.ok) {
            showToast("Video uploaded successfully.", 'success');
            document.querySelector(".column-left").innerHTML = `
                <video width="300" controls muted>
                    <source src="/video/${data.video_id}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            `;
        } else {
            showToast("Error uploading video.", "error");
        }

    } catch (error) {
        showToast("An error occurred.", "error");
    }
}

document.querySelector("#uploadButton").addEventListener("click", function () {
    let fileInput = document.querySelector("#videoFile");
    let file = fileInput.files[0];

    if (!file) {
        showToast("No file selected.", "error");
    } else if (!file.type.startsWith("video/")) {
        showToast("Please upload a valid video file.", "error");
    } else {
        showToast("Preparing to upload: ${file.name}", "processing");
        sendVideo(file);
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
            fetch("/logout", { method: "POST" })
                .then(response => {
                    if (response.ok) {
                        window.location.href = "/loginPage"; // Redirect to login page
                    } else {
                        console.error("Logout failed");
                    }
                })
                .catch(error => console.error("An error occurred:", error));
        }
    );
});