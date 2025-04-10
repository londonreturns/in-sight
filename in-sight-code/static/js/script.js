import showToast from "./toast.js";

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
            showToast('Video uploaded successfully.');
            document.querySelector(".column-left").innerHTML = `
                <video width="300" controls muted>
                    <source src="/video/${data.video_id}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            `;
        } else {
            showToast('Error uploading video.');
        }

    } catch (error) {
        showToast('An error occurred.');
    }
}

document.querySelector("#uploadButton").addEventListener("click", function () {
    let fileInput = document.querySelector("#videoFile");
    let file = fileInput.files[0];

    if (!file) {
        showToast('No file selected.');
    } else if (!file.type.startsWith("video/")) {
        showToast('Please upload a valid video file.');
    } else {
        showToast(`Preparing to upload: ${file.name}`);
        sendVideo(file);
    }
});
