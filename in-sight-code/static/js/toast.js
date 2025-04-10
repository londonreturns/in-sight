function showToast(text, type = "success") {
    let toastMessage = document.querySelector("#toastMessage");
    let toastElement = new bootstrap.Toast(document.getElementById("liveToast"));

    // Set the text of the toast
    toastMessage.innerText = text;

    // Remove existing color classes
    let toastContainer = document.getElementById("liveToast");
    toastContainer.classList.remove("bg-success", "bg-danger", "bg-primary", "text-light-success", "text-light-error", "text-light-processing");

    // Add the appropriate color class based on the type
    if (type === "success") {
        toastContainer.classList.add("bg-success", "text-light-success");
    } else if (type === "error") {
        toastContainer.classList.add("bg-danger", "text-light-error");
    } else if (type === "processing") {
        toastContainer.classList.add("bg-primary", "text-light-processing");
    }

    // Show the toast
    toastElement.show();
}

export default showToast;