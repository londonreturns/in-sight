function showModal(title, body, actionButtonText, actionCallback) {
    document.getElementById('dynamicModalLabel').textContent = title;
    document.querySelector('#dynamicModal .modal-body').innerHTML = body;

    const actionButton = document.getElementById('modalActionButton');
    actionButton.textContent = actionButtonText;

    // Set button color to red for logout
    if (actionButtonText === "Logout") {
        actionButton.className = "btn btn-danger";
    } else {
        actionButton.className = "btn btn-primary";
    }

    const newActionButton = actionButton.cloneNode(true);
    actionButton.parentNode.replaceChild(newActionButton, actionButton);

    newActionButton.addEventListener('click', () => {
        if (actionCallback) {
            actionCallback();
        }
        const modalElement = document.getElementById('dynamicModal');
        const modalInstance = bootstrap.Modal.getInstance(modalElement);
        modalInstance.hide();
    });

    const modalElement = new bootstrap.Modal(document.getElementById('dynamicModal'));
    modalElement.show();
}

export default showModal;
