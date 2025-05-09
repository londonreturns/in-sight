import showToast from "../../modules/toast.js";
import delay from "../../modules/delay.js";
import validateEmail from "../../modules/emailRegex.js";
import validatePassword from "../../modules/passwordRegex.js";

document.querySelector("#registerButton").addEventListener("click", async function (event) {
    event.preventDefault();

    const registerButton = this;

    let email = document.querySelector("#email").value;
    let password = document.querySelector("#password").value;
    let confirmPassword = document.querySelector("#confirmPassword").value;

    if (passwordCompare(password, confirmPassword) === false) {
        return;
    }

    let data = {
        email: email,
        password: password,
        confirmPassword: confirmPassword
    };

    if (validateEmail(email) === false) {
        showToast("Invalid email address.", "error");
        return;
    }else if(validatePassword(password) === false){
        showToast("Password must contain at least 8 characters, one uppercase letter, one lowercase letter, one number, and one special character.", "error");
        return;
    }

    registerButton.disabled = true;
    registerButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Registering...';

    try {
        const response = await fetch("/registerUser", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        const responseData = await response.json();

        if (response.ok) {
            showToast("Redirecting to account verification...", "processing", 999999);
            await delay(1000);

            window.location.replace("/accountVerification");
        } else {
            showToast(responseData.error, "error");
            registerButton.disabled = false;
            registerButton.textContent = "Submit";
        }

    } catch (error) {
        showToast('An error occurred.', "error");
        registerButton.disabled = false;
        registerButton.textContent = "Submit";
    }
});

function passwordCompare(password, confirmPassword) {
    if (password !== confirmPassword) {
        let toastMessage = document.querySelector("#toastMessage");
        let toastElement = new bootstrap.Toast(document.getElementById("liveToast"));
        toastMessage.innerText = 'Passwords do not match.';
        toastElement.show();
        return false;
    }
    return true;
}
