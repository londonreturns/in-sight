function showToast(text, type = "success") {
    let toastMessage = document.querySelector("#toastMessage");
    let toastElement = new bootstrap.Toast(document.getElementById("liveToast"));

    toastMessage.innerText = text;

    let toastContainer = document.getElementById("liveToast");
    toastContainer.classList.remove("bg-success", "bg-danger", "bg-primary", "text-light-success", "text-light-error", "text-light-processing");

    if (type === "success") {
        toastContainer.classList.add("bg-success", "text-light-success");
    } else if (type === "error") {
        toastContainer.classList.add("bg-danger", "text-light-error");
    } else if (type === "processing") {
        toastContainer.classList.add("bg-primary", "text-light-processing");
    }

    toastElement.show();
}

export default showToast;