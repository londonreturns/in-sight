import showToast from "./toast.js";

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
            showToast("Registration successful! Redirecting to login...", "processing");
            setTimeout(() => {
                window.location.replace("/loginPage");
            }, 3000); // Redirect after 3 seconds
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