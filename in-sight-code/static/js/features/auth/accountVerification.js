import showToast from "../../modules/toast.js";
import delay from "../../modules/delay.js";

export function setupAccountVerificationForm() {
    document.addEventListener("DOMContentLoaded", () => {
        const otpInputs = document.querySelectorAll(".otp-digit");

        otpInputs.forEach((input, index) => {
            input.addEventListener("input", () => {
                input.value = input.value.replace(/\D/, "");
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

        const sendOtpBtn = document.querySelector("#sendOtp");
        if (!sendOtpBtn) return;

        sendOtpBtn.addEventListener("click", async () => {
            const otp = Array.from(otpInputs).map(input => input.value).join("");

            if (otp.length !== 6) {
                showToast("Please enter a valid 6-digit OTP.", "error");
                return;
            }

            sendOtpBtn.classList.add("disabled", "opacity-75");
            sendOtpBtn.style.cursor = "not-allowed";
            sendOtpBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Uploading...
            `;


            try {
                const response = await fetch("/verifyOtp", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ otp })
                });

                const result = await response.json();

                if (response.ok) {
                    showToast("Account verification successful!", "success");
                    await delay(1000);
                    showToast("Redirecting to login...", "processing", 99999);
                    await delay(1000);
                    window.location.replace("/loginPage/successfulRegistration");
                } else {
                    showToast(result.error, "error");
                }
            } catch (error) {
                showToast("An error occurred while verifying the OTP.", "error");
            } finally {
                sendOtpBtn.classList.remove("disabled", "opacity-75");
                sendOtpBtn.style.cursor = "pointer";
                sendOtpBtn.textContent = "Upload";
            }
        });
    });
}

setupAccountVerificationForm();