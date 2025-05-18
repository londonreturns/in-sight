import showToast from "../../modules/toast.js";
import delay from "../../modules/delay.js";

document.addEventListener("DOMContentLoaded", function () {
    let toastElement = document.getElementById("registrationToast");
    if (toastElement) {
        showToast(toastElement, "success");
    }

    document.querySelector("button[type='submit']").addEventListener("click", async function (event) {
        event.preventDefault();

        const submitButton = this;

        let email = document.querySelector("#exampleInputEmail1").value;
        let password = document.querySelector("#exampleInputPassword1").value;

        if (!email || !password) {
            showToast("Email and password are required.", "error");
            return;
        }

        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Logging in...';

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
                showToast("Login successful!", "success");
                await delay(1000);

                showToast("Redirecting to homepage...", "processing", 99999);
                await delay(1000);

                window.location.replace("/index");
            } else {
                showToast(responseData.error || "Invalid login credentials.", "error");
                submitButton.disabled = false;
                submitButton.textContent = "Submit";
                document.querySelector("#exampleInputEmail1").value = "";
                document.querySelector("#exampleInputPassword1").value = "";
            }
        } catch (error) {
            showToast("An error occurred while logging in.", "error");
            submitButton.disabled = false;
            submitButton.textContent = "Submit";
        }
    });
});
