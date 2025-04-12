import showToast from "./toast.js";
import delay from "./delay.js";

const otpInputs = document.querySelectorAll(".otp-digit");

otpInputs.forEach((input, index) => {
    input.addEventListener("input", () => {
        input.value = input.value.replace(/\D/, ""); // Only allow digits
        if (input.value && index < otpInputs.length - 1) {
            otpInputs[index + 1].focus();
        }
    });

    input.addEventListener("keydown", (e) => {
        if (e.key === "Backspace" && !input.value && index > 0) {
            otpInputs[index - 1].focus();
        }
    });
});

document.querySelector("#sendOtp").addEventListener("click", async function () {
    const otp = Array.from(otpInputs).map(input => input.value).join("");

    if (otp.length !== 6) {
        showToast("Please enter a valid 6-digit OTP.", "error");
        return;
    }

    try {
        const response = await fetch("/verifyOtp", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ otp: otp })
        });

        const responseData = await response.json();

        if (response.ok) {
            showToast("Account verification successful!", "success");
            await delay(1500);

            showToast("Redirecting to login...", "processing");
            await delay(1500);

            window.location.replace("/loginPage/successfulRegistration");
        } else {
            showToast(responseData.error, "error");
        }
    } catch (error) {
        showToast("An error occurred while verifying the OTP.", "error");
    }
});