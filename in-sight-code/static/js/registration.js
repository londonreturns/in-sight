import showToast from "./toast.js";
import delay from "./delay.js";
import validateEmail from "./emailRegex.js";
import validatePassword from "./passwordRegex.js";

document.querySelector("#registerButton").addEventListener("click", async function (event) {
    event.preventDefault();

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
        }

    } catch (error) {
        showToast('An error occurred.', "error");
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