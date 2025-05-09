import showToast from "../../modules/toast.js";

export function setupSummarySection(modalBody, videoId, contentType) {
    checkAndDisplaySummary(modalBody, videoId, contentType);

    const slider = modalBody.querySelector("#thresholdSlider");
    const sliderValue = modalBody.querySelector("#thresholdValue");
    const generateBtn = modalBody.querySelector("#generateSummaryBtn");

    if (slider && sliderValue) {
        slider.addEventListener("input", () => {
            sliderValue.textContent = slider.value;
        });
    }

    if (generateBtn) {
        generateBtn.addEventListener("click", async () => {
            try {
                generateBtn.disabled = true;
                generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
                showToast("Generating summary...", "processing", 999999);

                const threshold = parseFloat(slider?.value || "1.4");

                const response = await fetch(`/generateSummary/${videoId}`, {
                    method: "POST",
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ threshold })
                });

                const result = await response.json();

                if (!response.ok) {
                    showToast(result.error || "Error generating summary", "error");
                    return;
                }

                showToast("Summary generated successfully.", "success");
                displaySummary(modalBody, videoId, contentType, result.summary_text);
            } catch (err) {
                console.error("Error generating summary:", err);
                showToast("An error occurred while generating summary", "error");
            } finally {
                generateBtn.disabled = false;
                generateBtn.textContent = "Generate Summary";
            }
        });
    }
}

function checkAndDisplaySummary(modalBody, videoId, contentType) {
    fetch(`/checkSummaryExists/${videoId}`)
        .then(res => res.json())
        .then(data => {
            if (data.has_summary) {
                displaySummary(modalBody, videoId, contentType);
            }
        })
        .catch(err => {
            console.error("Error checking summary existence:", err);
        });
}

function displaySummary(modalBody, videoId, contentType, summaryText = null) {
    const summarySection = modalBody.querySelector("#summarySection");
    summarySection.classList.remove("d-none");

    const summaryTextContainer = modalBody.querySelector("#summaryTextContainer");
    summaryTextContainer.innerHTML = `<p>${summaryText || "Loading summary text..."}</p>`;

    const summarizedVideoContainer = modalBody.querySelector("#summarizedVideoContainer");
    summarizedVideoContainer.innerHTML = `
        <div class="ratio ratio-16x9">
            <video id="summarizedVideo" controls>
                <source src="/getSummarizedVideo/${videoId}" type="${contentType}">
                Your browser does not support the video tag.
            </video>
        </div>
        <div class="row">
            <div class="col-md-12 text-center">
                <div class="keyboard-controls-box">
                    <p>Keyboard Controls:</p>
                    <div class="btn-group">
                        <span class="btn btn-outline-black">J</span>
                        <span class="btn btn-outline-black" style="margin-left: 10px;">K</span>
                    </div>
                </div>
            </div>
        </div>
    `;

    setupKeyboardShortcuts(document.getElementById("summarizedVideo"));
}

function setupKeyboardShortcuts(videoEl) {
    if (!videoEl) return;

    if (window.videoKeyHandler) {
        document.removeEventListener("keydown", window.videoKeyHandler);
    }

    const handler = (e) => {
        const modal = document.getElementById("dynamicModal");
        if (!modal.classList.contains("show")) return;

        if (["j", "J", "k", "K"].includes(e.key)) {
            e.preventDefault();
        }

        if (e.key.toLowerCase() === "j") {
            videoEl.currentTime = 0;
            videoEl.pause();
        }

        if (e.key.toLowerCase() === "k") {
            videoEl.paused ? videoEl.play() : videoEl.pause();
        }
    };

    window.videoKeyHandler = handler;
    document.addEventListener("keydown", handler);
}