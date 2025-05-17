import showToast from "../../modules/toast.js";

export function setupSummarySection(modalBody, videoId, contentType) {
    checkAndDisplaySummary(modalBody, videoId, contentType);

    const slider = modalBody.querySelector("#videoShortnerSensitivity");
    const sliderValue = modalBody.querySelector("#thresholdValue");
    const keyframeSlider = modalBody.querySelector("#keyframeThreshold");
    const keyframeSliderValue = modalBody.querySelector("#keyframeThresholdValue");
    const generateBtn = modalBody.querySelector("#generateSummaryBtn");

    if (slider && sliderValue) {
        slider.addEventListener("input", () => {
            sliderValue.textContent = slider.value;
        });
    }

    if (keyframeSlider && keyframeSliderValue) {
        keyframeSliderValue.textContent = keyframeSlider.value;
        keyframeSlider.addEventListener("input", () => {
            keyframeSliderValue.textContent = keyframeSlider.value;
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
                    body: JSON.stringify({threshold})
                });

                const result = await response.json();

                if (!response.ok) {
                    showToast(result.error || "Error generating summary", "error");
                    return;
                }

                showToast("Summary generated successfully.", "success");
                displaySummary(modalBody, videoId, contentType);

                const summarizedVideoId = result.summarized_video_id;
                const keyframeThreshold = keyframeSlider ? keyframeSlider.value : 80;
                const summaryTextContainer = modalBody.querySelector("#summaryTextContainer");
                summaryTextContainer.innerHTML = `<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>`;
                try {
                    const textResp = await fetch(`/getSummarizedVideoText/${summarizedVideoId}?keyframe_threshold=${keyframeThreshold}`);
                    const textData = await textResp.json();
                    renderSummaryTabs(summaryTextContainer, textData);
                } catch (err) {
                    summaryTextContainer.innerHTML = `<div class="alert alert-danger">Failed to load summary text.</div>`;
                }

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
        .then(async data => {
            if (data.has_summary) {
                displaySummary(modalBody, videoId, contentType);
                const textResp = await fetch(`/getSummarizedTextFromDB/${videoId}`);
                const textData = await textResp.json();
                let summaryTextContainer = modalBody.querySelector("#summaryTextContainer");
                renderSummaryTabs(summaryTextContainer, textData);
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
    summaryTextContainer.innerHTML = `<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>`;

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


function renderSummaryTabs(container, summaryData) {
    if (!summaryData) {
        container.innerHTML = `<p>No summary data available.</p>`;
        return;
    }

    const frameSummaries = Array.isArray(summaryData.frame_summaries) ? summaryData.frame_summaries : [];
    const overallSummary = summaryData.overall_summary;

    // Build tab headers
    let tabs = `<ul class="nav nav-tabs" id="summaryTabs" role="tablist">`;
    tabs += `<li class="nav-item" role="presentation">
        <button class="nav-link active" id="overall-tab" data-bs-toggle="tab" data-bs-target="#overall" type="button" role="tab" aria-controls="overall" aria-selected="true">Overall Summary</button>
    </li>`;
    frameSummaries.forEach((_, idx) => {
        tabs += `<li class="nav-item" role="presentation">
            <button class="nav-link" id="frame${idx}-tab" data-bs-toggle="tab" data-bs-target="#frame${idx}" type="button" role="tab" aria-controls="frame${idx}" aria-selected="false">Frame ${idx + 1}</button>
        </li>`;
    });
    tabs += `</ul>`;

    // Build tab contents
    let tabContents = `<div class="tab-content mt-3" id="summaryTabsContent">`;
    tabContents += `<div class="tab-pane fade show active" id="overall" role="tabpanel" aria-labelledby="overall-tab">
        <pre style="white-space:pre-wrap;">${escapeHtml(overallSummary?.raw || "No overall summary available.")}</pre>
    </div>`;
    frameSummaries.forEach((frame, idx) => {
        tabContents += `<div class="tab-pane fade" id="frame${idx}" role="tabpanel" aria-labelledby="frame${idx}-tab">
            <pre style="white-space:pre-wrap;">${escapeHtml(frame.raw || "No summary for this frame.")}</pre>
        </div>`;
    });
    tabContents += `</div>`;

    container.innerHTML = tabs + tabContents;
}

// Utility to escape HTML for safe rendering in <pre>
function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/[&<>"']/g, function (m) {
        switch (m) {
            case '&':
                return '&amp;';
            case '<':
                return '&lt;';
            case '>':
                return '&gt;';
            case '"':
                return '&quot;';
            case "'":
                return '&#39;';
            default:
                return m;
        }
    });
}
