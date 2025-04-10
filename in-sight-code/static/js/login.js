import showToast from "./toast.js";

document.addEventListener("DOMContentLoaded", function () {
    // Handle registration success toast
    let toastElement = document.getElementById("registrationToast");
    if (toastElement) {
        showToast(toastElement);
    }

    // Handle login form submission
    document.querySelector("button[type='submit']").addEventListener("click", async function (event) {
        event.preventDefault();

        let email = document.querySelector("#exampleInputEmail1").value;
        let password = document.querySelector("#exampleInputPassword1").value;

        if (!email || !password) {
            showToast("Email and password are required.");
            return;
        }

        let data = {
            email: email,
            password: password
        };

        try {
            const response = await fetch("/loginUser", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            });

            const responseData = await response.json();

            if (response.ok) {
                window.location.replace("/index");
            } else {
                showToast(responseData.error || "Invalid login credentials.");
            }
        } catch (error) {
            showToast("An error occurred while logging in.");
        }
    });
});

