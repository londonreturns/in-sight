async function sendVideo(file) {
    const formData = new FormData();
    formData.append('video', file);

    try {
        const response = await fetch("/uploadVideo", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        let toastMessage = document.querySelector("#toastMessage");
        let toastElement = new bootstrap.Toast(document.getElementById("liveToast"));

        if (response.ok) {
            toastMessage.innerText = 'Video uploaded successfully';
            document.querySelector(".column-left").innerHTML = `
                <video width="300" controls muted>
                    <source src="/video/${data.video_id}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            `;
        } else {
            toastMessage.innerText = data.error || 'Error uploading video';
        }
        toastElement.show();

        console.log(data); // Log the response data for debugging
    } catch (error) {
        console.error('Error:', error);
        let toastMessage = document.querySelector("#toastMessage");
        let toastElement = new bootstrap.Toast(document.getElementById("liveToast"));
        toastMessage.innerText = 'An error occurred.';
        toastElement.show();
    }
}

document.querySelector("#uploadButton").addEventListener("click", function () {
    let fileInput = document.querySelector("#videoFile");
    let file = fileInput.files[0];
    let toastMessage = document.querySelector("#toastMessage");
    let toastElement = new bootstrap.Toast(document.getElementById("liveToast"));

    if (!file) {
        toastMessage.innerText = "No file selected.";
        toastElement.show();
    } else if (!file.type.startsWith("video/")) {
        toastMessage.innerText = "Please upload a valid video file.";
        toastElement.show();
    } else {
        toastMessage.innerText = `Preparing to upload: ${file.name}`;
        toastElement.show();
        sendVideo(file);
    }
});
