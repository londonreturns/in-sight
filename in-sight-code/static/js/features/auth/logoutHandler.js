import showModal from "../../modules/modal.js";

export function setupLogoutListener() {
    document.querySelector("#logoutButton").addEventListener("click", function (event) {
        event.preventDefault();

        showModal(
            "Confirm Logout",
            "Are you sure you want to log out?",
            "Logout",
            () => {
                fetch("/logout", { method: "POST" })
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
}
