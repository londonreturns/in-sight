function showModal(title, body, actionButtonText, actionCallback) {
    document.getElementById('dynamicModalLabel').textContent = title;
    document.querySelector('#dynamicModal .modal-body').innerHTML = body;

    const actionButton = document.getElementById('modalActionButton');
    actionButton.textContent = actionButtonText;

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